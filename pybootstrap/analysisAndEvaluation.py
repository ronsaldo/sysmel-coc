from parsetree import *
from hir import *

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

    def visitNodeExpectingType(self, node, expectedType):
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
        assert False

    def visitApplicationNode(self, node):
        functional = self.visitDecayedNode(node.functional)
        return functional.analyzeAndEvaluateApplicationNode(self, node, functional)

    def visitArgumentDefinitionNode(self, node):
        assert False

    def visitAssertNode(self, node):
        assert False

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        storeValue = self.visitNode(node.store)
        return storeValue.analyzeAndEvaluateAssignment(self, node)

    def visitAssociationNode(self, node):
        assert False

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        expandedMessageSend = node.expandAsMessageSends()
        return self.visitNode(expandedMessageSend)

    def visitFunctionTypeNode(self, node):
        assert False

    def visitFunctionNode(self, node):
        assert False

    def visitMethodNode(self, node):
        assert False

    def visitTemplateNode(self, node):
        assert False

    def visitCascadeMessageNode(self, node):
        assert False

    def visitDictionaryNode(self, node):
        assert False

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        bindingOrNone = self.evaluationContext.environment.lookSymbolRecursively(node.value)
        if bindingOrNone is None:
            raise RuntimeError("%s: %s identifier is not found." % (str(node.sourcePosition), node.value))    
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

    def visitMessageCascadeNode(self, node):
        assert False

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

    def visitRuntimeErrorNode(self, node):
        assert False

    def visitTupleNode(self, node):
        assert False

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

    def visitSwitchSelectionNode(self, node):
        assert False

    def visitReturnNode(self, node: ParseTreeReturnNode):
        assert False

    def visitWhileDoNode(self, node: ParseTreeWhileDoNode):
        while self.visitBooleanNode(node.condition):
            self.visitOptionalNode(node.bodyExpression)
            self.visitOptionalNode(node.continueExpression)
        return self.evaluationContext.context.coreTypes.voidValue

    def visitDoWhileNode(self, node: ParseTreeDoWhileNode):
        while True:
            self.visitOptionalNode(node.bodyExpression)
            self.visitOptionalNode(node.continueExpression)
            if not self.visitBooleanCondition(node.condition):
                break
        return self.evaluationContext.context.coreTypes.voidValue

    def visitNamespaceNode(self, node: ParseTreeNamespaceNode):
        assert False

    def visitClassDefinitionNode(self, node: ParseTreeClassDefinitionNode):
        assert False

    def visitStructDefinitionNode(self, node: ParseTreeStructDefinitionNode):
        assert False

    def visitEnumDefinitionNode(self, node: ParseTreeEnumDefinitionNode):
        assert False

    def visitFieldDefinitionNode(self, node: ParseTreeFieldDefinitionNode):
        assert False

    def visitLoadFileOnceNode(self, node: ParseTreeLoadFileOnceNode):
        assert False