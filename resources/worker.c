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

#define CMD_LISTEN_PORT 2333
#define DATA_CHUNK_SIZE 65536
#define CMD_DATA_LEN 1024

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
	ssize_t* sizes;
	unsigned short int port;
	char name[8];
	pthread_barrier_t ready;
};

struct mapper_connection {
	int s;
	ssize_t size;
	char* data;
	pthread_t th;
	int active;
};

struct map_address {
	unsigned short int port;
	struct in_addr addr;
};

struct reducer_args {
	int num_concurrent_conn;
	int num_mappers;
	char name[8];
	struct map_address* addresses;
	pthread_barrier_t ready;
	pthread_barrier_t* start;
};

struct reducer_connection_args {
	struct sockaddr_in addr;
};

struct reducer_conn_thread {
	int free;
	pthread_t th;
};

struct measurement {
	char th_name[8];
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

void cleanup_nodes(int num_nodes, pthread_t* nodes)
{
	int i;
	for (i = 0; i < num_nodes; i++) {
		pthread_cancel(nodes[i]);
		pthread_join(nodes[i], NULL);
	}
	free(nodes);
}

void* mapper_connection(void* vargs)
{
	struct mapper_connection* conn = vargs;
	char* ptr = conn->data;
	ssize_t bytes_sent = 0;

	conn->active = 1;
	while (bytes_sent < conn->size) {
		int ret, chunk_len;
		if (conn->size - bytes_sent < DATA_CHUNK_SIZE) {
			chunk_len = conn->size - bytes_sent;
		} else {
			chunk_len = DATA_CHUNK_SIZE;
		}
		ret = send(conn->s, ptr, chunk_len, 0);
		if (ret > 0) {
			bytes_sent += ret;
		}
	}

	free(conn->data);
	conn->active = 0;
	return NULL;
}

void* mapper(void* vargs)
{
	int s, ret, i, current_conn_count = 0, reducer_count = 0;
	struct mapper_args* args = vargs;
	struct mapper_connection** conn_data;

	fprintf(logfp, "(%s) Mapper thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	conn_data = malloc(args->num_reducers * sizeof(struct mapper_connection*));
	for (ret = 0; ret < args->num_reducers; ret++) {
		fprintf(logfp, "(%s) Allocating data for reducer %d\n", args->name, ret);
		conn_data[ret] = malloc(sizeof(struct mapper_connection));
		conn_data[ret]->size = args->sizes[ret];
		conn_data[ret]->data = malloc(sizeof(ssize_t) * args->sizes[ret]);
		fprintf(logfp, "(%s) Initializing data for reducer %d\n", args->name, ret);
		for (i = 0; i < args->sizes[ret]; i++) {
			conn_data[ret]->data[i] = i & 0x7F;
		}
	}

	fprintf(logfp, "(%s) Binding to port %d\n", args->name, args->port);
	s = listen_socket(args->port);

	// We are ready to start
	pthread_barrier_wait(&args->ready);

	while (reducer_count < args->num_reducers) {
		struct sockaddr_in peer_addr;
		int peer_s;
		socklen_t peer_addr_len;
		peer_s = accept(s, (struct sockaddr*)&peer_addr, &peer_addr_len);

		current_conn_count++;
		
		conn_data[reducer_count]->s = peer_s;	
		pthread_create(&conn_data[reducer_count]->th, NULL, mapper_connection, conn_data);

		while (current_conn_count >= args->num_concurrent_conn) {
			for (ret = 0; ret < reducer_count; ret++) {
				if (!conn_data[ret]->active) {
					pthread_join(conn_data[ret]->th, NULL);
					current_conn_count--;
				}
			}
		}
	}

	for (ret = 0; ret < reducer_count; ret++) {
		if (conn_data[ret]->active) {
			pthread_join(conn_data[ret]->th, NULL);
		}
		free(conn_data[ret]);
	}
	free(conn_data);
	free(args);
	return NULL;
}

void new_mapper(pthread_t *node, int id, char* data)
{
	char* aux = strtok(data, ",");
	ssize_t i;
	struct mapper_args* args;

	args = malloc(sizeof(struct mapper_args));

	pthread_barrier_init(&args->ready, NULL, 2);
	snprintf(args->name, 8, "mp%d", id);
	args->num_concurrent_conn = atol(aux);
	aux = strtok(NULL, ",");
	args->port = atol(aux);
	fprintf(logfp, "(%s) New mapper on port %d\n", args->name, args->port);
	aux = strtok(NULL, ",");
	args->num_reducers = atol(aux);
	args->sizes = malloc(args->num_reducers * sizeof(ssize_t));
	for (i = 0; i < args->num_reducers; i++) {
		aux = strtok(NULL, ",");
		args->sizes[i] = atoll(aux);
		fprintf(logfp, "(%s) -> reducer data size %ld\n", args->name, args->sizes[i]);
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

	s = socket(AF_INET, SOCK_STREAM, 0);

	ret = connect(s, &args->addr, sizeof(struct sockaddr_in));
	if (ret) {
		fprintf(logfp, "Connection error\n");
	}
	ret = recv(s, buf, DATA_CHUNK_SIZE, 0);
	while (ret != 0) {
		ret = recv(s, buf, DATA_CHUNK_SIZE, 0);
	}
	close(s);
	return NULL;
}

void* reducer(void* vargs)
{
	struct reducer_args* args = vargs;
	struct reducer_conn_thread* conns;
	struct reducer_connection_args* mappers;
	int i, remaining, conn_count = 0;

	fprintf(logfp, "(%s) Reducer thread started\n", args->name);

	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	conns = malloc(args->num_concurrent_conn * sizeof(struct reducer_conn_thread));
	mappers = malloc(args->num_mappers * sizeof(struct reducer_connection_args));

	for (i = 0; i < args->num_mappers; i++) {
		mappers[i].addr.sin_family = AF_INET;
		mappers[i].addr.sin_port = htons(args->addresses[i].port);
		mappers[i].addr.sin_addr = args->addresses[i].addr;
		conns[i].free = 1;
	}

	remaining = args->num_mappers;

	// Signal that we are ready
	pthread_barrier_wait(&args->ready);
	fprintf(logfp, "(%s) witing for START message\n", args->name);
	// Wait for start message
	pthread_barrier_wait(args->start);
	fprintf(logfp, "(%s) got START message\n", args->name);

	while (remaining > 0) {
		int idx = args->num_mappers - remaining;
		if (conn_count < args->num_concurrent_conn) {
			conns[idx].free = 0;
			pthread_create(&conns[idx].th, NULL, reducer_connection, &mappers[idx]);
			conn_count++;
		} else {
			for (i = 0; i < args->num_concurrent_conn; i++) {
				int ret;
				ret = pthread_tryjoin_np(conns[i].th, NULL);
				if (ret == 0) {
					remaining--;
					conn_count--;
					conns[i].free = 1;
					fprintf(logfp, "(%s) connection finished, %d remaining\n", args->name, remaining);
				}
			}
		}
	} // FIXME busy wait

	free(mappers);
	free(conns);

	return NULL;
}

void new_reducer(pthread_t *node, int id, char* data, pthread_barrier_t* barr)
{
	char* aux = strtok(data, ",");
	ssize_t i;
	int ret;
	struct reducer_args* args;

	args = malloc(sizeof(struct reducer_args));

	pthread_barrier_init(&args->ready, NULL, 2);
	snprintf(args->name, 8, "rd%d", id);
	fprintf(logfp, "(%s) New reducer\n", args->name);
	args->num_concurrent_conn = atol(aux);
	aux = strtok(NULL, ",");
	args->num_mappers = atol(aux);
	args->addresses = calloc(args->num_mappers, sizeof(struct map_address));
	for (i = 0; i < args->num_mappers; i++) {
		aux = strtok(NULL, ",");
		args->addresses[i].port = atol(aux);
		aux = strtok(NULL, ",");
		ret = inet_pton(AF_INET, aux, &args->addresses[i].addr);
		if (!ret) {
			fprintf(logfp, "(%s) -> failed to parse IP address '%s'\n", args->name, aux);
			continue;
		}
	}
	args->start = barr;

	pthread_create(node, NULL, reducer, args);

	pthread_barrier_wait(&args->ready);
	pthread_barrier_destroy(&args->ready); // Will not be used again
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
		fprintf(logfp, "Got command %d\n", cmd->type);
		switch(cmd->type) {
			case MSG_EXIT:
				exit = 1;
			case MSG_INIT:
				cleanup_nodes(num_nodes, nodes);
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

