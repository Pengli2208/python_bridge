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
    int i=0;
    for(; i <size;i++)
    {
        if(memcmp(&sockList[i].msgid[0], str1, strlen(str1))==0)
        {
            sockid = sockList[i].sockid;
            break;
        }
    }
    int n = snprintf(buff,MAXLINE,"%s:%s:%s",str1,str0,str2 );
    if(send(sockid, buff, n, 0) == -1)  
        perror("send error\n");
  //  else
  //      printf("forward:%s\n",buff); 
    semaphore_v();
    return 0;
}

int registerconnection(int sockid, const char* str0, const char* str1)
{
    char buff[MAXLINE];
    Pair st;
    semaphore_p();
    if( memcmp(str1,server, sizeof(server)) == 0)
    {
        st.sockid = sockid;
        memcpy(&st.msgid[0], server, sizeof(server));
        sockList.push_back(st);
    }
    else
    {
        st.sockid = sockid;
        //memcpy(&st.msgid[0], server, sizeof(server));
        snprintf(&st.msgid[0],HEAD_STR_LEN,"%s_%d",str1,sockid);
        sockList.push_back(st);
    }
    semaphore_v();
    int n = snprintf(buff,MAXLINE,"%s:%s:%s",str0,str1,st.msgid );
    if(send(sockid, buff, n, 0) == -1)  
        perror("send error\n");
 //   else
 //       printf("send:%s\n",buff);  
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
    printf("new socket is connected: %d\n",connect_fd); 	
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
		            registerconnection(connect_fd,&splittxt[0][0], &splittxt[1][0] );
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
    
int main(int argc, char** argv)  
{  
    int    socket_fd, connect_fd;  
    struct sockaddr_in     servaddr;  
    char    buff[4096];  
    int     n;  
    snprintf(&regtxt[0],MAXLINE,"register_server");
    snprintf(&server[0],MAXLINE,"host");
//static char server[30] = 'host';
    sem_id = semget((key_t) 1234, 1, 0666 | IPC_CREAT);
    if (!set_semvalue())
    {
        fprintf(stderr, "Failed to initialize semaphore\n");
        exit(EXIT_FAILURE);
    }
    //初始化Socket  
    if( (socket_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1 )
    {  
        printf("create socket error: %s(errno: %d)\n",strerror(errno),errno);  
        exit(0);  
    }  
    sockList.resize(CONNECTION_MAX+5);
    //初始化  
    memset(&servaddr, 0, sizeof(servaddr));  
    servaddr.sin_family = AF_INET;  
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);//IP地址设置成INADDR_ANY,让系统自动获取本机的IP地址。  
    servaddr.sin_port = htons(DEFAULT_PORT);//设置的端口为DEFAULT_PORT  
  
    //将本地地址绑定到所创建的套接字上  
    if( bind(socket_fd, (struct sockaddr*)&servaddr, sizeof(servaddr)) == -1)
    {  
        printf("bind socket error: %s(errno: %d)\n",strerror(errno),errno);  
        exit(0);  
    }  
    //开始监听是否有客户端连接  
    if( listen(socket_fd, CONNECTION_MAX) == -1)
    {  
        printf("listen socket error: %s(errno: %d)\n",strerror(errno),errno);  
        exit(0);  
    }  
    printf("======waiting for client's request======\n");  
    while(1)
    {  
//阻塞直到有客户端连接，不然多浪费CPU资源。
        connect_fd = accept(socket_fd, (struct sockaddr*)NULL, NULL);

        if( connect_fd == -1)
        {  
            printf("accept socket error: %s(errno: %d)\n",strerror(errno),errno);  
            continue;  
        }  
        else
        {
             
            if(!fork())
            { 
                //new process
                handlerec(connect_fd);
            } 
        } 
    }  
    close(socket_fd);  
}  
