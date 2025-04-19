#include "tsc.h"
#include <unordered_map>
#include <stdint.h>
#include <iostream>
#include <unistd.h>
#include <fstream>
#include <sstream>
#include <memory>
#include <vector>
#include <pthread.h>

void print_thread_name(std::ostream& out) {
    char name[16]{};
    if(pthread_getname_np(pthread_self(), name, sizeof(name)) == 0) {
        out << name;
    }
}

struct ThreadNode;

u64 dfs(std::ostream& out, std::vector<void*>& parents, const ThreadNode* node);

struct ThreadNode {
  std::unordered_map<void*, ThreadNode*> children;
  ThreadNode* parent;
  void* address;
  u64 total_time;
  u64 last_entry;
  u64 count;

  ThreadNode() : parent(nullptr) {
    std::cerr << "Initializing on thread: ";
    print_thread_name(std::cerr);
    std::cerr << std::endl;
  }
  ThreadNode(ThreadNode* parent, void* address) : parent(parent), address(address) {}
  
  ~ThreadNode() {
    std::cerr << "Destroying on thread: ";
    print_thread_name(std::cerr);
    std::cerr << std::endl;

    std::ostringstream filename;
    filename << "traces" << gettid() << ".txt";

    std::ofstream out(filename.str());

    out << "Thread: ";
    print_thread_name(out);
    out << std::endl;

    std::vector<void*> parents;
    for (auto const & child : children) {
      dfs(out, parents, child.second);
    }
    out.close();
  }
};

u64 dfs(std::ostream& out, std::vector<void*>& parents, const ThreadNode* node) {
  u64 children_time = 0;

  parents.push_back(node->address);
  for (auto const & child : node->children) {
    children_time += dfs(out, parents, child.second);
  }
  parents.pop_back();

  for (auto const & parent : parents) {
    out << parent << ';';
  }

  if (node->count == 0) {
    return 0;
  }

  out << node->address << ' ' << node->total_time - children_time << ' ' << node->count << '\n';
  return node->total_time;
}

thread_local ThreadNode* current;
thread_local std::unique_ptr<ThreadNode> root = []{
  auto ptr = std::unique_ptr<ThreadNode>(new ThreadNode());
  current = ptr.get();
  return std::move(ptr);
}();

extern "C" void __cyg_profile_func_enter(void *callee, void *caller) {
  (void)root;

  auto it = current->children.find((void*) callee);
  ThreadNode* next;
  if (it == current->children.end()) {
    next = new ThreadNode(current, (void*) callee);
    current->children[(void*) callee] = next;
    current = next;
  } else {
    current = it->second;
  }
  current->last_entry = rdtsc();
}

extern "C" void __cyg_profile_func_exit(void *callee, void *caller) {
  if (current->address != callee) {
    std::cerr << "Unexpected callee " << callee << std::endl;
    return;
  }
  current->total_time += rdtsc() - current->last_entry;
  current->count++;
  current = current->parent;
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
