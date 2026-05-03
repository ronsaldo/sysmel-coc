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

    def testIdentityFunction(self):
        argument = HIRArgument(self.context.coreTypes.integerType, "x")
        functionType = HIRDependentFunctionType([argument], self.context.coreTypes.integerType, self.context.coreTypes, None)
        identity = HIRFunction('test', functionType, None)
        
        entryBlock = HIRBasicBlock('entry', None)
        identity.addBasicBlock(entryBlock)

        print(identity.fullPrintString())

if __name__ == '__main__':
    unittest.main()