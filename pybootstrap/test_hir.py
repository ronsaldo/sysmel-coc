import unittest
from hir import *

class HIRTest(unittest.TestCase):
    def setUp(self):
        self.context = HIRContext()
        return super().setUp()

if __name__ == '__main__':
    unittest.main()