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
    
    def compileFunctionToMir(self, sourceString) -> MirFunction:
        hirFunction = self.evaluateTopLevelSourceString(sourceString)
        self.assertTrue(hirFunction.isFunction())
        mirPackage = self.compilePackageToMir()
        return mirPackage.translatedFunctionMap[hirFunction]
    
    def testEmpty(self):
        self.evaluateTopLevelSourceString('')
        mirPackage = self.compilePackageToMir()
        self.assertTrue(len(mirPackage.elementTable) == 0)

    def testIntegerIdentityFunction(self):
        mirFunction = self.compileFunctionToMir('public function identity(value: Integer) => Integer := value')
        result = mirFunction.evaluateWithArguments([42])
        self.assertEqual(result, 42)

    def testIntegerSumFunction(self):
        mirFunction = self.compileFunctionToMir('public function sum(first: Integer. second: Integer) => Integer := first + second')
        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testIntegerCallSumFunction(self):
        mirFunction = self.compileFunctionToMir("""
            function sum(first: Integer. second: Integer) => Integer := first + second.
            public function callSum(first: Integer. second: Integer) => Integer := sum(first. second).
        """)
        
        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)

    def testIntegerConstant(self):
        mirFunction = self.compileFunctionToMir('public function constant() => Integer := 42')
        #mirFunction.dumpToConsole()
        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42)

    def testCharacterConstant(self):
        mirFunction = self.compileFunctionToMir("public function constant() => Character := 'A'")
        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, ord('A'))

    def testFloatConstant(self):
        mirFunction = self.compileFunctionToMir("public function constant() => Float := 42.5")
        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42.5)

    def testFloat32Constant(self):
        mirFunction = self.compileFunctionToMir("public function constant() => Float32 := 42.5f32")
        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42.5)

    def testFloat64Constant(self):
        mirFunction = self.compileFunctionToMir("public function constant() => Float64 := 42.5f64")
        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 42.5)

    def testInt32Let(self):
        mirFunction = self.compileFunctionToMir("public function constant(x: Int32) => Int32 := {let y := x. y + 5i32}")
        result = mirFunction.evaluateWithArguments([0])
        self.assertEqual(result, 5)

    def testInt32LetMutable(self):
        mirFunction = self.compileFunctionToMir("public function constant(x: Int32) => Int32 := {let y mutable := x. y := y + 5i32. y + 7i32}")
        result = mirFunction.evaluateWithArguments([0])
        self.assertEqual(result, 12)

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
        
        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 1)

        result = mirFunction.evaluateWithArguments([2, 1])
        self.assertEqual(result, 1)

    def testInt32NegFunction(self):
        mirFunction = self.compileFunctionToMir("public function int32Neg(a: Int32) => Int32 := a negated")
        
        result = mirFunction.evaluateWithArguments([1])
        self.assertEqual(result, -1)

    def testInt32ArithmeticFunction(self):
        mirFunction = self.compileFunctionToMir("public function arithmetic(a: Int32. b: Int32. c: Int32. d: Int32. e: Int32) => Int32 := a negated + b - ((c * d) // e)")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5])
        self.assertEqual(result, -1)

    def testInt32BitwiseFunction(self):
        mirFunction = self.compileFunctionToMir("public function bitwise(a: Int32. b: Int32. c: Int32. d: Int32. e: Int32. f: Int32) => Int32 := a bitInvert & b | c ^ d << e >> f")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5, 6])
        self.assertEqual(result, 3)

    def testIntUInt32MinFunction(self):
        mirFunction = self.compileFunctionToMir('public function min(first: UInt32. second: UInt32) => UInt32 := if: first < second then: first else: second')
        
        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 1)

        result = mirFunction.evaluateWithArguments([2, 1])
        self.assertEqual(result, 1)

    def testUInt32CallSumFunction(self):
        mirFunction = self.compileFunctionToMir("""
            function sum(first: UInt32. second: UInt32) => UInt32 := first + second.
            public function callSum() => UInt32 := sum(1u32. 2u32).
        """)

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 3)

    def testUInt32ArithmeticFunction(self):
        mirFunction = self.compileFunctionToMir("public function arithmetic(a: UInt32. b: UInt32. c: UInt32. d: UInt32. e: UInt32) => UInt32 := a negated + b - ((c * d) // e)")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5])
        self.assertEqual(result, -1)

    def testUInt32BitwiseFunction(self):
        mirFunction = self.compileFunctionToMir("public function bitwise(a: UInt32. b: UInt32. c: UInt32. d: UInt32. e: UInt32. f: UInt32) => UInt32 := a bitInvert & b | c ^ d << e >> f")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5, 6])
        self.assertEqual(result, 3)

    def testInt64identityFunction(self):
        mirFunction = self.compileFunctionToMir('public function identity(value: Int64) => Int64 := value')
        result = mirFunction.evaluateWithArguments([42])
        self.assertEqual(result, 42)

    def testInt64SumFunction(self):
        mirFunction = self.compileFunctionToMir('public function sum(first: Int64. second: Int64) => Int64 := first + second')
        result = mirFunction.evaluateWithArguments([1, 2])
        self.assertEqual(result, 3)


    def testInt64CallSumFunction(self):
        mirFunction = self.compileFunctionToMir("""
            function sum(first: Int64. second: Int64) => Int64 := first + second.
            public function callSum() => Int64 := sum(1i64. 2i64).
        """)

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 3)

    def testInt64NegFunction(self):
        mirFunction = self.compileFunctionToMir("public function int64Neg(a: Int64) => Int64 := a negated")
        result = mirFunction.evaluateWithArguments([1])
        self.assertEqual(result, -1)

    def testInt64ArithmeticFunction(self):
        mirFunction = self.compileFunctionToMir("public function arithmetic(a: Int64. b: Int64. c: Int64. d: Int64. e: Int64) => Int64 := a negated + b - ((c * d) // e)")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5])
        self.assertEqual(result, -1)

    def testInt64BitwiseFunction(self):
        mirFunction = self.compileFunctionToMir("public function bitwise(a: Int64. b: Int64. c: Int64. d: Int64. e: Int64. f: Int64) => Int64 := a bitInvert & b | c ^ d << e >> f")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5, 6])
        self.assertEqual(result, 3)

    def testUInt64CallSumFunction(self):
        mirFunction = self.compileFunctionToMir("""
            function sum(first: UInt64. second: UInt64) => UInt64 := first + second.
            public function callSum() => UInt64 := sum(1u64. 2u64).
        """)

        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(result, 3)

    def testUInt64ArithmeticFunction(self):
        mirFunction = self.compileFunctionToMir("public function arithmetic(a: UInt64. b: UInt64. c: UInt64. d: UInt64. e: UInt64) => UInt64 := a negated + b - ((c * d) // e)")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5])
        self.assertEqual(result, -1)

    def testUInt64BitwiseFunction(self):
        mirFunction = self.compileFunctionToMir("public function bitwise(a: UInt64. b: UInt64. c: UInt64. d: UInt64. e: UInt64. f: UInt64) => UInt64 := a bitInvert & b | c ^ d << e >> f")
        result = mirFunction.evaluateWithArguments([1, 2, 3, 4, 5, 6])
        self.assertEqual(result, 3)

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

    def testClassInstantiation(self):
        mirFunction = self.compileFunctionToMir("""
        class TestPair definition: {
            public field first type: Int32.
            public field second type: Int32.
        }.
        public function makePair() => TestPair := TestPair()
""")
        result = mirFunction.evaluateWithArguments([])
        self.assertTrue(result.isMirMemorySimulationPointer())
        self.assertEqual(0, result.loadInt32())
        self.assertEqual(0, (result + 4).loadInt32())

    def testClassInstantiation2(self):
        mirFunction = self.compileFunctionToMir("""
        class TestPair definition: {
            public field first type: Int32.
            public field second type: Int32.
        }.
        public function makePair() => TestPair := TestPair(1i32. 2i32)
""")

        result = mirFunction.evaluateWithArguments([])
        self.assertTrue(result.isMirMemorySimulationPointer())
        self.assertEqual(1, result.loadInt32())
        self.assertEqual(2, (result + 4).loadInt32())

    def testClassExplicitFieldAccess(self):
        mirFunction = self.compileFunctionToMir("""
        class TestPair definition: {
            public field first type: Int32.
            public field second type: Int32.
        }.
        public function getSecond(pair: TestPair) => Int32 := pair second.
""")

        structPointer = MirMemorySimulationPointer(MirMemorySimulation(8), 0)
        structPointer.storeInt32(1)
        (structPointer + 4).storeInt32(2)

        result = mirFunction.evaluateWithArguments([structPointer])
        self.assertEqual(result, 2)

    def testStructInstantiation(self):
        mirFunction = self.compileFunctionToMir("""
        struct TestPair definition: {
            public field first type: Int32.
            public field second type: Int32.
        }.
        public function makePair() => TestPair := TestPair()
""")
        
        result = mirFunction.evaluateWithArguments([])
        self.assertTrue(result.isMirMemorySimulationPointer())
        self.assertEqual(0, result.loadInt32())
        self.assertEqual(0, (result + 4).loadInt32())


    def testStructInstantiation2(self):
        mirFunction = self.compileFunctionToMir("""
        struct TestPair definition: {
            public field first type: Int32.
            public field second type: Int32.
        }.
        public function makePair() => TestPair := TestPair(1i32. 2i32)
""")
        result = mirFunction.evaluateWithArguments([])
        self.assertTrue(result.isMirMemorySimulationPointer())
        self.assertEqual(1, result.loadInt32())
        self.assertEqual(2, (result + 4).loadInt32())

    def testStructExplicitFieldAccess(self):
        mirFunction = self.compileFunctionToMir("""
        struct TestPair definition: {
            public field first type: Int32.
            public field second type: Int32.
        }.
        public function getSecond(pair: TestPair) => Int32 := pair second.
""")

        structPointer = MirMemorySimulationPointer(MirMemorySimulation(8), 0)
        structPointer.storeInt32(1)
        (structPointer + 4).storeInt32(2)

        result = mirFunction.evaluateWithArguments([structPointer])
        self.assertEqual(result, 2)

    def testEnumAccess(self):
        mirFunction = self.compileFunctionToMir("""
        enum MyEnum baseType: Int32 values: #{First: 1i32. Second: 2i32. Third:}.
        public function getThird() => MyEnum := MyEnum Third
""")
        result = mirFunction.evaluateWithArguments([])
        self.assertEqual(3, result)

    def testEnumValueAccess(self):
        mirFunction = self.compileFunctionToMir("""
        enum MyEnum baseType: Int32 values: #{First: 1i32. Second: 2i32. Third:}.
        public function access(e: MyEnum) => Int32 := e value.
""")
        result = mirFunction.evaluateWithArguments([2])
        self.assertEqual(2, result)

    def testEnumValueMake(self):
        mirFunction = self.compileFunctionToMir("""
        enum MyEnum baseType: Int32 values: #{First: 1i32. Second: 2i32. Third:}.
        public function access(v: Int32) => MyEnum := MyEnum value: v.
""")
        result = mirFunction.evaluateWithArguments([2])
        self.assertEqual(2, result)

if __name__ == '__main__':
    unittest.main()