import math

class MirContext:
    def __init__(self, pointerSize = 8):
        self.pointerSize = pointerSize
        self.pointerAlignment = pointerSize
        self.gcPointerSize = pointerSize
        self.gcPointerAlignment = pointerSize

        self.typeNameMap = {}

        self.basicBlockType = self.addNamedType(MirBasicBlockType(self, 'BasicBlock', self.pointerSize, self.pointerAlignment))
        self.gcPointerType  = self.addNamedType(MirGCPointerType(self, 'GCPointer', self.gcPointerSize, self.gcPointerAlignment))
        self.pointerType    = self.addNamedType(MirPointerType(self, 'Pointer', self.pointerSize, self.pointerAlignment))
        self.voidType       = self.addNamedType(MirVoidType(self, 'Void', 0, 1))
        self.boolean8Type   = self.addNamedType(MirBoolean8Type(self, 'Boolean8', 1, 1))
        self.int8Type       = self.addNamedType(MirInt8Type(self, 'Int8', 1, 1))
        self.int16Type      = self.addNamedType(MirInt16Type(self, 'Int16', 2, 2))
        self.int32Type      = self.addNamedType(MirInt32Type(self, 'Int32', 4, 4))
        self.int64Type      = self.addNamedType(MirInt64Type(self, 'Int64', 8, 8))
        self.uint8Type      = self.addNamedType(MirUInt8Type(self, 'UInt8', 1, 1))
        self.uint16Type     = self.addNamedType(MirUInt16Type(self, 'UInt16', 2, 2))
        self.uint32Type     = self.addNamedType(MirUInt32Type(self, 'UInt32', 4, 4))
        self.uint64Type     = self.addNamedType(MirUInt64Type(self, 'UInt64', 8, 8))
        self.float32Type    = self.addNamedType(MirFloat32Type(self, 'Float32', 4, 4))
        self.float64Type    = self.addNamedType(MirFloat64Type(self, 'Float64', 8, 8))

        if pointerSize == 4:
            self.sizeType = self.uint32Type
            self.uintPointerType = self.uint32Type
            self.intPointerType = self.int32Type
        else:
            assert pointerSize == 8
            self.sizeType = self.uint64Type
            self.uintPointerType = self.uint64Type
            self.intPointerType = self.int64Type

        self.typeNameMap['Size'] = self.sizeType
        self.typeNameMap['UIntPointer'] = self.uintPointerType
        self.typeNameMap['IntPointer'] = self.intPointerType

        self.primitiveTranslatorMap = {}
        self.runtimePrimitiveImplementations = {}
        self.primitiveRuntimeFunctionNameMap = {}
        self.addPrimitiveTranslators()
    
    def addNamedType(self, type):
        self.typeNameMap[type.name] = type
        return type

    def getTypeNamed(self, typeName):
        return self.typeNameMap[typeName]

    def addPrimitiveTranslators(self):
        self.addInt32Primitives()
        self.addUInt32Primitives()
        self.addInt64Primitives()
        self.addUInt64Primitives()
        self.addCalloutPrimitives()

    def addInt32Primitives(self):
        self.primitiveTranslatorMap['Int32::negated'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int32NegAt(operand, sourcePosition))
        self.primitiveTranslatorMap['Int32::bitInvert'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int32BitNotAt(operand, sourcePosition))

        self.primitiveTranslatorMap['Int32::+']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32AddAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::-']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32SubAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::*']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32MulAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32:://'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32SDivAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::%']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32SModAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['Int32::&']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32BitAndAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::|']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32BitOrAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::^']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32BitXorAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::<<'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32ShiftLeftAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::>>'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32AShiftRightAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['Int32::=']   = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32EqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::~=']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32NotEqualsAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['Int32::<']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32LessThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::<='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32LessOrEqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::>']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32GreaterThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int32::>='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32GreaterOrEqualsAt(left, right, sourcePosition))

    def addUInt32Primitives(self):
        self.primitiveTranslatorMap['UInt32::negated'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int32NegAt(operand, sourcePosition))
        self.primitiveTranslatorMap['UInt32::bitInvert'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int32BitNotAt(operand, sourcePosition))

        self.primitiveTranslatorMap['UInt32::+']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32AddAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::-']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32SubAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::*']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32MulAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32:://'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32UDivAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::%']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32UModAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['UInt32::&']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32BitAndAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::|']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32BitOrAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::^']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32BitXorAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::<<'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32ShiftLeftAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::>>'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32LShiftRightAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['UInt32::=']   = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32EqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::~=']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int32NotEqualsAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['UInt32::<']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint32LessThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::<='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint32LessOrEqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::>']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint32GreaterThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt32::>='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint32GreaterOrEqualsAt(left, right, sourcePosition))

    def addInt64Primitives(self):
        self.primitiveTranslatorMap['Int64::negated'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int64NegAt(operand, sourcePosition))
        self.primitiveTranslatorMap['Int64::bitInvert'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int64BitNotAt(operand, sourcePosition))

        self.primitiveTranslatorMap['Int64::+']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64AddAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::-']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64SubAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::*']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64MulAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64:://'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64SDivAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::%']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64SModAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['Int64::&']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64BitAndAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::|']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64BitOrAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::^']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64BitXorAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::<<'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64ShiftLeftAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::>>'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64AShiftRightAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['Int64::=']   = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64EqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::~=']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64NotEqualsAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['Int64::<']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64LessThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::<='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64LessOrEqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::>']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64GreaterThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['Int64::>='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64GreaterOrEqualsAt(left, right, sourcePosition))

    def addUInt64Primitives(self):
        self.primitiveTranslatorMap['UInt64::negated'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int64NegAt(operand, sourcePosition))
        self.primitiveTranslatorMap['UInt64::bitInvert'] = self.makeBuilderTranslator(lambda builder, sourcePosition, operand: builder.int64BitNotAt(operand, sourcePosition))

        self.primitiveTranslatorMap['UInt64::+']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64AddAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::-']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64SubAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::*']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64MulAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64:://'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64UDivAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::%']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64UModAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['UInt64::&']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64BitAndAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::|']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64BitOrAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::^']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64BitXorAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::<<'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64ShiftLeftAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::>>'] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64LShiftRightAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['UInt64::=']   = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64EqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::~=']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.int64NotEqualsAt(left, right, sourcePosition))

        self.primitiveTranslatorMap['UInt64::<']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint64LessThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::<='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint64LessOrEqualsAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::>']  = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint64GreaterThanAt(left, right, sourcePosition))
        self.primitiveTranslatorMap['UInt64::>='] = self.makeBuilderTranslator(lambda builder, sourcePosition, left, right: builder.uint64GreaterOrEqualsAt(left, right, sourcePosition))

    def makeBuilderTranslator(self, translationFunction):
        def translator(mir2hir, callInstruction):
            arguments = list(map(lambda arg: mir2hir.translateValue(arg), callInstruction.arguments))
            return translationFunction(mir2hir.builder, callInstruction.sourcePosition, *arguments)
        return translator

    def addCalloutPrimitives(self):
        for pair in [
            ## IO
            ('IO::print', "__sysmel_io_print", lambda x: print(str(x), end='')),
            ('IO::printLine', "__sysmel_io_printLine", lambda x: print(str(x))),
            ('IO::writeLine', "__sysmel_io_writeLine", lambda x: print(str(x))),

            ## Boolean
            ('Boolean::not', "__sysmel_boolean_not", lambda x: not x),
            
            ## Character
            ('Character::negated',    "__sysmel_character_negated",   lambda x: -x),
            ('Character::bitInvert',  "__sysmel_character_bitInvert", lambda x: 1 - x),

            ('Character::+',  "__sysmel_character_add", lambda x, y: x + y),
            ('Character::-',  "__sysmel_character_sub", lambda x, y: x - y),
            ('Character::*',  "__sysmel_character_mul", lambda x, y: x * y),
            ('Character:://', "__sysmel_character_div", lambda x, y: x // y),
            ('Character::%',  "__sysmel_character_mod", lambda x, y: x % y),

            ('Character::&',  "__sysmel_character_and",        lambda x, y: x & y),
            ('Character::|',  "__sysmel_character_or",         lambda x, y: x | y),
            ('Character::^',  "__sysmel_character_xor",        lambda x, y: x ^ y),
            ('Character::<<', "__sysmel_character_shiftLeft",  lambda x, y: x << y),
            ('Character::>>', "__sysmel_character_shiftRight", lambda x, y: x >> y),

            ('Character::=',    "__sysmel_character_equals",          lambda x, y: x == y),
            ('Character::!=',   "__sysmel_character_notEquals",       lambda x, y: x != y),
            ('Character::hash', "__sysmel_character_hash",            lambda x: hash(x)),

            ('Character::<',   "__sysmel_character_lessThan",        lambda x, y: x < y),
            ('Character::<=',  "__sysmel_character_lessOrEquals",    lambda x, y: x <= y),
            ('Character::>',   "__sysmel_character_greaterThan",     lambda x, y: x < y),
            ('Character::>=',  "__sysmel_character_greaterOrEquals", lambda x, y: x <= y),

            ## Integer
            ('Integer::negated',    "__sysmel_integer_negated",   lambda x: -x),
            ('Integer::bitInvert',  "__sysmel_integer_bitInvert", lambda x: 1 - x),

            ('Integer::+',  "__sysmel_integer_add", lambda x, y: x + y),
            ('Integer::-',  "__sysmel_integer_sub", lambda x, y: x - y),
            ('Integer::*',  "__sysmel_integer_mul", lambda x, y: x * y),
            ('Integer:://', "__sysmel_integer_div", lambda x, y: x // y),
            ('Integer::%',  "__sysmel_integer_mod", lambda x, y: x % y),

            ('Integer::&',  "__sysmel_integer_and",        lambda x, y: x & y),
            ('Integer::|',  "__sysmel_integer_or",         lambda x, y: x | y),
            ('Integer::^',  "__sysmel_integer_xor",        lambda x, y: x ^ y),
            ('Integer::<<', "__sysmel_integer_shiftLeft",  lambda x, y: x << y),
            ('Integer::>>', "__sysmel_integer_shiftRight", lambda x, y: x >> y),

            ('Integer::=',    "__sysmel_integer_equals",          lambda x, y: x == y),
            ('Integer::~=',   "__sysmel_integer_notEquals",       lambda x, y: x != y),
            ('Integer::hash', "__sysmel_integer_hash",            lambda x: hash(x)),

            ('Integer::<',   "__sysmel_integer_lessThan",        lambda x, y: x < y),
            ('Integer::<=',  "__sysmel_integer_lessOrEquals",    lambda x, y: x <= y),
            ('Integer::>',   "__sysmel_integer_greaterThan",     lambda x, y: x < y),
            ('Integer::>=',  "__sysmel_integer_greaterOrEquals", lambda x, y: x <= y),

            ('Integer::asInt8',  "__sysmel_integer_asInt8",  lambda x: x),
            ('Integer::asInt16', "__sysmel_integer_asInt16", lambda x: x),
            ('Integer::asInt32', "__sysmel_integer_asInt32", lambda x: x),
            ('Integer::asInt64', "__sysmel_integer_asInt64", lambda x: x),

            ('Integer::asUInt8',  "__sysmel_integer_asUInt8",  lambda x: x),
            ('Integer::asUInt16', "__sysmel_integer_asUInt16", lambda x: x),
            ('Integer::asUInt32', "__sysmel_integer_asUInt32", lambda x: x),
            ('Integer::asUInt64', "__sysmel_integer_asUInt64", lambda x: x),

            ('Integer::asChar8',  "__sysmel_integer_asChar8",  lambda x: x),
            ('Integer::asChar16', "__sysmel_integer_asChar16", lambda x: x),
            ('Integer::asChar32', "__sysmel_integer_asChar32", lambda x: x),

            ## Float
            ('Float::negated',    "__sysmel_float_negated",   lambda x: -x),
            ('Float::sqrt',  "__sysmel_float_sqrt", lambda x: math.sqrt(x)),

            ('Float::+', "__sysmel_float_add", lambda x, y: x + y),
            ('Float::-', "__sysmel_float_sub", lambda x, y: x - y),
            ('Float::*', "__sysmel_float_mul", lambda x, y: x * y),
            ('Float::/', "__sysmel_float_div", lambda x, y: x // y),
            ('Float::%', "__sysmel_float_mod", lambda x, y: x % y),

            ('Float::=',   "__sysmel_float_equals",          lambda x, y: x == y),
            ('Float::~=',  "__sysmel_float_notEquals",       lambda x, y: x != y),
            ('Float::hash', "__sysmel_float_hash",           lambda x: hash(x)),

            ('Float::<',   "__sysmel_float_lessThan",        lambda x, y: x < y),
            ('Float::<=',  "__sysmel_float_lessOrEquals",    lambda x, y: x <= y),
            ('Float::>',   "__sysmel_float_greaterThan",     lambda x, y: x < y),
            ('Float::>=',  "__sysmel_float_greaterOrEquals", lambda x, y: x <= y),

        ]:
            primitiveName, runtimeName, implementation = pair
            self.addCalloutPrimitive(primitiveName, runtimeName)
            if implementation is not None:
                self.runtimePrimitiveImplementations[runtimeName] = implementation

    def addCalloutPrimitive(self, primitiveName, runtimeName):
        def primitiveTranslator(mi2hir, callInstruction):
            return mi2hir.callRuntimeFunctionWithName(callInstruction, runtimeName)
        self.primitiveTranslatorMap[primitiveName] = primitiveTranslator
        self.primitiveRuntimeFunctionNameMap[primitiveName] = runtimeName

    def getPrimitiveRuntimeFunctionNameFor(self, primitiveName):
        return self.primitiveRuntimeFunctionNameMap.get(primitiveName, None)

    def getPrimitiveTranslatorFor(self, primitiveName):
        return self.primitiveTranslatorMap[primitiveName]

    def getRuntimePrimitiveImplementationOrNone(self, runtimeName):
        return self.runtimePrimitiveImplementations.get(runtimeName, None)
    
    def createTypeForStruct(self, structType):
        mirType = MirStructType(self, structType)
        return mirType

class MirType:
    def __init__(self, context: MirContext, name: str, valueSize: int, valueAlignment: int):
        self.context = context
        self.name = name
        self.valueSize = valueSize
        self.valueAlignment = valueAlignment
        self.memoryDescriptor = None
        self.module = None
        self.owner = None

    def addToPackage(self, package):
        return package.addElement(self)
    
    def getInstanceSize(self):
        return self.valueSize

    def isGlobalConstant(self):
        return True    

    def emitArgumentWithBuilder(self, builder, sourcePosition):
        assert False

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        assert False

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        assert False

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        assert False

    def emitPhiWithBuilder(self, builder, sourcePosition):
        assert False
    
    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        assert False

    def emitLoadWithBuilder(self, builder, pointer, sourcePosition):
        assert False

    def emitStoreWithBuilder(self, builder, pointer, value, sourcePosition):
        assert False

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        assert False

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        assert False

    def emitFloatConstantWithBuilder(self, builder, integer, sourcePosition):
        assert False

    def emitVoidConstantWithBuilder(self, builder, sourcePosition):
        assert False

    def emitNilConstantWithBuilder(self, builder, sourcePosition):
        assert False

    def isBehaviorType(self) -> bool:
        return False

    def isGCPointerType(self) -> bool:
        return False
    
    def isInt8Type(self) -> bool:
        return False

    def isInt16Type(self) -> bool:
        return False

    def isInt32Type(self) -> bool:
        return False

    def isInt64Type(self) -> bool:
        return False
    
    def isUInt8Type(self) -> bool:
        return False

    def isUInt16Type(self) -> bool:
        return False

    def isUInt32Type(self) -> bool:
        return False

    def isUInt64Type(self) -> bool:
        return False

    def isFloat32Type(self) -> bool:
        return False

    def isFloat64Type(self) -> bool:
        return False

    def isVoidType(self) -> bool:
        return False
    
    def isClosureType(self) -> bool:
        return False
    
    def isFunctionType(self) -> bool:
        return False

    def __str__(self) -> str:
        return self.name

class MirVoidType(MirType):
    def isVoidType(self) -> bool:
        return True
    
    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callVoidResultAt(functional, sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnVoidAt(sourcePosition)
            
    def emitVoidConstantWithBuilder(self, builder, sourcePosition):
        return builder.constVoidAt(sourcePosition)

class MirBoolean8Type(MirType):
    def isBoolean8Type(self) -> bool:
        return True

class MirInt8Type(MirType):
    def isInt8Type(self):
        return True
    
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt32At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt32At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt32At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt32ResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt32At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt32At(targetTemp, sourceTemp, sourcePosition)

    def emitLoadWithBuilder(self, builder, pointer, sourcePosition):
        return builder.loadInt32At(pointer, sourcePosition)

    def emitStoreWithBuilder(self, builder, pointer, value, sourcePosition):
        return builder.storeInt32At(pointer, value, sourcePosition)

class MirInt16Type(MirType):
    def isInt16Type(self):
        return True
    
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt32At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt32At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt32At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt32ResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt32At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt32At(targetTemp, sourceTemp, sourcePosition)

    def emitLoadWithBuilder(self, builder, pointer, sourcePosition):
        return builder.loadInt32At(pointer, sourcePosition)

    def emitStoreWithBuilder(self, builder, pointer, value, sourcePosition):
        return builder.storeInt32At(pointer, value, sourcePosition)

class MirInt32Type(MirType):
    def isInt32Type(self):
        return True
    
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt32At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt32At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt32At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt32ResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt32At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt32At(targetTemp, sourceTemp, sourcePosition)

    def emitLoadWithBuilder(self, builder, pointer, sourcePosition):
        return builder.loadInt32At(pointer, sourcePosition)

    def emitStoreWithBuilder(self, builder, pointer, value, sourcePosition):
        return builder.storeInt32At(pointer, value, sourcePosition)

class MirInt64Type(MirType):
    def isInt64Type(self):
        return True
    
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt64At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt64At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt64At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt64ResultAt(functional, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt64At(integer, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt64At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt64At(targetTemp, sourceTemp, sourcePosition)

class MirUInt8Type(MirType):
    def isUInt8Type(self):
        return True

    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt32At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt32At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt32At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt32ResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        return builder.constInt32At(character, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)
    
    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt32At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt32At(targetTemp, sourceTemp, sourcePosition)

class MirUInt16Type(MirType):
    def isUInt16Type(self):
        return True

    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt32At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt32At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt32At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt32ResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        return builder.constInt32At(character, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)
    
    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt32At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt32At(targetTemp, sourceTemp, sourcePosition)
    
class MirUInt32Type(MirType):
    def isUInt32Type(self):
        return True

    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt32At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt32At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt32At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt32ResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        return builder.constInt32At(character, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt32At(integer, sourcePosition)
    
    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt32At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt32At(targetTemp, sourceTemp, sourcePosition)

class MirUInt64Type(MirType):
    def isUInt64Type(self):
        return True

    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentInt64At(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnInt64At(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentInt64At(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callInt64ResultAt(functional, sourcePosition)

    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constInt64At(integer, sourcePosition)
    
    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiInt64At(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceInt64At(targetTemp, sourceTemp, sourcePosition)

class MirFloat32Type(MirType):
    def isFloat32Type(self):
        return True
    
    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnFloat32At(returnValue, sourcePosition)

    def emitFloatConstantWithBuilder(self, builder, floatValue, sourcePosition):
        return builder.constFloat32At(floatValue, sourcePosition)
        
class MirFloat64Type(MirType):
    def isFloat64Type(self):
        return True
    
    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnFloat64At(returnValue, sourcePosition)

    def emitFloatConstantWithBuilder(self, builder, floatValue, sourcePosition):
        return builder.constFloat64At(floatValue, sourcePosition)

class MirGCPointerType(MirType):
    def isGCPointerType(self) -> bool:
        return True

    def emitLoadWithBuilder(self, builder, pointer, sourcePosition):
        assert False

    def emitStoreWithBuilder(self, builder, pointer, value, sourcePosition):
        return builder.storeGCPointerAt(pointer, value, sourcePosition)
        
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentGCPointerAt(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnGCPointerAt(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentGCPointerAt(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callGCPointerResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        return builder.constCharacterAt(character, sourcePosition)
    
    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constIntegerAt(integer, sourcePosition)

    def emitFloatConstantWithBuilder(self, builder, floatValue, sourcePosition):
        return builder.constFloatAt(floatValue, sourcePosition)

    def emitNilConstantWithBuilder(self, builder, sourcePosition):
        return builder.constGCPointerAt(0, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiGCPointerAt(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceGCPointerAt(targetTemp, sourceTemp, sourcePosition)

class MirClosureType(MirType):
    def isClosureType(self) -> bool:
        return True

class MirBasicBlockType(MirType):
    pass

class MirPointerType(MirType):
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentPointerAt(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnPointerAt(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentPointerAt(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callPointerResultAt(functional, sourcePosition)

    def emitNilConstantWithBuilder(self, builder, sourcePosition):
        return builder.constPointerAt(0, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiPointerAt(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourcePointerAt(targetTemp, sourceTemp, sourcePosition)

class MirBehaviorType(MirType):
    def __init__(self, context, behavior, name):
        super().__init__(context, name, behavior.getValueSize(), behavior.getValueAlignment())
        self.behavior = behavior

    def getInstanceSize(self):
        return self.behavior.getInstanceSize()

    def isBehaviorType(self) -> bool:
        return True

    def buildGCLayout(self):
        pass

    ##def buildMemoryDescriptor(self, packageTranslator):
    ##    self.memoryDescriptor = MemoryDescriptor(self.behavior.getInstanceSize(), self.behavior.getInstanceAlignment())
    ##    for field in self.behavior.allFields:
    ##        fieldMirType = packageTranslator.translateValue(field.type)
    ##        if fieldMirType.isGCPointerType():
    ##            assert False

    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentGCPointerAt(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnGCPointerAt(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentGCPointerAt(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callGCPointerResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        return builder.constCharacterAt(character, sourcePosition)
    
    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constIntegerAt(integer, sourcePosition)

    def emitFloatConstantWithBuilder(self, builder, floatValue, sourcePosition):
        return builder.constFloatAt(floatValue, sourcePosition)

    def emitNilConstantWithBuilder(self, builder, sourcePosition):
        return builder.constGCPointerAt(0, sourcePosition)
    
    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiGCPointerAt(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceGCPointerAt(targetTemp, sourceTemp, sourcePosition)
    
class MirClassType(MirBehaviorType):
    def __init__(self, context, behavior, name):
        super().__init__(context, behavior, name)
        self.type = None

    def accept(self, visitor):
        return visitor.visitClassType(self)

class MirMetaclassType(MirBehaviorType):
    def __init__(self, context, behavior):
        super().__init__(context, behavior, None)
        self.thisClass = None

    def accept(self, visitor):
        return visitor.visitMetaclassType(self)

class MirStructType(MirType):
    def __init__(self, context, structType):
        super().__init__(context, structType.name, structType.getValueSize(), structType.getValueAlignment())
        self.structType = structType

    def getInstanceSize(self):
        return self.structType.getValueSize()

    def isStructType(self) -> bool:
        return True

    def buildMemoryDescriptor(self, packageTranslator):
        self.memoryDescriptor = MemoryDescriptor(self.structType.getValueSize(), self.structType.getValueAlignment())
        for field in self.structType.fields:
            fieldMirType = packageTranslator.translateValue(field.type)
            if fieldMirType.isGCPointerType():
                assert False

    ## TODO: Treat structs as values.
    def emitArgumentWithBuilder(self, builder, sourcePosition):
        return builder.argumentGCPointerAt(sourcePosition)

    def emitReturnWithBuilder(self, builder, returnValue, sourcePosition):
        return builder.returnGCPointerAt(returnValue, sourcePosition)

    def emitCallArgumentWithBuilder(self, builder, argument, sourcePosition):
        return builder.callArgumentGCPointerAt(argument, sourcePosition)

    def emitCallWithBuilder(self, builder, functional, sourcePosition):
        return builder.callGCPointerResultAt(functional, sourcePosition)

    def emitCharacterConstantWithBuilder(self, builder, character, sourcePosition):
        return builder.constCharacterAt(character, sourcePosition)
    
    def emitIntegerConstantWithBuilder(self, builder, integer, sourcePosition):
        return builder.constIntegerAt(integer, sourcePosition)

    def emitFloatConstantWithBuilder(self, builder, floatValue, sourcePosition):
        return builder.constFloatAt(floatValue, sourcePosition)

    def emitPhiWithBuilder(self, builder, sourcePosition):
        return builder.phiGCPointerAt(sourcePosition)

    def emitPhiSourceWithBuilder(self, builder, targetTemp, sourceTemp, sourcePosition):
        return builder.phiSourceGCPointerAt(targetTemp, sourceTemp, sourcePosition)