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
        self.pendingFunctionTranslationQueue = []
        self.callingConvention = X64SysVCallingConvention()

    def translateMirPackage(self, mirPackage: MirPackage):
        self.lirModule = LirModule()
        self.lirModule.name = mirPackage.name

        self.lirModule.getOrCreateCommonSections()

        self.asm = LirAssembler(self.lirModule)
        self.asm.textSection()

        self.translateValue(mirPackage)
        self.translatePendingFunctions()
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

    def visitStringConstant(self, globalConstant):
        assert False

    def visitSymbolConstant(self, globalConstant):
        assert False

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
        if instruction.firstArgumentLocation is not None:
            self.moveFromTemporaryIntoLocation(instruction.firstArgument, instruction.firstArgumentLocation)
        if instruction.secondArgumentLocation is not None:
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

            case MirOpcode.ReturnInt32 | MirOpcode.ReturnInt64 | MirOpcode.ReturnPointer | MirOpcode.ReturnGCPointer:
                instruction.firstArgumentLocation = MirRegisterLocation(X86_RAX, instruction.firstArgument.type.valueSize)

            case MirOpcode.ReturnVoid:
                pass

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

    def moveFromTemporaryIntoLocation(self, temporary, location):
        temporaryLocation = self.stackFrameLayout.temporaryLocationMap[temporary]
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

            case _:
                raise RuntimeError("Unimplemented instruction " + instruction.opcode.name)


    def emitFrameReturn(self):
        self.asm.x86_add64RegImmS32(X86_RSP, self.stackFrameLayout.stackFrameSubtractionSize)
        self.asm.x86_pop(X86_RBP)
        self.asm.x86_ret()
