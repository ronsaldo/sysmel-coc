from hir import *
from mirContext import *
from mir import *

class HirPackage2Mir(HIRVisitor):
    def __init__(self, coreTypes: HIRCoreTypes, context: MirContext):
        super().__init__()
        self.hirCoreTypes = coreTypes
        self.context = context
        self.valueMap = {}
        self.packageList = []
        self.currentMirPackage = None
        self.setCoreTypeMappings()

    def setCoreTypeMappings(self):
        self.coreTypeMappings = {
            self.hirCoreTypes.boolean8Type : self.context.boolean8Type,

            self.hirCoreTypes.int8Type  : self.context.int8Type,
            self.hirCoreTypes.int16Type : self.context.int16Type,
            self.hirCoreTypes.int32Type : self.context.int32Type,
            self.hirCoreTypes.int64Type : self.context.int64Type,

            self.hirCoreTypes.uint8Type :  self.context.uint8Type,
            self.hirCoreTypes.uint16Type : self.context.uint16Type,
            self.hirCoreTypes.uint32Type : self.context.uint32Type,
            self.hirCoreTypes.uint64Type : self.context.uint64Type,

            self.hirCoreTypes.char8Type :  self.context.uint8Type,
            self.hirCoreTypes.char16Type : self.context.uint16Type,
            self.hirCoreTypes.char32Type : self.context.uint32Type,

            self.hirCoreTypes.float32Type : self.context.float32Type,
            self.hirCoreTypes.float64Type : self.context.float64Type,
       }

    def translateHirPackage2Mir(self, hirPackage: HIRPackage):
        return self.translateValue(hirPackage)
    
    def translateValue(self, value: HIRValue):
        if value in self.valueMap:
            return self.valueMap[value]
        
        assert not value.isFunctionLocalValue()
        translatedValue = self.visitNextValue(value)
        self.valueMap[value] = translatedValue
        return translatedValue

    def makeNominalTypeWithMethods(self, type: HIRNominalType):
        typeWithMethodDictionary = MirTypeWithMethodDictionary(type.name, type)
        self.currentMirPackage.addElement(typeWithMethodDictionary)
        for method in type.childrenMethods:
            translatedMethod = self.translateValue(method)
            if translatedMethod is not None:
                typeWithMethodDictionary.withSelectorAddMethod(method.selector, translatedMethod)

        return typeWithMethodDictionary

    def visitNextValue(self, value: HIRValue):
        return value.accept(self)

    def visitValue(self, value):
        assert False

    def visitType(self, value):
        assert False

    def visitNominalType(self, type: HIRNominalType):
        mirType = self.coreTypeMappings.get(type, self.context.gcPointerType)
        self.valueMap[type] = mirType

        self.makeNominalTypeWithMethods(type)
        return mirType
    
    def visitPrimitiveType(self, type):
        return self.visitNominalType(type)

    def visitDynamicType(self, type: HIRDynamicType):
        return self.context.gcPointerType

    def visitVoidType(self, type: HIRVoidType):
        return self.context.voidType

    def visitUndefinedType(self, type: HIRUndefinedType):
        return self.context.pointerType

    def visitControlFlowEscapeType(self, type: HIRControlFlowEscapeType):
        return self.context.voidType

    def visitUniverseType(self, type: HIRUniverseType):
        return self.context.gcPointerType

    def visitAssociationType(self, type: HIRAssociationType):
        return self.context.gcPointerType

    def visitDictionaryType(self, type: HIRDictionaryType):
        assert False

    def visitEnumType(self, type: HIREnumType):
        assert False

    def visitBehavior(self, type: HIRBehavior):
        assert False

    def visitClass(self, classType: HIRClass):
        mirType = MirBehaviorType(self, classType)
        self.valueMap[type] = classType

        mirType.buildMemoryDescriptor(self)
        self.makeNominalTypeWithMethods(classType)
        return mirType
    
    def visitMetaclass(self, type: HIRMetaclass):
        assert False
        return self.context.gcPointerType

    def visitStructType(self, type: HIRStructType):
        assert False

    def visitTupleType(self, type: HIRTupleType):
        assert False

    def visitDerivedType(self, type: HIRDerivedType):
        assert False

    def visitPointerLikeType(self, type: HIRPointerLikeType):
        # TODO: inspect the base type to determine the corrent pointer type
        return self.context.gcPointerType

    def visitPointerType(self, type: HIRPointerType):
        return self.visitPointerLikeType(type)

    def visitReferenceType(self, type: HIRReferenceType):
        return self.visitPointerLikeType(type)

    def visitMutableValueBoxType(self, type: HIRMutableValueBoxType):
        return self.context.gcPointerType

    def visitSimpleFunctionType(self, type: HIRSimpleFunctionType):
        return self.context.gcPointerType
    
    def visitDependentFunctionType(self, type: HIRDependentFunctionType):
        return self.context.gcPointerType
    
    def visitConstantLiteralBooleanValue(self, value):
        return MirGlobalConstant(value.value, self.context.boolean8Type)
    
    def visitConstantLiteralVoidValue(self, value):
        return MirGlobalConstant(None, self.context.voidType)

    def visitConstantLiteralNilValue(self, value):
        return MirGlobalConstant(None, self.context.pointerType)
    
    def visitMetaBuilderFactory(self, value):
        return None
    
    def visitPrimitiveFunction(self, primitiveFunction):
        runtimeFunctionName = self.context.getPrimitiveRuntimeFunctionNameFor(primitiveFunction.name)
        if runtimeFunctionName is None:
            return None
        return self.currentMirPackage.getOrCreateRuntimePrimitiveNamed(runtimeFunctionName)

    def visitPrimitiveMacro(self, value):
        return None
    
    def visitFunction(self, value: HIRFunction):
        mirFunction = MirFunction(value.name)
        mirFunction.sourceFunction = value
        self.valueMap[value] = mirFunction
        self.currentMirPackage.addMirFunction(mirFunction)

        HirFunction2Mir(self).translateHirFunctionToMir(value, mirFunction)
        return mirFunction

    def visitPackage(self, package: HIRPackage):
        if package in self.valueMap:
            return self.valueMap[package]
        
        # Start translating the package.
        oldCurrentPackage = self.currentMirPackage
        mirPackage = MirPackage(self.context, package.name)
        self.valueMap[package] = mirPackage
        self.currentMirPackage = mirPackage

        # Translate the used packages.
        for usedPackage in package.usedPackages:
            self.translateValue(usedPackage)
            
        # Translate the children
        package.finishPendingAnalysis()
        for child in package.children:
            self.translateValue(child)

        self.currentMirPackage = oldCurrentPackage
        #mirPackage.dumpToConsole()
        return mirPackage

class HirFunction2Mir(HIRVisitor):
    def __init__(self, packageTranslator: HirPackage2Mir):
        super().__init__()
        self.packageTranslator = packageTranslator
        self.prologueBuilder: MirBuilder = None
        self.builder: MirBuilder = None
        self.valueMap = {}

    def translateHirFunctionToMir(self, hirFunction: HIRFunction, mirFunction: MirFunction):
        self.hirFunction = hirFunction
        self.mirFunction = mirFunction

        prologueBlock = MirBasicBlock(hirFunction.sourcePosition, 'prologue')
        mirFunction.addBasicBlock(prologueBlock)

        # Prologue block for receiving arguments, closure captures and constants.
        self.prologueBuilder = MirBuilder(mirFunction, prologueBlock)
        self.builder = MirBuilder(mirFunction, prologueBlock)
        for argument in hirFunction.dependentFunctionType.arguments:
            self.visitNextValue(argument)

        # Translate th basic blocks
        self.createAndMapBasicBlocks()

        # Translate the basic blocks
        self.translateBasicBlocks()

        # End the prologue
        firstBasicBlock = self.valueMap[hirFunction.firstBasicBlock]
        self.prologueBuilder.jump(firstBasicBlock, hirFunction.sourcePosition)

    def createAndMapBasicBlocks(self):
        basicBlock = self.hirFunction.firstBasicBlock
        while basicBlock is not None:
            mirBasicBlock = MirBasicBlock(basicBlock.sourcePosition, basicBlock.name)
            self.mirFunction.addBasicBlock(mirBasicBlock)
            self.valueMap[basicBlock] = mirBasicBlock
            self.translateBasicBlockPhis(basicBlock, mirBasicBlock)

            basicBlock = basicBlock.nextBlock

    def translateBasicBlockPhis(self, basicBlock: HIRBasicBlock, mirBasicBlock: MirBasicBlock):
        self.builder.basicBlock = mirBasicBlock

        instruction = basicBlock.firstInstruction
        while instruction is not None and instruction.isPhiInstruction():
            phiType = self.packageTranslator.translateValue(instruction.getType())
            phiValue = phiType.emitPhiWithBuilder(self.builder, instruction.sourcePosition)
            self.valueMap[instruction] = phiValue
            
            instruction = instruction.nextInstruction

    def translateBasicBlocks(self):
        block = self.hirFunction.firstBasicBlock
        while block is not None:
            self.builder.basicBlock = self.valueMap[block]
            instruction = block.firstInstruction
            while instruction is not None:
                self.translateInstruction(instruction)
                instruction = instruction.nextInstruction
            block = block.nextBlock

    def translateInstruction(self, instruction: HIRInstruction):
        # Phis are crearted in the basic block creation pass
        if instruction.isPhiInstruction():
            assert instruction in self.valueMap
            return

        assert instruction not in self.valueMap
        value = self.visitNextValue(instruction)
        self.valueMap[instruction] = value
    
    def translateValue(self, value):
        if value in self.valueMap:
            return self.valueMap[value]
        
        assert not value.isFunctionLocalValue()
        translatedValue = self.visitNextValue(value)
        self.valueMap[value] = translatedValue
        return translatedValue
    
    def visitNextValue(self, value: HIRValue):
        return value.accept(self)
    
    def visitValue(self, value):
        assert False

    def visitConstantLiteralCharacterValue(self, constantLiteral: HIRConstantLiteralCharacterValue):
        constantType = self.packageTranslator.translateValue(constantLiteral.getType())
        return constantType.emitCharacterConstantWithBuilder(self.prologueBuilder, constantLiteral.value, constantLiteral.sourcePosition)

    def visitConstantLiteralFloatValue(self, constantLiteral: HIRConstantLiteralCharacterValue):
        constantType = self.packageTranslator.translateValue(constantLiteral.getType())
        return constantType.emitFloatConstantWithBuilder(self.prologueBuilder, constantLiteral.value, constantLiteral.sourcePosition)

    def visitConstantLiteralIntegerValue(self, constantLiteral: HIRConstantLiteralIntegerValue):
        constantType = self.packageTranslator.translateValue(constantLiteral.getType())
        return constantType.emitIntegerConstantWithBuilder(self.prologueBuilder, constantLiteral.value, constantLiteral.sourcePosition)

    def visitConstantLiteralVoidValue(self, constantLiteral: HIRConstantLiteralIntegerValue):
        constantType = self.packageTranslator.translateValue(constantLiteral.getType())
        return constantType.emitVoidConstantWithBuilder(self.prologueBuilder, constantLiteral.sourcePosition)

    def visitConstantLiteralNilValue(self, constantLiteral: HIRConstantLiteralIntegerValue):
        constantType = self.packageTranslator.translateValue(constantLiteral.getType())
        return constantType.emitNilConstantWithBuilder(self.prologueBuilder, constantLiteral.sourcePosition)
    
    def visitFunction(self, hirFunction):
        return self.packageTranslator.translateValue(hirFunction)

    def visitArgument(self, argument: HIRArgument):
        argumentType = self.packageTranslator.translateValue(argument.type)
        argumentTemporary = argumentType.emitArgumentWithBuilder(self.builder, argument.sourcePosition)
        self.valueMap[argument] = argumentTemporary

    def visitCapture(self, capture: HIRCapture):
        assert False

    def visitAllocaInstruction(self, instruction: HIRAllocaInstruction):
        valueType = self.packageTranslator.translateValue(instruction.valueType)
        memoryDescriptor = valueType.getMemoryDescriptor()
        return self.builder.gcAllocateAt(memoryDescriptor, instruction.sourcePosition)

    def visitAssertInstruction(self, instruction):
        assert False

    def visitRuntimeErrorInstruction(self, instruction):
        assert False

    def visitLoadInstruction(self, instruction):
        storage = self.translateValue(instruction.storage)
        loadType = self.packageTranslator.translateValue(instruction.getType())
        return loadType.emitLoadWithBuilder(self.builder, storage, instruction.sourcePosition)

    def visitStoreInstruction(self, instruction):
        storage = self.translateValue(instruction.storage)
        valueToStore = self.translateValue(instruction.valueToStore)
        return valueToStore.type.emitStoreWithBuilder(self.builder, storage, valueToStore, instruction.sourcePosition)

    def visitBranchInstruction(self, instruction):
        self.builder.jump(self.valueMap[instruction.destination], instruction.sourcePosition)

    def visitConditionalBranchInstruction(self, instruction):
        condition = self.translateValue(instruction.condition)
        trueDestination = self.translateValue(instruction.trueDestination)
        falseDestination = self.translateValue(instruction.falseDestination)
        self.builder.conditionalBranchAt(condition, trueDestination, falseDestination, instruction.sourcePosition)

    def visitCallInstruction(self, instruction):
        if instruction.functional.isPrimitiveFunction():
            primitiveName = instruction.functional.getPrimitiveName()
            translator = self.packageTranslator.context.getPrimitiveTranslatorFor(primitiveName)
            return translator(self, instruction)

        functional = self.translateValue(instruction.functional)
        self.builder.beginCallAt(instruction.sourcePosition)
        for argument in instruction.arguments:
            argumentValue = self.translateValue(argument)
            argumentType = self.packageTranslator.translateValue(argument.getType())
            argumentType.emitCallArgumentWithBuilder(self.builder, argumentValue, argument.sourcePosition)

        callType = self.packageTranslator.translateValue(instruction.getType())
        return callType.emitCallWithBuilder(self.builder, functional, instruction.sourcePosition)

    def callRuntimeFunctionWithName(self, instruction: HIRCallInstruction, runtimePrimitiveName):
        primitive = self.packageTranslator.currentMirPackage.getOrCreateRuntimePrimitiveNamed(runtimePrimitiveName)
        self.builder.beginCallAt(instruction.sourcePosition)
        for argument in instruction.arguments:
            argumentValue = self.translateValue(argument)
            argumentType = self.packageTranslator.translateValue(argument.getType())
            argumentType.emitCallArgumentWithBuilder(self.builder, argumentValue, argument.sourcePosition)

        callType = self.packageTranslator.translateValue(instruction.getType())
        return callType.emitCallWithBuilder(self.builder, primitive, instruction.sourcePosition)

    def visitSendInstruction(self, instruction):
        assert False

    def visitEnumBoxValueInstruction(self, instruction):
        assert False

    def visitEnumUnboxValueInstruction(self, instruction):
        assert False

    def visitExtractFieldReferenceInstruction(self, instruction):
        assert False

    def visitSetAggregateFieldInstruction(self, instruction):
        assert False

    def visitDynamicUnboxInstruction(self, instruction):
        assert False

    def visitDynamicUnboxInstruction(self, instruction):
        assert False

    def visitMakeAssociationInstruction(self, instruction):
        assert False

    def visitMakeClosureInstruction(self, instruction):
        assert False

    def visitMakeObjectInstruction(self, instruction):
        objectType = self.packageTranslator.translateValue(instruction.getType())
        memoryDescriptor = objectType.getMemoryDescriptor()
        return self.builder.gcAllocateAt(memoryDescriptor, instruction.sourcePosition)

    def visitMakeStructInstruction(self, instruction):
        assert False

    def visitPhiInstruction(self, instruction):
        raise RuntimeError("Phi should be translated during the basic block creation pass")

    def visitPhiSourceInstruction(self, instruction):
        targetPhi = self.valueMap[instruction.targetPhi]
        sourceValue = self.translateValue(instruction.sourceValue)
        sourceValueType = sourceValue.type
        return sourceValueType.emitPhiSourceWithBuilder(self.builder, targetPhi, sourceValue, instruction.sourcePosition)


    def visitReturnInstruction(self, instruction):
        # TODO: handle return void
        hirReturnType = instruction.valueToReturn.getType()
        if hirReturnType.isVoidType():
            return self.builder.returnVoidAt(instruction.sourcePosition)

        returnType = self.packageTranslator.translateValue(hirReturnType)
        returnValue = self.translateValue(instruction.valueToReturn)
        return returnType.emitReturnWithBuilder(self.builder, returnValue, instruction.sourcePosition)

    def visitUnreachableInstruction(self, instruction):
        assert False
