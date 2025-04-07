#include "tsc.h"
#include <atomic>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

struct AddressRange {
  uintptr_t start;
  uintptr_t end;
};

static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static __thread FILE *fp;
static __thread std::atomic_flag lock_taken = ATOMIC_FLAG_INIT;
static FILE **fp_array;
static int fp_array_next_idx = 0;
static u64 last_rtdsc = 0;
static AddressRange *asprof_range;

bool check_asprof_range(uintptr_t address) {
  return asprof_range->start < address && address < asprof_range->end;
}

extern "C" void initialize_asprof_address_range() {
  FILE *proc_maps_fp = fopen("/proc/self/maps", "r");
  if (proc_maps_fp == NULL) {
    fprintf(stderr, "Could not open /proc/self/maps\n");
    return;
  }

  asprof_range = (AddressRange *)malloc(sizeof(AddressRange));
  asprof_range->start = 0;
  asprof_range->end = 0;

  char *prev_line = NULL;
  char *line = NULL;
  char expected[] = "libasyncProfiler.so\n\0";
  size_t len = 0;
  ssize_t read;
  while ((read = getline(&line, &len, proc_maps_fp)) != -1) {
    char *comparison_start = line + read - 20;
    if (strcmp(comparison_start, expected) == 0) {
      if (asprof_range->start == 0) {
        int i = 0;
        while (line[++i] != '-')
          ;
        line[i] = 0;
        asprof_range->start = strtoul(line, NULL, 16);
      }
      char *tmp = prev_line;
      prev_line = line;
      line = tmp;
    } else if (asprof_range->start != 0) {
      int i = 0;
      while (prev_line[++i] != '-')
        ;
      ++i;
      int j = i;
      while (prev_line[++j] != ' ')
        ;
      prev_line[j] = 0;
      asprof_range->end = strtoul(prev_line + i, NULL, 16);
      break;
    }
  }
}

extern "C" __attribute__((constructor)) void tracing_constructor(void) {
  FILE *proc_maps_in = fopen("/proc/self/maps", "r");
  if (proc_maps_in == NULL) {
    fprintf(stderr, "Could not open /proc/self/maps\n");
    return;
  }

  const char *proc_maps_out_name = getenv("PROC_MAPS_COPY_PATH");
  FILE *proc_maps_out = fopen(proc_maps_out_name, "w");
  if (proc_maps_out == NULL) {
    fprintf(stderr, "Could not open '%s'\n", proc_maps_out_name);
    return;
  }

  char buffer[1024];
  size_t read_chars;
  while ((read_chars = fread(buffer, sizeof(char), 1024, proc_maps_in)) > 0) {
    if (fwrite(buffer, sizeof(char), read_chars, proc_maps_out) != read_chars) {
      fprintf(stderr, "An error occurred\n");
      break;
    }
  }

  fclose(proc_maps_in);
  fclose(proc_maps_out);
}

extern "C" __attribute__((destructor)) void tracing_deconstructor(void) {
  pthread_mutex_lock(&mutex);
  for (int i = 0; i < fp_array_next_idx; i++) {
    fflush(fp_array[i]);
    fclose(fp_array[i]);
  }
  free(fp_array);
  free(asprof_range);
  pthread_mutex_unlock(&mutex);
}

extern "C" void __cyg_profile_func_enter(void *callee, void *caller) {
  if (fp == NULL) {
    pthread_mutex_lock(&mutex);

    char buffer[50];
    sprintf(buffer, "traces%d.txt", gettid());
    // Truncate
    fp = fopen(buffer, "w");
    if (fp == NULL) {
      fprintf(stderr, "Could not open file %s\n", buffer);
      return;
    }
    fp = freopen(buffer, "a", fp);
    if (fp == NULL) {
      fprintf(stderr, "Could not reopen file %s\n", buffer);
      return;
    }

    last_rtdsc = rdtsc();

    if (fp_array == NULL) {
      fp_array = (FILE **)malloc(50 * sizeof(FILE *));
      initialize_asprof_address_range();
    }
    fp_array[fp_array_next_idx++] = fp;

    pthread_mutex_unlock(&mutex);
  }

  if (!check_asprof_range((uintptr_t)callee))
    return;

  char buffer[50];
  u64 now = rdtsc();
  sprintf(buffer, "E,%u,%p,%p\n", (u32)(now - last_rtdsc), (int *)caller,
          (int *)callee);
  if (!atomic_flag_test_and_set(&lock_taken)) {
    last_rtdsc = now;
    fputs(buffer, fp);
    atomic_flag_clear(&lock_taken);
  } else {
    fprintf(stderr, "Dropping E %p -> %p\n", caller, callee);
  }
}

extern "C" void __cyg_profile_func_exit(void *callee, void *caller) {
  if (!check_asprof_range((uintptr_t)callee))
    return;

  char buffer[50];
  u64 now = rdtsc();
  sprintf(buffer, "X,%u,%p,%p\n", (u32)(now - last_rtdsc), (int *)caller,
          (int *)callee);
  if (!atomic_flag_test_and_set(&lock_taken)) {
    last_rtdsc = now;
    fputs(buffer, fp);
    atomic_flag_clear(&lock_taken);
  } else {
    fprintf(stderr, "Dropping X %p -> %p\n", caller, callee);
  }
}
