"""A bitmap and a binary search tree, two kernel data structures."""


# ---------------------------------------------------------------------------
# Part 1: a bitmap


class Bitmap:
    def __init__(self, n):
        self.n = n
        self.bits = 0   # bit i is item i: 1 = in use, 0 = free

    def is_used(self, i):
        """True if item i is in use. IndexError unless 0 <= i < n."""
        # TODO
        pass

    def use(self, i):
        """Mark item i in use. IndexError unless 0 <= i < n."""
        # TODO
        pass

    def free(self, i):
        """Mark item i free. IndexError unless 0 <= i < n."""
        # TODO
        pass

    def allocate(self):
        """Mark the lowest-numbered free item in use and return it; -1 if none."""
        # TODO
        pass

    def count_used(self):
        """How many items are in use."""
        # TODO
        pass

    def __str__(self):
        """The bits as "0"/"1" characters, item 0 first."""
        # TODO
        return ""


# ---------------------------------------------------------------------------
# Part 2: a binary search tree


class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


def insert(root, key):
    """Insert key and return the root. Smaller keys go left; >= go right."""
    # TODO
    pass


def search_steps(root, key):
    """Nodes visited to find key, counting the one where it's found. If it's
    missing, the nodes visited before falling off the bottom."""
    # TODO
    pass


def height(root):
    """Nodes on the longest root-to-leaf path. Empty tree: 0."""
    # TODO
    pass


def build(keys):
    """Insert keys in order into an empty tree; return the root."""
    # TODO
    pass


if __name__ == "__main__":
    b = Bitmap(10)
    for i in (2, 4, 5, 8):
        b.use(i)
    print(b)                  # 0010110010
    print(b.allocate())       # 0
    print(b.count_used())     # 5

    tree = build([17, 12, 35, 6, 14, 32, 40])
    print(height(tree))                 # 3
    print(search_steps(tree, 32))       # 3
    print(height(build(sorted([17, 12, 35, 6, 14, 32, 40]))))   # 7
