/* 
 * File:   sync01.cpp
 * Author: dkeeper
 * 
 * Created on 2014年8月27日, 下午3:01
 */

#include "sync02.h"

#include <stdio.h> 
#include <pthread.h>
#include <assert.h>

int num_sy02;

pthread_mutex_t m_sy02;
pthread_cond_t empty_sy02, full_sy02;

void * thread1_sync02(void * arg) {
    pthread_mutex_lock(&m_sy02);

    while (num_sy02 > 0)
        pthread_cond_wait(&empty_sy02, &m_sy02);

    num_sy02++;

    pthread_mutex_unlock(&m_sy02);
    pthread_cond_signal(&full_sy02);
}

void * thread2_sync02(void * arg) {
    pthread_mutex_lock(&m_sy02);

    while (num_sy02 == 0)
        pthread_cond_wait(&full_sy02, &m_sy02);

    num_sy02--;

    pthread_mutex_unlock(&m_sy02);

    pthread_cond_signal(&empty_sy02);
}

sync02::sync02() {
    pthread_t t1, t2;

    num_sy02 = 1;

    pthread_mutex_init(&m_sy02, 0);
    pthread_cond_init(&empty_sy02, 0);
    pthread_cond_init(&full_sy02, 0);

    pthread_create(&t1, 0, thread1_sync02, 0);
    pthread_create(&t2, 0, thread2_sync02, 0);

    pthread_join(t1, 0);
    pthread_join(t2, 0);

    assert(num_sy02 == 1);
    //    if (num != 1) {
    //ERROR:
    //        goto ERROR;
    //        ;
    //    }
}

sync02::sync02(const sync02& orig) {
}

sync02::~sync02() {
}

