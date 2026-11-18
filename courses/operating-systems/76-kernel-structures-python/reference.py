"""A bitmap and a binary search tree, two kernel data structures."""


class Bitmap:
    def __init__(self, n):
        self.n = n
        self.bits = 0

    def _check(self, i):
        if not 0 <= i < self.n:
            raise IndexError(f"item {i} out of range 0..{self.n - 1}")

    def is_used(self, i):
        self._check(i)
        return (self.bits >> i) & 1 == 1

    def use(self, i):
        self._check(i)
        self.bits |= 1 << i

    def free(self, i):
        self._check(i)
        self.bits &= ~(1 << i)

    def allocate(self):
        for i in range(self.n):
            if not (self.bits >> i) & 1:
                self.bits |= 1 << i
                return i
        return -1

    def count_used(self):
        return bin(self.bits).count("1")

    def __str__(self):
        return "".join(str((self.bits >> i) & 1) for i in range(self.n))


class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


def insert(root, key):
    if root is None:
        return Node(key)
    if key < root.key:
        root.left = insert(root.left, key)
    else:
        root.right = insert(root.right, key)
    return root


def search_steps(root, key):
    steps = 0
    node = root
    while node is not None:
        steps += 1
        if key == node.key:
            return steps
        node = node.left if key < node.key else node.right
    return steps


def height(root):
    if root is None:
        return 0
    return 1 + max(height(root.left), height(root.right))


def build(keys):
    root = None
    for k in keys:
        root = insert(root, k)
    return root
