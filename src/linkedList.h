/*
 * Copyright The async-profiler authors
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef _LINKEDLIST_H
#define _LINKEDLIST_H

#include <stdlib.h>
#include "arch.h"

template<class T>
class LinkedListNode {
  public:
    LinkedListNode* next;
    T value;

    LinkedListNode() : LinkedListNode(nullptr, 0) {}
    LinkedListNode(LinkedListNode* next, T value) : next(next), value(value) {}

    ~LinkedListNode() {
        delete next;
    }

    LinkedListNode<T>* insert8(u8 value) {
        next = new LinkedListNode(next, value);
        return next;
    }

    LinkedListNode<T>* insert16(u16 value) {
        return insert8((value >> 8) & 0xFF)->insert8(value & 0xFF);
    }
};

template<class T>
LinkedListNode<T>* toLinkedList(const T* arr, size_t len) {
    if (len == 0) return nullptr;

    LinkedListNode<T>* node = new LinkedListNode<T>(nullptr, arr[0]);
    LinkedListNode<T>* head = node;
    for (size_t i = 1; i < len; ++i) {
        node->next = new LinkedListNode<T>(nullptr, arr[i]);
        node = node->next;
    }
    return head;
}

#endif // _LINKEDLIST_H
