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

    def testWhileDoMacro(self):
        topLevelResult = self.evaluateTopLevelSourceString('while: false do: {}')
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
        value = self.evaluateTopLevelSourceString('1.0 + 2.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(3, value.value)

        value = self.evaluateTopLevelSourceString('1.0 - 2.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(-1, value.value)

        value = self.evaluateTopLevelSourceString('2.0 * 3.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(6, value.value)

        value = self.evaluateTopLevelSourceString('6.0 / 3.0')
        self.assertTrue(value.isFloatConstant())
        self.assertEqual(2, value.value)

        value = self.evaluateTopLevelSourceString('2.0 = 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(True, value.value)

        value = self.evaluateTopLevelSourceString('2.0 ~= 2.0')
        self.assertTrue(value.isBooleanConstant())
        self.assertEqual(False, value.value)