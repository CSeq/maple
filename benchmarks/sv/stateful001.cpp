/* 
 * File:   stateful001.cpp
 * Author: dkeeper
 * 
 * Created on 2014年8月27日, 下午2:40
 */

#include "stateful001.h"
#include <pthread.h>
#include <stdio.h>
#include <assert.h>

pthread_mutex_t ma_st001, mb_st001;
int data1_st001, data2_st001;

void * thread1_stateful001(void * arg) {
    pthread_mutex_lock(&ma_st001);
    data1_st001++;
    pthread_mutex_unlock(&ma_st001);

    pthread_mutex_lock(&ma_st001);
    data2_st001++;
    pthread_mutex_unlock(&ma_st001);
}

void * thread2_stateful001(void * arg) {
    pthread_mutex_lock(&ma_st001);
    data1_st001 += 5;
    pthread_mutex_unlock(&ma_st001);

    pthread_mutex_lock(&ma_st001);
    data2_st001 -= 6;
    pthread_mutex_unlock(&ma_st001);
}

stateful001::stateful001() {
    pthread_t t1, t2;

    pthread_mutex_init(&ma_st001, 0);
    pthread_mutex_init(&mb_st001, 0);

    data1_st001 = 10;
    data2_st001 = 10;

    pthread_create(&t1, 0, thread1_stateful001, 0);
    pthread_create(&t2, 0, thread2_stateful001, 0);

    pthread_join(t1, 0);
    pthread_join(t2, 0);

    assert(data1_st001 == 16 && data2_st001 == 5);

    //    if (data1 != 16 && data2 != 5) {
    //ERROR:
    //        goto ERROR;
    //        ;
    //    }
}

stateful001::stateful001(const stateful001& orig) {
}

stateful001::~stateful001() {
}

