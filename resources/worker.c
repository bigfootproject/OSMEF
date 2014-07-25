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

struct mapper_connection_args {
	int s;
	ssize_t size;
	char data[DATA_CHUNK_SIZE];
	int id;
	char* reducer_name;
	char name[NAME_LEN];
	sem_t* finish_sem;
};

struct mapper_conn_thread {
	int free;
	int joined;
	pthread_t th;
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
	int id;
	char* mapper_name;
	char* name;
	sem_t* finish_sem;
};

struct reducer_conn_thread {
	int free;
	pthread_t th;
};

struct measurement {
	char th_name[NAME_LEN];
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
	struct mapper_connection_args* args = vargs;
	ssize_t bytes_sent = 0;
	struct measurement* result;
	long long time_s, time_e;

	result = malloc(sizeof(struct measurement));
	check_alloc(result, "mapper_connection_1");
	strncpy(result->th_name, args->name, NAME_LEN);

	fprintf(logfp, "(%s) thread started, have to send %ld bytes\n", args->name, args->size);

	result->time_start_ms = get_wall_time_ms();
	time_s = get_timestamp_ms();

	while (bytes_sent < args->size) {
		int ret, chunk_len;

		if (args->size - bytes_sent < DATA_CHUNK_SIZE) {
			chunk_len = args->size - bytes_sent;
		} else {
			chunk_len = DATA_CHUNK_SIZE;
		}
		ret = send(args->s, args->data, chunk_len, 0);
		if (ret > 0) {
			bytes_sent += ret;
		}
	}

	args->data[0] = 0xFF;
	send(args->s, args->data, 1, 0);

	time_e = get_timestamp_ms();

	result->time_elapsed = time_e - time_s;
	result->bytes_moved = bytes_sent + 1;
	result->thread_time = get_thread_time_ms();

	close(args->s);
	fprintf(logfp, "(%s) all data sent, thread exiting\n", args->name);
	sem_post(args->finish_sem);
	return result;
}

void* mapper(void* vargs)
{
	int s, ret, i, current_conn_count = 0, remaining, to_start;
	struct mapper_args* args = vargs;
	struct mapper_connection_args** reducers;
	struct mapper_conn_thread* conn_threads;
	sem_t th_completion_sem;
	struct results *results;

	fprintf(logfp, "(%s) Mapper thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	reducers = malloc(args->num_reducers * sizeof(struct mapper_connection_args*));
	check_alloc(reducers, "mapper_1");
	for (i = 0; i < args->num_reducers; i++) {
		int j;
//		fprintf(logfp, "(%s) Allocating data for reducer %s\n", args->name, args->reducer_names[i]);
		reducers[i] = malloc(sizeof(struct mapper_connection_args));
		check_alloc(reducers[i], "mapper_2");
		reducers[i]->size = args->reducer_sizes[i];
		reducers[i]->reducer_name = args->reducer_names[i];
		reducers[i]->finish_sem = &th_completion_sem;
		for (j = 0; j < DATA_CHUNK_SIZE; j++) {
			reducers[i]->data[j] = j & 0x7F;
		}
	}

	conn_threads = malloc(args->num_concurrent_conn * sizeof(struct mapper_conn_thread));
	check_alloc(conn_threads, "mapper_4");
	for (i = 0; i < args->num_concurrent_conn; i++) {
		conn_threads[i].free = 1;
		conn_threads[i].joined = 1;
	}

	fprintf(logfp, "(%s) Binding to port %d\n", args->name, args->port);
	s = listen_socket(args->port);

	sem_init(&th_completion_sem, 0, 0);

	to_start = remaining = args->num_reducers;

	results = malloc(sizeof(struct results));
	check_alloc(results, "mapper_5");
	results->meas = calloc(args->num_reducers, sizeof(struct measurement*));
	check_alloc(results->meas, "mapper_6");
	results->count = args->num_reducers;
	strncpy(results->th_name, args->name, NAME_LEN);

	// We are ready to start
	pthread_barrier_wait(&args->ready);

	while (remaining > 0) {
		struct sockaddr_in peer_addr;
		int peer_s, found = -1;
		char peer_name[NAME_LEN];
		socklen_t peer_addr_len;
//		fprintf(logfp, "(%s) Current connection count: %d\n", args->name, current_conn_count);

		if (to_start > 0 && current_conn_count < args->num_concurrent_conn) {
			peer_addr_len = sizeof(struct sockaddr_in);
			peer_s = accept(s, (struct sockaddr*)&peer_addr, &peer_addr_len);
			if (peer_s < 0) {
				fprintf(logfp, "(%s) accept error: %s\n", args->name, strerror(errno));
				continue;
			}

			to_start--;
			current_conn_count++;
			ret = recv(peer_s, peer_name, NAME_LEN, 0);
			if (ret < NAME_LEN) {
				fprintf(logfp, "(%s) --> Short recv while reading the reducer name\n", args->name);
				if (ret < 0) {
					fprintf(logfp, "(%s) recv error: %s\n", args->name, strerror(errno));
				}
			}
			// Look for the data for this reducer
			for (i = 0; i < args->num_reducers; i++) {
				if (strncmp(peer_name, reducers[i]->reducer_name, NAME_LEN) == 0) {
					found = i;
					break;
				}
			}
			if (found < 0) {
				fprintf(logfp, "(%s) Got connection from unknown reducer '%s'\n", args->name, peer_name);
				close(peer_s);
				continue;
			}

			fprintf(logfp, "(%s) Got connection from reducer %s\n", args->name, peer_name);
			// Look for a free slot
			for (i = 0; i < args->num_concurrent_conn; i++) {
				if (conn_threads[i].free) {
					reducers[found]->s = peer_s;
					snprintf(reducers[found]->name, NAME_LEN, "%s:%d", args->name, found);
					conn_threads[i].free = 0;
					conn_threads[i].joined = 0;
					pthread_create(&conn_threads[found].th, NULL, mapper_connection, reducers[found]);
					pthread_setname_np(conn_threads[found].th, reducers[found]->name);
					fprintf(logfp, "(%s) new thread ID: %lx\n", reducers[found]->name, conn_threads[found].th);
					break;
				}
			}
		} else {
			void* result;
			fprintf(logfp, "(%s) Waiting for a thread to finish\n", args->name);
			sem_wait(&th_completion_sem);
			i = 0;
			do {
				result = NULL;
				while (conn_threads[i].free) { // There is at least one that is not free
					i = (i + 1) % args->num_concurrent_conn;
				}
				if (!conn_threads[i].joined) {
					ret = pthread_join(conn_threads[i].th, &result);
					assert(ret == 0);
					conn_threads[i].joined = 1;
				}
			} while (ret != 0);
			assert(result != NULL);
			current_conn_count--;
			remaining--;
			conn_threads[i].free = 1;
			i = 0;
			while (results->meas[i] != NULL) {
				i++;
			}
			results->meas[i] = result;
			fprintf(logfp, "(%s) thread %d (%lx) joined, %d connections remaining\n", args->name, i, conn_threads[i].th, remaining);
		}
	}

	sem_destroy(&th_completion_sem);
	free(conn_threads);
	for (i = 0; i < args->num_reducers; i++) {
		free(reducers[i]);
	}
	free(reducers);
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
	fprintf(logfp, "(%s) New mapper on port %d\n", args->name, args->port);
	aux = strtok(NULL, ",");
	args->num_reducers = atol(aux);
	args->reducer_sizes = malloc(args->num_reducers * sizeof(ssize_t));
	check_alloc(args->reducer_sizes, "new_mapper_2");
	args->reducer_names = malloc(args->num_reducers * sizeof(ssize_t));
	check_alloc(args->reducer_names, "new_mapper_3");
	fprintf(logfp, "(%s) -> will serve %d reducers\n", args->name, args->num_reducers);
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
	fprintf(logfp, "(%s) new thread ID: %lx\n", args->name, *node);

	pthread_barrier_wait(&args->ready);
	pthread_barrier_destroy(&args->ready); // Will not be used again
}

void* reducer_connection(void* vargs)
{
	struct reducer_connection_args* args = vargs;
	int s, ret;
	char buf[DATA_CHUNK_SIZE];
	char my_name[NAME_LEN];
	ssize_t data_recv_size = 0;
	char* end_character = NULL;
	struct measurement* result;
	long long time_s, time_e;

	result = malloc(sizeof(struct measurement));
	check_alloc(result, "reducer_connection_1");

	snprintf(my_name, NAME_LEN, "%s:%d", args->name, args->id);
	strncpy(result->th_name, my_name, NAME_LEN);

	s = socket(AF_INET, SOCK_STREAM, 0);

	result->time_start_ms = get_wall_time_ms();
	time_s = get_timestamp_ms();

	ret = connect(s, &args->addr, sizeof(struct sockaddr_in));
	if (ret) {
		fprintf(logfp, "Connection error\n");
	}

	fprintf(logfp, "(%s) Connection established with %s\n", my_name, args->mapper_name);

	send(s, args->name, NAME_LEN, 0);
	do {
		ret = recv(s, buf, DATA_CHUNK_SIZE, 0);
		data_recv_size += ret;
		end_character = memchr(buf, 0xFF, ret);
	} while (end_character == NULL);

	time_e = get_timestamp_ms();
	result->time_elapsed = time_e - time_s;
	result->bytes_moved = data_recv_size;
	result->thread_time = get_thread_time_ms();

	close(s);
	fprintf(logfp, "(%s) Connection to %s finished, received %ld bytes\n", my_name, args->mapper_name, data_recv_size);
	sem_post(args->finish_sem);
	return result;
}

void* reducer(void* vargs)
{
	struct reducer_args* args = vargs;
	struct reducer_conn_thread* conns;
	struct reducer_connection_args* mappers;
	struct results* results;
	int i, ret, to_start, remaining, conn_count = 0, next_mapper = 0;
	sem_t th_completion_sem;

	fprintf(logfp, "(%s) Reducer thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	mappers = malloc(args->num_mappers * sizeof(struct reducer_connection_args));
	check_alloc(mappers, "reducer_1");
	for (i = 0; i < args->num_mappers; i++) {
		mappers[i].addr.sin_family = AF_INET;
		mappers[i].addr.sin_port = htons(args->addresses[i].port);
		mappers[i].addr.sin_addr = args->addresses[i].addr;
		mappers[i].mapper_name = args->addresses[i].name;
		mappers[i].name = args->name;
		mappers[i].finish_sem = &th_completion_sem;
	}

	conns = malloc(args->num_concurrent_conn * sizeof(struct reducer_conn_thread));
	check_alloc(conns, "reducer_2");
	for (i = 0; i < args->num_concurrent_conn; i++) {
		conns[i].free = 1;
	}

	results = malloc(sizeof(struct results));
	check_alloc(results, "reducer_3");
	results->meas = calloc(args->num_mappers, sizeof(struct measurement*));
	check_alloc(results->meas, "reducer_4");
	strncpy(results->th_name, args->name, NAME_LEN);
	results->count = args->num_mappers;

	to_start = remaining = args->num_mappers;

	sem_init(&th_completion_sem, 0, 0);

	// Signal that we are ready
	pthread_barrier_wait(&args->ready);
	fprintf(logfp, "(%s) waiting for START message\n", args->name);
	// Wait for start message
	pthread_barrier_wait(args->start);
	fprintf(logfp, "(%s) got START message\n", args->name);

	while (remaining > 0) {
		if (to_start > 0 && conn_count < args->num_concurrent_conn) {
			fprintf(logfp, "(%s) Starting new connection thread\n", args->name);
			i = 0;
			while (!conns[i].free) {
				i++;
			}
			mappers[next_mapper].id = i;
			conns[i].free = 0;
			pthread_create(&conns[i].th, NULL, reducer_connection, &mappers[next_mapper]);
			pthread_setname_np(conns[i].th, args->name);
			fprintf(logfp, "(%s) new thread ID: %lx\n", args->name, conns[i].th);
			conn_count++;
			next_mapper++;
			to_start--;
		} else {
			void* result;
			fprintf(logfp, "(%s) Maximum number of connections reached (%d), waiting for a thread to finish\n", args->name, conn_count);
			sem_wait(&th_completion_sem);
			i = 0;
			do {
				result = NULL;
				while (conns[i].free) { // There is at least one that is not free
					i = (i + 1) % args->num_concurrent_conn;
				}
				ret = pthread_tryjoin_np(conns[i].th, &result);
			} while (ret != 0);
			assert(result != NULL);
			remaining--;
			conn_count--;
			conns[i].free = 1;
			fprintf(logfp, "(%s) thread %d (%lx) joined, %d connections remaining\n", args->name, i, conns[i].th, remaining);
			i = 0;
			while (results->meas[i] != NULL) {
				i++;
			}
			results->meas[i] = result;
		}
	}

	sem_destroy(&th_completion_sem);

	free(mappers);
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
	fprintf(logfp, "(%s) New reducer\n", reducer_args->name);

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
			fprintf(logfp, "(%s) -> failed to parse IP address '%s'\n", reducer_args->name, aux);
			continue;
		}
	}
	reducer_args->start = barr;

	pthread_create(node, NULL, reducer, reducer_args);
	pthread_setname_np(*node, reducer_args->name);
	fprintf(logfp, "(%s) new thread ID: %lx\n", reducer_args->name, *node);

	pthread_barrier_wait(&reducer_args->ready);
	pthread_barrier_destroy(&reducer_args->ready); // Will not be used again
}

void send_results(struct results* results)
{
	int i;

	fprintf(logfp, RESULT_PFX "start node %s\n", results->th_name);
	for (i = 0; i < results->count; i++) {
		fprintf(logfp, RESULT_PFX "%s,%lld,%d,%d,%ld\n",
				results->meas[i]->th_name,
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
		char thname[10];
		pthread_getname_np(nodes[i], thname, 10);
		fprintf(logfp, "Waiting for thread %s (%lx) to join...\n", thname, nodes[i]);
		pthread_join(nodes[i], &retval);
		results = retval;
		send_results(results);
		fprintf(logfp, "Thread %s (%lx) joined\n", results->th_name, nodes[i]);
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

