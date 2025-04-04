#include <stdlib.h> 
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <time.h>
#include <pthread.h>
#include <unistd.h>

static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static __thread FILE *fp;
static FILE **fp_array;
static int fp_array_next_idx = 0;

extern "C" __attribute__((destructor)) void tracing_deconstructor(void) {
  pthread_mutex_lock(&mutex);
  for (int i = 0; i < fp_array_next_idx; i++) {
    fflush(fp_array[i]);
    fclose(fp_array[i]);
  }
  pthread_mutex_unlock(&mutex);
}

extern "C" void __cyg_profile_func_enter(void *callee, void *caller) {
  if (fp == NULL) {
    char buffer[50];
    sprintf(buffer, "traces%d.txt", gettid());
    fp = fopen(buffer, "w");

    if (fp_array == NULL) {
      pthread_mutex_lock(&mutex);
      if (fp_array == NULL) {
        fp_array = (FILE**) malloc(50 * sizeof(FILE*));
        fp_array[fp_array_next_idx++] = fp;
      }
      pthread_mutex_unlock(&mutex);
    } else {
      pthread_mutex_lock(&mutex);
      fp_array[fp_array_next_idx++] = fp;
      pthread_mutex_unlock(&mutex);
    }
  }

  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  fprintf(fp, "E,%ld,%ld,%p,%p\n", ts.tv_sec, ts.tv_nsec, (int *)caller, (int *)callee);
}

extern "C" void __cyg_profile_func_exit(void *callee, void *caller) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  fprintf(fp, "X,%ld,%ld,%p,%p\n", ts.tv_sec, ts.tv_nsec, (int *)caller, (int *)callee);
}
