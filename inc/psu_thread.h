#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ucontext.h>
#include <pthread.h>
#include <netinet/in.h> 
#include <sys/socket.h> 
#define PORT 8080 
//you write the code here

#define REG_EBP 10 
#define REG_ESP 15
#define REG_EIP 16

#define FBP_H_ADDR 0x4
#define RAS_ADDR 0x8

#define GREGS_SIZE 0x10

typedef struct psu_thread_info 
{
	int mode;                /* Socket Programming */
	int mssg_read, socket;   /* Socket Programming */
	struct sockaddr_in addr; /* Socket Programming */
 	
	//static ucontext_t ctxt;
	//#pragma pack(1)
	//ucontext_t ctxt;
	//#pragma pack(0)
} psu_thread_info_t;

psu_thread_info_t obj;
pthread_t thread_id;

void psu_thread_setup_init(int mode)
{
	memset(&obj, '0', sizeof(obj)); //Init stuct obj with '0'
	//Read from a file to set up the socket connection between the client and the server
	if (mode == 0) {
	    //Client Mode
	    obj.mode = 0;
            obj.socket = socket(AF_INET, SOCK_STREAM, 0);
	    if (obj.socket < 0) 
	    { 
		printf(" Socket creation error"); 
		return -1; 
	    } 
	    //memset(&obj.addr, '0', sizeof(obj.addr)); 
	    obj.addr.sin_family = AF_INET; 
	    obj.addr.sin_port = htons(PORT);
	} else if (mode == 1) {
	    //Server Mode
	    int opt = 1;
	    obj.mode = 1;
	    obj.socket = socket(AF_INET, SOCK_STREAM, 0);

	    if (obj.socket == 0) 
	    { 
		perror("socket failed"); 
		exit(EXIT_FAILURE); 
	    }

	    if (setsockopt(obj.socket, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, 
							  &opt, sizeof(opt))) 
	    { 
		perror("setsockopt"); 
		exit(EXIT_FAILURE); 
	    } 
	    obj.addr.sin_family = AF_INET; 
	    obj.addr.sin_addr.s_addr = INADDR_ANY; 
	    obj.addr.sin_port = htons(PORT);
	    if (bind(obj.socket, (struct sockaddr *)&obj.addr,  
					 sizeof(obj.addr))<0) 
	    { 
		perror("bind failed"); 
		exit(EXIT_FAILURE); 
	    } 
	} else {
	  printf(" Invalid mode. Please choose either 0/1. \n");
	  exit(1);
	}
	return 0;
}

int psu_thread_create(void * (*user_func)(void*), void *user_args)
{
	// make thread related setup
	// create thread and start running the function based on *user_func
	if (obj.mode == 0) {
		int is_successful = pthread_create(&thread_id, NULL, *user_func, user_args);
		if(is_successful !=0) {
		   //Error while creating thread
		   printf("Not able to create thread.\n");
		   return -1;
		}
		pthread_join(thread_id, NULL);
	} else {
		server_listen();
	}

	return 0; 
}

void psu_thread_migrate(const char *hostname)
{
	/*char stack[16384];
	
	if (getcontext(&obj.ctxt) == -1) { 
               perror("getcontext");
	       exit(EXIT_FAILURE); 
	}
	obj.ctxt.uc_stack.ss_sp = stack;
	obj.ctxt.uc_stack.ss_size = sizeof(stack);
        obj.ctxt.uc_link = NULL;
        makecontext(&obj.ctxt, psu_thread_migrate, 0);*/
	//thread Migration related code
	if(obj.mode == 0) { //Client Mode
	    ucontext_t 	context , *cp = &context;
            					
	    char *hello = "Hello from client\n"; 
	    if(inet_pton(AF_INET, hostname , &obj.addr.sin_addr)<=0)  
	    { 
		printf(" Invalid address/ Address not supported"); 
		return -1; 
	    } 
	   
	    if (connect(obj.socket, (struct sockaddr *)&obj.addr, sizeof(obj.addr)) < 0) 
	    { 
		printf(" Connection Failed"); 
		return -1; 
	    } 

 	    if(getcontext(cp) == -1) 
	 	{
			printf("getcontext() error\n");
			exit(EXIT_FAILURE);
		}

	    //APP1- sending EBP to server	
            printf("stack base pointer:%x stack head pointer:%x\n", (long)cp->uc_mcontext.gregs[REG_EBP], (long)cp->uc_mcontext.gregs[REG_ESP]);
	    uint64_t _RAS = cp->uc_mcontext.gregs[REG_EBP] + RAS_ADDR; //EBP
	    printf("EBP (previous frame pointer)stored at: %x\n", _RAS);  	

            //send(obj.socket , _EBP, sizeof(uint64_t) , 0 );

            //APP2- sending stack to serve
            uint64_t _FPSP = cp->uc_mcontext.gregs[REG_EBP] + GREGS_SIZE;
	    uint64_t *higher_nibble_addr = (cp->uc_mcontext.gregs[REG_EBP]+ FBP_H_ADDR);
            uint64_t *lower_nibble_addr = cp->uc_mcontext.gregs[REG_EBP];
	    uint64_t _FPBP =  ((*higher_nibble_addr << 32) | *lower_nibble_addr) ;  
            printf("higher nibble:%x lowernibble:%x\n", *higher_nibble_addr, *lower_nibble_addr);
            printf("previous stack base pointer:%x stack head pointer:%x\n", _FPBP, _FPSP);

            uint64_t _FPstacksize = _FPBP - _FPSP;		
            printf("stack size:%x\n", _FPstacksize);

	    //send(obj.socket , _FPstacksize, sizeof(uint64_t) , 0 );
	    uint64_t num_stack = 1;
	    uint64_t *ptr = _FPBP;

	    while(*ptr != 0x0){
		ptr = *ptr;
		num_stack++;
	    };
	    char *buffer = (char*) malloc(num_stack*(_FPstacksize + GREGS_SIZE)); //size in bytes
            memcpy(buffer, _FPSP, num_stack*(_FPstacksize + GREGS_SIZE));

            char *sendobject = (char*) malloc(1024); //malloc(sizeof(uint64_t) + sizeof(uint64_t) + _FPstacksize);
            memcpy(sendobject, _RAS, sizeof(uint64_t));
	    memcpy(sendobject + sizeof(uint64_t), &_FPstacksize, sizeof(uint64_t));
            memcpy(sendobject + 2*sizeof(uint64_t), &num_stack, sizeof(uint64_t));
	    memcpy(sendobject + 3*sizeof(uint64_t), buffer, num_stack*(_FPstacksize+GREGS_SIZE));

            send(obj.socket , sendobject, 1024, 0);

	    free(buffer);
            free(sendobject);
	    exit(0); 
	    //send(obj.socket , hello, strlen(hello), 0 ); 
	} else if(obj.mode == 1){ //Server Mode
	    //Do nothing
	} else {
	    printf(" How??");  
	    exit(1);
	}
	return;
}

void server_listen() 
{
	int addrlen = sizeof(obj.addr); 
	char buffer[16384] = {0};
        ucontext_t curr_context; 
        char * recv = (char *) malloc(1024);
	if (listen(obj.socket, 3) < 0) 
	{ 
	perror("listen"); 
	exit(EXIT_FAILURE); 
	} 
	int client_socket = accept(obj.socket, (struct sockaddr *)&obj.addr, (socklen_t*)&addrlen);
	if (client_socket < 0)
	{ 
	perror("accept"); 
	exit(EXIT_FAILURE); 
	} 
	//obj.mssg_read = read(client_socket , buffer, 16384); 
	//printf("%s",buffer); 
	//swapcontext(&obj.ctxt, &buffer);
	size_t z = read(client_socket, &recv, 1024); //sizeof(uint64_t));
	if(z == -1){
		printf("setcontext() error");
		exit(EXIT_FAILURE);   
	}

        uint64_t recv_ras = 0;
        memcpy(&recv_ras, &recv, sizeof(uint64_t));

        uint64_t recv_ss = 0;
        memcpy(&recv_ss, &recv+0x1, sizeof(uint64_t)); 

	uint64_t recv_num_stack = 0;
        memcpy(&recv_num_stack, &recv+0x2, sizeof(uint64_t));

        char recv_buffer[recv_num_stack*(recv_ss+ GREGS_SIZE)];
        memcpy(&recv_buffer, &recv + 0x3, recv_num_stack*(recv_ss + GREGS_SIZE));

        getcontext(&curr_context);

        //APP1 - Setting  eip as ebp recieved
	curr_context.uc_mcontext.gregs[REG_EIP] = recv_ras;

        //Store exsisitng Return address, previous frame bp before new stack overwrite
        uint64_t *_prevRA = curr_context.uc_mcontext.gregs[REG_EBP] + RAS_ADDR;        
        uint64_t *lower_nibble_addr = (curr_context.uc_mcontext.gregs[REG_EBP]);

	int num_stack = 1;
        for(num_stack = 1; num_stack < recv_num_stack; num_stack++){
		uint64_t prev_ebp = ((char*) recv_buffer + (num_stack+1)*recv_ss + (num_stack)*GREGS_SIZE);
		memcpy(recv_buffer + num_stack*recv_ss + (num_stack-1)*GREGS_SIZE, &prev_ebp, sizeof(uint64_t));

	}
        memcpy(recv_buffer+ num_stack*recv_ss + (num_stack - 1)*GREGS_SIZE, lower_nibble_addr, sizeof(uint64_t));
        memcpy(recv_buffer + num_stack*recv_ss + (num_stack - 1)*GREGS_SIZE + RAS_ADDR, _prevRA, sizeof(uint64_t));
        
	curr_context.uc_mcontext.gregs[REG_EBP] = recv_buffer + recv_ss;
        curr_context.uc_mcontext.gregs[REG_ESP] = &recv_buffer;

        //APP2 - Setting bp and sp
	setcontext(&curr_context);
}
