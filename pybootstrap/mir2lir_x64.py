from mir import *
from lir import *

class MirPackage2LirX64(MirVisitor):
    def __init__(self, context: MirContext):
        super().__init__()
        self.context = context
        self.lirModule: LirModule = None
        self.asm: LirAssembler = None
        self.valueMap = {}
        self.pendingFunctionTranslationQueue = []

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
        assert False

    def visitGlobalConstant(self, globalConstant: MirGlobalConstant):
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
        self.asm = asm
        self.functionSymbol = functionSymbol
        self.stackFrameLayout: MirFunctionStackFrameLayout = None
        self.basicBlockToLabelMap = {}

    def translateFunction(self, function: MirFunction):
        function.dumpToConsole()

        self.stackFrameLayout = MirFunctionStackFrameLayout(self.packageTranslator.context)
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
        match instruction.opcode:
            case MirOpcode.ArgumentInt32:
                pass
            case MirOpcode.Jump:
                destinationLabel = self.basicBlockToLabelMap[instruction.firstArgument]
                self.asm.x86_jmpLsv(destinationLabel)

            case MirOpcode.Int32Add:
                pass

            case MirOpcode.ReturnInt32:
                self.emitFrameReturn()

            case _:
                raise RuntimeError("Unimplemented instruction " + instruction.opcode.name)


    def emitFrameReturn(self):
        self.asm.x86_add64RegImmS32(X86_RSP, self.stackFrameLayout.stackFrameSubtractionSize)
        self.asm.x86_pop(X86_RBP)
        self.asm.x86_ret()
