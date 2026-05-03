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
