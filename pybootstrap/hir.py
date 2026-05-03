from parsetree import *
from abc import ABC, abstractmethod
import math

class HIRVisitor(ABC):
    def visitValue(self, value):
        pass

class HIRValue(ABC):
    def __init__(self, sourcePosition: SourcePosition):
        self.sourcePosition = sourcePosition
    
    def accept(self, visitor: HIRVisitor):
        return visitor.visitValue(self)
    
    def analyzeAndEvaluateIdentifierReferenceNode(self, evaluator, node: ParseTreeIdentifierReferenceNode):
        return self

    def analyzeAndBuildIdentifierReferenceNode(self, analyzer, node: ParseTreeIdentifierReferenceNode):
        return self

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        selfType = self.getType()
        if selfType is None:
            raise RuntimeError(str(node.sourcePosition) +  ": cannot analyze and build non-functional value.")
        return selfType.analyzeAndBuildApplicationNode(buildPass, node, functional)

    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        selfType = self.getType()
        if selfType is None:
            raise RuntimeError(str(node.sourcePosition) +  ": cannot analyze and evaluate non-functional value.")
        return selfType.analyzeAndEvaluateApplicationNode(evaluationPass, node, functional)

    def analyzeAndBuildAssignment(self, buildPass, node: ParseTreeAssignmentNode):
        selfType = self.getType()
        if not selfType.isReferenceType():
            raise RuntimeError(str(node.sourcePosition) +  ": storage type does not support assignments.")

        baseType = selfType.baseType
        valueToStore = buildPass.visitNodeWithExpectedType(node.value, baseType)
        buildPass.builder.store(self, valueToStore, node.sourcePosition)
        return self
    
    def analyzeAndEvaluateAssignment(self, evaluationPass, node: ParseTreeAssignmentNode):
        selfType = self.getType()
        if not selfType.isReferenceType():
            raise RuntimeError(str(node.sourcePosition) +  ": storage type does not support assignments.")

        baseType = selfType.baseType
        valueToStore = evaluationPass.visitNodeWithExpectedType(node.value, baseType)
        self.storeValue(valueToStore)
        return self
    
    def analyzeAndEvaluateMessageSendNode(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        selfType = self.getType()
        return selfType.analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)

    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        selfType = self.getType()
        return selfType.analyzeAndBuildMessageSendNode(buildPass, node, receiver)

    @abstractmethod
    def getType(self):
        pass
    
    def isType(self):
        return False

    def isNominalType(self):
        return False

    def isDynamicType(self):
        return False

    def isUniverseType(self):
        return False

    def isAssociationType(self):
        return False

    def isTupleType(self):
        return False

    def isDerivedType(self):
        return False

    def isPointerLikeType(self):
        return False

    def isPointerType(self):
        return False

    def isReferenceType(self):
        return False

    def isReferenceValue(self):
        return False

    def isMutableValueBoxType(self):
        return False
    
    def isDependentFunctionType(self):
        return False

    def isSimpleFunctionType(self):
        return False
    
    def isCompileTimeFunction(self):
        return False

    def isPureFunction(self):
        return False

    def isConstantValue(self):
        return False

    def isIntegerConstant(self):
        return False

    def isFloatConstant(self):
        return False
    
    def isBooleanConstant(self):
        return False

    def isCharacterConstant(self):
        return False

    def isStringConstant(self):
        return False

    def isSymbolConstant(self):
        return False

    def isVoidConstant(self):
        return False

    def isVoidType(self):
        return False

    def isNilConstant(self):
        return False

    def isParseTreeConstant(self):
        return False

    def evaluateInActivationContext(self, context):
        raise RuntimeError("%s evaluateInActivationContext subclassResponsibility" % str(self.__class__))
    
    def getValueInEvaluationContext(self, context):
        raise RuntimeError("%s getValueInEvaluationContext subclassResponsibility" % str(self.__class__))

    def markDependentUsage(self):
        # By default do nothing
        pass

class HIRType(HIRValue):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(sourcePosition)
        self.coreTypes = coreTypes

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        raise RuntimeError(str(node.sourcePosition) +  ": cannot analyze and build non-functional value.")
    
    def analyzeAndEvaluateApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        raise RuntimeError(str(node.sourcePosition) +  ": cannot analyze and evaluate non-functional value.")

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        selector = evaluator.visitSymbolNode(node.selector)

        # FIXME: remove this hack.
        if selector == 'yourself':
            return receiver

        foundMethod = self.lookupSelector(selector)
        if foundMethod is None:
            raise RuntimeError("%s: type '%s' does not have method with selector #%s." % (str(node.sourcePosition), str(self), selector))
        return foundMethod.analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)
    
    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        selector = buildPass.evaluateSymbolNode(node.selector)

        # FIXME: remove this hack.
        if selector == 'yourself':
            return receiver

        foundMethod = self.lookupSelector(selector)
        if foundMethod is None:
            raise RuntimeError("%s: type '%s' does not have method with selector #%s." % (str(node.sourcePosition), str(self), selector))
        return foundMethod.analyzeAndBuildMessageSendNode(buildPass, node, receiver)

    def isSatisfiedByValue(self, value: HIRValue):
        return self.isSatisfiedByType(value.getType())

    def isSatisfiedByType(self, subtype):
        return self == subtype

    def getType(self):
        return self.coreTypes.getUniverseAtLevel(0)

    def getValueInEvaluationContext(self, context):
        return self

    def isType(self):
        return True
    
    def withSelectorAddMethod(self, selector, method):
        raise RuntimeError("Cannot add a method to type %s\n" %(str(self)))

    def lookupSelector(self, selector):
        return None

class HIRNominalType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name
        self.methodDictionary = {}

    def getName(self):
        return self.name

    def isNominalType(self):
        return True

    def __str__(self):
        return self.name
    
    def withSelectorAddMethod(self, selector, method):
        self.methodDictionary[selector] = method

    def lookupSelector(self, selector):
        if selector in self.methodDictionary:
            return self.methodDictionary[selector]
        return None

class HIRDynamicType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isDynamicType(self):
        return True
    
    def __str__(self):
        return self.name

class HIRVoidType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isVoidType(self):
        return True
    
    def __str__(self):
        return self.name
    
class HIRUniverseType(HIRType):
    def __init__(self, name: str, coreTypes, level: int):
        super().__init__(coreTypes, None)
        self.level = level
        self.name = name

    def getName(self):
        return self.name

    def getType(self):
        return self.coreTypes.getUniverseAtLevel(self.level + 1)

    def isUniverseType(self):
        return True

    def __str__(self):
        return self.name

class HIRAssociationType(HIRType):
    def __init__(self, keyType: HIRType, valueType: HIRType, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.keyType = keyType
        self.valueType = valueType

    def isAssociationType(self):
        return True    

class HIRTupleType(HIRType):
    def __init__(self, elements: list[HIRType], coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.elements = elements

    def isTupleType(self):
        return True

class HIRDerivedType(HIRType):
    def __init__(self, baseType, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.baseType = baseType

    def isDerivedType(self):
        return True

class HIRPointerLikeType(HIRDerivedType):
    def isPointerLikeType(self):
        return True

class HIRPointerType(HIRPointerLikeType):
    def isPointerType(self):
        return True

class HIRReferenceType(HIRPointerLikeType):
    def isReferenceType(self):
        return True

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        return self.baseType.analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)
    
    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        return self.baseType.analyzeAndBuildMessageSendNode(buildPass, node, receiver)

class HIRMutableValueBoxType(HIRPointerLikeType):
    def isMutableValueBoxType(self):
        return True

class HIRSimpleFunctionType(HIRType):
    def __init__(self, argumentTypes: HIRType, resultType: HIRType, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.argumentTypes = argumentTypes
        self.resultType = resultType

    def isSimpleFunctionType(self):
        return True
    
    def evaluateAndTypecheckArguments(self, evaluator, arguments, sourcePosition):
        if len(arguments) != len(self.argumentTypes):
            raise RuntimeError("%s: expected %d arguments instead of %d." % (str(sourcePosition), len(self.argumentTypes), len(arguments)))
        
        typecheckedArguments = []
        for i in range(len(arguments)):
            typecheckedArgument = evaluator.visitNodeWithExpectedType(arguments[i], self.argumentTypes[i])
            typecheckedArguments.append(typecheckedArgument)

        return typecheckedArguments, self.resultType

    def analyzeBuildAndTypecheckArguments(self, buildPass, arguments, sourcePosition):
        if len(arguments) != len(self.argumentTypes):
            raise RuntimeError("%s: expected %d arguments instead of %d." % (str(sourcePosition), len(self.argumentTypes), len(arguments)))
        
        typecheckedArguments = []
        for i in range(len(arguments)):
            typecheckedArgument = buildPass.visitNodeWithExpectedType(arguments[i], self.argumentTypes[i])
            typecheckedArguments.append(typecheckedArgument)

        return typecheckedArguments, self.resultType
    
class HIRDependentFunctionType(HIRType):
    def __init__(self, arguments, resultType: HIRValue, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.arguments = arguments
        self.resultType = resultType

    def isDependentFunctionType(self):
        return True
    
    def canSimplify(self):
        for argument in self.arguments:
            if argument.hasDependentUser:
                return False
        return True
    
    def asSimplifiedType(self):
        if not self.canSimplify():
            return self
        
        argumentTypes = []
        for argument in self.arguments:
            argumentTypes.append(argument.type)
        
        return HIRSimpleFunctionType(argumentTypes, self.resultType, self.coreTypes, self.sourcePosition)
    
class HIRConstant(HIRValue):
    def __init__(self, sourcePosition):
        super().__init__(sourcePosition)

    def isConstantValue(self):
        return True
    
    def getValueInEvaluationContext(self, context):
        return self

class HIRConstantLiteralValue(HIRConstant):
    def __init__(self, type: HIRType, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type

    def getType(self):
        return self.type

class HIRConstantLiteralIntegerValue(HIRConstantLiteralValue):
    def __init__(self, value: int, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def __repr__(self):
        return 'integer %d' % self.value

    def isIntegerConstant(self):
        return True

class HIRConstantLiteralFloatValue(HIRConstantLiteralValue):
    def __init__(self, value: float, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def __repr__(self):
        return 'float %f' % self.value

    def isFloatConstant(self):
        return True

class HIRConstantLiteralBooleanValue(HIRConstantLiteralValue):
    def __init__(self, value: bool, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def __repr__(self):
        if self.value:
            return 'true'
        else:
            return 'false'

    def isBooleanConstant(self):
        return True

class HIRConstantLiteralCharacterValue(HIRConstantLiteralValue):
    def __init__(self, value: int, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def isCharacterConstant(self):
        return True
    
class HIRConstantLiteralStringValue(HIRConstantLiteralValue):
    def __init__(self, value: str, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def isStringConstant(self):
        return True
    
class HIRConstantLiteralSymbolValue(HIRConstantLiteralValue):
    def __init__(self, value: str, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def isSymbolConstant(self):
        return True

class HIRConstantLiteralVoidValue(HIRConstantLiteralValue):
    def __init__(self, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)

    def isVoidConstant(self):
        return True

    def __str__(self):
        return 'void'

class HIRConstantLiteralNilValue(HIRConstantLiteralValue):
    def __init__(self, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)

    def isNilConstant(self):
        return True

    def __str__(self):
        return 'nil'

class HIRConstantLiteralParseTree(HIRConstantLiteralValue):
    def __init__(self, value: ParseTreeNode, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def isParseTreeConstant(self):
        return True

    def __str__(self):
        return 'parseTreeConstant(%s)' % str(self.value)

class HIRMutableValueBox(HIRValue):
    def __init__(self, type, initialValue, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type
        self.value = initialValue

    def getType(self):
        return self.type

    def storeValueAtIndex(self, valueToStore, index):
        assert index == 0
        self.value = valueToStore

    def loadValueAtIndex(self, index):
        assert index == 0
        return self.value
    
class HIRPointerLikeValue(HIRValue):
    def __init__(self, type, storage, index, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type
        self.storage = storage
        self.index = index

    def getType(self):
        return self.type

    def storeValue(self, valueToStore):
        self.storage.storeValueAtIndex(valueToStore, 0)

    def loadValue(self):
        return self.storage.loadValueAtIndex(0)

class HIRPointerValue(HIRPointerLikeValue):
    pass

class HIRReferenceValue(HIRPointerLikeValue):
    def isReferenceValue(self):
        return True

class HIRMacroContext:
    def __init__(self, sourcePosition: SourcePosition):
        self.sourcePosition = sourcePosition

class HIRPrimitiveMacro(HIRConstant):
    def __init__(self, name: str, type, primitiveFunction, sourcePosition):
        super().__init__(sourcePosition)
        self.name = name
        self.type = type
        self.primitiveFunction = primitiveFunction

    def getType(self):
        return self.type

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        macroContext = HIRMacroContext(node.sourcePosition)
        expandedMacro = self.primitiveFunction(macroContext, *node.arguments)
        return buildPass.visitNode(expandedMacro)

    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        macroContext = HIRMacroContext(node.sourcePosition)
        expandedMacro = self.primitiveFunction(macroContext, *node.arguments)
        return evaluationPass.visitNode(expandedMacro)

class HIRPrimitiveFunction(HIRConstant):
    def __init__(self, name: str, type, primitiveFunction, sourcePosition, isCompileTime = False, isPure = False):
        super().__init__(sourcePosition)
        self.name = name
        self.type = type
        self.primitiveFunction = primitiveFunction
        self.isCompileTime = isCompileTime
        self.isPure = isPure

    def getType(self):
        return self.type

    def isCompileTimeFunction(self):
        return self.isCompileTime

    def isPureFunction(self):
        return self.isPure

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        assert False

    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        assert False

    def analyzeAndEvaluateMessageSendNode(self, evaluationPass, node: ParseTreeMessageSendNode, receiver):
        receiverNode = ParseTreeLiteralValueNode(node.sourcePosition, receiver)
        typecheckedArguments, resultType = self.type.evaluateAndTypecheckArguments(evaluationPass, [receiverNode] + node.arguments, node.sourcePosition)
        return self.primitiveFunction(*typecheckedArguments, resultType)
    
    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        receiverNode = ParseTreeLiteralValueNode(node.sourcePosition, receiver)
        typecheckedArguments, resultType = self.type.analyzeBuildAndTypecheckArguments(buildPass, [receiverNode] + node.arguments, node.sourcePosition)
        return buildPass.builder.call(self, typecheckedArguments, resultType, node.sourcePosition)
    
    def evaluateWithArgumentsAndResultType(self, arguments, resultType):
        return self.primitiveFunction(*arguments, resultType)
    
    def __str__(self):
        return 'primitiveFunction(%s)' % self.name

class HIRFunction(HIRConstant):
    def __init__(self, name: str, dependentFunctionType: HIRDependentFunctionType, sourcePosition):
        super().__init__(sourcePosition)
        self.name = name
        self.dependentFunctionType = dependentFunctionType
        self.captures = []
        self.firstBasicBlock = None
        self.lastBasicBlock = None
        self.isTopLevel = False
        self.enumeratedInstructions = None

    def getType(self):
        return self.dependentFunctionType
    
    def addBasicBlock(self, basicBlock):
        if self.lastBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            basicBlock.previousBlock = self.lastBasicBlock
            self.lastBasicBlock.nextBlock = basicBlock
            self.lastBasicBlock = basicBlock

    def enumerateInstruction(self):
        if self.enumeratedInstructions is not None:
            return self.enumeratedInstructions
        
        self.enumeratedInstructions = []
        def addLocalValue(localValue):
            localValue.index = len(self.enumeratedInstructions)
            self.enumeratedInstructions.append(localValue)

        for argument in self.dependentFunctionType.arguments:
            addLocalValue(argument)

        for capture in self.captures:
            addLocalValue(capture)

        basicBlock = self.firstBasicBlock
        while basicBlock is not None:
            addLocalValue(basicBlock)

            instruction = basicBlock.firstInstruction
            while instruction is not None:
                addLocalValue(instruction)
                instruction = instruction.nextInstruction

            basicBlock = basicBlock.nextBlock

        return self.enumeratedInstructions

    def fullPrintString(self) -> str:
        self.enumerateInstruction()
        result = "HIRFunction "
        if self.name is not None:
            result += self.name
        result += " {\n"

        for argument in self.dependentFunctionType.arguments:
            result += argument.fullPrintString() + '\n'
        
        basicBlock = self.firstBasicBlock
        while basicBlock is not None:
            result += basicBlock.fullPrintString()
            basicBlock = basicBlock.nextBlock

        result += "}\n"
        return result

    def evaluateWithArgumentsAndCaptures(self, arguments, captures):
        self.enumerateInstruction()
        activationContext = HIRFunctionActivationContext(self.enumeratedInstructions, self.dependentFunctionType.coreTypes, self.sourcePosition)
        activationContext.setCallArgumentsAndCaptures(arguments, captures)
        activationContext.evaluateInstructions()
        return activationContext.returnValue

    def evaluateWithArguments(self, arguments):
        return self.evaluateWithArgumentsAndCaptures(arguments, [])

class HIRFunctionActivationContext:
    def __init__(self, instructions, coreTypes, sourcePosition):
        self.coreTypes = coreTypes
        self.sourcePosition = sourcePosition
        self.instructionPC = 0
        self.pc = 0

        self.instructions = instructions
        self.instructionValues = [coreTypes.voidValue]*len(self.instructions)

        self.returnValue = None

    def atPCSetValue(self, valuePC, value):
        self.instructionValues[valuePC] = value

    def setCallArgumentsAndCaptures(self, argumentValues, captureValues):
        ## Arguments
        for i in range(len(argumentValues)):
            self.instructionValues[i] = argumentValues[i]
        
        ## Captures
        for i in range(len(captureValues)):
            self.instructionValues[len(argumentValues) + i] = captureValues[i]

    def setCurrentInstructionValue(self, valueToSet):
        self.instructionValues[self.instructionPC] = valueToSet

    def evaluateInstructions(self):
        instructionCount = len(self.instructions)
        while self.pc < instructionCount:
            # Fetch the instruction
            self.instructionPC = self.pc
            self.pc = self.pc + 1
            instruction = self.instructions[self.instructionPC]

            # Evaluate the instruction
            instruction.evaluateInActivationContext(self)

            if self.returnValue is not None:
                return self.returnValue

        raise RuntimeError("Reached the end of a function instructions")

class HIRFunctionLocalValue(HIRValue):
    def __init__(self, type, name: str = None, sourcePosition = None):
        super().__init__(sourcePosition)
        self.type = type
        self.name = name
        self.index = -1

    def __str__(self):
        return '%d|%s' %(self.index, str(self.name))

    def getType(self):
        return self.type

    def getValueInEvaluationContext(self, context):
        return context.instructionValues[self.index]
    
class HIRArgument(HIRFunctionLocalValue):
    def __init__(self, type, name = None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.hasDependentUser = False
        self.isSelf = False

    def fullPrintString(self) -> str:
        return '%d|%s := argument' %(self.index, str(self.name))

    def evaluateInActivationContext(self, context):
        # Nothing is required here
        pass
    
    def markDependentUsage(self):
        self.hasDependentUser = True


class HIRCapture(HIRFunctionLocalValue):
    def fullPrintString(self) -> str:
        return '%d|%s := capture' %(self.index, str(self.name))

    def evaluateInActivationContext(self, context):
        # Nothing is required here
        pass

class HIRBasicBlock(HIRFunctionLocalValue):
    def __init__(self, name = None, sourcePosition=None):
        super().__init__(None, name, sourcePosition)
        self.previousBlock = None
        self.nextBlock = None
        self.firstInstruction = None
        self.lastInstruction = None

    def addInstruction(self, instruction):
        if self.lastInstruction is None:
            self.firstInstruction = self.lastInstruction = instruction
        else:
            instruction.previousInstruction = self.lastInstruction
            self.lastInstruction.nextInstruction = instruction
            self.lastInstruction = instruction

    def fullPrintString(self) -> str:
        result = '$' + str(self.index)
        if self.name is not None:
            result += '|' + self.name
        result += ':'

        instruction = self.firstInstruction
        while instruction is not None:
            result += '\n  ' + instruction.fullPrintString()
            instruction = instruction.nextInstruction

        result += '\n'
        return result

    def evaluateInActivationContext(self, context):
        # Nothing is required here
        pass

class HIRInstruction(HIRFunctionLocalValue):
    def __init__(self, type, name = None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.previousInstruction = None
        self.nextInstruction = None

    def isTerminator(self):
        return False

class HIRAllocaInstruction(HIRInstruction):
    def __init__(self, valueType, valueBoxType, referenceType, name=None, sourcePosition=None):
        super().__init__(referenceType, name, sourcePosition)
        self.valueType = valueType
        self.valueBoxType = valueBoxType

    def fullPrintString(self) -> str:
        return '%s := alloca %s' % (str(self), str(self.valueType))

    def evaluateInActivationContext(self, context: HIRFunctionActivationContext):
        valueBox = HIRMutableValueBox(self.valueBoxType, None, self.sourcePosition)
        if self.type.isReferenceType():
            allocaValue = HIRReferenceValue(self.type, valueBox, 0, self.sourcePosition)
        else:
            allocaValue = HIRPointerValue(self.type, valueBox, 0, self.sourcePosition)
        
        context.setCurrentInstructionValue(allocaValue)

class HIRLoadInstruction(HIRInstruction):
    def __init__(self, type, storage, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.storage = storage

    def fullPrintString(self) -> str:
        return '%s := load %s' % (str(self), str(self.storage))

    def evaluateInActivationContext(self, context: HIRFunctionActivationContext):
        storageValue = self.storage.getValueInEvaluationContext(context)
        context.setCurrentInstructionValue(storageValue.loadValue())

class HIRStoreInstruction(HIRInstruction):
    def __init__(self, type, storage, valueToStore, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.storage = storage
        self.valueToStore = valueToStore

    def fullPrintString(self) -> str:
            return 'store %s in %s' % (str(self.valueToStore), str(self.storage))

    def evaluateInActivationContext(self, context: HIRFunctionActivationContext):
        storageValue = self.storage.getValueInEvaluationContext(context)
        valueToStoreValue = self.valueToStore.getValueInEvaluationContext(context)
        storageValue.storeValue(valueToStoreValue)

class HIRBranchInstruction(HIRInstruction):
    def __init__(self, destination: HIRBasicBlock, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.destination = destination

    def isTerminator(self):
        return True

    def fullPrintString(self) -> str:
        return "branch " + str(self.destination)

    def evaluateInActivationContext(self, context):
        context.pc = self.destination.index

class HIRConditionalBranchInstruction(HIRInstruction):
    def __init__(self, condition: HIRValue, trueDestination: HIRBasicBlock, falseDestination: HIRBasicBlock, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.condition = condition
        self.trueDestination = trueDestination
        self.falseDestination = falseDestination
    
    def isTerminator(self):
        return True

    def fullPrintString(self) -> str:
        return "onCondition %s ifTrue: %s ifFalse: %s" % (str(self.condition), str(self.trueDestination), str(self.falseDestination))

    def evaluateInActivationContext(self, context):
        condition = self.condition.getValueInEvaluationContext(context).value
        if condition:
            context.pc = self.trueDestination.index
        else:
            context.pc = self.falseDestination.index

class HIRCallInstruction(HIRInstruction):
    def __init__(self, functional, arguments, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.functional = functional
        self.arguments = arguments

    def fullPrintString(self):
        return "%s := call %s with %s :: %s" % (str(self), str(self.functional), str(self.arguments), str(self.type))

    def evaluateInActivationContext(self, context):
        functional = self.functional.getValueInEvaluationContext(context)
        arguments = list(map(lambda arg: arg.getValueInEvaluationContext(context), self.arguments))
        result = functional.evaluateWithArgumentsAndResultType(arguments, self.type)
        context.setCurrentInstructionValue(result)

    def canSimplify(self):
        if not self.functional.isCompileTimeFunction():
            return False

        return True

    def simplifyWithBuilder(self, builder):
        if not self.canSimplify():
            return self
        
        simplified = self.functional.evaluateWithArgumentsAndResultType(self.arguments, self.type)
        return simplified

class HIRPhiInstrucion(HIRInstruction):
    def __init__(self, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)

    def fullPrintString(self):
        return "%s := phi %s" % (str(self), str(self.type))

    def evaluateInActivationContext(self, context):
        # Nothing is required here
        pass

class HIRPhiSourceInstruction(HIRInstruction):
    def __init__(self, targetPhi: HIRPhiInstrucion, sourceValue: HIRValue, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.targetPhi = targetPhi
        self.sourceValue = sourceValue

    def fullPrintString(self):
        return "phi: %s source: %s" % (str(self.targetPhi), str(self.sourceValue))

    def evaluateInActivationContext(self, context):
        sourceEvaluatedValue = self.sourceValue.getValueInEvaluationContext(context)
        context.atPCSetValue(self.targetPhi.index, sourceEvaluatedValue)

class HIRReturnInstruction(HIRInstruction):
    def __init__(self, valueToReturn, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.valueToReturn = valueToReturn

    def isTerminator(self):
        return True

    def fullPrintString(self) -> str:
        return "return " + str(self.valueToReturn)

    def evaluateInActivationContext(self, context):
        returnValue = self.valueToReturn.getValueInEvaluationContext(context)
        context.returnValue = returnValue


class HIRUnreachable(HIRInstruction):
    def __init__(self, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)

    def isTerminator(self):
        return True

    def fullPrintString(self) -> str:
        return "unreachable"

class HIRPackage(HIRValue):
    def __init__(self, name: str):
        self.name = name
        self.usedPackages = []
        self.children = []
        self.publicSymbolTable = {}
        self.coreTypes = None

    def addCoreTypes(self, coreTypes):
        self.coreTypes = coreTypes
        for type in coreTypes.coreTypeList:
            typeName = type.getName()
            self.addSymbolWithBinding(typeName, type)

        for value, name in coreTypes.coreValueList:
            self.addSymbolWithBinding(name, value)

        for macro in coreTypes.corePrimitiveMacros:
            self.addSymbolWithBinding(macro.name, macro)

    def addSymbolWithBinding(self, symbol: str, binding: HIRValue):
        self.children.append(binding)
        self.publicSymbolTable[symbol] = binding

    def getType(self):
        return self.coreTypes.packageType

    def lookupSymbolRecursivelyOrNone(self, symbol: str):
        if symbol in self.publicSymbolTable:
            return self.publicSymbolTable[symbol]
        
        for usedPackage in self.usedPackages:
            usedSymbol = usedPackage.lookupSymbolRecursivelyOrNone(symbol)
            if usedSymbol is not None:
                return usedSymbol
                    
        return None

    def usePackage(self, package):
        if package not in self.usedPackages:
            self.usedPackages.append(package)

class HIREnvironment:
    def __init__(self):
        pass

class HIREmptyEnvironment(HIREnvironment):
    def lookSymbolRecursively(self, symbol):
        return None

class HIRPackageEnvironment(HIREnvironment):
    def __init__(self, package, parent):
        super().__init__()
        self.package = package
        self.parent = parent

    def lookSymbolRecursively(self, symbol):
        packageSymbolBinding = self.package.lookupSymbolRecursivelyOrNone(symbol)
        if packageSymbolBinding is not None:
            return packageSymbolBinding

        return self.parent.lookSymbolRecursively(symbol)

class HIRLexicalEnvironment(HIREnvironment):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.symbolTable = {}

    def setSymbolBinding(self, symbol, binding):
        self.symbolTable[symbol] = binding
    
    def setNewSymbolBinding(self, symbol, binding, sourcePosition):
        if symbol in self.symbolTable:
            raise RuntimeError(str(sourcePosition) +  " a binding for symbol '" + symbol + "'already exists.")
        self.setSymbolBinding(symbol, binding)

    def lookSymbolRecursively(self, symbol):
        if symbol in self.symbolTable:
            return self.symbolTable[symbol]
        return self.parent.lookSymbolRecursively(symbol)

class HIRDependentFunctionTypeAnalysisEnvironment(HIRLexicalEnvironment):
    def __init__(self, parent):
        super().__init__(parent)

    def lookSymbolRecursively(self, symbol):
        if symbol in self.symbolTable:
            binding = self.symbolTable[symbol]
            binding.markDependentUsage()
            return binding
        return self.parent.lookSymbolRecursively(symbol)

class HIRCoreTypes:
    def __init__(self):
        self.pointerSize = 8
        self.pointerAlignment = 8

        self.integerType   = HIRNominalType('Integer', self, None);
        self.characterType = HIRNominalType('Character', self, None);
        self.floatType     = HIRNominalType('Float', self, None);
        self.booleanType   = HIRNominalType('Boolean', self, None);
        self.stringType    = HIRNominalType('String', self, None);
        self.symbolType    = HIRNominalType('Symbol', self, None);
        self.undefinedType = HIRNominalType('Undefined', self, None);
        
        self.dynamicType = HIRDynamicType('Dynamic', self, None)
        self.voidType      = HIRVoidType('Void', self, None);

        self.packageType = HIRNominalType('Package', self, None)
        self.parseTreeNodeType = HIRNominalType('ParseTreeNode', self, None)
        self.primitiveMacroType = HIRNominalType('PrimitiveMacro', self, None)

        self.prop = HIRUniverseType('Prop', self, 0);
        self.type = HIRUniverseType('Type', self, 1);
        self.universeLevels = {
            0: self.prop,
            1: self.type,
        }

        self.voidValue = HIRConstantLiteralVoidValue(self.voidType, None)
        self.falseValue = HIRConstantLiteralBooleanValue(False, self.booleanType, None)
        self.trueValue = HIRConstantLiteralBooleanValue(True, self.booleanType, None)
        self.nilValue = HIRConstantLiteralNilValue(self.undefinedType, None)

        self.coreTypeList = [
            self.integerType,
            self.characterType,
            self.floatType,
            self.booleanType,
            self.stringType,
            self.symbolType,
            self.undefinedType,

            self.dynamicType,
            self.voidType,

            self.packageType,
            self.parseTreeNodeType,
            self.primitiveMacroType,

            self.prop,
            self.type,
        ]
        self.coreValueList = [
            (self.voidValue,  'void'),
            (self.falseValue, 'false'),
            (self.trueValue,  'true'),
            (self.nilValue,   'nil'),
        ]
        
        self.createCorePrimitiveMacros()
        self.createCorePrimitiveFunctions()

    def createCorePrimitiveMacros(self):
        def letWith(macroContext: HIRMacroContext, nameExpression: ParseTreeNode, initialValue: ParseTreeNode):
            return ParseTreeVariableDefinitionNode(macroContext.sourcePosition, nameExpression, None, initialValue, False)
        def letMutableWith(macroContext: HIRMacroContext, nameExpression: ParseTreeNode, initialValue: ParseTreeNode):
            return ParseTreeVariableDefinitionNode(macroContext.sourcePosition, nameExpression, None, initialValue, True)

        def ifThenElse(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, trueExpression: ParseTreeNode, falseExpression: ParseTreeNode):
            return ParseTreeIfSelectionNode(macroContext.sourcePosition, conditionExpression, trueExpression, falseExpression)
        def ifThen(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, trueExpression: ParseTreeNode):
            return ParseTreeIfSelectionNode(macroContext.sourcePosition, conditionExpression, trueExpression, None)

        def whileDoContinueWith(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, bodyExpression: ParseTreeNode, continueExpression: ParseTreeNode):
            return ParseTreeWhileDoNode(macroContext.sourcePosition, conditionExpression, bodyExpression, continueExpression)
        def whileDo(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, bodyExpression: ParseTreeNode):
            return ParseTreeWhileDoNode(macroContext.sourcePosition, conditionExpression, bodyExpression, None)

        def returnMacro(macroContext: HIRMacroContext, valueExpression: ParseTreeNode):
            return ParseTreeReturnNode(macroContext.sourcePosition, valueExpression)

        self.corePrimitiveMacros = [
            HIRPrimitiveMacro('let:with:', self.primitiveMacroType, letWith, None),
            HIRPrimitiveMacro('let:mutableWith:', self.primitiveMacroType, letMutableWith, None),

            HIRPrimitiveMacro('if:then:else:', self.primitiveMacroType, ifThenElse, None),
            HIRPrimitiveMacro('if:then:', self.primitiveMacroType, ifThen, None),

            HIRPrimitiveMacro('while:do:continueWith:', self.primitiveMacroType, whileDoContinueWith, None),
            HIRPrimitiveMacro('while:do:', self.primitiveMacroType, whileDo, None),

            HIRPrimitiveMacro('return:', self.primitiveMacroType, returnMacro, None),
        ]

    def createCorePrimitiveFunctions(self):
        self.createIntegerPrimitiveFunctions()
        self.createFloatPrimitiveFunctions()

    def getBooleanConstant(self, value):
        if value:
            return self.trueValue
        else:
            return self.falseValue

    def createIntegerPrimitiveFunctions(self):
        def integerNegated(operand, resultType):
            assert operand.isIntegerConstant()
            return HIRConstantLiteralIntegerValue(-operand.value, resultType, None)
        def integerBitInvert(operand, resultType):
            assert operand.isIntegerConstant()
            return HIRConstantLiteralIntegerValue(1 - operand.value, resultType, None)
        
        def integerAdd(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return HIRConstantLiteralIntegerValue(leftOperand.value + rightOperand.value, resultType, None)
        def integerSubtract(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return HIRConstantLiteralIntegerValue(leftOperand.value - rightOperand.value, resultType, None)
        def integerMultiply(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return HIRConstantLiteralIntegerValue(leftOperand.value * rightOperand.value, resultType, None)
        def integerDivide(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return HIRConstantLiteralIntegerValue(leftOperand.value // rightOperand.value, resultType, None)

        def integerEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return self.getBooleanConstant(leftOperand.value == rightOperand.value)
        def integerNotEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return self.getBooleanConstant(leftOperand.value != rightOperand.value)

        def integerLessThan(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return self.getBooleanConstant(leftOperand.value < rightOperand.value)
        def integerLessOrEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return self.getBooleanConstant(leftOperand.value <= rightOperand.value)
        def integerGreaterThan(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return self.getBooleanConstant(leftOperand.value > rightOperand.value)
        def integerGreaterOrEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isIntegerConstant()
            assert rightOperand.isIntegerConstant()
            return self.getBooleanConstant(leftOperand.value >= rightOperand.value)

        self.integerType.withSelectorAddMethod('negated', HIRPrimitiveFunction('Integer::negated', self.getOrCreateSimpleFunctionType((self.integerType,), self.integerType), integerNegated, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('bitInvert', HIRPrimitiveFunction('Integer::bitInvert', self.getOrCreateSimpleFunctionType((self.integerType,), self.integerType), integerBitInvert, None, isPure = True, isCompileTime = True))

        self.integerType.withSelectorAddMethod('+',  HIRPrimitiveFunction('Integer::+', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.integerType), integerAdd, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('-',  HIRPrimitiveFunction('Integer::-', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.integerType), integerSubtract, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('*',  HIRPrimitiveFunction('Integer::*', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.integerType), integerMultiply, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('//', HIRPrimitiveFunction('Integer:://', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.integerType), integerDivide, None, isPure = True, isCompileTime = True))

        self.integerType.withSelectorAddMethod('=',  HIRPrimitiveFunction('Integer::=',  self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.booleanType), integerEquals, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('~=', HIRPrimitiveFunction('Integer::~=', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.booleanType), integerNotEquals, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('<',  HIRPrimitiveFunction('Integer::<',  self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.booleanType), integerLessThan, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('<=', HIRPrimitiveFunction('Integer::<=', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.booleanType), integerLessOrEquals, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('>',  HIRPrimitiveFunction('Integer::>',  self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.booleanType), integerGreaterThan, None, isPure = True, isCompileTime = True))
        self.integerType.withSelectorAddMethod('>=', HIRPrimitiveFunction('Integer::>=', self.getOrCreateSimpleFunctionType((self.integerType, self.integerType), self.booleanType), integerGreaterOrEquals, None, isPure = True, isCompileTime = True))

    def createFloatPrimitiveFunctions(self):
        def floatNegated(operand, resultType):
            assert operand.isFloatConstant()
            return HIRConstantLiteralFloatValue(-operand.value, resultType, None)
        def floatSqrt(operand, resultType):
            assert operand.isFloatConstant()
            return HIRConstantLiteralFloatValue(math.sqrt(operand.value), resultType, None)
        
        def floatAdd(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return HIRConstantLiteralFloatValue(leftOperand.value + rightOperand.value, resultType, None)
        def floatSubtract(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return HIRConstantLiteralFloatValue(leftOperand.value - rightOperand.value, resultType, None)
        def floatMultiply(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return HIRConstantLiteralFloatValue(leftOperand.value * rightOperand.value, resultType, None)
        def floatDivide(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return HIRConstantLiteralFloatValue(leftOperand.value // rightOperand.value, resultType, None)

        def floatEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return self.getBooleanConstant(leftOperand.value == rightOperand.value)
        def floatNotEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return self.getBooleanConstant(leftOperand.value != rightOperand.value)

        def floatLessThan(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return self.getBooleanConstant(leftOperand.value < rightOperand.value)
        def floatLessOrEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return self.getBooleanConstant(leftOperand.value <= rightOperand.value)
        def floatGreaterThan(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return self.getBooleanConstant(leftOperand.value > rightOperand.value)
        def floatGreaterOrEquals(leftOperand, rightOperand, resultType):
            assert leftOperand.isFloatConstant()
            assert rightOperand.isFloatConstant()
            return self.getBooleanConstant(leftOperand.value >= rightOperand.value)

        self.floatType.withSelectorAddMethod('negated', HIRPrimitiveFunction('Float::negated', self.getOrCreateSimpleFunctionType((self.floatType,), self.floatType), floatNegated, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('sqrt',    HIRPrimitiveFunction('Float::sqrt', self.getOrCreateSimpleFunctionType((self.floatType,), self.floatType),    floatSqrt, None, isPure = True, isCompileTime = True))

        self.floatType.withSelectorAddMethod('+', HIRPrimitiveFunction('Float::+', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.floatType), floatAdd, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('-', HIRPrimitiveFunction('Float::-', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.floatType), floatSubtract, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('*', HIRPrimitiveFunction('Float::*', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.floatType), floatMultiply, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('/', HIRPrimitiveFunction('Float::/', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.floatType), floatDivide, None, isPure = True, isCompileTime = True))

        self.floatType.withSelectorAddMethod('=',  HIRPrimitiveFunction('Float::=',  self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.booleanType), floatEquals, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('~=', HIRPrimitiveFunction('Float::~=', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.booleanType), floatNotEquals, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('<',  HIRPrimitiveFunction('Float::<',  self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.booleanType), floatLessThan, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('<=', HIRPrimitiveFunction('Float::<=', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.booleanType), floatLessOrEquals, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('>',  HIRPrimitiveFunction('Float::>',  self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.booleanType), floatGreaterThan, None, isPure = True, isCompileTime = True))
        self.floatType.withSelectorAddMethod('>=', HIRPrimitiveFunction('Float::>=', self.getOrCreateSimpleFunctionType((self.floatType, self.floatType), self.booleanType), floatGreaterOrEquals, None, isPure = True, isCompileTime = True))

    def getOrCreateSimpleFunctionType(self, argumentTypes, resultType):
        return HIRSimpleFunctionType(argumentTypes, resultType, self, None)
    
    def getUniverseAtLevel(self, level):
        if level in self.universeLevels:
            return self.universeLevels[level]
        newLevel = HIRUniverseType(None, self, level)
        self.universeLevels[level] = newLevel
        return newLevel

class HIRContext:
    def __init__(self):
        self.coreTypes = HIRCoreTypes()
        self.corePackage = HIRPackage('CoreLib')
        self.corePackage.addCoreTypes(self.coreTypes)
        self.currentPackage = self.corePackage

    def createTopLevelEnvironment(self, sourceCode: SourceCode):
        lexicalEnvironment = HIRLexicalEnvironment(HIRPackageEnvironment(self.currentPackage, HIREmptyEnvironment()))
        if sourceCode.directory is not None:
            lexicalEnvironment.setSymbolBinding('__FileDir__', HIRConstantLiteralStringValue(sourceCode.directory, self.coreTypes.stringType, None))
        if sourceCode.name is not None:
            lexicalEnvironment.setSymbolBinding('__FileName__', HIRConstantLiteralStringValue(sourceCode.name, self.coreTypes.stringType, None))
        return lexicalEnvironment
    
    def createTopLevelEvaluationContext(self, sourceCode: SourceCode):
        return HIREvaluationContext(self, self.createTopLevelEnvironment(sourceCode))

    def createTopLevelFunctionBuilder(self, sourcePosition: SourcePosition = None):
        dependentFunctionType = HIRDependentFunctionType([], self.coreTypes.dynamicType, self.coreTypes, sourcePosition)
        topLevelFunction = HIRFunction(None, dependentFunctionType, sourcePosition)
        topLevelFunction.isTopLevel = True
        topLevelEnvironment = self.createTopLevelEnvironment(sourcePosition.sourceCode)

        # Alloca block
        allocaBlock = HIRBasicBlock("alloca", sourcePosition)
        topLevelFunction.addBasicBlock(allocaBlock)
        allocaBuilder = HIRBuilder(topLevelFunction, self, allocaBlock, topLevelEnvironment)

        # Entry block
        entryBlock = HIRBasicBlock("entry", sourcePosition)
        topLevelFunction.addBasicBlock(entryBlock)
        builder = HIRBuilder(topLevelFunction, self, entryBlock, topLevelEnvironment)
        builder.allocaBuilder = allocaBuilder
        builder.entryBasicBlock = entryBlock

        return builder

    def getOrCreatePointerType(self, baseType):
        return HIRPointerType(baseType, self.coreTypes, None)

    def getOrCreateReferenceType(self, baseType):
        return HIRReferenceType(baseType, self.coreTypes, None)

    def getOrCreateMutableValueBoxType(self, baseType):
        return HIRMutableValueBoxType(baseType, self.coreTypes, None)

class HIREvaluationContext:
    def __init__(self, context: HIRContext, environment: HIRLexicalEnvironment):
        self.context = context
        self.environment = environment

class HIRBuilder:
    def __init__(self, function: HIRFunction, context: HIRContext, basicBlock: HIRBasicBlock, environment: HIRLexicalEnvironment):
        self.function = function
        self.context = context
        self.basicBlock = basicBlock
        self.environment = environment
        self.allocaBuilder = None
        self.entryBasicBlock = None

    def addInstruction(self, instruction):
        self.basicBlock.addInstruction(instruction)

    def copyWithBasicBlock(self, basicBlock):
        result = HIRBuilder(self.function, self.context, basicBlock, self.environment)
        result.allocaBuilder = self.allocaBuilder
        result.entryBasicBlock = self.entryBasicBlock
        return result

    def isLastTerminator(self):
        if self.basicBlock is None or self.basicBlock.lastInstruction is None:
            return False

        return self.basicBlock.lastInstruction.isTerminator()

    def finishBuilding(self):
        if self.allocaBuilder is not None:
            if self.entryBasicBlock is not None:
                self.allocaBuilder.branch(self.entryBasicBlock, None)

    def integerConstant(self, value: int, type: HIRType, sourcePosition: SourcePosition):
        return HIRConstantLiteralIntegerValue(value, type, sourcePosition)

    def characterConstant(self, value: int, type: HIRType, sourcePosition: SourcePosition):
        return HIRConstantLiteralCharacterValue(value, type, sourcePosition)

    def floatConstant(self, value: float, type: HIRType, sourcePosition: SourcePosition):
        return HIRConstantLiteralFloatValue(value, type, sourcePosition)

    def stringConstant(self, value: str, type: HIRType, sourcePosition: SourcePosition):
        return HIRConstantLiteralStringValue(value, type, sourcePosition)

    def symbolConstant(self, value: str, type: HIRType, sourcePosition: SourcePosition):
        return HIRConstantLiteralSymbolValue(value, type, sourcePosition)

    def alloca(self, valueType, referenceType, sourcePosition):
        valueBoxType = self.context.getOrCreateMutableValueBoxType(valueType)
        instruction = HIRAllocaInstruction(valueType, valueBoxType, referenceType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def branch(self, destination, sourcePosition):
        instruction = HIRBranchInstruction(destination, self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def conditionalBranch(self, condition, trueDestination, falseDestination, sourcePosition):
        instruction = HIRConditionalBranchInstruction(condition, trueDestination, falseDestination, self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def call(self, functional, arguments, resultType, sourcePosition):
        instruction = HIRCallInstruction(functional, arguments, resultType, None, sourcePosition)
        simplified = instruction.simplifyWithBuilder(self)
        if instruction == simplified:
            self.addInstruction(instruction)
        return simplified

    def load(self, type, storage, sourcePosition):
        instruction = HIRLoadInstruction(type, storage, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def store(self, storage, valueToStore, sourcePosition):
        instruction = HIRStoreInstruction(self.context.coreTypes.voidType, storage, valueToStore, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def phi(self, type, sourcePosition):
        instruction = HIRPhiInstrucion(type, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def phiSource(self, targetPhi, sourceValue, sourcePosition):
        instruction = HIRPhiSourceInstruction(targetPhi, sourceValue, self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def returnValue(self, valueToReturn, sourcePosition):
        instruction = HIRReturnInstruction(valueToReturn, self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def returnVoid(self, sourcePosition):
        return self.returnValue(self.context.coreTypes.voidValue, sourcePosition)

    def unreachable(self, valueToReturn, sourcePosition):
        instruction = HIRUnreachable(self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
