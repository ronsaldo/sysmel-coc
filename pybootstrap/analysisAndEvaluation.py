from parsetree import *
from hir import *
from parser import parseFileNamed
import os.path

class AnalysisAndEvaluationPass(ParseTreeVisitor):
    def __init__(self, evaluationContext: HIREvaluationContext):
        super().__init__()
        self.evaluationContext = evaluationContext

    def visitDecayedNode(self, node: ParseTreeNode):
        value = self.visitNode(node)
        if value.isReferenceValue():
            return value.loadValue()

        return value

    def visitNodeWithExpectedType(self, node, expectedType):
        value = self.visitDecayedNode(node)
        if (expectedType is not None) and (not expectedType.isSatisfiedByValue(value)):
            raise RuntimeError(str(node.sourcePosition) +  " Error: Expected a value whose type is " + str(expectedType))
        return value

    def visitNodeExpectingType(self, node):
        value = self.visitDecayedNode(node)
        if not value.isType():
            raise RuntimeError(str(node.sourcePosition) +  " Error: Expected a type instead of  " + str(value))
        return value
    
    def visitBooleanNode(self, node: ParseTreeNode):
        evaluatedNode = self.visitNodeWithExpectedType(node, self.evaluationContext.context.coreTypes.booleanType)
        assert evaluatedNode.isBooleanConstant()
        return evaluatedNode.value

    def visitSymbolNode(self, node: ParseTreeNode):
        evaluatedNode = self.visitNodeWithExpectedType(node, self.evaluationContext.context.coreTypes.symbolType)
        assert evaluatedNode.isSymbolConstant()
        return evaluatedNode.value

    def visitOptionalSymbolNode(self, node: ParseTreeNode):
        if node is None:
            return None
        return self.visitSymbolNode(node)

    def visitErrorNode(self, node):
        raise RuntimeError("%s: %s" % (str(node.sourcePosition), node.message))

    def visitApplicationNode(self, node):
        functional = self.visitDecayedNode(node.functional)
        return functional.analyzeAndEvaluateApplicationNode(self, node, functional)

    def visitArgumentDefinitionNode(self, node: ParseTreeArgumentDefinitionNode):
        argumentType = self.evaluationContext.context.coreTypes.dynamicType
        if node.typeExpression is not None:
            argumentType = self.visitNodeExpectingType(node.typeExpression)

        argument = HIRArgument(argumentType, node.name)
        argument.isSelf = node.isSelf
        return argument

    def visitAssertNode(self, node: ParseTreeAssertNode):
        expressionValue = self.visitBooleanNode(node.expression)
        if not expressionValue:
            raise AssertionError('%s: assertion failed: %s' % (str(node.sourcePosition), node.sourcePosition.getStringValue())) 
        
        return self.evaluationContext.context.coreTypes.voidValue

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        storeValue = self.visitNode(node.store)
        return storeValue.analyzeAndEvaluateAssignment(self, node)

    def visitAssociationNode(self, node: ParseTreeAssociationNode):
        key = self.visitDecayedNode(node.key)
        value = self.evaluationContext.context.coreTypes.nilValue
        if node.value is not None:
            value = self.visitDecayedNode(node.value)

        if key.isType() and value.isType():
            return self.evaluationContext.context.getOrCreateAssociationType(key, value)

        keyType = key.getType()
        valueType = value.getType()
        associationType = self.evaluationContext.context.getOrCreateAssociationType(keyType, valueType)
        return HIRConstantAssociation(key, value, associationType, node.sourcePosition)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        expandedMessageSend = node.expandAsMessageSends()
        return self.visitNode(expandedMessageSend)

    def visitFunctionTypeNode(self, node: ParseTreeFunctionTypeNode):
        oldEnvironment = self.evaluationContext.environment
        analysisEnvironment = HIRDependentFunctionTypeAnalysisEnvironment(oldEnvironment)
        self.evaluationContext.environment = analysisEnvironment

        argumentDefinitions = []
        for argument in node.argumentDefinitions:
            argumentDefinitions.append(self.visitNode(argument))

        resultType = self.evaluationContext.context.coreTypes.dynamicType
        if node.resultTypeExpression is not None:
            resultType = self.visitNodeExpectingType(node.resultTypeExpression)

        functionType = HIRDependentFunctionType(analysisEnvironment.captureList, argumentDefinitions, resultType, self.evaluationContext.context.coreTypes, node.sourcePosition)
        self.evaluationContext.environment = oldEnvironment
        return functionType

    def visitFunctionNode(self, node: ParseTreeFunctionNode):
        name = self.visitOptionalSymbolNode(node.nameExpression)

        dependentFunctionType = self.visitNode(node.functionType)

        function = HIRFunction(name, dependentFunctionType, node.sourcePosition)
        function.definitionBody = node.body
        function.definitionContext = self.evaluationContext.context
        function.definitionEnvironment = self.evaluationContext.environment
        self.evaluationContext.context.addEntityWithPendingAnalysis(function)

        if name is not None:
            self.evaluationContext.environment.setNewSymbolBinding(name, function, node.sourcePosition)
            if node.isPublic:
                owner = self.evaluationContext.environment.lookupProgramEntityOwner()
                owner.addPublicNamedElement(name, function, node.sourcePosition)

        return function

    def visitCascadeMessageNode(self, node: ParseTreeCascadedMessageNode):
        assert False

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        associations = list(map(self.visitNode, node.elements))
        dictionaryType = self.evaluationContext.context.coreTypes.dynamicDictionaryType
        return HIRConstantDictionary(associations, dictionaryType, node.sourcePosition)

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        bindingOrNone = self.evaluationContext.environment.lookSymbolRecursively(node.value)
        if bindingOrNone is None:
            raise RuntimeError("%s: #%s identifier is not found." % (str(node.sourcePosition), node.value))    
        return bindingOrNone.analyzeAndEvaluateIdentifierReferenceNode(self, node)

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        childEnvironment = HIRLexicalEnvironment(self.evaluationContext.environment)
        oldEnvironment = self.evaluationContext.environment
        self.evaluationContext.environment = childEnvironment

        result = self.visitNode(node.body)

        self.evaluationContext.environment = oldEnvironment
        return result

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        return HIRConstantLiteralCharacterValue(node.value, self.evaluationContext.context.coreTypes.characterType, node.sourcePosition)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        return HIRConstantLiteralFloatValue(node.value, self.evaluationContext.context.coreTypes.floatType, node.sourcePosition)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        return HIRConstantLiteralIntegerValue(node.value, self.evaluationContext.context.coreTypes.integerType, node.sourcePosition)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        return HIRConstantLiteralSymbolValue(node.value, self.evaluationContext.context.coreTypes.symbolType, node.sourcePosition)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        return HIRConstantLiteralStringValue(node.value, self.evaluationContext.context.coreTypes.stringType, node.sourcePosition)

    def visitLiteralValueNode(self, node: ParseTreeLiteralValueNode):
        return node.value

    def visitMessageCascadeNode(self, node: ParseTreeMessageCascadeNode):
        resultValue = self.visitNode(node.receiver)
        receiverNodeValue = ParseTreeLiteralValueNode(node.receiver.sourcePosition, resultValue)

        for cascaded in node.messages:
            cascadedMessage = cascaded.asMessageSendWithReceiver(receiverNodeValue)
            resultValue = self.visitNode(cascadedMessage)

        return resultValue

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        receiver = self.visitNode(node.receiver)
        return receiver.analyzeAndEvaluateMessageSendNode(self, node, receiver)

    def visitQuasiQuoteNode(self, node):
        assert False

    def visitQuasiUnquoteNode(self, node: ParseTreeQuasiUnquoteNode):
        raise RuntimeError("%s: invalid location for a quasi unquote." % str(node.sourcePosition))

    def visitSpliceNode(self, node):
        raise RuntimeError("%s: invalid location for a splice." % str(node.sourcePosition))

    def visitQuoteNode(self, node: ParseTreeQuoteNode):
        return HIRConstantLiteralParseTree(node.term, self.evaluationContext.context.coreTypes.parseTreeNodeType, node.sourcePosition)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        result = self.evaluationContext.context.coreTypes.voidValue
        for element in node.elements:
            result = self.visitNode(element)
        return result

    def visitRuntimeErrorNode(self, node: ParseTreeRuntimeErrorNode):
        message = self.visitNodeWithExpectedType(node.messageExpression, self.evaluationContext.context.coreTypes.stringType)
        raise RuntimeError(message.value)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        tupleElements = []
        tupleTypes = []
        hasOnlyTypes = True
        for elementNode in node.elements:
            elementValue = self.visitDecayedNode(elementNode)
            tupleElements.append(elementValue)
            tupleTypes.append(elementValue.getType())
            if not elementValue.isType():
                hasOnlyTypes = False

        if hasOnlyTypes:
            return self.evaluationContext.context.getOrCreateTupleType(tupleElements)
        
        tupleType = self.evaluationContext.context.getOrCreateTupleType(tupleTypes)
        return HIRConstantTuple(tupleElements, tupleType, node.sourcePosition)

    def visitVariableDefinitionNode(self, node: ParseTreeVariableDefinitionNode):
        name = self.visitOptionalSymbolNode(node.nameExpression)
        
        typeValue = None
        if node.typeExpression is not None:
            typeValue = self.visitNodeExpectingType(node.typeExpression)

        initialValue = None
        if node.initialValue is not None:
            initialValue = self.visitNodeWithExpectedType(node.initialValue, typeValue)

        if initialValue is None:
            if typeValue is None:
                raise RuntimeError(str(node.sourcePosition) +  " at least a type or an initial value must be specified.")
            initialValue = typeValue.getOrCreateDefaultValue()

        if node.isMutable:
            valueType = typeValue
            if valueType is None:
                valueType = initialValue.getType()

            valueBoxType = self.evaluationContext.context.getOrCreateMutableValueBoxType(valueType)
            valueBox = HIRMutableValueBox(valueBoxType, initialValue, node.sourcePosition)

            referenceType = self.evaluationContext.context.getOrCreateReferenceType(valueType)
            referenceValue = HIRReferenceValue(referenceType, valueBox, 0, node.sourcePosition)
            if name is not None:
                self.evaluationContext.environment.setNewSymbolBinding(name, referenceValue, node.sourcePosition)

            return referenceValue
        else:
            if name is not None:
                self.evaluationContext.environment.setNewSymbolBinding(name, initialValue, node.sourcePosition)
            return initialValue

    def visitIfSelectionNode(self, node: ParseTreeIfSelectionNode):
        condition = self.visitBooleanNode(node.condition)
        if condition:
            if node.trueExpression is None:
                return self.evaluationContext.context.coreTypes.voidValue
            return self.visitNode(node.trueExpression)
        else:
            if node.falseExpression is None:
                return self.evaluationContext.context.coreTypes.voidValue
            return self.visitNode(node.falseExpression)

    def visitSwitchSelectionNode(self, node: ParseTreeSwitchSelectionNode):
        value = self.visitDecayedNode(node.valueExpression)
        if not node.cases.isDictionaryNode():
            raise RuntimeError(str(node.cases.sourcePosition) + ": Expected a dictionary with switch cases.")

        for caseAssociation in node.cases.elements:
            if not caseAssociation.isAssociationNode():
                raise RuntimeError(str(caseAssociation.sourcePosition) + ": Expected an association with the case key and value.")
            caseKey = self.visitDecayedNode(caseAssociation.key)
            caseValue = self.evaluationContext.context.coreTypes.voidValue
            if value == caseKey or (caseKey.isSymbolConstant() and caseKey.value == '_'):
                if caseAssociation.value is not None:
                    ##print("caseAssociation.value ", caseAssociation.value)
                    caseValue = self.visitDecayedNode(caseAssociation.value)
                return caseValue

        return self.evaluationContext.context.coreTypes.voidValue

    def visitReturnNode(self, node: ParseTreeReturnNode):
        raise RuntimeError('%s: return expression is not supported in here.' % (str(node.sourcePosition)))

    def visitWhileDoNode(self, node: ParseTreeWhileDoNode):
        while self.visitBooleanNode(node.condition):
            self.visitOptionalNode(node.bodyExpression)
            self.visitOptionalNode(node.continueExpression)
        return self.evaluationContext.context.coreTypes.voidValue

    def visitDoWhileNode(self, node: ParseTreeDoWhileNode):
        while True:
            self.visitOptionalNode(node.bodyExpression)
            self.visitOptionalNode(node.continueExpression)
            if not self.visitBooleanNode(node.condition):
                break
        return self.evaluationContext.context.coreTypes.voidValue

    def visitNamespaceNode(self, node: ParseTreeNamespaceNode):
        assert False

    def visitClassDefinitionNode(self, node: ParseTreeClassDefinitionNode):
        assert False

    def visitStructDefinitionNode(self, node: ParseTreeStructDefinitionNode):
        name = self.visitOptionalSymbolNode(node.nameExpression)

        structType = HIRStructType(name, self.evaluationContext.context.coreTypes, node.sourcePosition)
        self.evaluationContext.context.addEntityWithPendingAnalysis(structType)
        if name is not None:
            self.evaluationContext.environment.setNewSymbolBinding(name, structType, node.sourcePosition)
        if node.isPublic:
            owner = self.evaluationContext.environment.lookupProgramEntityOwner()
            owner.addPublicNamedElement(name, structType, node.sourcePosition)

        structType.addPendingDefinitionBody(self.evaluationContext, node.definitionBody)
        return structType

    def visitEnumDefinitionNode(self, node: ParseTreeEnumDefinitionNode):
        name = self.visitSymbolNode(node.nameExpression)
        baseType = self.evaluationContext.context.coreTypes.dynamicType
        if node.baseTypeExpression:
            baseType = self.visitNodeExpectingType(node.baseTypeExpression)

        enumType = HIREnumType(name, baseType, self.evaluationContext.context.coreTypes, node.sourcePosition)
        self.evaluationContext.environment.setNewSymbolBinding(name, enumType, node.sourcePosition)
        if node.isPublic:
            owner = self.evaluationContext.environment.lookupProgramEntityOwner()
            owner.addPublicNamedElement(name, function, node.sourcePosition)

        valuesDictionary = self.visitDecayedNode(node.valuesExpression)
        if not valuesDictionary.isDictionaryConstant():
            raise RuntimeError(str(node.sourcePosition) + ": Expected a dictionary with the enum values.")

        nextImplicitValue = baseType.getDefaultValue()
        for association in valuesDictionary.elements:
            if not association.key.isSymbolConstant():
                raise RuntimeError(str(node.sourcePosition) + ": Expected symbols for the association names.")

            associationName = association.key.value
            associationValue = nextImplicitValue
            if association.value is not None and not association.value.isNilConstant():
                if not baseType.isSatisfiedByValue(association.value):
                    raise RuntimeError(str(node.sourcePosition) + ": association elements must be of type " + str(baseType))
                associationValue = association.value

            enumType.addElementAt(HIRConstantEnum(associationName, associationValue, enumType, association.key.sourcePosition), association.sourcePosition)
            nextImplicitValue = associationValue.plusOne()

        return enumType

    def visitFieldDefinitionNode(self, node: ParseTreeFieldDefinitionNode):
        name = self.visitOptionalSymbolNode(node.nameExpression)
        type = self.evaluationContext.context.coreTypes.dynamicType
        if node.typeExpression is not None:
            type = self.visitNodeExpectingType(node.typeExpression)

        owner = self.evaluationContext.environment.lookupProgramEntityOwner()
        field = HIRField(name, type, node.isPublic, self.evaluationContext.context.coreTypes, node.sourcePosition)
        owner.addField(field)
        return field

    def visitLoadFileOnceNode(self, node: ParseTreeLoadFileOnceNode):
        relativePath = self.visitNodeWithExpectedType(node.pathExpression, self.evaluationContext.context.coreTypes.stringType).value
        directoryValue = self.evaluationContext.environment.lookSymbolRecursively('__FileDir__')
        if directoryValue is None:
            raise RuntimeError(str(node.sourcePosition()) + ": loadFileOnce: is not in a file.")

        # Compute the file path.
        assert directoryValue.isStringConstant()
        directory = directoryValue.value
        path = os.path.join(directory, relativePath)

        # Load the file.
        ast = parseFileNamed(path)
        ParseTreeErrorVisitor().checkPrintErrorsAndRaiseException(ast)

        evaluationContext = self.evaluationContext.context.createTopLevelEvaluationContext(ast.sourcePosition.sourceCode)
        return AnalysisAndEvaluationPass(evaluationContext).visitDecayedNode(ast)
    