/* 
 * File:   stateful002.cpp
 * Author: dkeeper
 * 
 * Created on 2014年8月27日, 下午4:47
 */

#include "stateful002.h"
#include <pthread.h>
#include <stdio.h>
#include <assert.h>

pthread_mutex_t ma_st002, mb_st002;
int data1_st002, data2_st002;

void * thread1_stateful002(void * arg) {
    pthread_mutex_lock(&ma_st002);
    data1_st002++;
    pthread_mutex_unlock(&ma_st002);

    pthread_mutex_lock(&ma_st002);
    data2_st002++;
    pthread_mutex_unlock(&ma_st002);
}

void * thread2_stateful002(void * arg) {
    pthread_mutex_lock(&ma_st002);
    data1_st002 += 5;
    pthread_mutex_unlock(&ma_st002);

    pthread_mutex_lock(&ma_st002);
    data2_st002 -= 6;
    pthread_mutex_unlock(&ma_st002);
}

stateful002::stateful002() {
    pthread_t t1, t2;

    pthread_mutex_init(&ma_st002, 0);
    pthread_mutex_init(&mb_st002, 0);

    data1_st002 = 10;
    data2_st002 = 10;

    pthread_create(&t1, 0, thread1_stateful002, 0);
    pthread_create(&t2, 0, thread2_stateful002, 0);

    pthread_join(t1, 0);
    pthread_join(t2, 0);

    assert(data1_st002 == 16 && data2_st002 == 5);

    //    if (data1 != 16 && data2 != 5) {
    //ERROR:
    //        goto ERROR;
    //        ;
    //    }
}

stateful002::stateful002(const stateful002& orig) {
}

stateful002::~stateful002() {
}

