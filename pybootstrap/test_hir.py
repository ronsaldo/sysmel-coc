import unittest
from hir import *

class HIRTest(unittest.TestCase):
    def setUp(self):
        self.context = HIRContext()
        self.package = HIRPackage('Test')
        self.package.usePackage(self.context.corePackage)
        self.context.currentPackage = self.package
        return super().setUp()
    
    def testEmptyPackage(self):
        self.assertTrue(len(self.context.currentPackage.children) == 0)

if __name__ == '__main__':
    unittest.main()