import unittest
from mir import *

class MirTest(unittest.TestCase):
    def setUp(self):
        self.context = MirContext()
        self.module = MirPackage(self.context, 'TestModule')
        return super().setUp()
    
    def testEmptyModule(self):
        self.assertEqual(0, len(self.module.elementTable))

    def testReturnVoid(self):
        function = MirFunction("main")
        self.module.addElement(function)
        
        entryBlock = MirBasicBlock(None, 'entry')
        function.addBasicBlock(entryBlock)

        builder = MirBuilder(function, entryBlock)
        builder.returnVoidAt(None)

        result = function.evaluateWithArguments([])
        self.assertEqual(None, result)

    def testReturnInt32(self):
        function = MirFunction("main")
        self.module.addElement(function)
        
        entryBlock = MirBasicBlock(None, 'entry')
        function.addBasicBlock(entryBlock)

        builder = MirBuilder(function, entryBlock)
        constant = builder.constInt32At(42, None)
        builder.returnInt32At(constant, None)

        ##function.dumpToConsole()
        result = function.evaluateWithArguments([])
        self.assertEqual(result, 42)

    def makeSumInt32Function(self):
        function = MirFunction("sum")
        self.module.addElement(function)
        
        entryBlock = MirBasicBlock(None, 'entry')
        function.addBasicBlock(entryBlock)

        builder = MirBuilder(function, entryBlock)
        firstArgument = builder.argumentInt32At(None, 'first')
        secondArgument = builder.argumentInt32At(None, 'second')
        sumValue = builder.int32AddAt(firstArgument, secondArgument, None)
        builder.returnInt32At(sumValue, None)
        return function

    def testSumArguments(self):
        function = self.makeSumInt32Function()
        result = function.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testCallSumInt32(self):
        sumFunction = self.makeSumInt32Function()

        function = MirFunction("callSum")
        self.module.addElement(function)
        
        entryBlock = MirBasicBlock(None, 'entry')
        function.addBasicBlock(entryBlock)

        builder = MirBuilder(function, entryBlock)
        firstArgument = builder.constInt32At(1, None)
        secondArgument = builder.constInt32At(2, None)

        builder.beginCallAt(None)
        builder.callArgumentInt32At(firstArgument, None)
        builder.callArgumentInt32At(secondArgument, None)
        callResult = builder.callInt32ResultAt(sumFunction, None)

        builder.returnInt32At(callResult, None)        
        ##function.dumpToConsole()

        result = function.evaluateWithArguments([])
        self.assertEqual(3, result)

    def testInt32Min(self):
        function = MirFunction("sum")
        self.module.addElement(function)
        
        entryBlock = MirBasicBlock(None, 'entry')
        function.addBasicBlock(entryBlock)

        builder = MirBuilder(function, entryBlock)
        firstArgument = builder.argumentInt32At(None, 'first')
        secondArgument = builder.argumentInt32At(None, 'second')
        isLessThan = builder.int32LessThanAt(firstArgument, secondArgument, None)

        lessThanBlock = MirBasicBlock(None, 'lessThanBlock')
        greaterThanBlock = MirBasicBlock(None, 'greaterThanBlock')

        builder.conditionalBranchAt(isLessThan, lessThanBlock, greaterThanBlock, None)

        function.addBasicBlock(lessThanBlock)
        builder.basicBlock = lessThanBlock
        builder.returnInt32At(firstArgument, None)

        function.addBasicBlock(greaterThanBlock)
        builder.basicBlock = greaterThanBlock
        builder.returnInt32At(secondArgument, None)

        ## function.dumpToConsole()

        result = function.evaluateWithArguments([1, 2])
        self.assertEqual(result, 1)

        result = function.evaluateWithArguments([2, 1])
        self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
