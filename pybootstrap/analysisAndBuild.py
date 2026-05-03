from parsetree import *
from hir import *

class AnalysisAndBuildPass(ParseTreeVisitor):
    def __init__(self, builder: HIRBuilder):
        super().__init__()
        self.builder = builder

    def visitDecayedNode(self, node: ParseTreeNode):
        value = self.visitNode(node)
        # TODO: Load references.
        return value
    
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

    def visitIdentifierReferenceNode(self, node):
        assert False

    def visitLexicalBlockNode(self, node):
        assert False

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
        result = self.builder.context.coreTypes.voidValue
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