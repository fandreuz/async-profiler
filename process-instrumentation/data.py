from __future__ import annotations

import typing


class TrieNode:
    def __init__(self, name: str, parent: typing.Optional[TrieNode] = None):
        self.name = name
        self.children: dict[str, TrieNode] = dict()
        self.parent = parent

        self.last_entry_time_ns = -1
        self.time_ns = 0
