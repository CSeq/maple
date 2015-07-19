#include <pthread.h>  
#include <iostream> 
#include <stdlib.h>
#include <assert.h>

int inputX = 0;
int inputY = 0;
int data1 = -1;
int data2 = -1;
int data3 = -1;
int data4 = -1;
pthread_mutex_t m;

void add1()
{
    pthread_mutex_lock(&m);
    data1++;
    pthread_mutex_unlock(&m);
}
void add2()
{
    pthread_mutex_lock(&m);
    data2++;
    pthread_mutex_unlock(&m);
}
void add3()
{
    pthread_mutex_lock(&m);
    data3++;
    pthread_mutex_unlock(&m);
}
void add4()
{
    pthread_mutex_lock(&m);
    data4++;
    pthread_mutex_unlock(&m);
}

void *thread1(void *arg){
    pthread_mutex_lock(&m);
    data1 ++;
    pthread_mutex_unlock(&m);
    
    pthread_mutex_lock(&m);
    data2 ++;
    pthread_mutex_unlock(&m);
    
    pthread_mutex_lock(&m);
    data3 ++;
    pthread_mutex_unlock(&m);
    
//    pthread_mutex_lock(&m);
    data4 ++;
//    pthread_mutex_unlock(&m);
}
void *thread2(void *arg){
    if(inputX>0 && inputY>0)
    {
        add1();
        add2();
    }
    else if(inputX>0)
    {
        add1();
        add3();
    }
    else if(inputX<0 && inputY>0)
    {
        add2();
        add3();
    }
    else
    {
        add2();
        add4();
    }
}

int main(int argc, char ** argv) {

    inputX = atoi(argv[1]);
    inputY = atoi(argv[2]);
    
    pthread_t t1,t2;
    
    pthread_create(&t1, 0, thread1, 0);
    pthread_create(&t2, 0, thread2, 0);
    
    pthread_join(t1, 0);
    pthread_join(t2, 0);
    if(inputY <= 0 && inputX <= 0 && data4!=1)
    {
        std::cout << "data1 = " << data1 << std::endl;
        std::cout << "data2 = " << data2 << std::endl;
        std::cout << "data3 = " << data3 << std::endl;
        std::cout << "data4 = " << data4 << std::endl;
    }
    
    assert(inputX>0 || inputY>0 || data4==1);
    
    return 0;
} 
