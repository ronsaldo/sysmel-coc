from parsetree import *
from hir import *

class AnalysisAndEvaluationPass(ParseTreeVisitor):
    def __init__(self, evaluationContext: HIREvaluationContext):
        super().__init__()
        self.evaluationContext = evaluationContext

    def visitDecayedNode(self, node):
        # TODO: Load the references.
        return self.visitNode(node)

    def visitErrorNode(self, node):
        assert False

    def visitApplicationNode(self, node):
        assert False

    def visitArgumentDefinitionNode(self, node):
        assert False

    def visitAssertNode(self, node):
        assert False

    def visitAssignmentNode(self, node):
        assert False

    def visitAssociationNode(self, node):
        assert False

    def visitBinaryExpressionSequenceNode(self, node):
        assert False

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

    def visitMessageSendNode(self, node):
        assert False

    def visitQuasiQuoteNode(self, node):
        assert False

    def visitQuasiUnquoteNode(self, node):
        assert False

    def visitQuoteNode(self, node):
        assert False

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        result = self.evaluationContext.context.coreTypes.voidValue
        for element in node.elements:
            result = self.visitNode(element)
        return result

    def visitSpliceNode(self, node):
        assert False

    def visitRuntimeErrorNode(self, node):
        assert False

    def visitTupleNode(self, node):
        assert False

    def visitVariableDefinitionNode(self, node):
        assert False

    def visitIfSelectionNode(self, node):
        assert False

    def visitSwitchSelectionNode(self, node):
        assert False

    def visitReturnNode(self, node):
        assert False

    def visitWhileDoNode(self, node):
        assert False

    def visitDoWhileNode(self, node):
        assert False

    def visitNamespaceNode(self, node):
        assert False

    def visitClassDefinitionNode(self, node):
        assert False

    def visitStructDefinitionNode(self, node):
        assert False

    def visitEnumDefinitionNode(self, node):
        assert False

    def visitFieldDefinitionNode(self, node):
        assert False

    def visitLoadFileOnceNode(self, node):
        assert False