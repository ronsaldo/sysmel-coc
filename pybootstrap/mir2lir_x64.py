from mir import *
from lir import *

class X64SysVCallingConvention(MirCallingConvention):
    def __init__(self):
        self.stackAlignment = 16
        self.stackParameterAlignment = 8
        self.calloutShadowSpace = 0

        self.integerPassingRegister = [ X86_RDI, X86_RSI, X86_RDX, X86_RCX, X86_R8, X86_R9 ]
        self.firstIntegerResultRegister = X86_RAX
        self.secondIntegerResultRegister = X86_RDX

        self.closureRegister = X86_R10
        self.closureGCRegister = X86_R11

        self.floatPassingRegisters = [
            X86_XMM0,  X86_XMM1,  X86_XMM2,  X86_XMM3,
            X86_XMM4,  X86_XMM5,  X86_XMM6,  X86_XMM7,
        ]
        self.firstFloatResultRegister = X86_XMM0
        self.secondFloatResultRegister = X86_XMM1

        self.allocatableIntegerRegisters = [
            X86_RAX,

            X86_RDI, # Arg 1
            X86_RSI, # Arg 2
            X86_RDX, # Arg 3
            X86_RCX, # Arg 4
            X86_R8,  # Arg 5
            X86_R9,  # Arg 6
            X86_R10, # Static function chain/Closure pointer
            X86_R11, # Closure GC pointer

            X86_RBX,

            X86_R12,
            X86_R13,
            X86_R14,
            X86_R15, # Optional GOT pointer
        ]
        self.allocatableFloatRegisters = [
            X86_XMM0,  X86_XMM1,  X86_XMM2,  X86_XMM3,
            X86_XMM4,  X86_XMM5,  X86_XMM6,  X86_XMM7,
            X86_XMM8,  X86_XMM9,  X86_XMM10, X86_XMM11,
            X86_XMM12, X86_XMM13, X86_XMM14, X86_XMM15,
        ]

        self.callTouchedIntegerRegisters = [
            X86_RAX, X86_RCX, X86_RDX, X86_RSI, X86_RDI, X86_R8, X86_R9, X86_R10, X86_R11
        ]
        self.callTouchedFloatRegisters = [
            X86_XMM0,  X86_XMM1,  X86_XMM2,  X86_XMM3,
            X86_XMM4,  X86_XMM5,  X86_XMM6,  X86_XMM7,
            X86_XMM8,  X86_XMM9,  X86_XMM10, X86_XMM11,
            X86_XMM12, X86_XMM13, X86_XMM14, X86_XMM15,
        ]

        self.callPreservedIntegerRegisters = [
            X86_RBX, X86_R12, X86_R13, X86_R14, X86_R15, X86_RSP, X86_RBP
        ]
        self.callPreservedFloatRegisters = []
        self.variadicCountRegister = X86_RAX

class MirPackage2LirX64(MirVisitor):
    def __init__(self, context: MirContext):
        super().__init__()
        self.context = context
        self.lirModule: LirModule = None
        self.asm: LirAssembler = None
        self.valueMap = {}
        self.externalGlobalSymbols = {}
        self.pendingFunctionTranslationQueue = []
        self.callingConvention = X64SysVCallingConvention()
        self.objectDataSectionStartSymbol = None
        self.objectDataSectionEndSymbol = None
        self.identityHashSeed = 7

    def getNextIdentityHash(self):
        self.identityHashSeed = (self.identityHashSeed * 1664525) & 0xFFFFFFFF
        return self.identityHashSeed

    def translateMirPackage(self, mirPackage: MirPackage):
        self.lirModule = LirModule()
        self.lirModule.name = mirPackage.name

        self.lirModule.getOrCreateCommonSections()

        self.asm = LirAssembler(self.lirModule)
        self.odsAsm = LirAssembler(self.lirModule)

        # Begin the object data section
        self.odsAsm.objectDataSection()
        self.objectDataSectionStartSymbol = self.odsAsm.makeGlobalObjectSymbol('__sysmel_ods_start')
        self.objectDataSectionEndSymbol = self.odsAsm.makeGlobalObjectSymbol('__sysmel_ods_end')
        self.odsAsm.setSymbolHere(self.objectDataSectionStartSymbol)
                
        self.asm.textSection()

        self.translateValue(mirPackage)
        self.translatePendingFunctions()

        # Finish the object data section
        self.odsAsm.objectDataSection()
        self.odsAsm.setSymbolHere(self.objectDataSectionEndSymbol)

        return self.lirModule
    
    def translateValue(self, value):
        if value in self.valueMap:
            return self.valueMap[value]
        
        translatedValue = self.visitValue(value)
        self.valueMap[value] = translatedValue
        return translatedValue

    def visitPackage(self, package: MirPackage):
        for element in package.elementTable:
            self.translateValue(element)
        return self.lirModule

    def visitImportedFunction(self, importedFunction):
        functionSymbolValue = importedFunction.getSymbolName()
        return self.asm.makeGlobalFunctionSymbol(functionSymbolValue)

    def visitBooleanConstant(self, globalConstant):
        assert False

    def visitVoidConstant(self, globalConstant):
        assert False

    def visitNilConstant(self, globalConstant):
        assert False

    def getOrCreateExternalGlobalSymbol(self, symbolValue):
        if symbolValue in self.externalGlobalSymbols:
            return self.externalGlobalSymbols[symbolValue]
        
        symbol = self.asm.makeGlobalObjectSymbol(symbolValue)
        self.externalGlobalSymbols[symbolValue] = symbol
        return symbol

    def getOrCreateExternalGlobalFunctionSymbol(self, symbolValue):
        if symbolValue in self.externalGlobalSymbols:
            return self.externalGlobalSymbols[symbolValue]
        
        symbol = self.asm.makeGlobalFunctionSymbol(symbolValue)
        self.externalGlobalSymbols[symbolValue] = symbol
        return symbol
            
    def computeStringHash(self, string):
        hash = (len(string)*1664525) & 0xFFFFFFFF
        for char in string:
            hash = ((hash + char)*1664525) & 0xFFFFFFFF
        return hash

    def makeNativeMethod(self, argumentCount, functionSymbol):
        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        nativeMethodSymbol = self.odsAsm.makePrivateSymbol('nativeMethod')

        self.odsAsm.setSymbolHere(nativeMethodSymbol)
        self.odsAsm.addPointer(self.getOrCreateExternalGlobalSymbol('NativeMethod_Class'), 0)
        self.odsAsm.addQWord(40) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(self.getNextIdentityHash()) # identity hash

        self.odsAsm.addQWord(0) # argumentCount
        self.odsAsm.addPointer(functionSymbol, 0) # nativeFunction

        return nativeMethodSymbol
    
    def makeMethodDictElementPointer(self, element):
        if element is None:
            return None
        if isinstance(element, MirMethodDictionarySymbol):
            return self.getOrCreateLiteralSymbolWithByteString(element.value)
        if element.isMirFunction():
            return self.makeNativeMethod(element.getArgumentCount(), self.translateValue(element))
        assert False

    def makeArrayWithMethodDictElements(self, elements):
        elementPointers = list(map(self.makeMethodDictElementPointer, elements))

        size = len(elementPointers)
        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        arraySymbol = self.odsAsm.makePrivateSymbol('array')

        self.odsAsm.setSymbolHere(arraySymbol)
        self.odsAsm.addPointer(self.getOrCreateExternalGlobalSymbol('Array_Class'), 0)
        self.odsAsm.addQWord(24 + size*8) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(self.getNextIdentityHash()) # identity hash

        for element in elementPointers:
            if element is None:
                self.odsAsm.addQWord(0)
            else:
                self.odsAsm.addPointer(element, 0)
        return arraySymbol

    def makeMethodDictionary(self, behaviorType):
        methodDictionary = behaviorType.typeWithMethodDictionary.methodDictionary
        arraySymbol = self.makeArrayWithMethodDictElements(methodDictionary.array)

        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        methodDictionarySymbol = self.odsAsm.makePrivateSymbol('methodDict')

        self.odsAsm.setSymbolHere(methodDictionarySymbol)
        self.odsAsm.addPointer(self.getOrCreateExternalGlobalSymbol('MethodDictionary_Class'), 0)
        self.odsAsm.addQWord(40) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(self.getNextIdentityHash()) # identity hash

        self.odsAsm.addQWord(methodDictionary.tally) # tally
        self.odsAsm.addPointer(arraySymbol, 0) # array

        return methodDictionarySymbol

    def visitClassType(self, classType: MirClassType):
        classSymbolName = classType.name + '_Class'
        classSymbol = self.getOrCreateExternalGlobalSymbol(classSymbolName)
        self.valueMap[classType] = classSymbol

        metaclass = self.translateValue(classType.type)
        methodDictionary = self.makeMethodDictionary(classType)
        nameSymbol = self.getOrCreateLiteralSymbolWithValue(classType.name)

        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        self.odsAsm.setSymbolHere(classSymbol)

        self.odsAsm.addPointer(metaclass, 0)
        self.odsAsm.addQWord(72) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(self.getNextIdentityHash()) # identity hash

        # Type
        self.odsAsm.addQWord(0) #GCLayoutRef gcLayout;
        self.odsAsm.addPointer(methodDictionary, 0) #MethodDictionaryRef methodDictionary;
        if classType.behavior.superclass is not None:
            superclassSymbol = self.getOrCreateExternalGlobalSymbol(classType.behavior.superclass.name + '_Class')
            self.odsAsm.addPointer(superclassSymbol, 0) #Object super;
        else:
            self.odsAsm.addQWord(0) #TypeRef supertype;

        self.odsAsm.addQWord(16) #size_t instanceAlignment;
        self.odsAsm.addQWord(72) #size_t instanceSize; # Class instance size

        #Class
        self.odsAsm.addPointer(nameSymbol, 0) #SymbolRef name
        
        return classSymbol

    def visitMetaclassType(self, metaclassType: MirMetaclassType):
        metaclassClassSymbol = self.getOrCreateExternalGlobalSymbol('Metaclass_Class')
        metaclassSymbolName = metaclassType.thisClass.name + '_Metaclass'
        metaclassSymbol = self.getOrCreateExternalGlobalSymbol(metaclassSymbolName)
        self.valueMap[metaclassType] = metaclassSymbol

        thisClass = self.translateValue(metaclassType.thisClass)
        methodDictionary = self.makeMethodDictionary(metaclassType)

        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        self.odsAsm.setSymbolHere(metaclassSymbol)

        self.odsAsm.addPointer(metaclassClassSymbol, 0)
        self.odsAsm.addQWord(72) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(self.getNextIdentityHash()) # identity hash
    
        # Type
        self.odsAsm.addQWord(0) #GCLayoutRef gcLayout;
        self.odsAsm.addPointer(methodDictionary, 0) #MethodDictionaryRef methodDictionary;
        if metaclassType.behavior.superclass is not None:
            superClassName = metaclassType.behavior.superclass.thisClass.name
            superMetaclassSymbol = self.getOrCreateExternalGlobalSymbol(superClassName + '_Metaclass')
            self.odsAsm.addPointer(superMetaclassSymbol, 0)
        else:
            self.odsAsm.addQWord(0) #TypeRef supertype;
        self.odsAsm.addQWord(0) #size_t instanceAlignment;
        self.odsAsm.addQWord(0) #size_t instanceSize;

        #Metaclass
        self.odsAsm.addPointer(thisClass, 0) #thisClass

        return metaclassSymbol
    
    def visitStringConstant(self, globalConstant):
        stringData = globalConstant.value.encode(encoding="utf-8")
        byteSize = 24 + len(stringData)
        identityHash = self.computeStringHash(stringData)

        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        stringConstantSymbol = self.odsAsm.makePrivateSymbol('stringConstant')
        self.odsAsm.setSymbolHere(stringConstantSymbol)
        self.odsAsm.addPointer(self.getOrCreateExternalGlobalSymbol('String_Class'), 0)
        self.odsAsm.addQWord(byteSize) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(identityHash) # identity hash
        self.odsAsm.addByteList(stringData)
        return stringConstantSymbol

    def getOrCreateLiteralSymbolWithValue(self, symbolValue: str):
        mirSymbol = MirSymbolConstant(symbolValue, self.context.gcPointerType)
        return self.translateValue(mirSymbol)
    
    def getOrCreateLiteralSymbolWithByteString(self, symbolValue: bytes):
        return self.getOrCreateLiteralSymbolWithValue(symbolValue.decode('utf-8'))

    def visitSymbolConstant(self, globalConstant):
        stringData = globalConstant.value.encode(encoding="utf-8")
        byteSize = 24 + len(stringData)
        identityHash = self.computeStringHash(stringData)

        self.odsAsm.objectDataSection()
        self.odsAsm.dataAlign(16)
        stringConstantSymbol = self.odsAsm.makePrivateSymbol('symbolConstant')
        self.odsAsm.setSymbolHere(stringConstantSymbol)
        self.odsAsm.addPointer(self.getOrCreateExternalGlobalSymbol('Symbol_Class'), 0)
        self.odsAsm.addQWord(byteSize) # Byte Size
        self.odsAsm.addDWord(0) # GC color
        self.odsAsm.addDWord(identityHash) # identity hash
        self.odsAsm.addByteList(stringData)
        return stringConstantSymbol

    def visitFunction(self, function: MirFunction):
        functionSymbolValue = function.getSymbolName()
        functionSymbol = self.asm.makeGlobalFunctionSymbol(functionSymbolValue)
        self.pendingFunctionTranslationQueue.append(function)
        return functionSymbol

    def translatePendingFunctions(self):
        while len(self.pendingFunctionTranslationQueue) != 0:
            toTranslate = self.pendingFunctionTranslationQueue
            self.pendingFunctionTranslationQueue = []
            for function in toTranslate:
                self.translateFunction(function)
    
    def translateFunction(self, function: MirFunction):
        functionSymbol = self.valueMap[function]
        MirFunction2LirX64(self, self.asm, functionSymbol).translateFunction(function)

class MirFunction2LirX64(MirVisitor):
    def __init__(self, packageTranslator: MirPackage2LirX64, asm: LirAssembler, functionSymbol):
        super().__init__()
        self.packageTranslator = packageTranslator
        self.callingConvention = packageTranslator.callingConvention
        self.asm = asm
        self.functionSymbol = functionSymbol
        self.stackFrameLayout: MirFunctionStackFrameLayout = None
        self.basicBlockToLabelMap = {}

    def translateFunction(self, function: MirFunction):
        #function.dumpToConsole()

        self.computeInstructionsConstraints(function)

        self.stackFrameLayout = MirFunctionStackFrameLayout(self.packageTranslator.context)
        self.stackFrameLayout.callingConvention = self.packageTranslator.callingConvention
        function.computeStackFrameLayoutIn(self.stackFrameLayout)

        self.stackFrameLayout.addFramePointer()
        self.stackFrameLayout.addReturnPointer()
        self.stackFrameLayout.finish()

        self.createBasicBlockLabels(function)

        self.asm.textSection()

        self.asm.setSymbolHere(self.functionSymbol)
        self.asm.x86_endbr64()
        self.asm.x86_push(X86_RBP)
        self.asm.x86_mov64RegReg(X86_RBP, X86_RSP)
        self.asm.x86_sub64RegImmS32(X86_RSP, self.stackFrameLayout.stackFrameSubtractionSize)

        self.translateBasicBlocks(function)

        self.asm.endFunctionSymbolHere(self.functionSymbol)

    def computeInstructionsConstraints(self, function: MirFunction):
        self.integerArgumentCount = 0
        self.floatArgumentCount = 0

        self.calloutIntegerArgumentCount = 0
        self.calloutFloatArgumentCount = 0

        basicBlock = function.firstBasicBlock
        while basicBlock is not None:
            instruction = basicBlock.firstInstruction
            while instruction is not None:
                self.computeInstructionConstraints(instruction)
                instruction = instruction.next
            basicBlock = basicBlock.next

    def createBasicBlockLabels(self, function: MirFunction):
        basicBlock = function.firstBasicBlock
        while basicBlock is not None:
            basicBlockSymbol = self.asm.makePrivateSymbol(basicBlock.name)
            self.basicBlockToLabelMap[basicBlock] = basicBlockSymbol
            basicBlock = basicBlock.next

    def translateBasicBlocks(self, function: MirFunction):
        basicBlock = function.firstBasicBlock
        while basicBlock is not None:
            self.translateBasicBlock(basicBlock)
            basicBlock = basicBlock.next

    def translateBasicBlock(self, basicBlock: MirBasicBlock):
        self.asm.setSymbolHere(self.basicBlockToLabelMap[basicBlock])
        instruction = basicBlock.firstInstruction
        while instruction is not None:
            self.translateInstruction(instruction)
            instruction = instruction.next
    def translateInstruction(self, instruction: MirInstruction):
        # Load the arguments
        if instruction.firstArgumentLocation is not None and instruction.firstArgument is not None:
            self.moveFromTemporaryIntoLocation(instruction.firstArgument, instruction.firstArgumentLocation)
        if instruction.secondArgumentLocation is not None and instruction.secondArgument is not None:
            self.moveFromTemporaryIntoLocation(instruction.secondArgument, instruction.secondArgumentLocation)

        # Generate the code
        self.translateInstructionWithOpcode(instruction)

        # Store the result
        if instruction.resultLocation is not None:
            self.moveFromLocationIntoTemporary(instruction.resultLocation, instruction.result)

    def computeInstructionConstraints(self, instruction: MirInstruction):
        firstIntegerRegister = self.callingConvention.allocatableIntegerRegisters[0]
        secondIntegerRegister = self.callingConvention.allocatableIntegerRegisters[1]
        resultIntegerRegister = firstIntegerRegister

        match instruction.opcode:
            case MirOpcode.ArgumentInt32 | MirOpcode.ArgumentInt64 | MirOpcode.ArgumentPointer | MirOpcode.ArgumentGCPointer:
                if self.integerArgumentCount < len(self.callingConvention.integerPassingRegister):
                    instruction.resultLocation = MirRegisterLocation(self.callingConvention.integerPassingRegister[self.integerArgumentCount], instruction.result.type.valueSize)
                self.integerArgumentCount += 1
            case MirOpcode.ArgumentFloat32 | MirOpcode.ArgumentFloat64:
                if self.floatArgumentCount < len(self.callingConvention.floatPassingRegisters):
                    instruction.resultLocation = MirFloatRegisterLocation(self.callingConvention.floatPassingRegisters[self.floatArgumentCount], instruction.result.type.valueSize)
                self.floatArgumentCount += 1

            case MirOpcode.BeginCall:
                self.calloutIntegerArgumentCount = 0
                self.calloutFloatArgumentCount = 0

            case MirOpcode.CallArgumentInt32 | MirOpcode.CallArgumentInt64 | MirOpcode.CallArgumentPointer | MirOpcode.CallArgumentGCPointer:
                assert self.calloutIntegerArgumentCount < len(self.callingConvention.integerPassingRegister)
                argumentRegister = self.callingConvention.integerPassingRegister[self.calloutIntegerArgumentCount]
                instruction.firstArgumentLocation = MirRegisterLocation(argumentRegister, instruction.firstArgument.type.valueSize)

                self.calloutIntegerArgumentCount += 1

            case MirOpcode.CallInt32Result | MirOpcode.CallInt64Result | MirOpcode.CallPointerResult | MirOpcode.CallGCPointerResult:
                if instruction.firstArgument.isTemporary():
                    instruction.firstArgumentLocation = MirRegisterLocation(self.callingConvention.firstIntegerResultRegister, instruction.firstArgument.type.valueSize)
                instruction.resultLocation = MirRegisterLocation(self.callingConvention.firstIntegerResultRegister, instruction.result.type.valueSize)


            case MirOpcode.CallVoidResult:
                pass

            case MirOpcode.ConstInt32 | MirOpcode.ConstInt64 | MirOpcode.ConstPointer | MirOpcode.ConstGCPointer| MirOpcode.ConstCharacter | MirOpcode.ConstInteger:
                instruction.resultLocation = MirRegisterLocation(resultIntegerRegister, instruction.result.type.valueSize)
            case MirOpcode.ConstVoid:
                pass

            case MirOpcode.Jump:
                pass

            case MirOpcode.Int32Add:
                instruction.firstArgumentLocation = MirRegisterLocation(firstIntegerRegister, instruction.firstArgument.type.valueSize)
                instruction.secondArgumentLocation = MirRegisterLocation(secondIntegerRegister, instruction.secondArgument.type.valueSize)
                instruction.resultLocation = MirRegisterLocation(firstIntegerRegister, instruction.result.type.valueSize)
            
            case MirOpcode.PointerAddConstantOffset:
                instruction.firstArgumentLocation = MirRegisterLocation(firstIntegerRegister, instruction.firstArgument.type.valueSize)
                instruction.resultLocation = MirRegisterLocation(firstIntegerRegister, instruction.result.type.valueSize)

            case MirOpcode.ReturnInt32 | MirOpcode.ReturnInt64 | MirOpcode.ReturnPointer | MirOpcode.ReturnGCPointer:
                instruction.firstArgumentLocation = MirRegisterLocation(X86_RAX, instruction.firstArgument.type.valueSize)

            case MirOpcode.ReturnVoid:
                pass

            case MirOpcode.LoadPointer | MirOpcode.LoadGCPointer:
                instruction.firstArgumentLocation = MirRegisterLocation(firstIntegerRegister, instruction.firstArgument.type.valueSize)
                instruction.resultLocation = MirRegisterLocation(firstIntegerRegister, instruction.result.type.valueSize)

            case MirOpcode.StoreInt8 | MirOpcode.StoreInt16 | MirOpcode.StoreInt32 | MirOpcode.StoreInt64 | MirOpcode.StorePointer | MirOpcode.StoreGCPointer:
                instruction.firstArgumentLocation = MirRegisterLocation(firstIntegerRegister, instruction.firstArgument.type.valueSize)
                instruction.secondArgumentLocation = MirRegisterLocation(secondIntegerRegister, instruction.secondArgument.type.valueSize)

            case MirOpcode.GCAllocate:
                argumentRegister = self.callingConvention.integerPassingRegister[0]
                instruction.firstArgumentLocation = MirRegisterLocation(argumentRegister, instruction.firstArgument.type.valueSize)
                instruction.resultLocation = MirRegisterLocation(self.callingConvention.firstIntegerResultRegister, instruction.result.type.valueSize)

            case _:
                raise RuntimeError("Unimplemented instruction constraints " + instruction.opcode.name)
    
    def moveFromLocationIntoTemporary(self, location, temporary):
        temporaryLocation = self.stackFrameLayout.temporaryLocationMap[temporary]
        self.moveFromLocationIntoLocation(location, temporaryLocation)

    def moveFromLocationIntoLocation(self, sourceLocation, destinationLocation):
        if sourceLocation.isRegisterLocation() and destinationLocation.isStackFrameLocation():
            return self.moveFromRegisterIntoStackFrame(sourceLocation, destinationLocation)
        if sourceLocation.isStackFrameLocation() and destinationLocation.isRegisterLocation():
            return self.moveFromStackFrameIntoRegister(sourceLocation, destinationLocation)
        assert False

    def moveFromRegisterIntoStackFrame(self, registerLocation, stackFrameLocation):
        if registerLocation.isFloatRegisterLocation():
            assert False

        if stackFrameLocation.size == 4:
            return self.asm.x86_mov32RmoReg(X86_RSP, stackFrameLocation.stackPointerRelativeOffset, registerLocation.value)
        elif stackFrameLocation.size == 8:
            return self.asm.x86_mov64RmoReg(X86_RSP, stackFrameLocation.stackPointerRelativeOffset, registerLocation.value)
        assert False

    def moveFromStackFrameIntoRegister(self, stackFrameLocation, registerLocation):
        if registerLocation.isFloatRegisterLocation():
            assert False

        if stackFrameLocation.size == 4:
            return self.asm.x86_mov32RegRmo(registerLocation.value, X86_RSP, stackFrameLocation.stackPointerRelativeOffset)
        elif stackFrameLocation.size == 8:
            return self.asm.x86_mov64RegRmo(registerLocation.value, X86_RSP, stackFrameLocation.stackPointerRelativeOffset)
        assert False

    def moveSymbolAddressIntoRegister(self, symbol, destinationRegister):
        self.asm.x86_lea64RegLsv(destinationRegister.value, symbol, 0)

    def moveSymbolAddressIntoLocation(self, symbol, destinationLocation):
        if destinationLocation.isRegisterLocation():
            return self.moveSymbolAddressIntoRegister(symbol, destinationLocation)
        assert False

    def moveFromTemporaryIntoLocation(self, temporaryOrGlobalConstant, location):
        if temporaryOrGlobalConstant.isGlobalConstant():
            globalConstantSymbol = self.packageTranslator.translateValue(temporaryOrGlobalConstant)
            return self.moveSymbolAddressIntoLocation(globalConstantSymbol, location)

        temporaryLocation = self.stackFrameLayout.temporaryLocationMap[temporaryOrGlobalConstant]
        self.moveFromLocationIntoLocation(temporaryLocation, location)

    def translateInstructionWithOpcode(self, instruction: MirInstruction):
        match instruction.opcode:
            case MirOpcode.ArgumentInt32 | MirOpcode.ArgumentInt64 | MirOpcode.ArgumentPointer |MirOpcode.ArgumentGCPointer | MirOpcode.ArgumentFloat32 | MirOpcode.ArgumentFloat64:
                pass

            case MirOpcode.BeginCall:
                pass

            case MirOpcode.CallArgumentInt32 | MirOpcode.CallArgumentInt64 | MirOpcode.CallArgumentPointer | MirOpcode.CallArgumentGCPointer | MirOpcode.CallArgumentFloat32 | MirOpcode.CallArgumentFloat64:
                pass

            case MirOpcode.CallInt32Result | MirOpcode.CallInt64Result | MirOpcode.CallPointerResult | MirOpcode.CallGCPointerResult | MirOpcode.CallVoidResult:
                if instruction.firstArgumentLocation is not None:
                    self.asm.x86_callReg(instruction.firstArgumentLocation.value)
                else:
                    calledFunction = self.packageTranslator.translateValue(instruction.firstArgument)
                    self.asm.x86_callGsv(calledFunction)

            case MirOpcode.ConstInt32:
                self.asm.x86_mov32RegImm32(instruction.resultLocation.value, instruction.firstArgument)
                pass

            case MirOpcode.ConstCharacter:
                # Integer encoding
                # TODO: Handle large integers
                self.asm.x86_mov32RegImm32(instruction.resultLocation.value, (instruction.firstArgument << 3) | 2)

            case MirOpcode.ConstInteger:
                # Integer encoding
                # TODO: Handle large integers
                self.asm.x86_mov32RegImm32(instruction.resultLocation.value, (instruction.firstArgument << 3) | 1)

            case MirOpcode.Jump:
                destinationLabel = self.basicBlockToLabelMap[instruction.firstArgument]
                self.asm.x86_jmpLsv(destinationLabel)

            case MirOpcode.Int32Add:
                self.asm.x86_mov32RegReg(instruction.resultLocation.value, instruction.firstArgumentLocation.value)
                self.asm.x86_add32RegReg(instruction.resultLocation.value, instruction.secondArgumentLocation.value)
                pass

            case MirOpcode.ReturnInt32 | MirOpcode.ReturnInt64 | MirOpcode.ReturnPointer | MirOpcode.ReturnFloat32 | MirOpcode.ReturnFloat64 | MirOpcode.ReturnGCPointer | MirOpcode.ReturnVoid:
                self.emitFrameReturn()

            case MirOpcode.PointerAddConstantOffset:
                self.asm.x86_mov64RegReg(instruction.resultLocation.value, instruction.firstArgumentLocation.value)
                self.asm.x86_add64RegImmS32(instruction.resultLocation.value, instruction.secondArgument)

            case MirOpcode.LoadInt64 | MirOpcode.LoadPointer | MirOpcode.LoadGCPointer:
                self.asm.x86_mov64RegRmo(instruction.resultLocation.value, instruction.firstArgumentLocation.value, 0)

            case MirOpcode.StoreInt64 | MirOpcode.StorePointer | MirOpcode.StoreGCPointer:
                self.asm.x86_mov64RmoReg(instruction.firstArgumentLocation.value, 0, instruction.secondArgumentLocation.value)

            case MirOpcode.GCAllocate:
                secondArgumentRegister = self.callingConvention.integerPassingRegister[1]
                # Fixme: Use a 64 bit integer here
                self.asm.x86_mov32RegImm32(secondArgumentRegister, instruction.secondArgument)

                allocateFunction = self.packageTranslator.getOrCreateExternalGlobalFunctionSymbol('sysmel_type_allocateWithByteVariableSizedData')
                self.asm.x86_callGsv(allocateFunction)

            case _:
                raise RuntimeError("Unimplemented instruction " + instruction.opcode.name)


    def emitFrameReturn(self):
        self.asm.x86_add64RegImmS32(X86_RSP, self.stackFrameLayout.stackFrameSubtractionSize)
        self.asm.x86_pop(X86_RBP)
        self.asm.x86_ret()
