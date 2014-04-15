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

#define CMD_LISTEN_PORT 2333
#define DATA_CHUNK_SIZE 65536
#define CMD_DATA_LEN 1024
#define NAME_LEN 16

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
	char* data;
	int id;
	char* reducer_name;
	char name[NAME_LEN];
	sem_t* finish_sem;
};

struct mapper_conn_thread {
	int free;
	pthread_t th;
};

struct map_address {
	unsigned short int port;
	struct in_addr addr;
	char reducer_name[NAME_LEN];
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
	char* name;
	sem_t* finish_sem;
};

struct reducer_conn_thread {
	int free;
	pthread_t th;
};

struct measurement {
	char th_name[NAME_LEN];
};

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
	char buf[1024], *aux;
	ret = recv(s, buf, 1024, MSG_WAITALL);
	if (ret != 1024) {
		fprintf(logfp, "Received only %ld bytes in command message\n", ret);
		tmp->type = MSG_EXIT;
	}
	buf[1023] = '\0';
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
	snprintf(rep.data, CMD_DATA_LEN, "DONE");
	send_reply(s, &rep);
}

void* mapper_connection(void* vargs)
{
	struct mapper_connection_args* args = vargs;
	char* ptr = args->data;
	ssize_t bytes_sent = 0;

	fprintf(logfp, "(%s) thread started, have to send %ld bytes\n", args->name, args->size);
	while (bytes_sent < args->size) {
		int ret, chunk_len;

		if (args->size - bytes_sent < DATA_CHUNK_SIZE) {
			chunk_len = args->size - bytes_sent;
		} else {
			chunk_len = DATA_CHUNK_SIZE;
		}
		ret = send(args->s, ptr, chunk_len, 0);
		if (ret > 0) {
			bytes_sent += ret;
		}
	}
	args->data[0] = 0xFF;
	send(args->s, args->data, 1, 0);

	free(args->data);
	close(args->s);
	fprintf(logfp, "(%s) all data sent, thread exiting\n", args->name);
	sem_post(args->finish_sem);
	return NULL;
}

void* mapper(void* vargs)
{
	int s, ret, i, current_conn_count = 0, remaining, to_start;
	struct mapper_args* args = vargs;
	struct mapper_connection_args** reducers;
	struct mapper_conn_thread* conn_threads;
	sem_t th_completion_sem;
	struct measurement* result;

	fprintf(logfp, "(%s) Mapper thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	reducers = malloc(args->num_reducers * sizeof(struct mapper_connection_args*));
	for (i = 0; i < args->num_reducers; i++) {
		int j;
		fprintf(logfp, "(%s) Allocating data for reducer %s\n", args->name, args->reducer_names[i]);
		reducers[i] = malloc(sizeof(struct mapper_connection_args));
		reducers[i]->size = args->reducer_sizes[i];
		reducers[i]->data = malloc(sizeof(ssize_t) * args->reducer_sizes[i]);
		reducers[i]->reducer_name = args->reducer_names[i];
		reducers[i]->finish_sem = &th_completion_sem;
		for (j = 0; j < args->reducer_sizes[i]; j++) {
			reducers[i]->data[j] = j & 0x7F;
		}
	}

	conn_threads = malloc(args->num_concurrent_conn * sizeof(struct mapper_conn_thread));
	for (i = 0; i < args->num_concurrent_conn; i++) {
		conn_threads[i].free = 1;
	}

	fprintf(logfp, "(%s) Binding to port %d\n", args->name, args->port);
	s = listen_socket(args->port);

	result = malloc(sizeof(struct measurement));
	strncpy(result->th_name, args->name, NAME_LEN);

	sem_init(&th_completion_sem, 0, 0);

	to_start = remaining = args->num_reducers;

	// We are ready to start
	pthread_barrier_wait(&args->ready);

	while (remaining > 0) {
		struct sockaddr_in peer_addr;
		int peer_s, found = -1;
		char peer_name[NAME_LEN];
		socklen_t peer_addr_len;
		fprintf(logfp, "(%s) Current connection count: %d\n", args->name, current_conn_count);

		if (to_start > 0 && current_conn_count < args->num_concurrent_conn) {
			peer_s = accept(s, (struct sockaddr*)&peer_addr, &peer_addr_len);

			to_start--;
			current_conn_count++;
			ret = recv(peer_s, peer_name, NAME_LEN, 0);
			// Look for the data for this reducer
			for (i = 0; i < args->num_reducers; i++) {
				if (strncmp(peer_name, reducers[i]->reducer_name, NAME_LEN) == 0) {
					found = i;
					break;
				}
			}
			if (found < 0) {
				fprintf(logfp, "(%s) Got connection from unknown reducer %s\n", args->name, peer_name);
				close(peer_s);
				continue;
			}

			fprintf(logfp, "(%s) Got connection from reducer %s\n", args->name, peer_name);
			// Look for a free slot
			for (i = 0; i < args->num_concurrent_conn; i++) {
				if (conn_threads[i].free) {
					reducers[found]->s = peer_s;
					snprintf(reducers[found]->name, NAME_LEN, "%s:%d", args->name, found);
					pthread_create(&conn_threads[found].th, NULL, mapper_connection, reducers[found]);
					conn_threads[i].free = 0;
					break;
				}
			}
		} else {
			fprintf(logfp, "(%s) Waiting for a thread to finish\n", args->name);
			sem_wait(&th_completion_sem);
			i = 0;
			do {
				i = (i + 1) % args->num_concurrent_conn;
				if (conn_threads[i].free) {
					continue;
				}
				ret = pthread_tryjoin_np(conn_threads[i].th, NULL);
			} while (ret != 0);
			current_conn_count--;
			remaining--;
			conn_threads[i].free = 1;
			fprintf(logfp, "(%s) thread %d joined, %d connections remaining\n", args->name, i, remaining);
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
	return result;
}

void new_mapper(pthread_t *node, int id, char* data)
{
	char* aux = strtok(data, ",");
	ssize_t i;
	struct mapper_args* args;

	args = malloc(sizeof(struct mapper_args));

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
	args->reducer_names = malloc(args->num_reducers * sizeof(ssize_t));
	for (i = 0; i < args->num_reducers; i++) {
		args->reducer_names[i] = malloc(NAME_LEN * sizeof(char));
		aux = strtok(NULL, ",");
		strncpy(args->reducer_names[i], aux, NAME_LEN);
		aux = strtok(NULL, ",");
		args->reducer_sizes[i] = atoll(aux);
		fprintf(logfp, "(%s) -> reducer data size %ld\n", args->name, args->reducer_sizes[i]);
	}

	pthread_create(node, NULL, mapper, args);

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

	snprintf(my_name, NAME_LEN, "%s:%d", args->name, args->id);

	s = socket(AF_INET, SOCK_STREAM, 0);

	ret = connect(s, &args->addr, sizeof(struct sockaddr_in));
	if (ret) {
		fprintf(logfp, "Connection error\n");
	}

	fprintf(logfp, "(%s) Connection established\n", my_name);

	send(s, args->name, NAME_LEN, 0);
	do {
		ret = recv(s, buf, DATA_CHUNK_SIZE, 0);
		data_recv_size += ret;
		end_character = memchr(buf, 0xFF, ret);
	} while (end_character == NULL);
	close(s);
	fprintf(logfp, "(%s) Connection finished, received %ld bytes\n", my_name, data_recv_size);
	sem_post(args->finish_sem);
	return NULL;
}

void* reducer(void* vargs)
{
	struct reducer_args* args = vargs;
	struct reducer_conn_thread* conns;
	struct reducer_connection_args* mappers;
	struct measurement* result;
	int i, ret, remaining, conn_count = 0, next_mapper = 0;
	sem_t th_completion_sem;

	fprintf(logfp, "(%s) Reducer thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	mappers = malloc(args->num_mappers * sizeof(struct reducer_connection_args));
	for (i = 0; i < args->num_mappers; i++) {
		mappers[i].addr.sin_family = AF_INET;
		mappers[i].addr.sin_port = htons(args->addresses[i].port);
		mappers[i].addr.sin_addr = args->addresses[i].addr;
		mappers[i].name = args->name;	
		mappers[i].finish_sem = &th_completion_sem;
	}

	conns = malloc(args->num_concurrent_conn * sizeof(struct reducer_conn_thread));
	for (i = 0; i < args->num_concurrent_conn; i++) {
		conns[i].free = 1;
	}

	result = malloc(sizeof(struct measurement));
	strncpy(result->th_name, args->name, NAME_LEN);

	remaining = args->num_mappers;

	sem_init(&th_completion_sem, 0, 0);

	// Signal that we are ready
	pthread_barrier_wait(&args->ready);
	fprintf(logfp, "(%s) waiting for START message\n", args->name);
	// Wait for start message
	pthread_barrier_wait(args->start);
	fprintf(logfp, "(%s) got START message\n", args->name);

	while (remaining > 0) {
		for (i = 0; i < args->num_concurrent_conn; i++) {
			if (conns[i].free && next_mapper < args->num_mappers) {
				fprintf(logfp, "(%s) Starting new connection thread\n", args->name);
				mappers[next_mapper].id = i;
				pthread_create(&conns[i].th, NULL, reducer_connection, &mappers[next_mapper]);
				conns[i].free = 0;
				conn_count++;
				next_mapper++;
			}
		}
		if (conn_count >= args->num_concurrent_conn) {
			fprintf(logfp, "(%s) Maximum number of connections reached (%d), waiting for a thread to finish\n", args->name, conn_count);
			sem_wait(&th_completion_sem);
			i = 0;
			do {
				i = (i + 1) % args->num_concurrent_conn;
				if (conns[i].free) {
					continue;
				}
				ret = pthread_tryjoin_np(conns[i].th, NULL);
			} while (ret != 0);
			remaining--;
			conn_count--;
			conns[i].free = 1;
			fprintf(logfp, "(%s) thread %d joined, %d connections remaining\n", args->name, i, remaining);
		}
	}

	sem_destroy(&th_completion_sem);

	free(mappers);
	free(conns);
	fprintf(logfp, "(%s) all done, exiting\n", args->name);
	free(args->addresses);
	free(args);
	return result;
}

void new_reducer(pthread_t *node, int id, char* data, pthread_barrier_t* barr)
{
	char* aux = strtok(data, ",");
	ssize_t i;
	int ret;
	struct reducer_args* reducer_args;

	reducer_args = malloc(sizeof(struct reducer_args));

	pthread_barrier_init(&reducer_args->ready, NULL, 2);
	strncpy(reducer_args->name, aux, NAME_LEN);
	aux = strtok(NULL, ",");
	fprintf(logfp, "(%s) New reducer\n", reducer_args->name);
	reducer_args->num_concurrent_conn = atol(aux);
	aux = strtok(NULL, ",");
	reducer_args->num_mappers = atol(aux);
	reducer_args->addresses = calloc(reducer_args->num_mappers, sizeof(struct map_address));
	for (i = 0; i < reducer_args->num_mappers; i++) {
		aux = strtok(NULL, ",");
		strncpy(reducer_args->addresses[i].reducer_name, aux, NAME_LEN);
		aux = strtok(NULL, ",");
		reducer_args->addresses[i].port = atol(aux);
		aux = strtok(NULL, ",");
		ret = inet_pton(AF_INET, aux, &reducer_args->addresses[i].addr);
		if (!ret) {
			fprintf(logfp, "(%s) -> failed to parse IP address '%s'\n", reducer_args->name, aux);
			continue;
		}
	}
	reducer_args->start = barr;

	pthread_create(node, NULL, reducer, reducer_args);

	pthread_barrier_wait(&reducer_args->ready);
	pthread_barrier_destroy(&reducer_args->ready); // Will not be used again
}

void send_results(int num_nodes, struct measurement** results)
{
}

void wait_for_results(int num_nodes, pthread_t* nodes)
{
	int i;
	void* retval;
	struct measurement* results[num_nodes];

	for (i = 0; i < num_nodes; i++) {
		pthread_join(nodes[i], &retval);
		results[i] = retval;
		fprintf(logfp, "Node %s joined\n", results[i]->th_name);
	}

	send_results(num_nodes, results);

	for (i = 0; i < num_nodes; i++) {
		free(results[i]);
	}
}

void command_thread()
{
	int s;
	struct sockaddr_in peer_addr;
	int exit = 0, peer_s, node_count = 0;
	int num_nodes = 0, num_mappers = 0, num_reducers = 0;
	socklen_t peer_addr_len;
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

	if (argc == 1)
		daemon(1, 0);
	command_thread();

	return 0;
}

