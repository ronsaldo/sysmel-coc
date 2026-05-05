from parsetree import *
from abc import ABC, abstractmethod
import math

def alignedTo(offset, alignment):
    return (offset + alignment - 1) & (-alignment)

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
        return selfType.analyzeAndEvaluateMessageSendNodeOnType(evaluator, node, receiver)

    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        selfType = self.getType()
        return selfType.analyzeAndBuildMessageSendNodeOnType(buildPass, node, receiver)
    
    def performWithArguments(self, selector, arguments, sourcePosition):
        # FIXME: Remove this hack
        if selector == 'yourself':
            return self
        
        selfType = self.getType()

        foundMethod = selfType.lookupSelector(selector)
        if foundMethod is None:
            raise RuntimeError("%s: %s [%s] doesNotUnderstand %s" % (str(sourcePosition), str(self), str(selfType), selector))
        return foundMethod.evaluateWithArgumentsAt([self] + arguments, sourcePosition)

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
    
    def isDictionaryType(self):
        return False

    def isEnumType(self):
        return False

    def isBehaviorType(self):
        return False

    def isClassType(self):
        return False

    def isMetaclassType(self):
        return False

    def isStructType(self):
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

    def isControlFlowEscapeType(self):
        return False

    def isNilConstant(self):
        return False

    def isParseTreeConstant(self):
        return False
    
    def isAssociationConstant(self):
        return False

    def isDictionaryConstant(self):
        return False

    def isEnumConstant(self):
        return False

    def isObjectValue(self):
        return False

    def isStructValue(self):
        return False

    def isTupleConstant(self):
        return False
    
    def isFunctionLocalValue(self):
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
        raise RuntimeError(str(node.sourcePosition) +  ": cannot analyze and evaluate non-functional value "+ str(self))

    def analyzeAndEvaluateMessageSendNodeOnType(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        selector = evaluator.visitSymbolNode(node.selector)

        # FIXME: remove this hack.
        if selector == 'yourself':
            return receiver

        foundMethod = self.lookupSelector(selector)
        if foundMethod is None:
            raise RuntimeError("%s: type '%s' does not have method with selector #%s." % (str(node.sourcePosition), str(self), selector))
        return foundMethod.analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)
    
    def analyzeAndBuildMessageSendNodeOnType(self, buildPass, node: ParseTreeMessageSendNode, receiver):
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

    def lookupField(self, selector):
        return None

    def lookupSelector(self, selector):
        return None
    
    def asArrowArguments(self):
        return (self,)
    
    def getValueAlignment(self):
        return self.coreTypes.pointerAlignment

    def getValueSize(self):
        return self.coreTypes.pointerSize

class PendingDefinitionBody:
    def __init__(self, evaluationContext, definitionBody):
        self.evaluationContext = evaluationContext
        self.definitionBody = definitionBody

    def evaluateForOwner(self, owner):
        from analysisAndEvaluation import AnalysisAndEvaluationPass
        bodyContext = self.evaluationContext.clone()
        bodyContext.environment = HIRLexicalEnvironment(HIROwnerEnvironment(self.evaluationContext.environment, owner))
        return AnalysisAndEvaluationPass(bodyContext).visitDecayedNode(self.definitionBody)

class HIRNominalType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name
        self.methodDictionary = {}
        self.defaultValue = None
        self.pendingDefinitionBodies = []

    def addPendingDefinitionBody(self, evaluationContext, definitionBody):
        self.pendingDefinitionBodies.append(PendingDefinitionBody(evaluationContext, definitionBody))

    def ensureAnalysis(self):
        while len(self.pendingDefinitionBodies) != 0:
            bodiesToAnalyze = self.pendingDefinitionBodies
            self.pendingDefinitionBodies = []
            for body in bodiesToAnalyze:
                body.evaluateForOwner(self)
    
    def getDefaultValue(self):
        if self.defaultValue is None:
            raise RuntimeError('Nominal type %s does not have a default value.' % (self))
        return self.defaultValue

    def getName(self):
        return self.name

    def isNominalType(self):
        return True

    def __repr__(self):
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
    
    def isSatisfiedByValue(self, value):
        return True

    def analyzeAndBuildMessageSendNodeOnType(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        selector = buildPass.evaluateSymbolNode(node.selector)

        # FIXME: remove this hack.
        if selector == 'yourself':
            return receiver
        
        arguments = []
        for argumentNode in node.arguments:
            arguments.append(buildPass.visitNodeWithExpectedType(argumentNode, self))

        return buildPass.builder.send(receiver, selector, arguments, self, node.sourcePosition)

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

class HIRControlFlowEscapeType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isControlFlowEscapeType(self):
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

    def analyzeAndEvaluateMessageSendNodeOnType(self, evaluator, node, receiver):
        selector = evaluator.visitSymbolNode(node.selector)
        
        # FIXME: Remove this hack by using a method dictionary
        if selector == '=>':
            arguments = tuple(receiver.asArrowArguments())
            resultType = evaluator.visitNodeExpectingType(node.arguments[0])
            return self.coreTypes.getOrCreateSimpleFunctionType(arguments, resultType, node.sourcePosition)
        
        return super().analyzeAndEvaluateMessageSendNodeOnType(evaluator, node, receiver)

    def analyzeAndBuildMessageSendNodeOnType(self, buildPass, node, receiver):
        selector = buildPass.evaluateSymbolNode(node.selector)
        
        # FIXME: Remove this hack by using a method dictionary
        if selector == '=>':
            arguments = tuple(receiver.asArrowArguments())
            resultType = buildPass.visitNodeExpectingType(node.arguments[0])
            return self.coreTypes.getOrCreateSimpleFunctionType(arguments, resultType, node.sourcePosition)

        return super().analyzeAndBuildMessageSendNodeOnType(buildPass, node, receiver)
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.level == other.level
    
    def __str__(self):
        return self.name

class HIRAssociationType(HIRType):
    def __init__(self, keyType: HIRType, valueType: HIRType, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.keyType = keyType
        self.valueType = valueType

    def isAssociationType(self):
        return True
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.keyType == other.keyType and self.valueType == other.valueType

    def __str__(self):
        return '(%s : %s)' % (self.keyType, self.valueType)

class HIRDictionaryType(HIRType):
    def __init__(self, associationType: HIRAssociationType, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.associationType = associationType

    def isDictionaryType(self):
        return True
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.associationType == other.associationType

    def __str__(self):
        return 'Dictionary(%s : %s)' % (self.associationType.keyType, self.associationType.valueType)

class HIREnumType(HIRType):
    def __init__(self, name, baseType, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.name = name
        self.baseType = baseType
        self.values = []
        self.valueTable = {}

    def addElementAt(self, element, sourcePosition):
        if element.name in self.valueTable:
            raise RuntimeError('%s: enum has duplicated definitions for symbol #"%s".' % (str(sourcePosition), str(element.name)))
        self.values.append(element)
        self.valueTable[element.name] = element

    def isEnumType(self):
        return True
    
    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        selector = buildPass.evaluateSymbolNode(node.selector)
        if selector in self.valueTable:
            return self.valueTable[selector]
        
        if selector == 'value:':
            assert len(node.arguments) == 1
            value = buildPass.visitNodeWithExpectedType(node.arguments[0], self.baseType)
            return buildPass.builder.enumBoxValue(value, self, node.sourcePosition)

        return super().analyzeAndBuildMessageSendNode(buildPass, node, receiver)
    
    def analyzeAndBuildMessageSendNodeOnType(self, buildPass, node, receiver):
        selector = buildPass.evaluateSymbolNode(node.selector)
        if selector == 'value':
            return buildPass.builder.enumUnboxValue(receiver, self.baseType, node.sourcePosition)
        return super().analyzeAndBuildMessageSendNodeOnType(buildPass, node, receiver)
    
    def analyzeAndEvaluateMessageSendNode(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        selector = evaluator.visitSymbolNode(node.selector)
        if selector in self.valueTable:
            return self.valueTable[selector]

        if selector == 'value:' :
            assert len(node.arguments) == 1
            value = evaluator.visitNodeWithExpectedType(node.arguments[0], self.baseType)
            return HIRConstantEnum(None, value, self, node.sourcePosition)
        return super().analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)

    def analyzeAndEvaluateMessageSendNodeOnType(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        selector = evaluator.visitSymbolNode(node.selector)
        if selector == 'value':
            assert receiver.isEnumConstant()
            return receiver.value

        return super().analyzeAndEvaluateMessageSendNodeOnType(evaluator, node, receiver)

    def __str__(self):
        return 'EnumType(%s %s)' % (self.name, str(self.baseType))

class HIRField(HIRValue):
    def __init__(self, name, type, isPublic, coreTypes, sourcePosition):
        super().__init__(sourcePosition)
        self.name = name
        self.type = type
        self.coreTypes = coreTypes
        self.isPublic = isPublic
        self.offset = None
        self.size = 0
        self.index = None
        self.owner = None

    def getType(self):
        return self.coreTypes.fieldType

    def getValidIndex(self):
        if self.index is None:
            self.owner.ensureLayout()
            if self.index is None:
                self.owner.ensureLayout()
                assert False
        assert self.index is not None
        return self.index

    def getValidOffset(self):
        if self.offset is None:
            self.owner.ensureLayout()
        assert self.offset is not None
        return self.offset
    
    def isField(self):
        return True

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        if len(node.arguments) == 0:
            return receiver.loadValueAtIndex(self.index)
        elif len(node.arguments) == 1:
            newValue = evaluator.visitNodeWithExpectedType(node.arguments[0], self.type)
            receiver.storeValueAtIndex(newValue, self.index)
            return newValue

        return super().analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)
    
    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        fieldReferenceType = buildPass.builder.context.getOrCreateReferenceType(self.type)
        if len(node.arguments) == 0:
            fieldReference = buildPass.builder.extractFieldReference(fieldReferenceType, receiver, self, node.sourcePosition)
            return buildPass.builder.load(self.type, fieldReference, node.sourcePosition)
        elif len(node.arguments) == 1:
            fieldValue = buildPass.visitNodeWithExpectedType(node.arguments[0], self.type)
            fieldReference = buildPass.builder.extractFieldReference(fieldReferenceType, receiver, self, node.sourcePosition)
            buildPass.builder.store(fieldReference, fieldValue, node.sourcePosition)
            return fieldReference
        return super().analyzeAndBuildMessageSendNode(buildPass, node, receiver)

    def __str__(self):
        return 'field %s (index: %d offset: %d)' %(str(self.name), self.getValidIndex(), self.getValidOffset())

class HIRBehavior(HIRNominalType):
    def __init__(self, name, coreTypes, sourcePosition=None):
        super().__init__(name, coreTypes, sourcePosition)
        self.type = None
        self.superclass = None
        self.fields = []
        self.fieldMap = {}
        self.allFields = []
        self.publicFields = {}
        self.instanceSize = None
        self.instanceAlignment = None
        self.totalFieldCount = None

    def isBehaviorType(self):
        return True

    def getSupertype(self):
        return self.superclass

    def lookupField(self, name: str):
        self.ensureAnalysis()
        if name in self.fieldMap:
            return self.fieldMap[name]
        if self.superclass is not None:
            return self.superclass.lookupField(name)
        return None

    def lookupSelector(self, selector: str):
        self.ensureAnalysis()
        if selector in self.methodDictionary:
            return self.methodDictionary[selector]
        if selector in self.publicFields:
            return self.publicFields[selector]
        if self.superclass is not None:
            return self.superclass.lookupSelector(selector)
        return None

    def addField(self, field):
        self.fields.append(field)
        self.invalidateLayout()
        field.owner = self

        if field.name is not None:
            self.fieldMap[field.name] = field

        if field.isPublic and field.name is not None:
            self.publicFields[field.name] = field # Getter
            self.publicFields[field.name + ':'] = field #Setter

    def invalidateLayout(self):
        self.instanceSize = None
        self.instanceAlignment = None

    def ensureLayout(self):
        self.ensureAnalysis()
        if self.instanceSize is not None:
            return
        
        self.instanceSize = 0
        self.instanceAlignment = 1
        self.totalFieldCount = 0
        self.allFields = self.fields

        if self.superclass is not None:
            self.superclass.ensureLayout()
            self.instanceSize = self.superclass.instanceSize
            self.instanceAlignment = self.superclass.instanceAlignment
            self.totalFieldCount = self.superclass.totalFieldCount
            self.allFields = self.superclass.allFields + self.fields

        for field in self.fields:
            field.index = self.totalFieldCount
            fieldAlignment = field.type.getValueAlignment()
            fieldSize = field.type.getValueSize()
            
            self.instanceSize = alignedTo(self.instanceSize, fieldAlignment)
            field.offset = self.instanceSize
            self.instanceSize += fieldSize

            self.instanceAlignment = max(self.instanceAlignment, fieldAlignment)
            self.totalFieldCount += 1

    def getType(self):
        return self.type

    def getInstanceSize(self):
        self.ensureLayout()
        return self.instanceSize

    def getInstanceAlignment(self):
        self.ensureLayout()
        return self.instanceAlignment
    
class HIRClass(HIRBehavior):
    def __init__(self, name, metaclass, coreTypes, sourcePosition=None):
        super().__init__(name, coreTypes, sourcePosition)
        self.type = metaclass

    def isClassType(self):
        return True

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        self.ensureLayout()
        if len(node.arguments) > len(self.allFields):
            raise RuntimeError("%s: class construction can have at most %d arguments." %(str(node.sourcePosition), len(self.fields)))

        objectFields = list(map(lambda f: f.type.getDefaultValue(), self.allFields))
        objectValue = buildPass.builder.makeObject(self, objectFields, node.sourcePosition)
        for i in range(len(node.arguments)):
            element = buildPass.visitNodeWithExpectedType(node.arguments[i], self.allFields[i].type)
            buildPass.builder.setAggregateField(objectValue, element, self.allFields[i], node.sourcePosition)

        initializeMethod = self.lookupSelector("initialize")
        if initializeMethod is not None:
            buildPass.builder.call(initializeMethod.analyzeAndBuild(buildPass), [objectValue], buildPass.builder.coreTypes.voidType, node.sourcePosition)

        return objectValue
    
    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        self.ensureLayout()
        if len(node.arguments) > len(self.allFields):
            raise RuntimeError("%s: class construction can have at most %d arguments." %(str(node.sourcePosition), len(self.fields)))

        objectFields = list(map(lambda f: f.type.getDefaultValue(), self.allFields))
        for i in range(len(node.arguments)):
            element = evaluationPass.visitNodeWithExpectedType(node.arguments[i], self.fields[i].type)
            objectFields[i] = element

        objectValue = HIRObjectValue(self, objectFields, node.sourcePosition)
        if self.lookupSelector('initialize'):
            objectValue.performWithArguments('initialize', [], node.sourcePosition)
        return objectValue
    
    def __str__(self):
        if self.name is None:
            return 'an anonymous class'
        return self.name

class HIRMetaclass(HIRBehavior):
    def __init__(self, coreTypes, sourcePosition=None):
        super().__init__(None, coreTypes, sourcePosition)
        self.thisClass = None

    def isMetaclassType(self):
        return True

    def __str__(self):
        return str(self.thisClass) + " class"

class HIRStructType(HIRNominalType):
    def __init__(self, name, coreTypes, sourcePosition):
        super().__init__(name, coreTypes, sourcePosition)
        self.fields = []
        self.fieldMap = {}
        self.publicFields = {}
        self.valueSize = None
        self.valueAlignment = None

    def isStructType(self):
        return True

    def invalidateLayout(self):
        self.valueSize = None
        self.valueAlignment = None

    def lookupSelector(self, selector):
        self.ensureAnalysis()
        if selector in self.methodDictionary:
            return self.methodDictionary[selector]
        if selector in self.publicFields:
            return self.publicFields[selector]
        return None

    def addField(self, field):
        self.fields.append(field)
        self.invalidateLayout()
        field.owner = self

        if field.name is not None:
            self.fieldMap[field.name] = field

        if field.isPublic and field.name is not None:
            self.publicFields[field.name] = field # Getter
            self.publicFields[field.name + ':'] = field #Setter

    def lookupField(self, selector):
        if selector in self.fieldMap:
            return self.fieldMap[selector]
        return None

    def getValueSize(self):
        self.ensureLayout()
        return self.valueSize

    def getValueAlignment(self):
        self.ensureLayout()
        return self.valueAlignment

    def ensureLayout(self):
        if self.valueSize is not None:
            return
        self.ensureAnalysis()
        self.valueSize = 0
        self.valueAlignment = 1
        
        fieldCount = 0
        for field in self.fields:
            field.index = fieldCount
            fieldAlignment = field.type.getValueAlignment()
            fieldSize = field.type.getValueSize()
            
            self.valueSize = alignedTo(self.valueSize, fieldAlignment)
            field.offset = self.valueSize
            self.valueSize += fieldSize

            self.valueAlignment = max(self.valueAlignment, fieldAlignment)
            fieldCount += 1

        self.valueSize = alignedTo(self.valueSize, self.valueAlignment)

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        self.ensureLayout()
        if len(node.arguments) > len(self.fields):
            raise RuntimeError("%s: struct construction can have at most %d arguments." %(str(node.sourcePosition), len(self.fields)))

        structElements = list(map(lambda f: f.type.getDefaultValue(), self.fields))
        structValue = buildPass.builder.makeStruct(self, structElements, node.sourcePosition)
        for i in range(len(node.arguments)):
            element = buildPass.visitNodeWithExpectedType(node.arguments[i], self.fields[i].type)
            buildPass.builder.setAggregateField(structValue, element, self.fields[i], node.sourcePosition)

        return structValue
    
    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        self.ensureLayout()
        if len(node.arguments) > len(self.fields):
            raise RuntimeError("%s: struct construction can have at most %d arguments." %(str(node.sourcePosition), len(self.fields)))

        structElements = list(map(lambda f: f.type.getDefaultValue(), self.fields))
        for i in range(len(node.arguments)):
            element = evaluationPass.visitNodeWithExpectedType(node.arguments[i], self.fields[i].type)
            structElements[i] = element

        return HIRStructValue(self, structElements, node.sourcePosition)

    def __str__(self):
        return self.name

class HIRTupleType(HIRType):
    def __init__(self, elements: list[HIRType], coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.elements = elements

    def isTupleType(self):
        return True

    def asArrowArguments(self):
        return self.elements

    def __str__(self):
        result = '('
        for element in self.elements:
            if result != '(':
                result += ', '
            result += str(element)
        result += ')'
        return result

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.elements == other.elements
    
class HIRDerivedType(HIRType):
    def __init__(self, baseType, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.baseType = baseType

    def isDerivedType(self):
        return True

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.baseType == other.baseType

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

    def lookupSelector(self, selector):
        return self.baseType.lookupSelector(selector)

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
    
    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        typecheckArguments, resultType = self.analyzeBuildAndTypecheckArguments(buildPass, node.arguments, node.sourcePosition)
        return buildPass.builder.call(functional, typecheckArguments, resultType, node.sourcePosition)
    
    def evaluateAndTypecheckArguments(self, evaluator, arguments, sourcePosition):
        if len(arguments) != len(self.argumentTypes):
            raise RuntimeError("%s: expected %d arguments instead of %d." % (str(sourcePosition), len(self.argumentTypes), len(arguments)))
        
        typecheckedArguments = []
        for i in range(len(arguments)):
            typecheckedArgument = evaluator.visitNodeWithExpectedType(arguments[i], self.argumentTypes[i])
            typecheckedArguments.append(typecheckedArgument)

        return typecheckedArguments, self.resultType

    def typecheckArguments(self, arguments, sourcePosition):
        if len(arguments) != len(self.argumentTypes):
            raise RuntimeError("%s: expected %d arguments instead of %d." % (str(sourcePosition), len(self.argumentTypes), len(arguments)))
        
        typecheckedArguments = []
        for i in range(len(arguments)):
            argument = arguments[i]
            expectedType = self.argumentTypes[i]
            if not expectedType.isSatisfiedByValue(argument):
                raise RuntimeError("%s: argument of type %s instead of %s." % (str(sourcePosition), len(expectedType), len(argument.getType())))
            typecheckedArguments.append(argument)

        return typecheckedArguments, self.resultType
    
    def analyzeBuildAndTypecheckArguments(self, buildPass, arguments, sourcePosition):
        if len(arguments) != len(self.argumentTypes):
            raise RuntimeError("%s: expected %d arguments instead of %d." % (str(sourcePosition), len(self.argumentTypes), len(arguments)))
        
        typecheckedArguments = []
        for i in range(len(arguments)):
            typecheckedArgument = buildPass.visitNodeWithExpectedType(arguments[i], self.argumentTypes[i])
            typecheckedArguments.append(typecheckedArgument)

        return typecheckedArguments, self.resultType

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.argumentTypes == other.argumentTypes and self.resultType == other.resultType

    def __str__(self):
        result = '('
        for argumentType in self.argumentTypes:
            if result != '(':
                result += ', '
            result += str(argumentType)

        result += ') => '
        result += str(self.resultType)
        return result

class HIRDependentFunctionType(HIRType):
    def __init__(self, captures, arguments, resultType: HIRValue, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.captures = captures
        self.arguments = arguments
        self.resultType = resultType

    def copyWithImplicitArgument(self, implicitArgument):
        return HIRDependentFunctionType(self.captures, [implicitArgument] + self.arguments, self.resultType, self.coreTypes, self.sourcePosition)

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
        
        return HIRSimpleFunctionType(tuple(argumentTypes), self.resultType, self.coreTypes, self.sourcePosition)
    
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

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return 'integer(%d)' % self.value

    def isIntegerConstant(self):
        return True
    
    def plusOne(self):
        return HIRConstantLiteralIntegerValue(self.value + 1, self.type, self.sourcePosition)

class HIRConstantLiteralFloatValue(HIRConstantLiteralValue):
    def __init__(self, value: float, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def __repr__(self):
        return 'float(%f)' % self.value

    def isFloatConstant(self):
        return True

class HIRConstantLiteralBooleanValue(HIRConstantLiteralValue):
    def __init__(self, value: bool, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

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

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def __repr__(self):
        return 'character(%d)' % self.value

    def isCharacterConstant(self):
        return True
    
class HIRConstantLiteralStringValue(HIRConstantLiteralValue):
    def __init__(self, value: str, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def __str__(self):
        return self.value

    def __repr__(self):
        return 'string(%s)' % self.value

    def isStringConstant(self):
        return True
    
class HIRConstantLiteralSymbolValue(HIRConstantLiteralValue):
    def __init__(self, value: str, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def __repr__(self):
        return 'symbol(#"%s")' % self.value
    
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

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def isParseTreeConstant(self):
        return True

    def __str__(self):
        return 'parseTreeConstant(%s)' % str(self.value)

class HIRConstantAssociation(HIRConstant):
    def __init__(self, key, value, type, sourcePosition):
        super().__init__(sourcePosition)
        self.key = key
        self.value = value
        self.type = type

    def getType(self):
        return self.type
    
    def isAssociationConstant(self):
        return True

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.key == other.key and self.value == other.value

    def __str__(self):
        return 'association(%s : %s)' % (str(self.key), str(self.value))

class HIRConstantDictionary(HIRConstant):
    def __init__(self, elements, type, sourcePosition):
        super().__init__(sourcePosition)
        self.elements = elements
        self.type = type

    def getType(self):
        return self.type
    
    def isDictionaryConstant(self):
        return True

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.elements == other.elements

    def __str__(self):
        return 'dictionary(%s)' % (str(self.elements))

class HIRConstantEnum(HIRConstant):
    def __init__(self, name, value, type, sourcePosition):
        super().__init__(sourcePosition)
        self.name = name
        self.value = value
        self.type = type

    def getType(self):
        return self.type

    def isEnumConstant(self):
        return True

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.value == other.value

    def __str__(self):
        return 'enumValue(%s: %s)' % (str(self.name), str(self.value))
    

class HIRConstantTuple(HIRConstant):
    def __init__(self, elements, type, sourcePosition):
        super().__init__(sourcePosition)
        self.elements = elements
        self.type = type

    def getType(self):
        return self.type
    
    def isTupleConstant(self):
        return True

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.elements == other.elements

    def __str__(self):
        return 'tupe(%s)' % (str(self.elements))

class HIRObjectValue(HIRValue):
    def __init__(self, type, fields, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type
        self.fields = fields

    def getType(self):
        return self.type

    def isObjectValue(self):
        return True
    
    def storeValueAtIndex(self, valueToStore, index):
        assert index < len(self.fields)
        self.fields[index] = valueToStore

    def loadValueAtIndex(self, index):
        assert index < len(self.fields)
        return self.fields[index]

class HIRStructValue(HIRValue):
    def __init__(self, type, fields, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type
        self.fields = fields

    def getType(self):
        return self.type

    def isStructValue(self):
        return True
    
    def storeValueAtIndex(self, valueToStore, index):
        assert index < len(self.fields)
        self.fields[index] = valueToStore

    def loadValueAtIndex(self, index):
        assert index < len(self.fields)
        return self.fields[index]
    
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
        self.storage.storeValueAtIndex(valueToStore, self.index)

    def loadValue(self):
        return self.storage.loadValueAtIndex(self.index)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.type == other.type and self.storage == other.storage and self.index == other.index
    
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

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node, receiver):
        macroContext = HIRMacroContext(node.sourcePosition)
        macroArguments = [ParseTreeLiteralValueNode(node.sourcePosition, receiver)] + node.arguments
        expandedMacro = self.primitiveFunction(macroContext, *macroArguments)
        return evaluator.visitNode(expandedMacro)

    def analyzeAndBuildMessageSendNode(self, buildPass, node, receiver):
        macroContext = HIRMacroContext(node.sourcePosition)
        macroArguments = [ParseTreeLiteralValueNode(node.sourcePosition, receiver)] + node.arguments
        expandedMacro = self.primitiveFunction(macroContext, *macroArguments)
        return buildPass.visitNode(expandedMacro)

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
        typecheckedArguments, resultType = self.type.analyzeBuildAndTypecheckArguments(buildPass, node.arguments, node.sourcePosition)
        return buildPass.builder.call(self, typecheckedArguments, resultType, node.sourcePosition)

    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        typecheckedArguments, resultType = self.type.evaluateAndTypecheckArguments(evaluationPass, node.arguments, node.sourcePosition)
        return self.primitiveFunction(*typecheckedArguments, resultType)

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
    
    def evaluateWithArgumentsAt(self, arguments, sourcePosition):
        typecheckedArguments, resultType = self.type.typecheckArguments(arguments, sourcePosition)
        return self.evaluateWithArgumentsAndResultType(typecheckedArguments, resultType)
    
    def __str__(self):
        return 'primitiveFunction(%s)' % self.name

class HIRFunction(HIRConstant):
    def __init__(self, name: str, dependentFunctionType: HIRDependentFunctionType, sourcePosition):
        super().__init__(sourcePosition)
        self.name = name
        self.dependentFunctionType = dependentFunctionType
        self.simplifiedType = dependentFunctionType.asSimplifiedType()
        self.captures = []
        self.firstBasicBlock = None
        self.lastBasicBlock = None
        self.isTopLevel = False
        self.definitionBody: ParseTreeFunctionNode = None
        self.definitionContext: HIRContext = None
        self.definitionEnvironment: HIRContext = None
        self.enumeratedInstructions = None

    def getType(self):
        return self.simplifiedType
    
    def addBasicBlock(self, basicBlock):
        if self.lastBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            basicBlock.previousBlock = self.lastBasicBlock
            self.lastBasicBlock.nextBlock = basicBlock
            self.lastBasicBlock = basicBlock

    def ensureAnalysis(self):
        from analysisAndBuild import AnalysisAndBuildPass

        if self.firstBasicBlock is not None:
            return
        
        # Function environment arguments
        selfArgument = None
        if len(self.dependentFunctionType.arguments) >= 1:
            firstArgument = self.dependentFunctionType.arguments[0]
            if firstArgument.isSelf:
                selfArgument = firstArgument

        functionEnvironment = HIRFunctionAnalysisEnvironment(self.definitionEnvironment, self.dependentFunctionType.resultType, selfArgument, self.definitionContext)
        functionEnvironment.addDependentFunctionTypeCaptures(self.dependentFunctionType.captures)
        for argument in self.dependentFunctionType.arguments:
            if argument.name is not None:
                functionEnvironment.setNewSymbolBinding(argument.name, argument, argument.sourcePosition)

        # Body environment
        bodyEnvironment = HIRLexicalEnvironment(functionEnvironment)

        # Alloca block
        allocaBlock = HIRBasicBlock("alloca", self.sourcePosition)
        self.addBasicBlock(allocaBlock)
        allocaBuilder = HIRBuilder(self, self.definitionContext, allocaBlock, bodyEnvironment)

        # Entry block
        entryBlock = HIRBasicBlock("entry", self.sourcePosition)
        self.addBasicBlock(entryBlock)
        builder = HIRBuilder(self, self.definitionContext, entryBlock, bodyEnvironment)
        builder.allocaBuilder = allocaBuilder
        builder.entryBasicBlock = entryBlock

        # Build the body.
        result = AnalysisAndBuildPass(builder).visitNodeWithExpectedType(self.definitionBody, self.dependentFunctionType.resultType)
        if not builder.isLastTerminator():
            builder.returnValue(result, self.sourcePosition)

        builder.finishBuilding()
        self.captures = functionEnvironment.captureList

    def enumerateInstruction(self):
        if self.enumeratedInstructions is not None:
            return self.enumeratedInstructions
        
        self.ensureAnalysis()
        
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
        self.ensureAnalysis()
        self.enumerateInstruction()
        result = "HIRFunction "
        if self.name is not None:
            result += self.name
        result += " {\n"

        for argument in self.dependentFunctionType.arguments:
            result += argument.fullPrintString() + '\n'

        for capture in self.captures:
            result += capture.fullPrintString() + '\n'

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
    
    def evaluateWithArgumentsAndResultType(self, arguments, resultType):
        return self.evaluateWithArguments(arguments)
    
    def analyzeAndEvaluateApplicationNode(self, evaluationPass, node: ParseTreeApplicationNode, functional):
        typecheckedArguments, resultType = self.simplifiedType.evaluateAndTypecheckArguments(evaluationPass, node.arguments, node.sourcePosition)
        return self.evaluateWithArguments(typecheckedArguments)
    
    def analyzeAndEvaluateMessageSendNode(self, evaluationPass, node: ParseTreeMessageSendNode, receiver):
        receiverNode = ParseTreeLiteralValueNode(node.sourcePosition, receiver)
        typecheckedArguments, resultType = self.simplifiedType.evaluateAndTypecheckArguments(evaluationPass, [receiverNode] + node.arguments, node.sourcePosition)
        return self.evaluateWithArgumentsAndResultType(typecheckedArguments, resultType)
    
    def __repr__(self):
        return 'HIRFunction(%s)' % self.name

class HIRFunctionClosure(HIRConstant):
    def __init__(self, function: HIRFunction, captureVector: list[HIRValue], sourcePosition):
        super().__init__(sourcePosition)
        self.function = function
        self.captureVector = captureVector
    
    def getType(self):
        return self.function.getType()
    
    def evaluateWithArguments(self, arguments):
        return self.function.evaluateWithArgumentsAndCaptures(arguments, self.captureVector)

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

    def __repr__(self):
        return '%d|%s' %(self.index, str(self.name))

    def getType(self):
        return self.type

    def getValueInEvaluationContext(self, context):
        return context.instructionValues[self.index]
    
    def isFunctionLocalValue(self):
        return True

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
    def __init__(self, sourceValue, type, name = None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.sourceValue = sourceValue

    def fullPrintString(self) -> str:
        return '%d|%s := capture source %s' %(self.index, str(self.name), self.sourceValue)

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

class HIRAssertInstruction(HIRInstruction):
    def __init__(self, condition, errorMessage, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.condition = condition
        self.errorMessage = errorMessage

    def fullPrintString(self) -> str:
        return 'assert %s : %s' % (str(self.condition), str(self.errorMessage))

    def evaluateInActivationContext(self, context: HIRFunctionActivationContext):
        conditionValue = self.condition.getValueInEvaluationContext(context)
        if not conditionValue.value:
            messageValue = self.errorMessage.getValueInEvaluationContext(context)
            raise AssertionError(str(self.sourcePosition) + ": " + messageValue.value)

class HIRRuntimeErrorInstruction(HIRInstruction):
    def __init__(self, errorMessage, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.errorMessage = errorMessage

    def fullPrintString(self) -> str:
        return 'runtimeError %s' % str(self.errorMessage)

    def evaluateInActivationContext(self, context: HIRFunctionActivationContext):
        messageValue = self.errorMessage.getValueInEvaluationContext(context)
        assert messageValue.isStringConstant()
        raise RuntimeError(messageValue.value)

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

        for argument in self.arguments:
            if not argument.isConstantValue():
                return False

        return True

    def simplifyWithBuilder(self, builder):
        if not self.canSimplify():
            return self
        
        simplified = self.functional.evaluateWithArgumentsAndResultType(self.arguments, self.type)
        return simplified

class HIRSendInstruction(HIRInstruction):
    def __init__(self, receiver, selector, arguments, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.receiver = receiver
        self.selector = selector
        self.arguments = arguments

    def fullPrintString(self):
        return "%s := send %s to %s with: %s :: %s" % (str(self), str(self.selector), str(self.receiver), str(self.arguments), str(self.type))

    def evaluateInActivationContext(self, context):
        receiver = self.receiver.getValueInEvaluationContext(context)
        selector = self.selector
        arguments = list(map(lambda arg: arg.getValueInEvaluationContext(context), self.arguments))
        result = receiver.performWithArguments(selector, arguments, self.sourcePosition)
        context.setCurrentInstructionValue(result)

class HIREnumBoxValueInstruction(HIRInstruction):
    def __init__(self, value, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.value = value

    def evaluateInActivationContext(self, context):
        value = self.value.getValueInEvaluationContext(context)
        context.setCurrentInstructionValue(HIRConstantEnum(None, value, self.type, self.sourcePosition))

    def fullPrintString(self):
        return "%s := enumBoxValue %s :: %s" % (str(self), str(self.value), str(self.type))

class HIREnumUnboxValueInstruction(HIRInstruction):
    def __init__(self, enumValue, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.enumValue = enumValue

    def evaluateInActivationContext(self, context):
        enumValue = self.enumValue.getValueInEvaluationContext(context)
        context.setCurrentInstructionValue(enumValue.value)

    def fullPrintString(self):
        return "%s := enumUnboxValue %s :: %s" % (str(self), str(self.enumValue), str(self.type))

class HIRExtractFieldReferenceInstruction(HIRInstruction):
    def __init__(self, type, aggregate, field, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.aggregate = aggregate
        self.field = field

    def evaluateInActivationContext(self, context):
        aggregateValue = self.aggregate.getValueInEvaluationContext(context)

        if self.type.isReferenceType():
            fieldReference = HIRReferenceValue(self.type, aggregateValue, self.field.getValidIndex(), self.sourcePosition)
        else:
            fieldReference = HIRPointerValue(self.type, aggregateValue, self.field.getValidIndex(), self.sourcePosition)

        context.setCurrentInstructionValue(fieldReference)

    def fullPrintString(self):
        return "%s := extractFieldReference %s.%s :: %s" % (str(self), str(self.aggregate), str(self.field), str(self.type))

class HIRSetAggregateFieldInstruction(HIRInstruction):
    def __init__(self, type, aggregate, value, field, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.aggregate = aggregate
        self.value = value
        self.field = field

    def evaluateInActivationContext(self, context):
        aggregateValue = self.aggregate.getValueInEvaluationContext(context)
        valueValue = self.value.getValueInEvaluationContext(context)
        aggregateValue.fields[self.field.getValidIndex()] = valueValue

    def fullPrintString(self):
        return "setAggregateField %s.%s to %s:: %s" % (str(self.aggregate), str(self.field), str(self.value), str(self.type))

class HIRDynamicUnboxInstruction(HIRInstruction):
    def __init__(self, boxedValue, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.boxedValue = boxedValue

    def evaluateInActivationContext(self, context):
        boxedValue = self.boxedValue.getValueInEvaluationContext(context)
        if not self.type.isSatisfiedByValue(boxedValue):
            raise RuntimeError('%s: Expected a value with type %s instead of %s.' %(str(self.sourcePosition), str(self.type), str(boxedValue.getType())))
        context.setCurrentInstructionValue(boxedValue)

    def fullPrintString(self):
        return "%s := dynamicUnbox %s :: %s" % (str(self), str(self.boxedValue), str(self.type))

class HIRMakeAssociationInstruction(HIRInstruction):
    def __init__(self, key: HIRValue, value: HIRValue, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.key = key
        self.value = value

    def evaluateInActivationContext(self, context):
        key = self.key.getValueInEvaluationContext(context)
        value = self.value.getValueInEvaluationContext(context)
        association = HIRConstantAssociation(key, value, self.type, self.sourcePosition)
        context.setCurrentInstructionValue(association)

    def fullPrintString(self):
        return "%s := makeAssociation %s with %s :: %s" % (str(self), str(self.key), str(self.value), str(self.type))

    def simplifyWithBuilder(self, builder):
        if self.key.isConstantValue() and self.value.isConstantValue():
            return HIRConstantAssociation(self.key, self.value, self.type, self.sourcePosition)
        return self

class HIRMakeClosureInstruction(HIRInstruction):
    def __init__(self, function, captureList, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.function = function
        self.captureList = captureList

    def evaluateInActivationContext(self, context):
        functionValue = self.function.getValueInEvaluationContext(context)
        captureVector = list(map(lambda x: x.getValueInEvaluationContext(context), self.captureList))
        closure = HIRFunctionClosure(functionValue, captureVector, self.sourcePosition)
        context.setCurrentInstructionValue(closure)

    def fullPrintString(self):
        return "%s := makeClosure %s, %s :: %s" % (str(self), str(self.function), str(self.captureList), str(self.type))

class HIRMakeObjectInstruction(HIRInstruction):
    def __init__(self, type, defaultElements, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.defaultElements = defaultElements

    def evaluateInActivationContext(self, context):
        context.setCurrentInstructionValue(HIRObjectValue(self.type, list(self.defaultElements), self.sourcePosition))

    def fullPrintString(self):
        return "%s := makeObject %s :: %s" % (str(self), str(self.defaultElements), str(self.type))

class HIRMakeStructInstruction(HIRInstruction):
    def __init__(self, type, defaultElements, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.defaultElements = defaultElements

    def evaluateInActivationContext(self, context):
        context.setCurrentInstructionValue(HIRStructValue(self.type, list(self.defaultElements), self.sourcePosition))

    def fullPrintString(self):
        return "%s := makeStruct %s :: %s" % (str(self), str(self.defaultElements), str(self.type))
    
class HIRMakeTupleInstruction(HIRInstruction):
    def __init__(self, elements: list[HIRValue], type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.elements = elements

    def evaluateInActivationContext(self, context):
        elements = list(map(lambda element: element.getValueInEvaluationContext(context), self.elements))
        result = HIRConstantTuple(elements, self.type, self.sourcePosition)
        context.setCurrentInstructionValue(result)

    def fullPrintString(self):
        return "%s := makeTuple %s :: %s" % (str(self), str(self.elements), str(self.type))

    def canSimplify(self):
        for element in self.elements:
            if not element.isConstantValue():
                return False

        return True

    def simplifyWithBuilder(self, builder):
        if not self.canSimplify():
            return self

        return HIRConstantTuple(self.elements, self.type, self.sourcePosition)

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
        self.pendingAnalysisList = []

    def addCoreTypes(self, coreTypes):
        self.coreTypes = coreTypes
        for type in coreTypes.coreTypeList:
            typeName = type.getName()
            self.addSymbolWithBinding(typeName, type)

        for value, name in coreTypes.coreValueList:
            self.addSymbolWithBinding(name, value)

        for macro in coreTypes.corePrimitiveMacros:
            self.addSymbolWithBinding(macro.name, macro)
    
    def addEntityWithPendingAnalysis(self, entity):
        self.pendingAnalysisList.append(entity)

    def addPublicNamedElement(self, name, binding, sourcePosition):
        if name in self.publicSymbolTable:
            raise RuntimeError(str(sourcePosition) +  " a binding for public symbol #'" + name + "'already exists.")
        self.addSymbolWithBinding(name, binding)

    def finishPendingAnalysis(self):
        while len(self.pendingAnalysisList) != 0:
            toAnalyze = self.pendingAnalysisList
            self.pendingAnalysisList = []
            for entity in toAnalyze:
                entity.ensureAnalysis()

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

    def lookupProgramEntityOwner(self):
        return None

class HIRPackageEnvironment(HIREnvironment):
    def __init__(self, package, parent):
        super().__init__()
        self.package = package
        self.parent = parent

    def lookupProgramEntityOwner(self):
        return self.package

    def lookSymbolRecursively(self, symbol):
        packageSymbolBinding = self.package.lookupSymbolRecursivelyOrNone(symbol)
        if packageSymbolBinding is not None:
            return packageSymbolBinding

        return self.parent.lookSymbolRecursively(symbol)

class HIROwnerEnvironment(HIREnvironment):
    def __init__(self, parent, owner):
        super().__init__()
        self.parent = parent
        self.owner = owner

    def lookupProgramEntityOwner(self):
        return self.owner

    def lookSymbolRecursively(self, symbol):
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

    def lookupProgramEntityOwner(self):
        return self.parent.lookupProgramEntityOwner()

    def lookSymbolRecursively(self, symbol):
        if symbol in self.symbolTable:
            return self.symbolTable[symbol]
        return self.parent.lookSymbolRecursively(symbol)

class HIRDependentFunctionTypeAnalysisEnvironment(HIRLexicalEnvironment):
    def __init__(self, parent):
        super().__init__(parent)
        self.captureTable = {}
        self.captureList = []

    def lookupProgramEntityOwner(self):
        return self.parent.lookupProgramEntityOwner()

    def lookSymbolRecursively(self, symbol):
        if symbol in self.symbolTable:
            binding = self.symbolTable[symbol]
            binding.markDependentUsage()
            return binding

        # Captures
        if symbol in self.captureTable:
            return self.captureTable[symbol]

        parentBinding = self.parent.lookSymbolRecursively(symbol)
        # Parent binding
        if parentBinding is not None:
            if parentBinding.isFunctionLocalValue():
                assert False
        return parentBinding

class HIRImplicitFieldAccess(HIRValue):
    def __init__(self, type, aggregate, field, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type
        self.aggregate = aggregate
        self.field = field

    def getType(self):
        return self.type

    def analyzeAndBuildIdentifierReferenceNode(self, buildPass, node):
        return buildPass.builder.extractFieldReference(self.type, self.aggregate, self.field, node.sourcePosition)

class HIRFunctionAnalysisEnvironment(HIRLexicalEnvironment):
    def __init__(self, parent, returnType, receiverValue, context):
        super().__init__(parent)
        self.captureTable = {}
        self.captureList = []
        self.receiverValue = receiverValue
        self.returnType = returnType
        self.context = context

    def addDependentFunctionTypeCaptures(self, captureList):
        for capture in captureList:
            self.captureTable[capture.name] = capture
            self.captureList.append(capture)

    def lookupProgramEntityOwner(self):
        return self.parent.lookupProgramEntityOwner()

    def lookSymbolRecursively(self, symbol):
        if symbol in self.symbolTable:
            binding = self.symbolTable[symbol]
            return binding
        
        if self.receiverValue is not None:
            field = self.receiverValue.getType().lookupField(symbol)
            if field is not None:
                fieldReferenceType = self.context.getOrCreateReferenceType(field.type)
                return HIRImplicitFieldAccess(fieldReferenceType, self.receiverValue, field, None)

        # Captures
        if symbol in self.captureTable:
            return self.captureTable[symbol]

        parentBinding = self.parent.lookSymbolRecursively(symbol)
        # Parent binding
        if parentBinding is not None:
            if parentBinding.isFunctionLocalValue():
                capture = HIRCapture(parentBinding, parentBinding.getType())
                capture.name = symbol
                self.captureTable[symbol] = capture
                self.captureList.append(capture)
                return capture
        return parentBinding

class HIRMetaBuilderFactory(HIRValue):
    def __init__(self, clazz, coreTypes, sourcePosition):
        super().__init__(sourcePosition)
        self.coreTypes = coreTypes
        self.clazz = clazz

    def analyzeAndEvaluateIdentifierReferenceNode(self, evaluator, node: ParseTreeIdentifierReferenceNode):
        return self.clazz(self.coreTypes, node.sourcePosition).analyzeAndEvaluateIdentifierReferenceNode(evaluator, node)

    def analyzeAndBuildIdentifierReferenceNode(self, analyzer, node: ParseTreeIdentifierReferenceNode):
        return self.clazz(self.coreTypes, node.sourcePosition).analyzeAndBuildIdentifierReferenceNode(analyzer, node)

    def getType(self):
        return self.coreTypes.metaBuilderFactoryType

class HIRMetaBuilder(HIRValue):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(sourcePosition)
        self.coreTypes = coreTypes

    def supportsSelector(self, selector):
        return False

    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector: str, receiver):
        return self

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node, receiver):
        selectorValue = evaluator.visitOptionalSymbolNode(node.selector)
        if self.supportsSelector(selectorValue):
            return self.expandMessageSend(evaluator, node, selectorValue, receiver)
        return super().analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)

    def analyzeAndBuildMessageSendNode(self, buildPass, node, receiver):
        selectorValue = buildPass.evaluateSymbolNode(node.selector)
        if self.supportsSelector(selectorValue):
            return self.expandMessageSend(buildPass, node, selectorValue, receiver)
        return super().analyzeAndBuildMessageSendNode(buildPass, node, receiver)

    def getType(self):
        return self.coreTypes.metaBuilderType

class HIRNamedMetaBuilder(HIRMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.nameExpression = None

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node: ParseTreeMessageSendNode, receiver):
        if self.nameExpression is None and len(node.arguments) == 0:
            self.nameExpression = node.selector
            return self
        return super().analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)
    
    def analyzeAndBuildMessageSendNode(self, buildPass, node: ParseTreeMessageSendNode, receiver):
        if self.nameExpression is None and len(node.arguments) == 0:
            self.nameExpression = node.selector
            return self
        return super().analyzeAndBuildMessageSendNode(buildPass, node, receiver)

class HIRLetMetaBuilder(HIRNamedMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.isMutable = False
        self.typeExpression = None

    def supportsSelector(self, selector):
        return selector in ('mutable', 'type:')

    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector: str, receiver):
        if selector == 'mutable':
            self.isMutable = True
        elif selector == 'type:':
            self.typeExpression = node.arguments[0]
        return self
    
    def analyzeAndEvaluateAssignment(self, evaluationPass, node: ParseTreeAssignmentNode):
        variableDefinition = ParseTreeVariableDefinitionNode(node.sourcePosition, self.nameExpression, self.typeExpression, node.value, self.isMutable)
        return evaluationPass.visitNode(variableDefinition)
    
    def analyzeAndBuildAssignment(self, buildPass, node):
        variableDefinition = ParseTreeVariableDefinitionNode(node.sourcePosition, self.nameExpression, self.typeExpression, node.value, self.isMutable)
        return buildPass.visitNode(variableDefinition)

class HIREnumMetaBuilder(HIRNamedMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.isPublic = False

    def supportsSelector(self, selector):
        return selector in ('baseType:values:')
    
    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector, receiver):
        if selector == 'baseType:values:':
            baseType = node.arguments[0]
            values = node.arguments[1]
            enumNode = ParseTreeEnumDefinitionNode(self.sourcePosition, self.nameExpression, baseType, values, self.isPublic)
            return evaluator.visitNode(enumNode)
        return super().expandMessageSend(evaluator, node, selector, receiver)

class HIRFieldMetaBuilder(HIRNamedMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.typeExpression = None
        self.isPublic = False

    def supportsSelector(self, selector):
        return selector in ('=>', 'type:')

    def expandMessageSend(self, evaluator, node, selector, receiver):
        if (selector == '=>') or (selector == 'type:'):
            self.typeExpression = node.arguments[0]
            fieldDefinition = ParseTreeFieldDefinitionNode(node.sourcePosition, self.nameExpression, self.typeExpression, self.isPublic)
            return evaluator.visitNode(fieldDefinition)
        return super().expandMessageSend(evaluator, node, selector, receiver)

class HIRFunctionMetaBuilder(HIRNamedMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.argumentDefinitions = []
        self.resultTypeExpression = None
        self.isPublic = False

    def supportsSelector(self, selector):
        return selector in ('=>')

    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector: str, receiver):
        if selector == '=>':
            self.resultTypeExpression = node.arguments[0]
        return self

    def analyzeAndEvaluateApplicationNode(self, evaluator, node: ParseTreeApplicationNode, functional):
        for argument in node.arguments:
            argumentDefinition = argument.parseAsArgumentDefinition()
            self.argumentDefinitions.append(argumentDefinition)
        return self

    def analyzeAndBuildApplicationNode(self, buildPass, node: ParseTreeApplicationNode, functional):
        for argument in node.arguments:
            argumentDefinition = argument.parseAsArgumentDefinition()
            self.argumentDefinitions.append(argumentDefinition)
        return self

    def makeFunctionType(self):
        return ParseTreeFunctionTypeNode(self.sourcePosition, self.argumentDefinitions, self.resultTypeExpression)

    def analyzeAndEvaluateAssignment(self, evaluationPass, node):
        functionNode = ParseTreeFunctionNode(node.sourcePosition, self.nameExpression, self.makeFunctionType(), node.value, self.isPublic)
        return evaluationPass.visitNode(functionNode)
    
    def analyzeAndBuildAssignment(self, buildPass, node):
        functionNode = ParseTreeFunctionNode(node.sourcePosition, self.nameExpression, self.makeFunctionType(), node.value, self.isPublic)
        return buildPass.visitNode(functionNode)

class HIRMethodMetaBuilder(HIRMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.selectorExpression = None
        self.argumentDefinitions = None
        self.resultTypeExpression = None
        self.isPublic = False

    def analyzeAndEvaluateMessageSendNode(self, evaluator, node, receiver):
        if self.argumentDefinitions is None:
            self.selectorExpression = node.selector
            self.argumentDefinitions = list(map(lambda each: each.parseAsArgumentDefinition(), node.arguments))
            return self
        return super().analyzeAndEvaluateMessageSendNode(evaluator, node, receiver)

    def supportsSelector(self, selector):
        return selector in ('=>')

    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector: str, receiver):
        if selector == '=>':
            self.resultTypeExpression = node.arguments[0]
        return self
        
    def makeFunctionType(self):
        return ParseTreeFunctionTypeNode(self.sourcePosition, self.argumentDefinitions, self.resultTypeExpression)

    def analyzeAndEvaluateAssignment(self, evaluationPass, node):
        functionNode = ParseTreeFunctionNode(node.sourcePosition, self.selectorExpression, self.makeFunctionType(), node.value, self.isPublic, True)
        return evaluationPass.visitNode(functionNode)

class HIRClassMetaBuilder(HIRNamedMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.superclassExpression = None
        self.isPublic = False

    def supportsSelector(self, selector):
        return selector in ('superclass:', 'definition:', 'superclass:definition:')

    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector, receiver):
        if selector == 'superclass:':
            self.superclassExpression = node.arguments[0]
        elif selector == 'definition:':
            structNode = ParseTreeClassDefinitionNode(node.sourcePosition, self.nameExpression, self.superclassExpression, node.arguments[0], self.isPublic )
            return evaluator.visitNode(structNode)
        elif selector == 'superclass:definition:':
            structNode = ParseTreeClassDefinitionNode(node.sourcePosition, self.nameExpression, node.arguments[0], node.arguments[1], self.isPublic )
            return evaluator.visitNode(structNode)
        return super().expandMessageSend(evaluator, node, selector, receiver)

class HIRStructMetaBuilder(HIRNamedMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.isPublic = False

    def supportsSelector(self, selector):
        return selector in ('definition:')

    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector, receiver):
        if selector == 'definition:':
            structNode = ParseTreeStructDefinitionNode(node.sourcePosition, self.nameExpression, node.arguments[0], self.isPublic )
            return evaluator.visitNode(structNode)
        return super().expandMessageSend(evaluator, node, selector, receiver)

class HIRPublicMetaBuilder(HIRMetaBuilder):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)

    def supportsSelector(self, selector):
        return selector in ('class', 'enum', 'field', 'function', 'struct')
    
    def expandMessageSend(self, evaluator, node: ParseTreeMessageSendNode, selector: str, receiver):
        if selector == 'class':
            metabuilder = HIRClassMetaBuilder(self.coreTypes, node.sourcePosition)
            metabuilder.isPublic = True
            return metabuilder
        elif selector == 'enum':
            metabuilder = HIREnumMetaBuilder(self.coreTypes, node.sourcePosition)
            metabuilder.isPublic = True
            return metabuilder
        elif selector == 'field':
            metabuilder = HIRFieldMetaBuilder(self.coreTypes, node.sourcePosition)
            metabuilder.isPublic = True
            return metabuilder
        elif selector == 'function':
            metabuilder = HIRFunctionMetaBuilder(self.coreTypes, node.sourcePosition)
            metabuilder.isPublic = True
            return metabuilder
        elif selector == 'struct':
            metabuilder = HIRStructMetaBuilder(self.coreTypes, node.sourcePosition)
            metabuilder.isPublic = True
            return metabuilder
        return self

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

        self.integerType.defaultValue = HIRConstantLiteralIntegerValue(0, self.integerType, None)

        self.dynamicType = HIRDynamicType('Dynamic', self, None)
        self.voidType    = HIRVoidType('Void', self, None);

        self.dynamicAssociationType = HIRAssociationType(self.dynamicType, self.dynamicType, self)
        self.dynamicDictionaryType = HIRDictionaryType(self.dynamicAssociationType, self)

        self.controlFlowEscapeType = HIRControlFlowEscapeType('ControlFlowEscape', self, None);

        self.packageType = HIRNominalType('Package', self, None)
        self.fieldType = HIRNominalType('Field', self, None)
        self.parseTreeNodeType = HIRNominalType('ParseTreeNode', self, None)
        self.primitiveMacroType = HIRNominalType('PrimitiveMacro', self, None)

        self.prop = HIRUniverseType('Prop', self, 0);
        self.type = HIRUniverseType('Type', self, 1);
        self.universeLevels = {
            0: self.prop,
            1: self.type,
        }

        self.metaBuilderFactoryType = HIRNominalType('MetaBuilderFactory', self, None)
        self.metaBuilderType = HIRNominalType('MetaBuilder', self, None)

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
        
        self.createCoreClassDefinitions()
        self.createCorePrimitiveMacros()
        self.createCorePrimitiveMetaBuilders()
        self.createCorePrimitiveFunctions()

    def makeCoreClassDefinition(self, name, superclass, fields, metaFields):
        metaclass = HIRMetaclass(self)
        metaclass.type = self.metaclassType

        clazz = HIRClass(name, metaclass, self)
        clazz.superclass = superclass
        if superclass is not None:
            metaclass.superclass = superclass.getType()

        metaclass.thisClass = clazz
        return clazz
    
    def fixupMetaclassTypes(self, typesTopFixup):
        for clazz in typesTopFixup:
            metaclass = clazz.getType()
            metaclass.type = self.metaclassType

    def createCoreClassDefinitions(self):
        self.metaclassType = None

        self.protoObjectClass  = self.makeCoreClassDefinition('ProtoObject', None, [], [])
        self.objectClass = self.makeCoreClassDefinition('Object', self.protoObjectClass, [], [])

        self.metaObjectClass = self.makeCoreClassDefinition('MetaObject', self.objectClass, [], [])
        self.typeClass = self.makeCoreClassDefinition('Type', self.metaObjectClass, [], [])
        self.nominalTypeClass = self.makeCoreClassDefinition('NominalType', self.typeClass, [], [])
        self.behaviorClass = self.makeCoreClassDefinition('Behavior', self.nominalTypeClass, [], [])
        self.classClass = self.makeCoreClassDefinition('Class', self.behaviorClass, [], [])
        self.metaclassType = self.makeCoreClassDefinition('Metaclass', self.behaviorClass, [], [])

        # Short circuit
        self.protoObjectClass.getType().superclass = self.classClass
        self.fixupMetaclassTypes([
            self.protoObjectClass, self.objectClass, self.metaObjectClass,
            self.typeClass, self.nominalTypeClass, self.behaviorClass, self.classClass,
            self.metaclassType
        ])

        self.coreTypeList += [
            self.protoObjectClass,
            self.objectClass,

            self.metaObjectClass,
            self.typeClass,
            self.nominalTypeClass,
            self.behaviorClass,
            self.classClass,
            self.metaclassType,
        ]

    def createCorePrimitiveMacros(self):

        def assertMacro(macroContext: HIRMacroContext, expression: ParseTreeNode):
            return ParseTreeAssertNode(macroContext.sourcePosition, expression)
        def errorMacro(macroContext: HIRMacroContext, messageExpression: ParseTreeNode):
            return ParseTreeRuntimeErrorNode(macroContext.sourcePosition, messageExpression)
        
        def loadFileOnce(macroContext: HIRMacroContext, fileName: ParseTreeNode):
            return ParseTreeLoadFileOnceNode(macroContext.sourcePosition, fileName)

        def letWith(macroContext: HIRMacroContext, nameExpression: ParseTreeNode, initialValue: ParseTreeNode):
            return ParseTreeVariableDefinitionNode(macroContext.sourcePosition, nameExpression, None, initialValue, False)
        def letMutableWith(macroContext: HIRMacroContext, nameExpression: ParseTreeNode, initialValue: ParseTreeNode):
            return ParseTreeVariableDefinitionNode(macroContext.sourcePosition, nameExpression, None, initialValue, True)

        def ifThenElse(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, trueExpression: ParseTreeNode, falseExpression: ParseTreeNode):
            return ParseTreeIfSelectionNode(macroContext.sourcePosition, conditionExpression, trueExpression, falseExpression)
        def ifThen(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, trueExpression: ParseTreeNode):
            return ParseTreeIfSelectionNode(macroContext.sourcePosition, conditionExpression, trueExpression, None)
        def switchWithCasesMacro(macroContext: HIRMacroContext, valueExpression: ParseTreeNode, cases: ParseTreeNode):
            return ParseTreeSwitchSelectionNode(macroContext.sourcePosition, valueExpression, cases)

        def whileDoContinueWith(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, bodyExpression: ParseTreeNode, continueExpression: ParseTreeNode):
            return ParseTreeWhileDoNode(macroContext.sourcePosition, conditionExpression, bodyExpression, continueExpression)
        def whileDo(macroContext: HIRMacroContext, conditionExpression: ParseTreeNode, bodyExpression: ParseTreeNode):
            return ParseTreeWhileDoNode(macroContext.sourcePosition, conditionExpression, bodyExpression, None)

        def doContinueWithWhile(macroContext: HIRMacroContext, bodyExpression: ParseTreeNode, continueExpression: ParseTreeNode, conditionExpression: ParseTreeNode):
            return ParseTreeDoWhileNode(macroContext.sourcePosition, bodyExpression, continueExpression, conditionExpression)
        def doWhile(macroContext: HIRMacroContext, bodyExpression: ParseTreeNode, conditionExpression: ParseTreeNode):
            return ParseTreeDoWhileNode(macroContext.sourcePosition, bodyExpression, None, conditionExpression)

        def returnMacro(macroContext: HIRMacroContext, valueExpression: ParseTreeNode):
            return ParseTreeReturnNode(macroContext.sourcePosition, valueExpression)

        self.corePrimitiveMacros = [
            HIRPrimitiveMacro('assert:', self.primitiveMacroType, assertMacro, None),
            HIRPrimitiveMacro('error:', self.primitiveMacroType, errorMacro, None),

            HIRPrimitiveMacro('loadFileOnce:', self.primitiveMacroType, loadFileOnce, None),

            HIRPrimitiveMacro('let:with:', self.primitiveMacroType, letWith, None),
            HIRPrimitiveMacro('let:mutableWith:', self.primitiveMacroType, letMutableWith, None),

            HIRPrimitiveMacro('if:then:else:', self.primitiveMacroType, ifThenElse, None),
            HIRPrimitiveMacro('if:then:', self.primitiveMacroType, ifThen, None),
            HIRPrimitiveMacro('switch:withCases:', self.primitiveMacroType, switchWithCasesMacro, None),

            HIRPrimitiveMacro('while:do:continueWith:', self.primitiveMacroType, whileDoContinueWith, None),
            HIRPrimitiveMacro('while:do:', self.primitiveMacroType, whileDo, None),

            HIRPrimitiveMacro('do:continueWith:while:', self.primitiveMacroType, doContinueWithWhile, None),
            HIRPrimitiveMacro('do:while:', self.primitiveMacroType, doWhile, None),

            HIRPrimitiveMacro('return:', self.primitiveMacroType, returnMacro, None),
        ]

    def createCorePrimitiveMetaBuilders(self):
        self.coreValueList += [
            (HIRMetaBuilderFactory(HIRClassMetaBuilder, self, None), 'class'),
            (HIRMetaBuilderFactory(HIREnumMetaBuilder, self, None), 'enum'),
            (HIRMetaBuilderFactory(HIRFieldMetaBuilder, self, None), 'field'),
            (HIRMetaBuilderFactory(HIRFunctionMetaBuilder, self, None), 'function'),
            (HIRMetaBuilderFactory(HIRLetMetaBuilder, self, None), 'let'),
            (HIRMetaBuilderFactory(HIRMethodMetaBuilder, self, None), 'method'),
            (HIRMetaBuilderFactory(HIRPublicMetaBuilder, self, None), 'public'),
            (HIRMetaBuilderFactory(HIRStructMetaBuilder, self, None), 'struct'),
        ]

    def createCorePrimitiveFunctions(self):
        self.createGlobalPrimitives()
        self.createBooleanPrimitiveFunctions()
        self.createIntegerPrimitiveFunctions()
        self.createFloatPrimitiveFunctions()

    def getBooleanConstant(self, value):
        if value:
            return self.trueValue
        else:
            return self.falseValue
    
    def createGlobalPrimitives(self):
        def printPrimitive(operand, resultType):
            print(str(operand), end='')
            return self.voidValue

        def printLinePrimitive(operand, resultType):
            print(str(operand))
            return self.voidValue

        def writeLinePrimitive(operand, resultType):
            print(str(operand))
            return self.voidValue

        self.coreValueList += [
            (HIRPrimitiveFunction('IO::print', self.getOrCreateSimpleFunctionType((self.dynamicType,), self.voidType), printPrimitive, None), 'print'),
            (HIRPrimitiveFunction('IO::printLine', self.getOrCreateSimpleFunctionType((self.dynamicType,), self.voidType), printLinePrimitive, None), 'printLine'),
            (HIRPrimitiveFunction('IO::writeLine', self.getOrCreateSimpleFunctionType((self.dynamicType,), self.voidType), writeLinePrimitive, None), 'writeLine'),
        ]

    def createBooleanPrimitiveFunctions(self):
        def booleanNot(operand, resultType):
            assert operand.isBooleanConstant()
            return self.getBooleanConstant(not operand.value)
        def booleanAnd(macroContext: HIRMacroContext, left: ParseTreeNode, right: ParseTreeNode):
            return ParseTreeIfSelectionNode(macroContext.sourcePosition, left, right, ParseTreeLiteralValueNode(macroContext.sourcePosition, self.falseValue))
        def booleanOr(macroContext: HIRMacroContext, left: ParseTreeNode, right: ParseTreeNode):
            return ParseTreeIfSelectionNode(macroContext.sourcePosition, left, ParseTreeLiteralValueNode(macroContext.sourcePosition, self.trueValue), right)
        
        self.booleanType.withSelectorAddMethod('not', HIRPrimitiveFunction('Boolean::not', self.getOrCreateSimpleFunctionType((self.booleanType,), self.booleanType), booleanNot, None, isPure = True, isCompileTime = True))
        self.booleanType.withSelectorAddMethod('&&', HIRPrimitiveMacro('&&', self.primitiveMacroType, booleanAnd, None))
        self.booleanType.withSelectorAddMethod('||', HIRPrimitiveMacro('||', self.primitiveMacroType, booleanOr, None))


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

    def getOrCreateSimpleFunctionType(self, argumentTypes, resultType, sourcePosition = None):
        return HIRSimpleFunctionType(argumentTypes, resultType, self, sourcePosition)
    
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

    def addEntityWithPendingAnalysis(self, entity):
        self.currentPackage.addEntityWithPendingAnalysis(entity)

    def finishPendingAnalysis(self):
        self.currentPackage.finishPendingAnalysis()

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
        dependentFunctionType = HIRDependentFunctionType([], [], self.coreTypes.dynamicType, self.coreTypes, sourcePosition)
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

    def getOrCreateAssociationType(self, keyType, valueType):
        return HIRAssociationType(keyType, valueType, self.coreTypes, None)

    def getOrCreateTupleType(self, elements):
        return HIRTupleType(elements, self.coreTypes, None)

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

    def clone(self):
        return HIREvaluationContext(self.context, self.environment)

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

    def assertCondition(self, condition, errorMessage, sourcePosition):
        instruction = HIRAssertInstruction(condition, errorMessage, self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def runtimeError(self, errorMessage, sourcePosition):
        instruction = HIRRuntimeErrorInstruction(errorMessage, self.context.coreTypes.controlFlowEscapeType, None, sourcePosition)
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
    
    def send(self, receiver, selector, arguments, resultTyoe, sourcePosition):
        instruction = HIRSendInstruction(receiver, selector, arguments, resultTyoe, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def dynamicUnbox(self, boxedValue, type, sourcePosition):
        instruction = HIRDynamicUnboxInstruction(boxedValue, type, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def enumBoxValue(self, value, type, sourcePosition):
        instruction = HIREnumBoxValueInstruction(value, type, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def enumUnboxValue(self, enumValue, type, sourcePosition):
        instruction = HIREnumUnboxValueInstruction(enumValue, type, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def extractFieldReference(self, referenceType, aggregate, field, sourcePosition):
        instruction = HIRExtractFieldReferenceInstruction(referenceType, aggregate, field, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def setAggregateField(self, aggregate, value, field, sourcePosition: SourcePosition = None):
        instruction = HIRSetAggregateFieldInstruction(self.context.coreTypes.voidType, aggregate, value, field, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def load(self, type, storage, sourcePosition):
        instruction = HIRLoadInstruction(type, storage, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction
    
    def store(self, storage, valueToStore, sourcePosition):
        instruction = HIRStoreInstruction(self.context.coreTypes.voidType, storage, valueToStore, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def makeAssociation(self, key, value, type, sourcePosition):
        instruction = HIRMakeAssociationInstruction(key, value,type, None, sourcePosition)
        simplified = instruction.simplifyWithBuilder(self)
        if instruction == simplified:
            self.addInstruction(instruction)
        return simplified

    def makeClosure(self, function, captureList, type, sourcePosition):
        instruction = HIRMakeClosureInstruction(function, captureList, type, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def makeObject(self, type, defaultElements, sourcePosition):
        instruction = HIRMakeObjectInstruction(type, defaultElements, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def makeStruct(self, type, defaultElements, sourcePosition):
        instruction = HIRMakeStructInstruction(type, defaultElements, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction

    def makeTuple(self, elements, type, sourcePosition):
        instruction = HIRMakeTupleInstruction(elements, type, None, sourcePosition)
        simplified = instruction.simplifyWithBuilder(self)
        if instruction == simplified:
            self.addInstruction(instruction)
        return simplified

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
