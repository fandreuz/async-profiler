#include "tsc.h"
#include "profiler.h"
#include <unordered_map>
#include <stdint.h>
#include <iostream>
#include <unistd.h>
#include <fstream>
#include <sstream>
#include <memory>
#include <vector>
#include <pthread.h>

thread_local bool enabled = true;

void print_thread_name(std::ostream& out) {
    char name[16]{};
    if(pthread_getname_np(pthread_self(), name, sizeof(name)) == 0) {
        out << name;
    }
}

struct ThreadNode;

struct ThreadNode {
  std::unordered_map<void*, ThreadNode> children;
  ThreadNode* parent;
  void* address;
  u64 total_time;
  u64 last_entry;
  u64 count;

  ThreadNode() : parent(nullptr), address(nullptr), total_time(0), last_entry(0), count(0) {}
  ThreadNode(ThreadNode* parent, void* address) : parent(parent), address(address), total_time(0), last_entry(0), count(0) {}

  u64 dfs(std::ostream& out, std::vector<const char*>& parents) const;
  
  ~ThreadNode() {
    // Start DFS only if I'm root
    if (address != nullptr) {
      return;
    }

    enabled = false;

    std::ostringstream filename;
    filename << "traces" << gettid() << ".txt";

    std::ofstream out(filename.str());

    out << "Thread: ";
    print_thread_name(out);
    out << std::endl;

    std::vector<const char*> parents;
    for (auto const & child : children) {
      child.second.dfs(out, parents);
    }
    out.close();
  }
};

char* get_function_name(void *address, bool *free_later) {
  const char* function_name = Profiler::instance()->findNativeMethod(address);
  if (Demangle::needsDemangling(function_name)) {
      char* demangled = Demangle::demangle(function_name, false);
      if (demangled != NULL) {
          *free_later = true;
          return demangled;
      }
  }
  *free_later = false;
  return const_cast<char*>(function_name);
}

u64 ThreadNode::dfs(std::ostream& out, std::vector<const char*>& parents) const {
  bool free_later;
  char* function_name = get_function_name(address, &free_later);
  parents.push_back(function_name);

  u64 children_time = 0;
  for (auto const & child : children) {
    children_time += child.second.dfs(out, parents);
  }
  parents.pop_back();

  for (auto const & parent : parents) {
    out << parent << ';';
  }

  if (count == 0) {
    return 0;
  }

  out << function_name << ' ' << total_time - children_time << ' ' << count << '\n';

  if (free_later) {
    free(function_name);
  }

  return total_time;
}

thread_local ThreadNode* current;
thread_local std::unique_ptr<ThreadNode> root = []{
  auto ptr = std::unique_ptr<ThreadNode>(new ThreadNode());
  current = ptr.get();
  return std::move(ptr);
}();

extern "C" void __cyg_profile_func_enter(void *callee, void *caller) {
  (void)root;

  if (!enabled) {
    return;
  }

  (current = &current->children.try_emplace(callee, current, callee).first->second)->last_entry = rdtsc();
}

extern "C" void __cyg_profile_func_exit(void *callee, void *caller) {
  if (!enabled) {
    return;
  }

  if (current->address != callee) {
    std::cerr << "Unexpected callee " << callee << std::endl;
    return;
  }
  current->total_time += rdtsc() - current->last_entry;
  current->count++;
  current = current->parent;
}
