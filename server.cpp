/* File Name: server.c */  
#include<stdio.h>  
#include<stdlib.h>  
#include<string.h>  
#include<errno.h>  
#include<sys/types.h>  
#include<sys/socket.h>  
#include<netinet/in.h>  
#include <sys/sem.h>
#include<iostream>
using namespace std;
#include<vector>
#include<exception>
#include<typeinfo>
#include <unistd.h>

#define DEFAULT_PORT        8000  
#define MAXLINE             1024
#define CONNECTION_MAX      50 
#define HEAD_STR_LEN        100

static char regtxt[30];
static char server[30];
static int sem_id = 0;
static int set_semvalue();
static void del_semvalue();
static int semaphore_p();
static int semaphore_v();

typedef struct{
int sockid;
char msgid[HEAD_STR_LEN];
}Pair;
 
static std::vector<Pair> sockList;

union semun
{
    int val;
    struct semid_ds *buf;
    unsigned short *arry;
};

static int set_semvalue()
{
    // 用于初始化信号量，在使用信号量前必须这样做
    union semun sem_union;
 
    sem_union.val = 1;
    if (semctl(sem_id, 0, SETVAL, sem_union) == -1)
    {
        return 0;
    }
    return 1;
}
 
static void del_semvalue()
{
    // 删除信号量
    union semun sem_union;
 
    if (semctl(sem_id, 0, IPC_RMID, sem_union) == -1)
    {
        fprintf(stderr, "Failed to delete semaphore\n");
    }
}
 
static int semaphore_p()
{
    // 对信号量做减1操作，即等待P（sv）
    struct sembuf sem_b;
    sem_b.sem_num = 0;
    sem_b.sem_op = -1;//P()
    sem_b.sem_flg = SEM_UNDO;
    if (semop(sem_id, &sem_b, 1) == -1)
    {
        fprintf(stderr, "semaphore_p failed\n");
        return 0;
    }
 
    return 1;
}
 
static int semaphore_v()
{
    // 这是一个释放操作，它使信号量变为可用，即发送信号V（sv）
    struct sembuf sem_b;
    sem_b.sem_num = 0;
    sem_b.sem_op = 1; // V()
    sem_b.sem_flg = SEM_UNDO;
    if (semop(sem_id, &sem_b, 1) == -1)
    {
        fprintf(stderr, "semaphore_v failed\n");
        return 0;
    }
 
    return 1;
}

int forwardmsg(int sockid, const char* str0, const char* str1, const char* str2)
{
    char buff[MAXLINE];
    semaphore_p();
    int size = sockList.size();
     int n = snprintf(buff,MAXLINE,"%s:%s:%s",str1,str0,str2 );
    if(send(sockid, buff, n, 0) == -1)  
        perror("send error\n");
  //  else
  //      printf("forward:%s\n",buff); 
    semaphore_v();
    return 0;
}


int split(const char* str, const int length, const char cmp, int size, char cpy[][MAXLINE])
{
    int findsplit = 0;
    int start = 0;

    for(int i=1; i<length;i++)
    {
        if( str[i] == cmp)
        {
            memcpy(&cpy[findsplit], &str[start], i-start);
            start = i+1;
            findsplit++;
            if(findsplit >= (size-1))
            {
                memcpy(&cpy[findsplit], &str[start], length-start);
                return 1;
            }
            
        }
    }
    return 0;

}


void handlerec(int connect_fd)
{
    char buff[MAXLINE];
    char splittxt[3][MAXLINE];
    int loop = 1;	
    while(loop)
    {
	    try
	    {
		int n = recv(connect_fd, buff, MAXLINE, 0);
		if(n > 0)
		{
		    int ret = split(buff, n, ':', 3, splittxt);
		    if(ret == 1)
		    {
		        //split ok
		        if (memcmp(regtxt, &splittxt[0], sizeof(regtxt)) == 0)
		        {
		            semaphore_p();
		            snprintf(server,30,"%s",&splittxt[2][0]);
		            semaphore_v();
		            printf("id is updated:%s\n",server);
		        }
		        else//message mapping
		        {                    
		            forwardmsg(connect_fd, &splittxt[0][0],&splittxt[1][0],&splittxt[2][0]);
		        }
                
		    }
		    else
		    {
		        if(send(connect_fd, buff, n, 0) == -1)  
		            perror("send error");  
		    }
		}
		else
		{
			loop = 0;
		}
	    }
	    catch (exception& e)  
	    {  
		perror( e.what()); 
		loop = 0;
	    }
    }
    close(connect_fd);
	printf("close socket:%d\n",connect_fd);  
}

int registerDevice(int sockid)
{
    char    buff[MAXLINE];  
    int n = snprintf(buff,MAXLINE,"%s:%s:%s",regtxt,server,"??" );
    if(send(sockid, buff, n, 0) == -1)
    {  
        perror("send error\n");
        return 0;
    }
    return 1;
}
int main(int argc, char** argv)  
{  
    int    socket_fd;  
    struct sockaddr_in     servaddr;  
    char    buff[4096];  
    int     n;
    int  loop = 0;  
    snprintf(&regtxt[0],MAXLINE,"register_server");
    snprintf(&server[0],MAXLINE,"host");
//static char server[30] = 'host';
    sem_id = semget((key_t) 2345, 1, 0666 | IPC_CREAT);
    if (!set_semvalue())
    {
        fprintf(stderr, "Failed to initialize semaphore\n");
        exit(EXIT_FAILURE);
    }
    socket_fd = socket(AF_INET,SOCK_STREAM, 0);
    //初始化  
    memset(&servaddr, 0, sizeof(servaddr));  
    servaddr.sin_family = AF_INET;  
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);//IP地址设置成INADDR_ANY,让系统自动获取本机的IP地址。  
    servaddr.sin_port = htons(DEFAULT_PORT);//设置的端口为DEFAULT_PORT  
  
    //连接服务器，成功返回0，错误返回-1
    if (connect(socket_fd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0)
    {
        perror("connect");
        exit(1);
    }
    printf("======connected======\n");  
    loop = registerDevice(socket_fd);
    if(loop)
    {  
        handlerec(socket_fd);
    }  
    close(socket_fd);  
}  
