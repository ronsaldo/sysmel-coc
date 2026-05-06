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
    
    def testEmpty(self):
        self.evaluateTopLevelSourceString('')
        mirPackage = self.compilePackageToMir()
        self.assertTrue(len(mirPackage.elementTable) == 0)

    def testIntegerAdd(self):
        addFunction = self.evaluateTopLevelSourceString('public function add(x: Integer. y: Integer) => Integer := x + y')
        self.assertTrue(addFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        addMirFunction = mirPackage.translatedFunctionMap[addFunction]

        result = addMirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testInt32Add(self):
        addFunction = self.evaluateTopLevelSourceString('public function add(x: Int32. y: Int32) => Int32 := x + y')
        self.assertTrue(addFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        addMirFunction = mirPackage.translatedFunctionMap[addFunction]

        result = addMirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testReturnChar8(self):
        hirFunction = self.evaluateTopLevelSourceString("public function testReturnChar8() => Char8 := 'A'c8")
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, ord('A'))

    def testReturnFloat32(self):
        hirFunction = self.evaluateTopLevelSourceString('public function returnInteger() => Float32 := 42f32')
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)


    def testReturnInt32(self):
        hirFunction = self.evaluateTopLevelSourceString('public function returnInteger() => Int32 := 42i32')
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)

    def testReturnCharacter(self):
        hirFunction = self.evaluateTopLevelSourceString("public function returnInteger() => Character := 'A'")
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, ord('A'))

    def testReturnFloat(self):
        hirFunction = self.evaluateTopLevelSourceString("public function returnInteger() => Float := 42.5")
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42.5)

    def testReturnInteger(self):
        hirFunction = self.evaluateTopLevelSourceString('public function returnInteger() => Integer := 42')
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)

    def testReturnNilInteger(self):
        hirFunction = self.evaluateTopLevelSourceString('public function returnInteger() => Integer := nil')
        self.assertTrue(hirFunction.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[hirFunction]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 0)

    def testReturnVoid(self):
        function = self.evaluateTopLevelSourceString('public function returnVoid() => Void := void')
        self.assertTrue(function.isFunction())

        mirPackage = self.compilePackageToMir()
        mirFunction = mirPackage.translatedFunctionMap[function]

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, None)

if __name__ == '__main__':
    unittest.main()