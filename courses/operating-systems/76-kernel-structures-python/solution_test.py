import unittest

from solution import Bitmap, build, height, insert, search_steps

EXAMPLE = [17, 12, 35, 6, 14, 32, 40]


class Bitmaps(unittest.TestCase):
    def test_starts_free(self):
        """A new bitmap has every item free"""
        b = Bitmap(8)
        self.assertEqual(str(b), "00000000")
        self.assertEqual(b.count_used(), 0)
        self.assertFalse(any(b.is_used(i) for i in range(8)))

    def test_reading_example(self):
        """Items 2, 4, 5, and 8 in use, from the reading"""
        b = Bitmap(10)
        for i in (2, 4, 5, 8):
            b.use(i)
        self.assertEqual(str(b), "0010110010")
        self.assertEqual(b.count_used(), 4)
        self.assertTrue(b.is_used(5))
        self.assertFalse(b.is_used(3))

    def test_uses_one_integer(self):
        """Bits live in self.bits: bit i is item i"""
        b = Bitmap(10)
        b.use(0)
        b.use(3)
        self.assertEqual(b.bits, 0b1001)

    def test_free(self):
        """Freeing an item clears its bit, and only its bit"""
        b = Bitmap(4)
        for i in range(4):
            b.use(i)
        b.free(1)
        self.assertEqual(str(b), "1011")
        b.free(1)
        self.assertEqual(str(b), "1011")

    def test_allocate(self):
        """allocate hands out the lowest free item"""
        b = Bitmap(5)
        b.use(0)
        b.use(1)
        b.use(3)
        self.assertEqual(b.allocate(), 2)
        self.assertEqual(b.allocate(), 4)
        self.assertEqual(b.allocate(), -1)
        b.free(1)
        self.assertEqual(b.allocate(), 1)
        self.assertEqual(str(b), "11111")

    def test_out_of_range(self):
        """Items outside 0..n-1 raise IndexError"""
        b = Bitmap(4)
        for bad in (-1, 4, 100):
            with self.subTest(i=bad):
                with self.assertRaises(IndexError):
                    b.use(bad)
                with self.assertRaises(IndexError):
                    b.is_used(bad)
                with self.assertRaises(IndexError):
                    b.free(bad)

    def test_large(self):
        """A bitmap for a million blocks"""
        b = Bitmap(1_000_000)
        b.use(999_999)
        self.assertTrue(b.is_used(999_999))
        self.assertEqual(b.allocate(), 0)
        self.assertEqual(b.count_used(), 2)


class Trees(unittest.TestCase):
    def test_empty(self):
        """An empty tree"""
        self.assertEqual(height(None), 0)
        self.assertEqual(search_steps(None, 5), 0)
        self.assertIsNone(build([]))

    def test_insert_shape(self):
        """Smaller keys go left, larger go right"""
        root = build(EXAMPLE)
        self.assertEqual(root.key, 17)
        self.assertEqual((root.left.key, root.right.key), (12, 35))
        self.assertEqual((root.left.left.key, root.left.right.key), (6, 14))
        self.assertEqual((root.right.left.key, root.right.right.key), (32, 40))

    def test_insert_returns_root(self):
        """insert returns the (possibly new) root"""
        root = insert(None, 5)
        self.assertEqual(root.key, 5)
        self.assertIs(insert(root, 3), root)
        self.assertEqual(root.left.key, 3)

    def test_equal_keys_go_right(self):
        """Keys equal to a node go right"""
        root = build([5, 5])
        self.assertIsNone(root.left)
        self.assertEqual(root.right.key, 5)

    def test_reading_search(self):
        """Finding 32 takes three steps: 17, 35, 32"""
        root = build(EXAMPLE)
        self.assertEqual(search_steps(root, 32), 3)
        self.assertEqual(search_steps(root, 17), 1)
        self.assertEqual(search_steps(root, 12), 2)

    def test_missing_key(self):
        """A missing key counts the nodes visited"""
        root = build(EXAMPLE)
        self.assertEqual(search_steps(root, 33), 3)   # 17, 35, 32, then off the bottom
        self.assertEqual(search_steps(root, 1), 3)

    def test_balanced_vs_sorted(self):
        """Same keys: height 3 in a good order, 7 in sorted order"""
        self.assertEqual(height(build(EXAMPLE)), 3)
        chain = build(sorted(EXAMPLE))
        self.assertEqual(height(chain), 7)
        self.assertEqual(search_steps(chain, 40), 7)

    def test_big_chain(self):
        """Sorted keys make the tree a linked list: O(n)"""
        chain = build(range(200))
        self.assertEqual(height(chain), 200)
        self.assertEqual(search_steps(chain, 199), 200)


if __name__ == "__main__":
    unittest.main()
