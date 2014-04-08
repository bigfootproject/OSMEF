#include <stdio.h>
#include <pthread.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <errno.h>

#define CMD_LISTEN_PORT 2333

#define MSG_EXIT  0
#define MSG_INIT  1
#define MSG_NODES 2

struct msg {
	unsigned int type;
	char data[1024];
};

struct msg* receive_command(int s)
{
	ssize_t ret;
	struct msg* tmp = calloc(1, sizeof(struct msg));
	ret = recv(s, tmp, sizeof(struct msg), MSG_WAITALL);
	if (ret != sizeof(struct msg)) {
		tmp->type = MSG_EXIT;
	}
	tmp->type = ntohl(tmp->type);
	return tmp;
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

void command_thread()
{
	FILE* logfp = fopen("/tmp/osmef_worker.log", "w");
	int s = socket(AF_INET, SOCK_STREAM, 0);
	struct sockaddr_in local_addr, peer_addr;
	int ret, exit = 0, peer_s, num_nodes;
	socklen_t peer_addr_len;
	pthread_t *nodes = NULL;

	memset(&local_addr, 0, sizeof(struct sockaddr_in));

	local_addr.sin_family = AF_INET;
	local_addr.sin_port = htons(CMD_LISTEN_PORT);
	local_addr.sin_addr.s_addr = INADDR_ANY;
	ret = bind(s, (struct sockaddr*)&local_addr, sizeof(struct sockaddr_in));
	if (ret) {
		fprintf(logfp, "Bind error: %s\n", strerror(errno));
		fflush(logfp);
		return;
	}
	listen(s, 1);
	fprintf(logfp, "Listening for command connection\n");
	fflush(logfp);
	peer_s = accept(s, (struct sockaddr*)&peer_addr, &peer_addr_len);

	while (!exit) {
		struct msg *cmd = receive_command(peer_s);
		switch(cmd->type) {
			case MSG_EXIT:
				exit = 1;
			case MSG_INIT:
				cleanup_nodes(num_nodes, nodes);
				num_nodes = 0;
				break;
			case MSG_NODES:
				num_nodes = atol(cmd->data);
				nodes = malloc(num_nodes * sizeof(pthread_t));
				break;
			default:
				fprintf(logfp, "Unknown command received: %d\n", cmd->type);
				fflush(logfp);
				break;
		}
		free(cmd);
	}
	fclose(logfp);
}

int main(int argc, char *argv[])
{
	printf("OSMeF worker starting\n");
	daemon(1, 0);
	command_thread();

	return 0;
}

