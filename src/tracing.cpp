#include "tsc.h"
#include <unordered_map>
#include <stdint.h>
#include <iostream>
#include <unistd.h>
#include <fstream>
#include <sstream>
#include <memory>
#include <vector>

struct ThreadNode;

void dfs(std::ostream& out, std::vector<void*>& parents, const ThreadNode* node);

struct ThreadNode {
  std::unordered_map<void*, ThreadNode*> children;
  ThreadNode* parent;
  void* address;
  u64 total_time;
  u64 last_entry;

  ThreadNode() : parent(nullptr) {}
  ThreadNode(ThreadNode* parent, void* address) : parent(parent), address(address) {} 
  
  ~ThreadNode() {
    std::ostringstream filename;
    filename << "thread" << gettid() << ".txt";

    std::ofstream out(filename.str());
    std::vector<void*> parents;
    for (auto const & child : children) {
      dfs(out, parents, child.second);
    }
    out.close();
  }
};

void dfs(std::ostream& out, std::vector<void*>& parents, const ThreadNode* node) {
  parents.push_back(node->address);
  for (auto const & child : node->children) {
    dfs(out, parents, child.second);
  }
  parents.pop_back();

  for (auto const & parent : parents) {
    out << parent << ';';
  }
  out << node->address << ' ' << node->total_time << '\n';
}

thread_local std::unique_ptr<ThreadNode> root;
thread_local ThreadNode* current;

extern "C" void __cyg_profile_func_enter(void *callee, void *caller) {
  if (!root) {
    root = std::unique_ptr<ThreadNode>(new ThreadNode());
    current = root.get();
  }

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
  current->total_time += (rdtsc() - current->last_entry);
  current->last_entry = 0;
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
