import unittest
from parsetree import *
from parser import parseSourceString
from analysisAndEvaluation import *
from hir import *

class TestAnalysisAndEvaluation(unittest.TestCase):
    def setUp(self):
        self.context = HIRContext()
        self.package = HIRPackage('Test')
        self.package.usePackage(self.context.corePackage)
        self.context.currentPackage = self.package
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

    def testEmptyTopLevel(self):
        topLevelResult = self.evaluateTopLevelSourceString('')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testLiteralInteger(self):
        topLevelResult = self.evaluateTopLevelSourceString('42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testLiteralFloat(self):
        topLevelResult = self.evaluateTopLevelSourceString('42.5')
        self.assertTrue(topLevelResult.isFloatConstant())
        self.assertEqual(topLevelResult.value, 42.5)

    def testLiteralCharacter(self):
        topLevelResult = self.evaluateTopLevelSourceString("'A'")
        self.assertTrue(topLevelResult.isCharacterConstant())
        self.assertEqual(topLevelResult.value, ord('A'))

    def testLiteralString(self):
        topLevelResult = self.evaluateTopLevelSourceString('"Hello World"')
        self.assertTrue(topLevelResult.isStringConstant())
        self.assertEqual(topLevelResult.value, 'Hello World')

    def testLiteralSymbol(self):
        topLevelResult = self.evaluateTopLevelSourceString('#hello')
        self.assertTrue(topLevelResult.isSymbolConstant())
        self.assertEqual(topLevelResult.value, 'hello')

    def testLexicalBlock(self):
        topLevelResult = self.evaluateTopLevelSourceString('{42}')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testPackageSymbols(self):
        topLevelResult = self.evaluateTopLevelSourceString('false')
        self.assertTrue(topLevelResult.isBooleanConstant())
        self.assertFalse(topLevelResult.value)
        
        topLevelResult = self.evaluateTopLevelSourceString('true')
        self.assertTrue(topLevelResult.isBooleanConstant())
        self.assertTrue(topLevelResult.value)

        topLevelResult = self.evaluateTopLevelSourceString('void')
        self.assertTrue(topLevelResult.isVoidConstant())

        topLevelResult = self.evaluateTopLevelSourceString('nil')
        self.assertTrue(topLevelResult.isNilConstant())

    def testLetWithMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('let: #x with: 42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

        topLevelResult = self.evaluateTopLevelSourceString('let: #x with: 42. x')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testLetMutableWithMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('let: #x mutableWith: 42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

        topLevelResult = self.evaluateTopLevelSourceString('let: #x mutableWith: 42. x := 5. x')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 5)

    def testLetMetaBuilder(self):
        topLevelResult = self.evaluateTopLevelSourceString('let x := 42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

        topLevelResult = self.evaluateTopLevelSourceString('let x := 42. x')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testLetMutableMetaBuilder(self):
        topLevelResult = self.evaluateTopLevelSourceString('let x mutable := 42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

        topLevelResult = self.evaluateTopLevelSourceString('let x mutable := 42. x := 5. x')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 5)

    def testIfThenElseMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('if: true then: 1 else: 2')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 1)

        topLevelResult = self.evaluateTopLevelSourceString('if: false then: 1 else: 2')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 2)

    def testIfThenMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('if: true then: 1')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 1)

    def testSwitchMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('switch: 1 withCases: #{1 : #first. 2 : #second. _: #somethingElse}')
        self.assertTrue(topLevelResult.isSymbolConstant())
        self.assertEqual(topLevelResult.value, 'first')

        topLevelResult = self.evaluateTopLevelSourceString('switch: 2 withCases: #{1 : #first. 2 : #second. _: #somethingElse}')
        self.assertTrue(topLevelResult.isSymbolConstant())
        self.assertEqual(topLevelResult.value, 'second')

        topLevelResult = self.evaluateTopLevelSourceString('switch: 42 withCases: #{1 : #first. 2 : #second. _: #somethingElse}')
        self.assertTrue(topLevelResult.isSymbolConstant())
        self.assertEqual(topLevelResult.value, 'somethingElse')

    def testWhileDoMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('while: false do: {}')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testWhileDoContinueWithMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('while: false do: {} continueWith: ()')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testDoWhileMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('do: {} while: false')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testDoContinueWithWhileMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('do: {} continueWith: () while: false')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testQuote(self):
        topLevelResult = self.evaluateTopLevelSourceString("`'42")
        self.assertTrue(topLevelResult.isParseTreeConstant())

    def testMessageSend(self):
        value = self.evaluateTopLevelSourceString('42 negated')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(-42, value.value)

    def testMessageSend2(self):
        value = self.evaluateTopLevelSourceString('1 + 2')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(3, value.value)

        value = self.evaluateTopLevelSourceString('1 - 2')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(-1, value.value)

        value = self.evaluateTopLevelSourceString('2 * 3')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(6, value.value)

        value = self.evaluateTopLevelSourceString('6 // 3')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(2, value.value)

        value = self.evaluateTopLevelSourceString('2 = 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('2 ~= 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelSourceString('1 < 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('1 <= 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('1 > 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelSourceString('1 >= 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

    def testMessageSend3(self):
        value = self.evaluateTopLevelSourceString('42.0 negated')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(-42.0, value.value)

        value = self.evaluateTopLevelSourceString('9.0 sqrt')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(3.0, value.value)

        value = self.evaluateTopLevelSourceString('1.0 + 2.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(3.0, value.value)

        value = self.evaluateTopLevelSourceString('1.0 - 2.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(-1.0, value.value)

        value = self.evaluateTopLevelSourceString('2.0 * 3.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(6.0, value.value)

        value = self.evaluateTopLevelSourceString('6.0 / 3.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(2.0, value.value)

        value = self.evaluateTopLevelSourceString('2.0 = 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('2.0 ~= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelSourceString('1.0 < 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('1.0 <= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('1.0 > 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelSourceString('1.0 >= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

    def testMessageSendCascade(self):
        value = self.evaluateTopLevelSourceString('1.0 + 2.0; yourself')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(1.0, value.value)

    def testFunctionType(self):
        value = self.evaluateTopLevelSourceString('{:(Integer)x :: Integer}')
        self.assertTrue(value.isDependentFunctionType())
        self.assertEqual(len(value.arguments), 1)
        self.assertEqual(value.arguments[0].name, 'x')
        self.assertEqual(value.arguments[0].type, self.context.coreTypes.integerType)
        self.assertEqual(value.resultType, self.context.coreTypes.integerType)

        simplifiedType = value.asSimplifiedType()
        self.assertTrue(simplifiedType.isSimpleFunctionType())
        self.assertEqual(len(simplifiedType.argumentTypes), 1)
        self.assertEqual(simplifiedType.argumentTypes[0], self.context.coreTypes.integerType)
        self.assertEqual(simplifiedType.resultType, self.context.coreTypes.integerType)

    def testFunction(self):
        functionValue = self.evaluateTopLevelSourceString('{:(Integer)x :: Integer | x}')
        result = functionValue.evaluateWithArguments([HIRConstantLiteralIntegerValue(42, self.context.coreTypes.integerType, None)])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 42)

        functionValue = self.evaluateTopLevelSourceString('{:(Integer)x :: Integer | x negated}')
        result = functionValue.evaluateWithArguments([HIRConstantLiteralIntegerValue(42, self.context.coreTypes.integerType, None)])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, -42)

    def testFunctionMetaBuilder(self):
        functionValue = self.evaluateTopLevelSourceString('function two() => Integer := 2')
        result = functionValue.evaluateWithArguments([])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 2)

    def testFunctionMetaBuilder2(self):
        functionValue = self.evaluateTopLevelSourceString('function identity(x: Integer) => Integer := x')
        result = functionValue.evaluateWithArguments([HIRConstantLiteralIntegerValue(42, self.context.coreTypes.integerType, None)])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 42)

    def testFunctionMetaBuilder3(self):
        functionValue = self.evaluateTopLevelSourceString('function identity(x: Integer. y: Integer) => Integer := x + y')
        result = functionValue.evaluateWithArguments([
            HIRConstantLiteralIntegerValue(1, self.context.coreTypes.integerType, None),
            HIRConstantLiteralIntegerValue(2, self.context.coreTypes.integerType, None)
        ])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 3)

    def testAssociationType(self):
        type = self.evaluateTopLevelSourceString('Symbol : Integer')
        self.assertTrue(type.isAssociationType())
        self.assertEqual(type.keyType, self.context.coreTypes.symbolType)
        self.assertEqual(type.valueType, self.context.coreTypes.integerType)

    def testAssociation(self):
        association = self.evaluateTopLevelSourceString('#first : 1')
        self.assertTrue(association.key.isSymbolConstant())
        self.assertEqual(association.key.value, 'first')

        self.assertTrue(association.value.isIntegerConstant())
        self.assertEqual(association.value.value, 1)

    def testTupleType(self):
        tupleType = self.evaluateTopLevelSourceString('Integer, Float, Character')
        self.assertTrue(tupleType.isTupleType())
        self.assertEqual(len(tupleType.elements), 3)
        self.assertEqual(tupleType.elements[0], self.context.coreTypes.integerType)
        self.assertEqual(tupleType.elements[1], self.context.coreTypes.floatType)
        self.assertEqual(tupleType.elements[2], self.context.coreTypes.characterType)

    def testTuple(self):
        tuple = self.evaluateTopLevelSourceString("1, 2.5, 'A'")
        self.assertTrue(tuple.isTupleConstant())
        self.assertEqual(len(tuple.elements), 3)
        
        self.assertTrue(tuple.elements[0].isIntegerConstant())
        self.assertEqual(tuple.elements[0].value, 1)
        
        self.assertTrue(tuple.elements[1].isFloatConstant())
        self.assertEqual(tuple.elements[1].value, 2.5)
        
        self.assertTrue(tuple.elements[2].isCharacterConstant())
        self.assertEqual(tuple.elements[2].value, ord('A'))
        
        tupleType = tuple.getType()
        self.assertTrue(tupleType.isTupleType())
        self.assertEqual(len(tupleType.elements), 3)
        self.assertEqual(tupleType.elements[0], self.context.coreTypes.integerType)
        self.assertEqual(tupleType.elements[1], self.context.coreTypes.floatType)
        self.assertEqual(tupleType.elements[2], self.context.coreTypes.characterType)

    def testDynamicSend(self):
        sendFunction = self.evaluateTopLevelSourceString("{:(Dynamic)x :(Dynamic)y :: Dynamic | x + y}")
        result = sendFunction.evaluateWithArguments([
            HIRConstantLiteralIntegerValue(1, self.context.coreTypes.integerType, None),
            HIRConstantLiteralIntegerValue(2, self.context.coreTypes.integerType, None),
        ])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 3)

    def testDynamicSend2(self):
        sendFunction = self.evaluateTopLevelSourceString("{:(Dynamic)x :(Integer)y :: Dynamic | x + y}")
        result = sendFunction.evaluateWithArguments([
            HIRConstantLiteralIntegerValue(1, self.context.coreTypes.integerType, None),
            HIRConstantLiteralIntegerValue(2, self.context.coreTypes.integerType, None),
        ])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 3)

    def testDynamicSend3(self):
        sendFunction = self.evaluateTopLevelSourceString("{:(Integer)x :(Dynamic)y :: Dynamic | x + y}")
        result = sendFunction.evaluateWithArguments([
            HIRConstantLiteralIntegerValue(1, self.context.coreTypes.integerType, None),
            HIRConstantLiteralIntegerValue(2, self.context.coreTypes.integerType, None),
        ])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 3)

    def testSimpleFunctionType(self):
        simpleFunctionType = self.evaluateTopLevelSourceString('(Integer) => Integer')
        self.assertTrue(simpleFunctionType.isSimpleFunctionType())
        
        self.assertEqual(len(simpleFunctionType.argumentTypes), 1)
        self.assertEqual(simpleFunctionType.argumentTypes[0], self.context.coreTypes.integerType)

        simpleFunctionType = self.evaluateTopLevelSourceString('(Integer, Integer) => Integer')
        self.assertTrue(simpleFunctionType.isSimpleFunctionType())
        
        self.assertEqual(len(simpleFunctionType.argumentTypes), 2)
        self.assertEqual(simpleFunctionType.argumentTypes[1], self.context.coreTypes.integerType)
        self.assertEqual(simpleFunctionType.argumentTypes[0], self.context.coreTypes.integerType)

    def testAssert(self):
        self.evaluateTopLevelSourceString("assert: true")
        with self.assertRaises(AssertionError):
            self.evaluateTopLevelSourceString("assert: false")

    def testRuntimeError(self):
        with self.assertRaises(RuntimeError):
            self.evaluateTopLevelSourceString('error: "test message"')

if __name__ == '__main__':
    unittest.main()