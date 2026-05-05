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

    def testRecursiveFunctionMetaBuilder(self):
        result = self.evaluateTopLevelSourceString("""
        function factorial(n: Integer) => Integer := {
            if: n <= 0
            then: 1
            else: factorial(n - 1) *n     
        }.
                                                          
        factorial(10)""")
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 3628800)

    def testPublicFunctionMetaBuilder(self):
        functionValue = self.evaluateTopLevelSourceString('public function two() => Integer := 2')
        result = functionValue.evaluateWithArguments([])
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(result.value, 2)

        functionGlobalValue = self.context.currentPackage.publicSymbolTable['two']
        self.assertEqual(functionValue, functionGlobalValue)

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

    def testEmptyDictionary(self):
        dictionary = self.evaluateTopLevelSourceString("#{}")
        self.assertTrue(dictionary.isDictionaryConstant())
        self.assertEqual(0, len(dictionary.elements))

    def testDictionary(self):
        dictionary = self.evaluateTopLevelSourceString("#{First: 1. Second: 2. Third:}")
        self.assertTrue(dictionary.isDictionaryConstant())
        self.assertEqual(3, len(dictionary.elements))

    def testEnum(self):
        enum = self.evaluateTopLevelSourceString("enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}")
        self.assertTrue(enum.isEnumType())
        
        self.assertEqual(3, len(enum.values))
        self.assertEqual('First', enum.values[0].name)
        self.assertEqual(1, enum.values[0].value.value)

        self.assertEqual('Second', enum.values[1].name)
        self.assertEqual(2, enum.values[1].value.value)

        self.assertEqual('Third', enum.values[2].name)
        self.assertEqual(3, enum.values[2].value.value)

    def testEnumAccess(self):
        enumValue = self.evaluateTopLevelSourceString("enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}. MyEnum First")
        self.assertTrue(enumValue.isEnumConstant())
        self.assertEqual('First', enumValue.name)
        self.assertEqual(1, enumValue.value.value)

    def testEnumValueAccess(self):
        enumValue = self.evaluateTopLevelSourceString("enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}. MyEnum First value")
        self.assertTrue(enumValue.isIntegerConstant())
        self.assertEqual(1, enumValue.value)

    def testEnumMakeValueAccess(self):
        enumValue = self.evaluateTopLevelSourceString("enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}. MyEnum value: 2")
        self.assertTrue(enumValue.isEnumConstant())
        self.assertEqual(None, enumValue.name)
        self.assertEqual(2, enumValue.value.value)
        
    def testEnumFunctionAccess(self):
        enumValue = self.evaluateTopLevelSourceString("""
        enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}.
        {:: MyEnum | MyEnum First} ()
        """)
        self.assertTrue(enumValue.isEnumConstant())
        self.assertEqual(1, enumValue.value.value)

    def testEnumFunctionValueAccess(self):
        enumValue = self.evaluateTopLevelSourceString("""
        enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}.
        {:(MyEnum)e :: Integer | e value} (MyEnum Second)
        """)

        self.assertTrue(enumValue.isIntegerConstant())
        self.assertEqual(2, enumValue.value)

    def testEnumMakeValueAccess(self):
        enumValue = self.evaluateTopLevelSourceString("""
        enum MyEnum baseType: Integer values: #{First: 1. Second: 2. Third:}.
        {:(Integer)x :: MyEnum | MyEnum value: x} (2)
        """)

        self.assertTrue(enumValue.isEnumConstant())
        self.assertTrue(enumValue.value.isIntegerConstant())
        self.assertEqual(2, enumValue.value.value)

    def testBooleanNot(self):
        value = self.evaluateTopLevelSourceString("false not")
        self.assertTrue(value.isBooleanConstant())
        self.assertTrue(value.value)

        value = self.evaluateTopLevelSourceString("true not")
        self.assertTrue(value.isBooleanConstant())
        self.assertFalse(value.value)

    def testBooleanAnd(self):
        value = self.evaluateTopLevelSourceString("false && false")
        self.assertTrue(value.isBooleanConstant())
        self.assertFalse(value.value)

        value = self.evaluateTopLevelSourceString("false && true")
        self.assertTrue(value.isBooleanConstant())
        self.assertFalse(value.value)

        value = self.evaluateTopLevelSourceString("true && false")
        self.assertTrue(value.isBooleanConstant())
        self.assertFalse(value.value)

        value = self.evaluateTopLevelSourceString("true && true")
        self.assertTrue(value.isBooleanConstant())
        self.assertTrue(value.value)

    def testBooleanOr(self):
        value = self.evaluateTopLevelSourceString("false || false")
        self.assertTrue(value.isBooleanConstant())
        self.assertFalse(value.value)

        value = self.evaluateTopLevelSourceString("false || true")
        self.assertTrue(value.isBooleanConstant())
        self.assertTrue(value.value)

        value = self.evaluateTopLevelSourceString("true || false")
        self.assertTrue(value.isBooleanConstant())
        self.assertTrue(value.value)

        value = self.evaluateTopLevelSourceString("true || true")
        self.assertTrue(value.isBooleanConstant())
        self.assertTrue(value.value)

    def testEmptyStruct(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {}')
        self.assertTrue(result.isStructType())
        self.assertEqual(0, result.getValueSize())
        self.assertEqual(1, result.getValueAlignment())

    def testStructWithField(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {public field f => Integer}')
        self.assertTrue(result.isStructType())
        self.assertEqual(8, result.getValueSize())
        self.assertEqual(8, result.getValueAlignment())

    def testInstantiateStruct(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {}. MyStruct()')
        self.assertTrue(result.isStructValue())
        self.assertEqual(0, len(result.fields))

    def testInstantiateStructWithField(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {public field f => Integer}. MyStruct()')
        self.assertTrue(result.isStructValue())
        self.assertTrue(result.fields[0].isIntegerConstant())
        self.assertEqual(0, result.fields[0].value)

    def testInstantiateStructWithField2(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {public field f => Integer}. MyStruct(42)')
        self.assertTrue(result.isStructValue())
        self.assertTrue(result.fields[0].isIntegerConstant())
        self.assertEqual(42, result.fields[0].value)

    def testStructFieldGetter(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {public field first => Integer}. MyStruct(42) first')
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(42, result.value)

    def testStructFieldSetter(self):
        result = self.evaluateTopLevelSourceString('struct MyStruct definition: {public field first => Integer}. MyStruct() first: 5; first')
        self.assertTrue(result.isIntegerConstant())
        self.assertEqual(5, result.value)

    def testStructExplicitGetterAccessor(self):
        value = self.evaluateTopLevelSourceString("""
        struct TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.

            method sumExplicit => Integer := self first + self second.
        }.
        TestPair(1. 2) sumExplicit
        """)
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(3, value.value)

    def testStructExplicitSetterAccessor(self):
        value = self.evaluateTopLevelSourceString("""
        struct TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.
                                          
            method setFirst: (firstValue: Integer) second: (secondValue: Integer) ::=> Void := {
                self first: firstValue.
                self second: secondValue.
                void
            }.

            method sumExplicit => Integer := self first + self second.
        }.
        TestPair(1. 2) setFirst: 5 second: 42; sumExplicit
        """)
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(47, value.value)

    def testStructImplicitFieldAccess(self):
        value = self.evaluateTopLevelSourceString("""
        struct TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.

            method sumImplicit => Integer := first + second.
        }.
        TestPair(1. 2) sumImplicit
        """)
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(3, value.value)

    def testEmptyClass(self):
        result = self.evaluateTopLevelSourceString('class MyClass definition: {}')
        self.assertTrue(result.isClassType())
        self.assertEqual(0, result.getInstanceSize())
        self.assertEqual(1, result.getInstanceAlignment())
    
    def testInstantiateEmptyClass(self):
        result = self.evaluateTopLevelSourceString('class MyClass definition: {}. MyClass()')
        self.assertTrue(result.isObjectValue())
        self.assertEqual(0, len(result.fields))

    def testClassWithField(self):
        result = self.evaluateTopLevelSourceString('class MyClass definition: {public field f => Integer}')
        self.assertTrue(result.isClassType())
        self.assertEqual(8, result.getInstanceSize())
        self.assertEqual(8, result.getInstanceAlignment())

    def testInstantiateClassWithField(self):
        result = self.evaluateTopLevelSourceString('class MyClass definition: {public field f => Integer}. MyClass(42)')
        self.assertTrue(result.isObjectValue())
        
        self.assertTrue(result.fields[0].isIntegerConstant())
        self.assertEqual(42, result.fields[0].value)

    def testClassWithSuperclassField(self):
        result = self.evaluateTopLevelSourceString('class MyClass superclass: Object definition: {public field f => Integer}')
        self.assertTrue(result.isClassType())
        self.assertEqual(8, result.getInstanceSize())
        self.assertEqual(8, result.getInstanceAlignment())

        self.assertEqual('Object', result.superclass.name)

    def testClassExplicitGetterAccessor(self):
        value = self.evaluateTopLevelSourceString("""
        class TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.

            method sumExplicit => Integer := self first + self second.
        }.
        TestPair(1. 2) sumExplicit
        """)
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(3, value.value)

    def testClassExplicitSetterAccessor(self):
        value = self.evaluateTopLevelSourceString("""
        class TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.
                                          
            method setFirst: (firstValue: Integer) second: (secondValue: Integer) ::=> Void := {
                self first: firstValue.
                self second: secondValue.
                void
            }.

            method sumExplicit => Integer := self first + self second.
        }.
        TestPair(1. 2) setFirst: 5 second: 42; sumExplicit
        """)
        self.assertTrue(value.isIntegerConstant())
        self.assertEqual(47, value.value)

    def testMakeStruct(self):
        value = self.evaluateTopLevelSourceString("""
        struct TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.
        }.
                                          
        { :: TestPair | TestPair()}()
        """)
        self.assertTrue(value.isStructValue())
        self.assertEqual(2, len(value.fields))

    def testMakeStruct2(self):
        value = self.evaluateTopLevelSourceString("""
        struct TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.
        }.
                                          
        { :: TestPair | TestPair(1. 2)}()
        """)
        self.assertTrue(value.isStructValue())
        self.assertEqual(2, len(value.fields))

        self.assertTrue(value.fields[0].isIntegerConstant())
        self.assertEqual(1, value.fields[0].value)

        self.assertTrue(value.fields[1].isIntegerConstant())
        self.assertEqual(2, value.fields[1].value)

    def testMakeClass(self):
        value = self.evaluateTopLevelSourceString("""
        class TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.
        }.
                                          
        { :: TestPair | TestPair()}()
        """)
        self.assertTrue(value.isObjectValue())
        self.assertEqual(2, len(value.fields))

    def testMakeClass2(self):
        value = self.evaluateTopLevelSourceString("""
        class TestPair definition: {
            public field first type: Integer.
            public field second type: Integer.
        }.
                                          
        { :: TestPair | TestPair(1. 2)}()
        """)
        self.assertTrue(value.isObjectValue())
        self.assertEqual(2, len(value.fields))

        self.assertTrue(value.fields[0].isIntegerConstant())
        self.assertEqual(1, value.fields[0].value)

        self.assertTrue(value.fields[1].isIntegerConstant())
        self.assertEqual(2, value.fields[1].value)

if __name__ == '__main__':
    unittest.main()