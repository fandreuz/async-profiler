#include <stdio.h>
#include "os.h"
#include "tsc.h"
#define N 100000
#define BIG 0x7FFFFFFFFFFFFFFF

static size_t francesco(u64 value) {
    if (value <= 0x7F) return 1;
    if (value <= 0x3FFF) return 2;
    if (value <= 0x1FFFFF) return 3;
    if (value <= 0xFFFFFFF) return 4;
    if (value <= 0x7FFFFFFFF) return 5;
    if (value <= 0x3FFFFFFFFFF) return 6;
    if (value <= 0x1FFFFFFFFFFFF) return 7;
    if (value <= 0xFFFFFFFFFFFFFF) return 8;
    if (value <= 0x7FFFFFFFFFFFFFFF) return 9;
    return 10;
}

static size_t andrei(u64 value) {
    return (640 - __builtin_clzll(value | 1) * 9) / 64;
}

static size_t bara(u64 value) {
  size_t size = 1;
  while ((value = value >> 7)) {
    size++;
  }
  return size;
}

int main() {
  u64 sink = 0;

  u64 before = rdtsc();
  for (u64 i = 0; i < N; ++i) sink += francesco(i);
  for (u64 i = BIG; i > BIG - N; --i) sink += francesco(i);
  u64 after = rdtsc();
  printf("Francesco: %08llu\n", after - before);

  before = rdtsc();
  for (u64 i = 0; i < N; ++i) sink += andrei(i);
  for (u64 i = BIG; i > BIG - N; --i) sink += andrei(i);
  after = rdtsc();
  printf("Andrei   : %08llu\n", after - before);

  before = rdtsc();
  for (u64 i = 0; i < N; ++i) sink += bara(i);
  for (u64 i = BIG; i > BIG - N; --i) sink += bara(i);
  after = rdtsc();
  printf("Bara     : %08llu\n", after - before);

  printf("Sink ignore me: %llu\n", sink);
}