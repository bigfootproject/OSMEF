#define _GNU_SOURCE

#include <stdio.h>
#include <pthread.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <errno.h>
#include <signal.h>
#include <arpa/inet.h>
#include <semaphore.h>
#include <sys/time.h>
#include <assert.h>
#include <sys/resource.h>

#define CMD_LISTEN_PORT 2333
#define DATA_CHUNK_SIZE 65536
#define CMD_DATA_LEN 2048
#define NAME_LEN 16
#define RESULT_PFX "*RES* "

#define MSG_EXIT    0
#define MSG_INIT    1
#define MSG_NODES   2
#define MSG_MAPPER  3
#define MSG_REDUCER 4
#define MSG_START   5

FILE* logfp;

struct msg {
	unsigned int type;
	char data[CMD_DATA_LEN];
};

struct reply {
	char data[CMD_DATA_LEN];
};

struct mapper_args {
	int num_concurrent_conn;
	int num_reducers;
	char** reducer_names;
	ssize_t* reducer_sizes;
	unsigned short int port;
	char name[NAME_LEN];
	pthread_barrier_t ready;
};

struct mapper_reducer_info {
	char* data;
	ssize_t size;
	char* name;
};

struct mapper_conn_thread {
	int* free;
	int running;
	int exit;
	int s;
	sem_t* finish_sem;
	sem_t start_sem;
	pthread_t th;
	char name[NAME_LEN];
	struct mapper_reducer_info* reducer_info;
	struct measurement* meas;
};

struct map_address {
	unsigned short int port;
	struct in_addr addr;
	char name[NAME_LEN];
};

struct reducer_args {
	int num_concurrent_conn;
	int num_mappers;
	char name[NAME_LEN];
	struct map_address* addresses;
	pthread_barrier_t ready;
	pthread_barrier_t* start;
};

struct reducer_connection_args {
	struct sockaddr_in addr;
	char* mapper_name;
};

struct reducer_conn_thread {
	struct reducer_connection_args* mappers;
	int num_mappers;
	pthread_t th;
	char* reducer_name;
	int id;
};

struct measurement {
	int empty;
	char th_name[NAME_LEN];
	char dest_name[NAME_LEN];
	long long time_start_ms;
	unsigned int time_elapsed;
	unsigned int thread_time;
	unsigned long int bytes_moved;
};

struct results {
	struct measurement** meas;
	int count;
	char th_name[NAME_LEN];
};

long long get_wall_time_ms()
{
	struct timeval t;
	gettimeofday(&t, NULL);
	return (((long long)t.tv_sec*1000000) + t.tv_usec)/1000;
}

long long get_timestamp_ms()
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (((long long)ts.tv_sec*1000000000) + ts.tv_nsec)/1000000;
}

unsigned int get_thread_time_ms()
{
	struct timespec ts;
        clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
	return (((long long)ts.tv_sec*1000000000) + ts.tv_nsec)/1000000;
}

void check_alloc(void* mem, char* name)
{
	if (mem == NULL) {
		fprintf(logfp, "(%s) Cannot allocate enough memory, crashing...\n", name);
		abort();
	}
}

int listen_socket(const unsigned short int port)
{
	int s, ret;
	struct sockaddr_in local_addr;

	s = socket(AF_INET, SOCK_STREAM, 0);
	ret = 1;
	setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &ret, sizeof(int));
	memset(&local_addr, 0, sizeof(struct sockaddr_in));

	local_addr.sin_family = AF_INET;
	local_addr.sin_port = htons(port);
	local_addr.sin_addr.s_addr = INADDR_ANY;
	ret = bind(s, (struct sockaddr*)&local_addr, sizeof(struct sockaddr_in));
	if (ret) {
		fprintf(logfp, "bind error to port %d: %s\n", port, strerror(errno));
		return -1;
	}
	listen(s, 40);
	return s;
}

struct msg* receive_command(int s)
{
	ssize_t ret;
	struct msg* tmp = calloc(1, sizeof(struct msg));
	check_alloc(tmp, "receive_command_1");
	char buf[CMD_DATA_LEN], *aux;
	ret = recv(s, buf, CMD_DATA_LEN, MSG_WAITALL);
	if (ret != CMD_DATA_LEN) {
		fprintf(logfp, "Received only %ld bytes in command message\n", ret);
		tmp->type = MSG_EXIT;
	}
	buf[CMD_DATA_LEN-1] = '\0';
	aux = strtok(buf, "|");
	tmp->type = atol(aux);
	aux = strtok(NULL, "|");
	if (aux != NULL) {
		strcpy(tmp->data, aux);
	}
	return tmp;
}

void send_reply(int s, struct reply* rep)
{
	send(s, rep, sizeof(struct reply), 0);
}

void send_done(int s)
{
	struct reply rep;
	memset(&rep, 0, sizeof(struct reply));
	snprintf(rep.data, CMD_DATA_LEN, "DONE");
	send_reply(s, &rep);
}

void* mapper_connection(void* vargs)
{
	struct mapper_conn_thread* args = vargs;
	ssize_t bytes_sent = 0;
	struct measurement* result = NULL;
	long long time_s, time_e;
	char end_char = 0xFF;

	while (1) {
		fprintf(logfp, "(%s) waiting for something to do...\n", args->name);
		sem_wait(&args->start_sem);

		if (args->exit) {
			fprintf(logfp, "(%s) got exit signal\n", args->name);
			assert(result != NULL);
			return result; // Terminates the thread
		}

		assert(args->s >= 0);
		assert(args->meas == NULL);
		result = malloc(sizeof(struct measurement));
		check_alloc(result, "mapper_connection_1");
		args->meas = result;
		strncpy(result->th_name, args->name, NAME_LEN);
		strncpy(result->dest_name, args->reducer_info->name, NAME_LEN);

		fprintf(logfp, "(%s) connection started, have to send %ld bytes to %s\n", args->name, args->reducer_info->size, args->reducer_info->name);

		result->time_start_ms = get_wall_time_ms();
		time_s = get_timestamp_ms();

		while (bytes_sent < args->reducer_info->size) {
			int ret, chunk_len;

			if (args->reducer_info->size - bytes_sent < DATA_CHUNK_SIZE) {
				chunk_len = args->reducer_info->size - bytes_sent;
			} else {
				chunk_len = DATA_CHUNK_SIZE;
			}
			ret = send(args->s, args->reducer_info->data, chunk_len, 0);
			if (ret > 0) {
				bytes_sent += ret;
			} else {
				fprintf(logfp, "(%s) send error: %s\n", args->name, strerror(errno));
			}
		}

		send(args->s, &end_char, 1, 0);

		time_e = get_timestamp_ms();

		result->time_elapsed = time_e - time_s;
		result->bytes_moved = bytes_sent + 1;
		result->thread_time = get_thread_time_ms();

		close(args->s);
		args->s = -1;
		fprintf(logfp, "(%s) all data sent, closing connection to %s\n", args->name, args->reducer_info->name);

		*(args->free) = 1;
		sem_post(args->finish_sem);
	}
	assert(1); // Will never reach
	return NULL;
}

void* mapper(void* vargs)
{
	int s, ret, i, remaining, free_result_idx = 0;
	struct mapper_args* args = vargs;
	struct mapper_reducer_info* reducer_list;
	struct mapper_conn_thread* conn_threads;
	struct results *results;
	sem_t th_completion_sem;
	int* threads_free;
	char* data;

	fprintf(logfp, "(%s) Mapper thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	sem_init(&th_completion_sem, 0, args->num_concurrent_conn);

	/* the data the mapper will send to every reducer */
	data = malloc(DATA_CHUNK_SIZE * sizeof(char));
	check_alloc(data, "mapper_1");
	for (i = 0; i < DATA_CHUNK_SIZE; i++) {
		data[i] = i & 0x7F;
	}

	/* vector threads use to signal they are free to do more work */
	threads_free = malloc(args->num_concurrent_conn * sizeof(int));
	check_alloc(threads_free, "mapper_2");
	for (i = 0; i < args->num_concurrent_conn; i++) {
		threads_free[i] = 1;
	}

	/* every reducer that will contact this mapper is in this list */
	reducer_list = malloc(args->num_reducers * sizeof(struct mapper_reducer_info));
	check_alloc(reducer_list, "mapper_3");
	for (i = 0; i < args->num_reducers; i++) {
		reducer_list[i].data = data;
		reducer_list[i].size = args->reducer_sizes[i];
		reducer_list[i].name = args->reducer_names[i];
	}

	/* each conn thread has a struct here */
	conn_threads = malloc(args->num_concurrent_conn * sizeof(struct mapper_conn_thread));
	check_alloc(conn_threads, "mapper_4");
	for (i = 0; i < args->num_concurrent_conn; i++) {
		conn_threads[i].free = &(threads_free[i]);
		conn_threads[i].running = 0;
		conn_threads[i].exit = 0;
		conn_threads[i].s = -1;
		conn_threads[i].finish_sem = &th_completion_sem;
		snprintf(conn_threads[i].name, NAME_LEN, "%s:th%d", args->name, i);
		conn_threads[i].meas = NULL;
	}

	fprintf(logfp, "(%s) Binding to port %d\n", args->name, args->port);
	s = listen_socket(args->port);

	remaining = args->num_reducers;

	results = malloc(sizeof(struct results));
	check_alloc(results, "mapper_5");
	results->meas = calloc(args->num_reducers, sizeof(struct measurement*));
	check_alloc(results->meas, "mapper_6");
	results->count = args->num_reducers;
	strncpy(results->th_name, args->name, NAME_LEN);

	// We are ready to start
	pthread_barrier_wait(&args->ready);
	fprintf(logfp, "(%s) Got START signal\n", args->name);

	while (remaining > 0) {
		struct sockaddr_in peer_addr;
		int peer_s, reducer_idx, thread_idx;
		char peer_name[NAME_LEN];
		socklen_t peer_addr_len;

		sem_wait(&th_completion_sem);

		// Look for a free thread
		thread_idx = -1;
		for (i = 0; i < args->num_concurrent_conn; i++) {
			if (threads_free[i]) {
				thread_idx = i;
				break;
			}
		}
		assert(thread_idx != -1);

		if (!conn_threads[thread_idx].running) {
			conn_threads[thread_idx].running = 1;
			sem_init(&conn_threads[i].start_sem, 0, 0);
			pthread_create(&conn_threads[thread_idx].th, NULL, mapper_connection, &(conn_threads[thread_idx]));
			fprintf(logfp, "(%s) new thread ID: %s\n", args->name, conn_threads[thread_idx].name);
		} else {
			if (conn_threads[i].meas != NULL) {
				results->meas[free_result_idx] = conn_threads[i].meas;
				free_result_idx++;
				assert(free_result_idx < args->num_reducers);
				conn_threads[i].meas = NULL;
			}
		}

		peer_addr_len = sizeof(struct sockaddr_in);
		peer_s = accept(s, (struct sockaddr*)&peer_addr, &peer_addr_len);
		if (peer_s < 0) {
			fprintf(logfp, "(%s) accept error: %s\n", args->name, strerror(errno));
			continue;
		}

		ret = recv(peer_s, peer_name, NAME_LEN, 0);
		if (ret < NAME_LEN) {
			fprintf(logfp, "(%s) --> Short recv while reading the reducer name\n", args->name);
			if (ret < 0) {
				fprintf(logfp, "(%s) recv error: %s\n", args->name, strerror(errno));
			}
		}
		// Look for the data for this reducer
		reducer_idx = -1;
		for (i = 0; i < args->num_reducers; i++) {
			if (strncmp(peer_name, reducer_list[i].name, NAME_LEN) == 0) {
				reducer_idx = i;
				break;
			}
		}
		if (reducer_idx == -1) {
			fprintf(logfp, "(%s) Got connection from unknown reducer '%s'\n", args->name, peer_name);
			close(peer_s);
			continue;
		}

		fprintf(logfp, "(%s) Got connection from reducer %s\n", args->name, peer_name);
		remaining--;

		threads_free[thread_idx] = 0;
		conn_threads[thread_idx].s = peer_s;
		conn_threads[thread_idx].reducer_info = &(reducer_list[i]);
		sem_post(&conn_threads[thread_idx].start_sem);
	}

	fprintf(logfp, "(%s) All reducers connected, waiting for threads to terminate\n", args->name);
	// Steal all the semaphore depth and then wait all threads to finish
	while(1) {
		int free_count;
		fprintf(logfp, "(%s) waiting on semaphore\n", args->name);
		sem_wait(&th_completion_sem);
		free_count = 0;
		for (i = 0; i < args->num_concurrent_conn; i++) {
			free_count += threads_free[i];
		}
		if (free_count == args->num_concurrent_conn) {
			break;
		}
		fprintf(logfp, "(%s) -> %d threads still running\n", args->name, args->num_concurrent_conn - free_count);
	}
	// Signal all threads to exit when ready
	fprintf(logfp, "(%s) Sending exit signal to all threads\n", args->name);
	for (i = 0; i < args->num_concurrent_conn; i++) {
		if (conn_threads[i].running) {
			conn_threads[i].exit = 1;
			sem_post(&conn_threads[i].start_sem);
		}
	}

	// Join all threads
	for (i = 0; i < args->num_concurrent_conn; i++) {
		if (conn_threads[i].running) {
			void* meas;
			pthread_join(conn_threads[i].th, &meas);
			fprintf(logfp, "(%s) thread %s joined\n", args->name, conn_threads[i].name);
			results->meas[free_result_idx] = meas;
			free_result_idx++;
			sem_destroy(&conn_threads[i].start_sem);
		}
	}
	assert(free_result_idx == args->num_reducers);

	sem_destroy(&th_completion_sem);
	free(data);
	free(conn_threads);
	free(threads_free);
	free(reducer_list);
	fprintf(logfp, "(%s) all done, exiting\n", args->name);
	free(args->reducer_sizes);
	for (i = 0; i < args->num_reducers; i++) {
		free(args->reducer_names[i]);
	}
	free(args->reducer_names);
	free(args);
	return results;
}

void new_mapper(pthread_t *node, int id, char* data)
{
	char* aux = strtok(data, ",");
	ssize_t i;
	struct mapper_args* args;

	args = malloc(sizeof(struct mapper_args));
	check_alloc(args, "new_mapper_1");

	pthread_barrier_init(&args->ready, NULL, 2);
	strncpy(args->name, aux, NAME_LEN);
	aux = strtok(NULL, ",");
	args->num_concurrent_conn = atol(aux);
	aux = strtok(NULL, ",");
	args->port = atol(aux);
	fprintf(logfp, "CONF: mapper on port %d\n", args->port);
	aux = strtok(NULL, ",");
	args->num_reducers = atol(aux);
	args->reducer_sizes = malloc(args->num_reducers * sizeof(ssize_t));
	check_alloc(args->reducer_sizes, "new_mapper_2");
	args->reducer_names = malloc(args->num_reducers * sizeof(ssize_t));
	check_alloc(args->reducer_names, "new_mapper_3");
	fprintf(logfp, "CONF: -> will serve %d reducers\n", args->num_reducers);
	for (i = 0; i < args->num_reducers; i++) {
		args->reducer_names[i] = malloc(NAME_LEN * sizeof(char));
		check_alloc(args->reducer_names[i], "new_mapper_4");
		aux = strtok(NULL, ",");
		strncpy(args->reducer_names[i], aux, NAME_LEN);
		aux = strtok(NULL, ",");
		args->reducer_sizes[i] = atoll(aux);
//		fprintf(logfp, "(%s) -> reducer data size %ld\n", args->name, args->reducer_sizes[i]);
	}

	pthread_create(node, NULL, mapper, args);
	pthread_setname_np(*node, args->name);
	fprintf(logfp, "(main) new thread ID: %s\n", args->name);

	pthread_barrier_wait(&args->ready);
	pthread_barrier_destroy(&args->ready); // Will not be used again
}

void* reducer_connection(void* varg)
{
	struct reducer_conn_thread* arg = varg;
	int ret, i;
	char buf[DATA_CHUNK_SIZE];
	char conn_name[NAME_LEN];
	char my_name[NAME_LEN];
	ssize_t data_recv_size;
	char* end_character = NULL;
	struct measurement** results;
	long long time_s, time_e;

	results = malloc(arg->num_mappers * sizeof(struct measurement*));
	check_alloc(results, "reducer_connection_1");
	for (i = 0; i < arg->num_mappers; i++) {
		results[i] = malloc(sizeof(struct measurement));
		results[i]->empty = 1;
	}
	snprintf(my_name, NAME_LEN, "%s:th%d", arg->reducer_name, arg->id);


	for (i = 0; i < arg->num_mappers; i++) {
		int s = socket(AF_INET, SOCK_STREAM, 0);
		// This connection name
		snprintf(conn_name, NAME_LEN, "%s:%d", my_name, i);
		strncpy(results[i]->th_name, conn_name, NAME_LEN);
		strncpy(results[i]->dest_name, arg->mappers[i].mapper_name, NAME_LEN);
		// Begin measurements
		results[i]->time_start_ms = get_wall_time_ms();
		time_s = get_timestamp_ms();
		// Connect
		ret = connect(s, &arg->mappers[i].addr, sizeof(struct sockaddr_in));
		if (ret) {
			fprintf(logfp, "(%s) Connection error with mapper %s\n", conn_name, arg->mappers[i].mapper_name);
			fprintf(logfp, "(%s) -> error was: %s\n", conn_name, strerror(errno)); // not threadsafe
			continue; // try to continue with the next mapper
		} else {
			fprintf(logfp, "(%s) Connection established with mapper %s\n", conn_name, arg->mappers[i].mapper_name);
		}
		// Send reducer name and receive the data, looking for the end character
		ret = send(s, arg->reducer_name, NAME_LEN, 0);
		if (ret) {
			fprintf(logfp, "(%s) -> error sending name: %s\n", conn_name, strerror(errno)); // not threadsafe
		}
		data_recv_size = 0;
		do {
			ret = recv(s, buf, DATA_CHUNK_SIZE, 0);
			if (ret) {
				fprintf(logfp, "(%s) -> error in recv: %s\n", conn_name, strerror(errno)); // not threadsafe
			}
			data_recv_size += ret;
			end_character = memchr(buf, 0xFF, ret);
		} while (end_character == NULL);

		close(s);

		// End measurements
		time_e = get_timestamp_ms();
		results[i]->time_elapsed = time_e - time_s;
		results[i]->bytes_moved = data_recv_size;
		results[i]->thread_time = get_thread_time_ms();
		results[i]->empty = 0;

		fprintf(logfp, "(%s) Connection to %s finished, received %ld bytes\n", conn_name, arg->mappers[i].mapper_name, data_recv_size);
	}

	fprintf(logfp, "(%s) Got data from all mappers, this reducer connection has finished.\n", my_name);

	return results;
}

void* reducer(void* vargs)
{
	struct reducer_args* args = vargs;
	struct reducer_conn_thread* conns;
	struct results* results;
	int i, j, remaining = 0, map_per_conn_count;
	int cur_conn = 0, cur_map = 0;
	struct measurement** free_measurement;

	fprintf(logfp, "(%s) Reducer thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	conns = malloc(args->num_concurrent_conn * sizeof(struct reducer_conn_thread));
	check_alloc(conns, "reducer_2");

	map_per_conn_count = (args->num_mappers / args->num_concurrent_conn) + 1;
	
	for (i = 0; i < args->num_concurrent_conn; i++) {
		conns[i].mappers = calloc(map_per_conn_count, sizeof(struct reducer_connection_args));
		check_alloc(conns[i].mappers, "reducer_3");
		conns[i].num_mappers = 0;
		conns[i].reducer_name = args->name;
		conns[i].id = i;
	}
	for (j = 0; j < args->num_mappers; j++) {
		conns[cur_conn].mappers[cur_map].addr.sin_family = AF_INET;
		conns[cur_conn].mappers[cur_map].addr.sin_port = htons(args->addresses[j].port);
		conns[cur_conn].mappers[cur_map].addr.sin_addr = args->addresses[j].addr;
		conns[cur_conn].mappers[cur_map].mapper_name = args->addresses[j].name;
		conns[cur_conn].num_mappers++;
		fprintf(stderr, "(%s) th%d will connect to %s in position %d\n", args->name, cur_conn, conns[cur_conn].mappers[cur_map].mapper_name, cur_map);
		cur_conn++;
		if ((cur_conn % args->num_concurrent_conn) == 0) {
			cur_conn = 0;
			cur_map++;
		}
	}

	results = malloc(sizeof(struct results));
	check_alloc(results, "reducer_3");
	results->count = 0;
	results->meas = calloc(args->num_mappers, sizeof(struct measurement*));
	check_alloc(results->meas, "reducer_4");
	strncpy(results->th_name, args->name, NAME_LEN);
	free_measurement = results->meas;

	// Signal that we are ready
	pthread_barrier_wait(&args->ready);
	fprintf(logfp, "(%s) waiting for START message\n", args->name);
	// Wait for start message
	pthread_barrier_wait(args->start);
	fprintf(logfp, "(%s) got START message\n", args->name);

	// Start all conn threads and wait for their termination
	for (i = 0; i < args->num_concurrent_conn; i++) {
		if (conns[i].num_mappers > 0) {
			pthread_create(&conns[i].th, NULL, reducer_connection, &conns[i]);
			fprintf(logfp, "(%s) new thread ID: th%d\n", args->name, conns[i].id);
			remaining++;
		}
	}

	for (i = 0; i < args->num_concurrent_conn; i++) {
		if (conns[i].num_mappers > 0) {
			void* result;
			struct measurement** r_meas;
			pthread_join(conns[i].th, &result);
			assert(result != NULL);
			remaining--;
			fprintf(logfp, "(%s) thread th%d joined, %d connection threads remaining\n", args->name, conns[i].id, remaining);
			r_meas = result;
			for (j = 0; j < conns[i].num_mappers; j++) {
				if (!r_meas[j]->empty) {
					*(free_measurement) = r_meas[j];
					results->count++;
					free_measurement++;
				} else {
					free(r_meas[j]);
				}
			}
			free(result); // Free the list of pointers
		}
	}

	assert(remaining == 0);
	for (i = 0; i < args->num_concurrent_conn; i++) {
		free(conns[i].mappers);
	}
	free(conns);
	fprintf(logfp, "(%s) all done, exiting\n", args->name);
	free(args->addresses);
	free(args);
	return results;
}

void new_reducer(pthread_t *node, int id, char* data, pthread_barrier_t* barr)
{
	char* aux = strtok(data, ",");
	ssize_t i;
	int ret;
	struct reducer_args* reducer_args;

	reducer_args = malloc(sizeof(struct reducer_args));
	check_alloc(reducer_args, "reducer_connection_1");

	pthread_barrier_init(&reducer_args->ready, NULL, 2);

	/* use name from strtok */
	strncpy(reducer_args->name, aux, NAME_LEN);
	fprintf(logfp, "CONF: reducer\n");

	/* concurrent connections */
	aux = strtok(NULL, ",");
	reducer_args->num_concurrent_conn = atol(aux);

	/* number of mappers */
	aux = strtok(NULL, ",");
	reducer_args->num_mappers = atol(aux);

	reducer_args->addresses = calloc(reducer_args->num_mappers, sizeof(struct map_address));
	check_alloc(reducer_args->addresses, "reducer_connection_2");

	for (i = 0; i < reducer_args->num_mappers; i++) {
		/* mapper name */
		aux = strtok(NULL, ",");
		strncpy(reducer_args->addresses[i].name, aux, NAME_LEN);
		/* mapper port */
		aux = strtok(NULL, ",");
		reducer_args->addresses[i].port = atol(aux);
		/* mapper ip address */
		aux = strtok(NULL, ",");
		ret = inet_pton(AF_INET, aux, &reducer_args->addresses[i].addr);
		if (!ret) {
			fprintf(logfp, "CONF: -> failed to parse IP address '%s' for reducer %s\n", aux, reducer_args->name);
			continue;
		}
	}
	reducer_args->start = barr;

	pthread_create(node, NULL, reducer, reducer_args);
	pthread_setname_np(*node, reducer_args->name);
	fprintf(logfp, "(main) new thread ID: %s\n", reducer_args->name);

	pthread_barrier_wait(&reducer_args->ready);
	pthread_barrier_destroy(&reducer_args->ready); // Will not be used again
}

void send_results(struct results* results)
{
	int i;

	fprintf(logfp, RESULT_PFX "start node %s\n", results->th_name);
	for (i = 0; i < results->count; i++) {
		fprintf(logfp, RESULT_PFX "%s,%s,%lld,%d,%d,%ld\n",
				results->meas[i]->th_name,
				results->meas[i]->dest_name,
				results->meas[i]->time_start_ms,
				results->meas[i]->time_elapsed,
				results->meas[i]->thread_time,
				results->meas[i]->bytes_moved);
	}
	fprintf(logfp, RESULT_PFX "end node %s\n", results->th_name);
}

void wait_for_results(int num_nodes, pthread_t* nodes)
{
	int i, j;
	void* retval;
	struct results* results;

	for (i = 0; i < num_nodes; i++) {
		char thname[16];
		pthread_getname_np(nodes[i], thname, 16);
		fprintf(logfp, "(main) Waiting for thread %s to join...\n", thname);
		pthread_join(nodes[i], &retval);
		results = retval;
		send_results(results);
		fprintf(logfp, "(main) Thread %s joined\n", results->th_name);
		for (j = 0; j < results->count; j++) {
			free(results->meas[j]);
		}
		free(results->meas);
		free(results);
	}
}

void command_thread()
{
	int s;
	struct sockaddr_in peer_addr;
	int exit = 0, peer_s, node_count = 0;
	int num_nodes = 0, num_mappers = 0, num_reducers = 0;
	socklen_t peer_addr_len = sizeof(struct sockaddr_in);
	pthread_t* nodes = NULL;
	pthread_barrier_t start_barr;

	fprintf(logfp, "Listening for command connection\n");
	s = listen_socket(CMD_LISTEN_PORT);
	peer_s = accept(s, (struct sockaddr*)&peer_addr, &peer_addr_len);

	while (!exit) {
		struct msg *cmd = receive_command(peer_s);
		char* tmp;
		switch(cmd->type) {
			case MSG_EXIT:
				exit = 1;
				break;
			case MSG_INIT:
				num_nodes = 0;
				node_count = 0;
				break;
			case MSG_NODES:
				tmp = strtok(cmd->data, ",");
				num_mappers = atol(tmp);
				tmp = strtok(NULL, ",");
				num_reducers = atol(tmp);
				num_nodes = num_mappers + num_reducers;
				nodes = malloc(num_nodes * sizeof(pthread_t));
				check_alloc(nodes, "command_thread_1");
				pthread_barrier_init(&start_barr, NULL, num_reducers + 1);
				send_done(peer_s);
				break;
			case MSG_MAPPER:
				new_mapper(&nodes[node_count], node_count, cmd->data);
				node_count++;
				send_done(peer_s);
				break;
			case MSG_REDUCER:
				new_reducer(&nodes[node_count], node_count, cmd->data, &start_barr);
				node_count++;
				send_done(peer_s);
				break;
			case MSG_START:
				pthread_barrier_wait(&start_barr);
				wait_for_results(num_nodes, nodes);
				free(nodes);
				nodes = NULL;
				send_done(peer_s);
				break;
			default:
				fprintf(logfp, "Unknown command received: %d\n", cmd->type);
				break;
		}
		free(cmd);
	}
	if (nodes != NULL) {
		free(nodes);
	}
	fprintf(logfp, "Worker terminating correctly\n");
}

void end()
{
	fflush(logfp);
	fclose(logfp);
}

void end_sig(int sig)
{
	fprintf(logfp, "Worker terminating by signal\n");
	end();
}

int main(int argc, char *argv[])
{
	struct rlimit core_limits;

	if (argc == 1) {
		logfp = fopen("/tmp/osmef_worker.log", "w");
	} else {
		logfp = stderr;
	}
	setbuf(logfp, NULL);
	atexit(end);
	signal(SIGTERM, end_sig);
	signal(SIGQUIT, end_sig);
	fprintf(logfp, "OSMeF worker starting\n");

	fprintf(logfp, "Enabling core dumping\n");
	core_limits.rlim_cur = core_limits.rlim_max = RLIM_INFINITY;
	setrlimit(RLIMIT_CORE, &core_limits);

	if (argc == 1)
		daemon(1, 0);
	command_thread();

	return 0;
}

