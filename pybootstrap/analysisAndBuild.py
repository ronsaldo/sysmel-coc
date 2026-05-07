from parsetree import *
from hir import *

class AnalysisAndBuildPass(ParseTreeVisitor):
    def __init__(self, builder: HIRBuilder):
        super().__init__()
        self.builder = builder

    def visitDecayedNode(self, node: ParseTreeNode):
        value = self.visitNode(node)
        valueType = value.getType()

        # Load references.
        if valueType.isReferenceType():
            return self.builder.load(valueType.baseType, value, node.sourcePosition)
        return value

    def castValueToExpectedType(self, value: HIRValue, expectedType: HIRType, sourcePosition: SourcePosition):
        if expectedType is None:
            return value

        valueType = value.getType()
        #if valueType.isControlFlowEscapeType():
        #    return value
        if valueType.isDynamicType():
            return self.builder.dynamicUnbox(value, expectedType, sourcePosition)
        #if expectedType.isVoidType() and not value.isVoidValue():
        #    return self.builder.getVoidLiteral(sourcePosition)

        # Undefine to nullable
        if expectedType.isNullableType() and valueType.isUndefinedType():
            return HIRConstantLiteralNilValue(expectedType, sourcePosition)
        
        if expectedType.isDynamicType() and not valueType.hasDirectDynamicCast():
            return self.builder.dynamicBox(value, sourcePosition)

        if not expectedType.isSatisfiedByValue(value):
            raise RuntimeError("%s: expected a value of type %s instead of %s." % (str(sourcePosition), str(expectedType), str(value.getType())))

        return value


    def visitNodeWithExpectedType(self, node: ParseTreeNode, expectedType: HIRType):
        decayedValue = self.visitDecayedNode(node)
        return self.castValueToExpectedType(decayedValue, expectedType, node.sourcePosition)

    def visitNodeExpectingType(self, node):
        value = self.visitDecayedNode(node)
        if not value.isType():
            raise RuntimeError(str(node.sourcePosition) +  " Error: Expected a type instead of  " + str(value))
        return value

    def visitBooleanCondition(self, node: ParseTreeNode):
        return self.visitNodeWithExpectedType(node, self.builder.context.coreTypes.booleanType)

    def evaluateSymbolNode(self, symbolNode: ParseTreeNode):
        symbolValue = self.visitDecayedNode(symbolNode)
        if not symbolValue.isSymbolConstant():
            raise RuntimeError("%s: expected a symbol value." % str(symbolNode.sourcePosition))
        return symbolValue.value

    def evaluateOptionalSymbolNode(self, symbolNode: ParseTreeNode):
        if symbolNode is None:
            return None
        return self.evaluateSymbolNode(symbolNode)
    
    def evaluateTypeExpression(self, symbolNode: ParseTreeNode):
        typeValue = self.visitDecayedNode(symbolNode)
        if not typeValue.isType():
            raise RuntimeError("%s: expected a type expression." % str(symbolNode.sourcePosition))
        return typeValue

    def visitErrorNode(self, node):
        raise RuntimeError("%s: %s" % (str(node.sourcePosition), node.message))

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        functional = self.visitDecayedNode(node.functional)
        return functional.analyzeAndBuildApplicationNode(self, node, functional)

    def visitArgumentDefinitionNode(self, node: ParseTreeArgumentDefinitionNode):
        argumentType = self.builder.context.coreTypes.dynamicType
        if node.typeExpression is not None:
            argumentType = self.visitNodeExpectingType(node.typeExpression)

        argument = HIRArgument(argumentType, node.name)
        argument.isSelf = node.isSelf
        return argument

    def visitAssertNode(self, node: ParseTreeAssertNode):
        condition = self.visitBooleanCondition(node.expression)
        message = HIRConstantLiteralStringValue(node.sourcePosition.getStringValue(), self.builder.context.coreTypes.stringType, node.sourcePosition)
        return self.builder.assertCondition(condition, message, node.sourcePosition)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        storeValue = self.visitNode(node.store)
        return storeValue.analyzeAndBuildAssignment(self, node)

    def visitAssociationNode(self, node: ParseTreeAssociationNode):
        key = self.visitDecayedNode(node.key)
        value = self.builder.context.coreTypes.nilValue
        if node.value is not None:
            value = self.visitDecayedNode(node.value)

        if key.isType() and value.isType():
            return self.builder.context.getOrCreateAssociationType(key, value)

        keyType = key.getType()
        valueType = value.getType()
        associationType = self.builder.context.getOrCreateAssociationType(keyType, valueType)
        return self.builder.makeAssociation(key, value, associationType, node.sourcePosition)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        return self.visitNode(node.expandAsMessageSends())

    def visitFunctionTypeNode(self, node: ParseTreeFunctionTypeNode):
        oldEnvironment = self.builder.environment
        analysisEnvironment = HIRDependentFunctionTypeAnalysisEnvironment(oldEnvironment)
        self.builder.environment = analysisEnvironment

        argumentDefinitions = []
        for argument in node.argumentDefinitions:
            argumentDefinitions.append(self.visitNode(argument))

        resultType = self.builder.context.coreTypes.dynamicType
        if node.resultTypeExpression is not None:
            resultType = self.visitNodeExpectingType(node.resultTypeExpression)

        functionType = HIRDependentFunctionType(analysisEnvironment.captureList, argumentDefinitions, resultType, self.builder.context.coreTypes, node.sourcePosition)
        self.builder.environment = oldEnvironment
        return functionType

    def visitFunctionNode(self, node: ParseTreeFunctionNode):
        name = self.evaluateOptionalSymbolNode(node.nameExpression)

        dependentFunctionType = self.visitNode(node.functionType)

        function = HIRFunction(name, dependentFunctionType, node.sourcePosition)
        function.definitionBody = node.body
        function.definitionContext = self.builder.context
        function.definitionEnvironment = self.builder.environment
        function.ensureAnalysis()
        
        functionValue = function
        if len(function.captures) != 0:
            captureValues = list(map(lambda capture: capture.sourceValue, function.captures))
            functionValue = self.builder.makeClosure(function, captureValues, function.getType(), node.sourcePosition)
        
        if name is not None:
           self.builder.environment.setNewSymbolBinding(name, functionValue, node.sourcePosition)

        return functionValue

    def visitCascadeMessageNode(self, node):
        assert False

    def visitDictionaryNode(self, node):
        assert False

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        bindingOrNone = self.builder.environment.lookSymbolRecursively(node.value)
        if bindingOrNone is None:
            raise RuntimeError("%s: #%s identifier is not found." % (str(node.sourcePosition), node.value))    

        return bindingOrNone.analyzeAndBuildIdentifierReferenceNode(self, node)

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        oldLexicalEnvironment = self.builder.environment
        childEnvironment = HIRLexicalEnvironment(oldLexicalEnvironment)

        self.builder.environment = childEnvironment

        result = self.visitNode(node.body)

        self.builder.environment = oldLexicalEnvironment
        return result

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        return self.builder.characterConstant(node.value, self.builder.context.coreTypes.characterType, node.sourcePosition)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        return self.builder.floatConstant(node.value, self.builder.context.coreTypes.floatType, node.sourcePosition)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        return self.builder.integerConstant(node.value, self.builder.context.coreTypes.integerType, node.sourcePosition)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        return self.builder.symbolConstant(node.value, self.builder.context.coreTypes.symbolType, node.sourcePosition)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        return self.builder.stringConstant(node.value, self.builder.context.coreTypes.stringType, node.sourcePosition)

    def visitLiteralValueNode(self, node: ParseTreeLiteralValueNode):
        return node.value

    def visitMessageCascadeNode(self, node: ParseTreeMessageCascadeNode):
        receiver = self.visitNode(node.receiver)
        receiverValueNode = ParseTreeLiteralValueNode(node.receiver, receiver)

        result = receiver
        for cascadedMessage in node.messages:
            cascadedMessageWithReceiver = cascadedMessage.asMessageSendWithReceiver(receiverValueNode)
            result = self.visitNode(cascadedMessageWithReceiver)
        return result

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        receiver = self.visitNode(node.receiver)
        return receiver.analyzeAndBuildMessageSendNode(self, node, receiver)

    def visitQuasiQuoteNode(self, node):
        assert False

    def visitQuasiUnquoteNode(self, node: ParseTreeQuasiUnquoteNode):
        raise RuntimeError("%s: invalid location for a quasi unquote." % str(node.sourcePosition))

    def visitSpliceNode(self, node):
        raise RuntimeError("%s: invalid location for a splice." % str(node.sourcePosition))

    def visitQuoteNode(self, node):
        return HIRConstantLiteralParseTree(node.term, self.builder.context.coreTypes.parseTreeNodeType, node.sourcePosition)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        result = self.builder.context.coreTypes.voidValue
        for element in node.elements:
            result = self.visitNode(element)
        return result

    def visitRuntimeErrorNode(self, node: ParseTreeRuntimeErrorNode):
        message = self.visitNodeWithExpectedType(node.messageExpression, self.builder.context.coreTypes.stringType)
        return self.builder.runtimeError(message, node.sourcePosition)

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
            return self.builder.context.getOrCreateTupleType(tupleElements)
        
        tupleType = self.builder.context.getOrCreateTupleType(tupleTypes)
        return self.builder.makeTuple(tupleElements, tupleType, node.sourcePosition )

    def visitVariableDefinitionNode(self, node: ParseTreeVariableDefinitionNode):
        name = self.evaluateOptionalSymbolNode(node.nameExpression)

        typeValue = None
        if node.typeExpression is not None:
            typeValue = self.evaluateTypeExpression(node.typeExpression)

        initialValue = self.builder.context.coreTypes.voidValue
        if node.initialValue is not None:
            initialValue = self.visitNodeWithExpectedType(node.initialValue, typeValue)

        if node.isMutable:
            assert self.builder.allocaBuilder is not None
            valueType = typeValue
            if valueType is None:
                valueType = initialValue.getType()

            referenceType = self.builder.context.getOrCreateReferenceType(valueType)
            
            alloca = self.builder.allocaBuilder.alloca(valueType, referenceType, node.sourcePosition)
            self.builder.store(alloca, initialValue, node.sourcePosition)

            if name is not None:
                self.builder.environment.setNewSymbolBinding(name, alloca, node.sourcePosition)
            return alloca
        else:
            if name is not None:
                self.builder.environment.setNewSymbolBinding(name, initialValue, node.sourcePosition)
            return initialValue

    def visitIfSelectionNode(self, node: ParseTreeIfSelectionNode):
        trueDestination = HIRBasicBlock("ifTrue", node.sourcePosition)
        falseDestination = HIRBasicBlock("ifFalse", node.sourcePosition)
        mergeDestination = HIRBasicBlock("ifMerge", node.sourcePosition)

        conditionValue = self.visitBooleanCondition(node.condition)
        self.builder.conditionalBranch(conditionValue, trueDestination, falseDestination, node.sourcePosition)

        # True destination
        self.builder.function.addBasicBlock(trueDestination)
        trueBuildPass = AnalysisAndBuildPass(self.builder.copyWithBasicBlock(trueDestination))

        trueResult = None
        if node.trueExpression is not None:
            trueResult = trueBuildPass.visitDecayedNode(node.trueExpression)

        # False destination
        self.builder.function.addBasicBlock(falseDestination)
        falseBuildPass = AnalysisAndBuildPass(self.builder.copyWithBasicBlock(falseDestination))

        falseResult = None
        if node.falseExpression is not None:
            falseResult = falseBuildPass.visitDecayedNode(node.falseExpression)

        # Merge
        self.builder.function.addBasicBlock(mergeDestination)
        self.builder.basicBlock = mergeDestination

        mergedResult = self.builder.context.coreTypes.voidValue
        if trueResult is not None and falseResult is not None:
            trueType = trueResult.getType()
            falseType = falseResult.getType()
            if not trueType.isVoidType() and trueType == falseType:
                phiNode = self.builder.phi(trueType, node.sourcePosition)
                trueBuildPass.builder.phiSource(phiNode, trueResult, node.sourcePosition)
                falseBuildPass.builder.phiSource(phiNode, falseResult, node.sourcePosition)
                mergedResult = phiNode
        
        trueBuildPass.builder.branch(mergeDestination, node.sourcePosition)
        falseBuildPass.builder.branch(mergeDestination, node.sourcePosition)

        return mergedResult

    def visitSwitchSelectionNode(self, node: ParseTreeSwitchSelectionNode):
        assert False

    def visitReturnNode(self, node: ParseTreeReturnNode):
        assert False

    def visitWhileDoNode(self, node: ParseTreeWhileDoNode):
        loopHeader = HIRBasicBlock("loopHeader", node.sourcePosition)
        loopBody = HIRBasicBlock("loopBody", node.sourcePosition)
        loopContinueWith = HIRBasicBlock("loopContinueWith", node.sourcePosition)
        loopMerge = HIRBasicBlock("loopMerge", node.sourcePosition)

        # Loop header
        self.builder.branch(loopHeader, node.sourcePosition)
        self.builder.basicBlock = loopHeader
        self.builder.function.addBasicBlock(loopHeader)

        conditionValue = self.visitBooleanCondition(node.condition)
        self.builder.conditionalBranch(conditionValue, loopBody, loopMerge, node.sourcePosition)

        # Loop body.
        self.builder.basicBlock = loopBody
        self.builder.function.addBasicBlock(loopBody)

        if node.bodyExpression is not None:
            self.visitNode(node.bodyExpression)

        if not self.builder.isLastTerminator():
            self.builder.branch(loopContinueWith, node.sourcePosition)

        # Loop continue with
        self.builder.basicBlock = loopContinueWith
        self.builder.function.addBasicBlock(loopContinueWith)
        
        if node.continueExpression is not None:
            self.visitNode(node.continueExpression)

        if not self.builder.isLastTerminator():
            self.builder.branch(loopHeader, node.sourcePosition)

        # Loop merge.
        self.builder.basicBlock = loopMerge
        self.builder.function.addBasicBlock(loopMerge)

        return self.builder.context.coreTypes.voidValue

    def visitDoWhileNode(self, node: ParseTreeDoWhileNode):
        loopHeader = HIRBasicBlock("loopHeader", node.sourcePosition)
        loopContinueWith = HIRBasicBlock("loopContinueWith", node.sourcePosition)
        loopCondition = HIRBasicBlock("loopCondition", node.sourcePosition)
        loopMerge = HIRBasicBlock("loopMerge", node.sourcePosition)

        self.builder.branch(loopHeader, node.sourcePosition)

        # Loop header
        self.builder.basicBlock = loopHeader
        self.builder.function.addBasicBlock(loopHeader)

        if node.bodyExpression is not None:
            self.visitNode(node.bodyExpression)

        if not self.builder.isLastTerminator():
            self.builder.branch(loopContinueWith, node.sourcePosition)

        # Loop continue with
        self.builder.basicBlock = loopContinueWith
        self.builder.function.addBasicBlock(loopContinueWith)

        if node.continueExpression is not None:
            self.visitNode(node.continueExpression)

        if not self.builder.isLastTerminator():
            self.builder.branch(loopCondition, node.sourcePosition)

        # Loop condition
        self.builder.basicBlock = loopCondition
        self.builder.function.addBasicBlock(loopCondition)

        conditionValue = self.visitBooleanCondition(node.condition)
        self.builder.conditionalBranch(conditionValue, loopHeader, loopMerge, node.sourcePosition)

        # Loop merge
        self.builder.basicBlock = loopMerge
        self.builder.function.addBasicBlock(loopMerge)

        return self.builder.context.coreTypes.voidValue

    def visitNamespaceNode(self, node):
        raise RuntimeError("%s: unsupported location for parse tree node." % str(node.sourcePosition))

    def visitClassDefinitionNode(self, node):
        raise RuntimeError("%s: unsupported location for parse tree node." % str(node.sourcePosition))

    def visitStructDefinitionNode(self, node):
        raise RuntimeError("%s: unsupported location for parse tree node." % str(node.sourcePosition))

    def visitEnumDefinitionNode(self, node):
        raise RuntimeError("%s: unsupported location for parse tree node." % str(node.sourcePosition))

    def visitFieldDefinitionNode(self, node):
        raise RuntimeError("%s: unsupported location for parse tree node." % str(node.sourcePosition))

    def visitLoadFileOnceNode(self, node):
        raise RuntimeError("%s: unsupported location for parse tree node." % str(node.sourcePosition))