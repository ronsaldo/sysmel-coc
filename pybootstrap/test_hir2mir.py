import unittest
from parsetree import *
from parser import parseSourceString
from analysisAndEvaluation import AnalysisAndEvaluationPass
from hir import *
from hir2mir import *

class HIR2MIRTest(unittest.TestCase):
    def setUp(self):
        self.context = HIRContext()
        self.package = HIRPackage('Test')
        self.package.usePackage(self.context.corePackage)
        self.context.currentPackage = self.package

        self.mirContext = MirContext()
        self.mirPackage = None

        return super().setUp()
    
    def tearDown(self):
        self.context.finishPendingAnalysis()
        return super().tearDown()
    
    def parseSourceStringWithoutErrors(self, string: str) -> ParseTreeNode:
        ast = parseSourceString(string)
        self.assertTrue(ParseTreeErrorVisitor().checkAndPrintErrors(ast))
        return ast
    
    def evaluateTopLevelSourceString(self, string: str):
        ast = self.parseSourceStringWithoutErrors(string)
        evaluationContext = self.context.createTopLevelEvaluationContext(ast.sourcePosition.sourceCode)
        return AnalysisAndEvaluationPass(evaluationContext).visitDecayedNode(ast)
    
    def compilePackageToMir(self) -> MirPackage:
        self.context.finishPendingAnalysis()
        self.mirPackage = HirPackage2Mir(self.context.coreTypes, self.mirContext).translateHirPackage2Mir(self.package, )
        return self.mirPackage
    
    def compileFunctionToMir(self, sourceString):
        hirFunction = self.evaluateTopLevelSourceString(sourceString)
        self.assertTrue(hirFunction.isFunction())
        mirPackage = self.compilePackageToMir()
        return mirPackage.translatedFunctionMap[hirFunction]
    
    def testEmpty(self):
        self.evaluateTopLevelSourceString('')
        mirPackage = self.compilePackageToMir()
        self.assertTrue(len(mirPackage.elementTable) == 0)

    def testIntegerAdd(self):
        mirFunction = self.compileFunctionToMir('public function add(x: Integer. y: Integer) => Integer := x + y')

        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testInt32Identity(self):
        mirFunction = self.compileFunctionToMir('public function identity(x: Int32) => Int32 := x')

        result = mirFunction.evaluateWithArguments([42])
        self.assertEqual(result, 42)

    def testInt32CallSum(self):
        mirFunction = self.compileFunctionToMir("""
            function sum(first: Int32. second: Int32) => Int32 := first + second.
            public function callSum() => Int32 := sum(1i32. 2i32).
        """)

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 3)


    def testInt32Add(self):
        mirFunction = self.compileFunctionToMir('public function add(x: Int32. y: Int32) => Int32 := x + y')

        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testInt32MinFunction(self):
        mirFunction = self.compileFunctionToMir('public function min(first: Int32. second: Int32) => Int32 := if: first < second then: first else: second')
        mirFunction.dumpToConsole()
        
        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 1)

        result = mirFunction.evaluateWithArguments([2, 1])
        self.assertEqual(result, 1)

    def testReturnChar8(self):
        mirFunction = self.compileFunctionToMir("public function testReturnChar8() => Char8 := 'A'c8")

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, ord('A'))

    def testReturnFloat32(self):
        mirFunction = self.compileFunctionToMir('public function returnFloat32() => Float32 := 42f32')

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)


    def testReturnInt32(self):
        mirFunction = self.compileFunctionToMir('public function returnInt23() => Int32 := 42i32')

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)

    def testReturnCharacter(self):
        mirFunction = self.compileFunctionToMir("public function returnCharacter() => Character := 'A'")

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, ord('A'))

    def testReturnFloat(self):
        mirFunction = self.compileFunctionToMir("public function returnInteger() => Float := 42.5")

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42.5)

    def testReturnInteger(self):
        mirFunction = self.compileFunctionToMir('public function returnInteger() => Integer := 42')

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)

    def testReturnNilInteger(self):
        mirFunction = self.compileFunctionToMir('public function returnNilInteger() => Integer := nil')

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 0)

    def testReturnVoid(self):
        mirFunction = self.compileFunctionToMir('public function returnVoid() => Void := void')

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, None)

if __name__ == '__main__':
    unittest.main()