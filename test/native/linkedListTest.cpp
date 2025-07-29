/*
 * Copyright The async-profiler authors
 * SPDX-License-Identifier: Apache-2.0
 */

#include "linkedList.h"
#include "testRunner.hpp"

TEST_CASE(LinkedList_insert8) {
    LinkedListNode<u8>* node3 = new LinkedListNode<u8>(nullptr, 3);
    LinkedListNode<u8>* node2 = new LinkedListNode<u8>(node3, 2);
    LinkedListNode<u8>* node1 = new LinkedListNode<u8>(node2, 1);

    node2->insert8(10);

    CHECK_EQ(node1->value, 1);
    CHECK_EQ(node1->next->value, 2);
    CHECK_EQ(node1->next->next->value, 10);
    CHECK_EQ(node1->next->next->next->value, 3);
    CHECK_EQ(node1->next->next->next->next, nullptr);
}

TEST_CASE(LinkedList_insert16) {
    LinkedListNode<u8>* node3 = new LinkedListNode<u8>(nullptr, 3);
    LinkedListNode<u8>* node2 = new LinkedListNode<u8>(node3, 2);
    LinkedListNode<u8>* node1 = new LinkedListNode<u8>(node2, 1);

    node2->insert16(5 << 8 | 6);

    CHECK_EQ(node1->value, 1);
    CHECK_EQ(node1->next->value, 2);
    CHECK_EQ(node1->next->next->value, 5);
    CHECK_EQ(node1->next->next->next->value, 6);
    CHECK_EQ(node1->next->next->next->next->value, 3);
    CHECK_EQ(node1->next->next->next->next->next, nullptr);
}

TEST_CASE(LinkedList_toLinkedList) {
    u8 arr[] = {1, 2, 3, 4};
    LinkedListNode<u8>* head = toLinkedList<u8>(arr, 4);

    CHECK_EQ(head->value, 1);
    CHECK_EQ(head->next->value, 2);
    CHECK_EQ(head->next->next->value, 3);
    CHECK_EQ(head->next->next->next->value, 4);
    CHECK_EQ(head->next->next->next->next, nullptr);
}

TEST_CASE(LinkedList_destructor) {
    u8 arr[] = {1, 2, 3, 4};
    LinkedListNode<u8>* head = toLinkedList(arr, 4);
    delete head;
}
