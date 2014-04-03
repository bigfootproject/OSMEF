#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <time.h>

#define BUF_LEN 65536

double timediff(struct timespec *s, struct timespec *e)
{
	double res;

	res = e->tv_sec - s->tv_sec;
	res += (e->tv_nsec - s->tv_nsec) / 1000000000.0;
	return res;
}

int main(int argc, char**argv)
{
	int listenfd, connfd, n;
	struct sockaddr_in servaddr, cliaddr;
	socklen_t clilen;
	char mesg[BUF_LEN];
	size_t byte_count;
	struct timespec start_time, end_time;

	listenfd = socket(AF_INET, SOCK_STREAM, 0);

	memset(&servaddr, 0, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
	servaddr.sin_port = htons(9997);
	bind(listenfd, (struct sockaddr *)&servaddr, sizeof(servaddr));

	listen(listenfd, 10);

	for(;;) {
		clilen = sizeof(cliaddr);
		connfd = accept(listenfd, (struct sockaddr *)&cliaddr, &clilen);
		byte_count = 0;
		clock_gettime(CLOCK_MONOTONIC, &start_time);
		for(;;) {
			n = recv(connfd, mesg, BUF_LEN, 0);
			byte_count += n;
			if (n == 0)
				break;
		}
		clock_gettime(CLOCK_MONOTONIC, &end_time);
		printf("Received %ld MB in %0.2f seconds, %0.2f Mbit/s\n", byte_count/1024/1024, timediff(&start_time, &end_time), ((byte_count*8)/timediff(&start_time, &end_time))/1000000);
	}
	close(connfd);
}

