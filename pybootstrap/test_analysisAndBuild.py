import unittest
from parsetree import *
from parser import parseSourceString
from analysisAndBuild import *
from hir import *

class TestAnalysisAndBuild(unittest.TestCase):
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

    def buildTopLevelSourceString(self, string: str):
        ast = self.parseSourceStringWithoutErrors(string)
        builder = self.context.createTopLevelFunctionBuilder(ast.sourcePosition)
        result = AnalysisAndBuildPass(builder).visitDecayedNode(ast)
        if not builder.isLastTerminator():
            builder.function.dependentFunctionType.resultType = result.getType()
            builder.returnValue(result, ast.sourcePosition)

        builder.finishBuilding()
        return builder.function

    def printTopLevelSourceStringFunction(self, string: str):
        topLevelFunction = self.buildTopLevelSourceString(string)
        print(topLevelFunction.fullPrintString())

    def evaluateTopLevelFunctionSourceString(self, string: str):
        topLevelFunction = self.buildTopLevelSourceString(string)
        return topLevelFunction.evaluateWithArguments([])

    def testEmptyTopLevel(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testLiteralInteger(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testLiteralFloat(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('42.5')
        self.assertTrue(topLevelResult.isFloatConstant())
        self.assertEqual(topLevelResult.value, 42.5)

    def testLiteralCharacter(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString("'A'")
        self.assertTrue(topLevelResult.isCharacterConstant())
        self.assertEqual(topLevelResult.value, ord('A'))

    def testLiteralString(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('"Hello World"')
        self.assertTrue(topLevelResult.isStringConstant())
        self.assertEqual(topLevelResult.value, 'Hello World')

    def testLiteralSymbol(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('#hello')
        self.assertTrue(topLevelResult.isSymbolConstant())
        self.assertEqual(topLevelResult.value, 'hello')

    def testLexicalBlock(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('{42}')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testPackageSymbols(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('false')
        self.assertTrue(topLevelResult.isBooleanConstant())
        self.assertFalse(topLevelResult.value)
        
        topLevelResult = self.evaluateTopLevelFunctionSourceString('true')
        self.assertTrue(topLevelResult.isBooleanConstant())
        self.assertTrue(topLevelResult.value)

        topLevelResult = self.evaluateTopLevelFunctionSourceString('void')
        self.assertTrue(topLevelResult.isVoidConstant())

        topLevelResult = self.evaluateTopLevelFunctionSourceString('nil')
        self.assertTrue(topLevelResult.isNilConstant())

    def testLetWithMacro(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('let: #x with: 42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

        topLevelResult = self.evaluateTopLevelFunctionSourceString('let: #x with: 42. x')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

    def testLetMutableWithMacro(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('let: #x mutableWith: 42')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 42)

        topLevelResult = self.evaluateTopLevelFunctionSourceString('let: #x mutableWith: 42. x := 5. x')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 5)

    def testIfThenElseMacro(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('if: true then: 1 else: 2')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 1)

        topLevelResult = self.evaluateTopLevelFunctionSourceString('if: false then: 1 else: 2')
        self.assertTrue(topLevelResult.isIntegerConstant())
        self.assertEqual(topLevelResult.value, 2)

    def testIfThenMacro(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('if: true then: 1')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testWhileDoMacro(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString('while: false do: {}')
        self.assertTrue(topLevelResult.isVoidConstant())

    def testQuote(self):
        topLevelResult = self.evaluateTopLevelFunctionSourceString("`'42")
        self.assertTrue(topLevelResult.isParseTreeConstant())

    def testMessageSend(self):
        value = self.evaluateTopLevelFunctionSourceString('42 negated')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(-42, value.value)

    def testMessageSend2(self):
        value = self.evaluateTopLevelFunctionSourceString('1 + 2')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(3, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1 - 2')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(-1, value.value)

        value = self.evaluateTopLevelFunctionSourceString('2 * 3')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(6, value.value)

        value = self.evaluateTopLevelFunctionSourceString('6 // 3')
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(2, value.value)

        value = self.evaluateTopLevelFunctionSourceString('2 = 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelFunctionSourceString('2 ~= 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1 < 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1 <= 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1 > 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1 >= 2')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

    def testMessageSend3(self):
        value = self.evaluateTopLevelFunctionSourceString('42.0 negated')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(-42.0, value.value)

        value = self.evaluateTopLevelFunctionSourceString('9.0 sqrt')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(3.0, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1.0 + 2.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(3.0, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1.0 - 2.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(-1.0, value.value)

        value = self.evaluateTopLevelFunctionSourceString('2.0 * 3.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(6.0, value.value)

        value = self.evaluateTopLevelFunctionSourceString('6.0 / 3.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(2.0, value.value)

        value = self.evaluateTopLevelFunctionSourceString('2.0 = 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelFunctionSourceString('2.0 ~= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1.0 < 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1.0 <= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1.0 > 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

        value = self.evaluateTopLevelFunctionSourceString('1.0 >= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)

    def testMessageSendCascade(self):
        value = self.evaluateTopLevelFunctionSourceString('1.0 + 2.0; yourself')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(1.0, value.value)

    def testAssociationType(self):
        type = self.evaluateTopLevelFunctionSourceString('Symbol : Integer')
        self.assertTrue(type.isAssociationType())
        self.assertEqual(type.keyType, self.context.coreTypes.symbolType)
        self.assertEqual(type.valueType, self.context.coreTypes.integerType)

    def testAssociation(self):
        association = self.evaluateTopLevelFunctionSourceString('#first : 1')
        self.assertTrue(association.key.isSymbolConstant())
        self.assertEqual(association.key.value, 'first')

        self.assertTrue(association.value.isIntegerConstant())
        self.assertEqual(association.value.value, 1)

    def testTupleType(self):
        tupleType = self.evaluateTopLevelFunctionSourceString('Integer, Float, Character')
        self.assertTrue(tupleType.isTupleType())
        self.assertEqual(len(tupleType.elements), 3)
        self.assertEqual(tupleType.elements[0], self.context.coreTypes.integerType)
        self.assertEqual(tupleType.elements[1], self.context.coreTypes.floatType)
        self.assertEqual(tupleType.elements[2], self.context.coreTypes.characterType)

    def testTuple(self):
        tuple = self.evaluateTopLevelFunctionSourceString("1, 2.5, 'A'")
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

    def testFunctionType(self):
        value = self.evaluateTopLevelFunctionSourceString('{:(Integer)x :: Integer}')
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