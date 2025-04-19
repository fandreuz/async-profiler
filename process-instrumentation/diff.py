import sys
import linecache

if __name__ == "__main__":
    left_file = sys.argv[1]
    right_file = sys.argv[2]

    left_file_lineno = 1
    right_file_lineno = 1
    while (left_line := linecache.getline(left_file, left_file_lineno).strip()) and (
        right_line := linecache.getline(right_file, right_file_lineno).strip()
    ):
        left_tree, left_value = left_line.rsplit(" ", maxsplit=1)
        right_tree, right_value = right_line.rsplit(" ", maxsplit=1)

        if left_tree == right_tree:
            tree = left_tree
            left_file_lineno += 1
            right_file_lineno += 1
        elif left_tree < right_tree:
            tree = left_tree
            right_value = 0
            left_file_lineno += 1
        else:
            tree = right_tree
            left_value = 0
            right_file_lineno += 1

        print(f"{tree} {left_value} {right_value}")
