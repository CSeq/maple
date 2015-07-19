#include <pthread.h>  
#include <iostream>
#include <stdlib.h>

int inputX = 0;
int inputY = 0;
int data1 = -1;
int data2 = -1;
int data3 = -1;
int data4 = -1;


void * thread1(void * arg){
    data1 ++;
    data2 ++;
    data3 ++;
    data4 ++;
}
void * thread2(void * arg){
    if(inputX > 0)
        data1 += 2;
    else
        data2 += 2;
    if(inputY > 0)
        data3 += 2;
    else
        data4 += 2;
}

int main(int argc, char ** argv) {
    inputX = atoi(argv[1]);
    inputY = atoi(argv[2]);
    pthread_t t1,t2;
    
    pthread_create(&t1, 0, thread1, 0);
    pthread_create(&t2, 0, thread2, 0);
    
    pthread_join(t1, 0);
    pthread_join(t2, 0);
    
    std::cout << "data1 = " << data1 << std::endl;
    std::cout << "data2 = " << data2 << std::endl;
    std::cout << "data3 = " << data3 << std::endl;
    std::cout << "data4 = " << data4 << std::endl;
    
    return 0;
} 
