from abc import ABC, abstractmethod

import os.path
import sys

class SourceCode:
    def __init__(self, directory: str | None, name: str, language: str, text: bytes) -> None:
        self.directory = directory
        self.name = name
        self.language = language
        self.text = text

    def __str__(self) -> str:
        if self.directory is None:
            return self.name
        return os.path.join(self.directory, self.name)

class SourcePosition:
    def __init__(self, sourceCode: SourceCode, startIndex: int, endIndex: int, startLine: int, startColumn: int, endLine: int, endColumn: int) -> None:
        self.sourceCode = sourceCode
        self.startIndex = startIndex
        self.endIndex = endIndex
        self.startLine = startLine
        self.startColumn = startColumn
        self.endLine = endLine
        self.endColumn = endColumn

    def getValue(self) -> bytes:
        return self.sourceCode.text[self.startIndex : self.endIndex]
    
    def getStringValue(self) -> str:
        return self.getValue().decode('utf-8')
    
    def until(self, endSourcePosition):
        return SourcePosition(self.sourceCode,
                self.startIndex, endSourcePosition.startIndex,
                self.startLine, self.startColumn,
                endSourcePosition.startLine, endSourcePosition.startColumn)

    def to(self, endSourcePosition):
        return SourcePosition(self.sourceCode,
                self.startIndex, endSourcePosition.endIndex,
                self.startLine, self.startColumn,
                endSourcePosition.endLine, endSourcePosition.endColumn)

    def __str__(self) -> str:
        return '%s:%d.%d-%d.%d' % (self.sourceCode, self.startLine, self.startColumn, self.endLine, self.endColumn)

class EmptySourcePosition:
    Singleton = None

    @classmethod
    def getSingleton(cls):
        if cls.Singleton is None:
            cls.Singleton = cls()
        return cls.Singleton

    def __str__(self) -> str:
        return '<no position>'
    

class ParseTreeVisitor(ABC):
    def visitNode(self, node):
        return node.accept(self)

    def visitOptionalNode(self, node):
        if node is not None:
            return self.visitNode(node)
        return None

    def visitNodes(self, nodes):
        for node in nodes:
            self.visitNode(node)

    def transformNodes(self, nodes):
        transformed = []
        for node in nodes:
            transformed.append(self.visitNode(node))
        return transformed

    @abstractmethod
    def visitErrorNode(self, node):
        pass

    @abstractmethod
    def visitApplicationNode(self, node):
        pass

    @abstractmethod
    def visitArgumentDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitAssertNode(self, node):
        pass

    @abstractmethod
    def visitAssignmentNode(self, node):
        pass

    @abstractmethod
    def visitAssociationNode(self, node):
        pass

    @abstractmethod
    def visitBinaryExpressionSequenceNode(self, node):
        pass

    @abstractmethod
    def visitFunctionTypeNode(self, node):
        pass

    @abstractmethod
    def visitFunctionNode(self, node):
        pass

    @abstractmethod
    def visitCascadeMessageNode(self, node):
        pass

    @abstractmethod
    def visitDictionaryNode(self, node):
        pass

    @abstractmethod
    def visitIdentifierReferenceNode(self, node):
        pass

    @abstractmethod
    def visitLexicalBlockNode(self, node):
        pass

    @abstractmethod
    def visitLiteralCharacterNode(self, node):
        pass

    @abstractmethod
    def visitLiteralFloatNode(self, node):
        pass

    @abstractmethod
    def visitLiteralIntegerNode(self, node):
        pass

    @abstractmethod
    def visitLiteralSymbolNode(self, node):
        pass

    @abstractmethod
    def visitLiteralStringNode(self, node):
        pass

    @abstractmethod
    def visitLiteralValueNode(self, node):
        pass

    @abstractmethod
    def visitMessageCascadeNode(self, node):
        pass

    @abstractmethod
    def visitMessageSendNode(self, node):
        pass

    @abstractmethod
    def visitQuasiQuoteNode(self, node):
        pass

    @abstractmethod
    def visitQuasiUnquoteNode(self, node):
        pass

    @abstractmethod
    def visitQuoteNode(self, node):
        pass

    @abstractmethod
    def visitSequenceNode(self, node):
        pass

    @abstractmethod
    def visitSpliceNode(self, node):
        pass

    @abstractmethod
    def visitRuntimeErrorNode(self, node):
        pass

    @abstractmethod
    def visitTupleNode(self, node):
        pass

    @abstractmethod
    def visitVariableDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitIfSelectionNode(self, node):
        pass

    @abstractmethod
    def visitSwitchSelectionNode(self, node):
        pass

    @abstractmethod
    def visitReturnNode(self, node):
        pass

    @abstractmethod
    def visitWhileDoNode(self, node):
        pass

    @abstractmethod
    def visitDoWhileNode(self, node):
        pass

    @abstractmethod
    def visitNamespaceNode(self, node):
        pass

    @abstractmethod
    def visitClassDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitStructDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitEnumDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitFieldDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitLoadFileOnceNode(self, node):
        pass

class ParseTreeNode(ABC):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

    @abstractmethod
    def accept(self, visitor: ParseTreeVisitor):
        pass

    def decayToExpectedType(self, targetType):
        return self

    def isParseTreeNode(self):
        return True

    def asMessageSendCascadeReceiverAndFirstMessage(self):
        return self, None
    
    def isApplicationNode(self) -> bool:
        return False

    def isAssertNode(self) -> bool:
        return False

    def isAssignmentNode(self) -> bool:
        return False

    def isAssociationNode(self) -> bool:
        return False

    def isArgumentDefinitionNode(self) -> bool:
        return False
    
    def isBinaryExpressionSequenceNode(self) -> bool:
        return False

    def isBindableNameNode(self) -> bool:
        return False

    def isFunctionTypeNode(self) -> bool:
        return False

    def isFunctionNode(self) -> bool:
        return False

    def isDictionaryNode(self) -> bool:
        return False

    def isErrorNode(self) -> bool:
        return False

    def isTemplateNode(self) -> bool:
        return False

    def isIdentifierReferenceNode(self) -> bool:
        return False

    def isLexicalBlockNode(self) -> bool:
        return False

    def isLiteralNode(self) -> bool:
        return False

    def isLiteralCharacterNode(self) -> bool:
        return False

    def isLiteralFloatNode(self) -> bool:
        return False

    def isLiteralIntegerNode(self) -> bool:
        return False

    def isLiteralStringNode(self) -> bool:
        return False

    def isLiteralSymbolNode(self) -> bool:
        return False

    def isLiteralValueNode(self) -> bool:
        return False

    def isMessageSendNode(self) -> bool:
        return False

    def isQuasiQuoteNode(self) -> bool:
        return False

    def isQuasiUnquoteNode(self) -> bool:
        return False

    def isQuoteNode(self) -> bool:
        return False
    
    def isSpliceNode(self) -> bool:
        return False
    
    def isSequenceNode(self) -> bool:
        return False

    def isTupleNode(self) -> bool:
        return False

    def isIfSelectionNode(self) -> bool:
        return False

    def isSwithcSelectionNode(self) -> bool:
        return False

    def isWhileDoNode(self) -> bool:
        return False

    def isDoWhileNode(self) -> bool:
        return False

    def isClassDefinitionNode(self) -> bool:
        return False

    def isStructDefinitionNode(self) -> bool:
        return False

    def isEnumDefinitionNode(self) -> bool:
        return False
    
    def isLoadFileOnceNode(self) -> bool:
        return False

class ParseTreeErrorNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, message: str, innerNodes: list[ParseTreeNode] = ()) -> None:
        super().__init__(sourcePosition)
        self.message = message
        self.innerNodes = innerNodes
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitErrorNode(self)
    
    def isErrorNode(self) -> bool:
        return True

class ParseTreeApplicationNode(ParseTreeNode):
    Normal = 0
    Bracket = 1
    CurlyBracket = 2
    ByteArrayStart = 3
    Block = 4
    Dictionary = 5

    def __init__(self, sourcePosition: SourcePosition, functional: ParseTreeNode, arguments: list[ParseTreeNode], kind) -> None:
        super().__init__(sourcePosition)
        self.functional = functional
        self.arguments = arguments
        self.kind = kind

    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitApplicationNode(self)
    
    def parseAsArgumentDefinition(self):
        if not self.functional.isIdentifierReferenceNode() or len(self.arguments) != 1:
            raise RuntimeError("Expected an argument definition expression.")

        name : str = self.functional.value
        if name.endswith(':'):
            name = name[0:-1]

        typeExpression = self.arguments[0]
        return ParseTreeArgumentDefinitionNode(self.sourcePosition, name, typeExpression)
    
    def isApplicationNode(self) -> bool:
        return True

class ParseTreeAssertNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, expression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.expression = expression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitAssertNode(self)

    def isAssertNode(self) -> bool:
        return True
    
class ParseTreeAssignmentNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, store: ParseTreeNode, value: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.store = store
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitAssignmentNode(self)

    def isAssignmentNode(self) -> bool:
        return True


class ParseTreeAssociationNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, key: ParseTreeNode, value: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.key = key
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitAssociationNode(self)

    def isAssociationNode(self) -> bool:
        return True
    
class ParseTreeBinaryExpressionSequenceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitBinaryExpressionSequenceNode(self)
    
    def isBinaryExpressionSequenceNode(self) -> bool:
        return True
    
    def asMessageSendCascadeReceiverAndFirstMessage(self):
        assert len(self.elements) >= 3
        if len(self.elements) == 3:
            return self.elements[0], ParseTreeCascadedMessageNode(self.sourcePosition, self.elements[1], [self.elements[2]])
        
        receiverSequence = ParseTreeBinaryExpressionSequenceNode(self.sourcePosition, self.elements[:-2])
        return receiverSequence, ParseTreeCascadedMessageNode(self.sourcePosition, self.elements[-2], [self.elements[-1]])
    
    def expandAsMessageSends(self):
        elementCount = len(self.elements)
        assert elementCount >= 1
        # TODO: Use an operator precedence parser
        previous = self.elements[0]

        i = 1
        while i < elementCount:
            operator = self.elements[i]
            operand = self.elements[i + 1]
            previous = ParseTreeMessageSendNode(operator.sourcePosition.until(operand.sourcePosition),
                                                previous, operator, [operand])
            i += 2

        return previous

class ParseTreeArgumentDefinitionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, name: str, typeExpression: ParseTreeNode, isSelf: bool = False) -> None:
        super().__init__(sourcePosition)
        self.name = name
        self.typeExpression = typeExpression
        self.isSelf = isSelf
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitArgumentDefinitionNode(self)

    def isArgumentDefinitionNode(self) -> bool:
        return True

class ParseTreeFunctionTypeNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, argumentDefinitions: list[ParseTreeNode], resultTypeExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.argumentDefinitions = argumentDefinitions
        self.resultTypeExpression = resultTypeExpression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitFunctionTypeNode(self)

    def isFunctionTypeNode(self) -> bool:
        return True    

class ParseTreeFunctionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, functionType: ParseTreeFunctionTypeNode, body: ParseTreeNode, isPublic: bool) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.functionType = functionType
        self.body = body
        self.isPublic = isPublic
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitFunctionNode(self)

    def isFunctionNode(self) -> bool:
        return True
    
class ParseTreeCascadedMessageNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, selector: ParseTreeNode, arguments: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.selector = selector
        self.arguments = arguments
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitCascadeMessageNode(self)    
    
    def isCascadeMessageNode(self) -> bool:
        return True

    def asMessageSendWithReceiver(self, receiver):
        return ParseTreeMessageSendNode(self.sourcePosition, receiver, self.selector, self.arguments)

class ParseTreeDictionaryNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitDictionaryNode(self)
    
    def isDictionaryNode(self) -> bool:
        return True
    
    
class ParseTreeIdentifierReferenceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, value: str) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitIdentifierReferenceNode(self)

    def parseAsArgumentDefinition(self):
        return ParseTreeArgumentDefinitionNode(self.sourcePosition, self.value, None)

    def isIdentifierReferenceNode(self) -> bool:
        return True
    
class ParseTreeLexicalBlockNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, body: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.body = body
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLexicalBlockNode(self)

    def isLexicalBlockNode(self) -> bool:
        return True
    
class ParseTreeLiteralNode(ParseTreeNode):
    def isLiteralNode(self) -> bool:
        return True

class ParseTreeLiteralCharacterNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: int) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralCharacterNode(self)

    def isLiteralCharacterNode(self) -> bool:
        return True

class ParseTreeLiteralFloatNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: float) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralFloatNode(self)

    def isLiteralFloatNode(self) -> bool:
        return True
        
class ParseTreeLiteralIntegerNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: int) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralIntegerNode(self)

    def isLiteralIntegerNode(self) -> bool:
        return True
    
class ParseTreeLiteralStringNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: str) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralStringNode(self)    

    def isLiteralStringNode(self) -> bool:
        return True
    
class ParseTreeLiteralSymbolNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: str) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralSymbolNode(self)

    def isLiteralSymbolNode(self) -> bool:
        return True
        
class ParseTreeLiteralValueNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralValueNode(self)

    def isLiteralValueNode(self) -> bool:
        return True
    
class ParseTreeMessageCascadeNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, receiver: ParseTreeNode, messages: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.receiver = receiver
        self.messages = messages
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitMessageCascadeNode(self)    

    def isMessageCascadeNode(self) -> bool:
        return True
    
class ParseTreeMessageSendNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, receiver: ParseTreeNode, selector: ParseTreeNode, arguments: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.receiver = receiver
        self.selector = selector
        self.arguments = arguments
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitMessageSendNode(self)    

    def isMessageSendNode(self) -> bool:
        return True
    
    def asMessageSendCascadeReceiverAndFirstMessage(self):
        return self.receiver, ParseTreeCascadedMessageNode(self.sourcePosition, self.selector, self.arguments)

class ParseTreeQuasiQuoteNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitQuasiQuoteNode(self)

    def isQuasiQuoteNode(self) -> bool:
        return True
    
class ParseTreeQuasiUnquoteNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitQuasiUnquoteNode(self)

    def isQuasiUnquoteNode(self) -> bool:
        return True

class ParseTreeQuoteNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitQuoteNode(self)

    def isQuoteNode(self) -> bool:
        return True
    
class ParseTreeRuntimeErrorNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, messageExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.messageExpression = messageExpression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitRuntimeErrorNode(self)

    def isRuntimeErrorNode(self) -> bool:
        return True
    
class ParseTreeSequenceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitSequenceNode(self)

    def isSequenceNode(self) -> bool:
        return True
    
class ParseTreeSpliceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitSpliceNode(self)

    def isSpliceNode(self) -> bool:
        return True

class ParseTreeTupleNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitTupleNode(self)
    
    def isTupleNode(self) -> bool:
        return True
    

class ParseTreeVariableDefinitionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, typeExpression: ParseTreeNode, initialValue: ParseTreeNode, isMutable: bool) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.typeExpression = typeExpression
        self.initialValue = initialValue
        self.isMutable = isMutable
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitVariableDefinitionNode(self)
    
    def isVariableDefinitionNode(self) -> bool:
        return True
    
class ParseTreeIfSelectionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, condition: ParseTreeNode, trueExpression: ParseTreeNode, falseExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.condition = condition
        self.trueExpression = trueExpression
        self.falseExpression = falseExpression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitIfSelectionNode(self)
    
    def isIfSelectionNode(self) -> bool:
        return True

class ParseTreeSwitchSelectionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, valueExpression: ParseTreeNode, cases: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.valueExpression = valueExpression
        self.cases = cases
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitSwitchSelectionNode(self)
    
    def isSwitchSelectionNode(self) -> bool:
        return True

class ParseTreeReturnNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, valueExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.valueExpression = valueExpression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitReturnNode(self)
    
    def isReturnNode(self) -> bool:
        return True

class ParseTreeWhileDoNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, condition: ParseTreeNode, bodyExpression: ParseTreeNode, continueExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.condition = condition
        self.bodyExpression = bodyExpression
        self.continueExpression = continueExpression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitWhileDoNode(self)
    
    def isWhileDoNode(self) -> bool:
        return True

class ParseTreeDoWhileNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, bodyExpression: ParseTreeNode, continueExpression: ParseTreeNode, condition: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.bodyExpression = bodyExpression
        self.continueExpression = continueExpression
        self.condition = condition
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitDoWhileNode(self)
    
    def isDoWhileNode(self) -> bool:
        return True

    
class ParseTreeNamespaceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, definitionBody: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.definitionBody = definitionBody
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitNamespaceNode(self)
    
    def isNamespaceNode(self) -> bool:
        return True

class ParseTreeFieldDefinitionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, typeExpression: ParseTreeNode, isPublic: bool) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.typeExpression = typeExpression
        self.isPublic = isPublic
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitFieldDefinitionNode(self)
    
    def isFieldDefinitionNode(self) -> bool:
        return True
        
class ParseTreeClassDefinitionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, superclassExpression: ParseTreeNode, definitionBody: ParseTreeNode, isPublic: bool) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.superclassExpression = superclassExpression
        self.definitionBody = definitionBody
        self.isPublic = isPublic
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitClassDefinitionNode(self)
    
    def isClassDefinitionNode(self) -> bool:
        return True
    
class ParseTreeStructDefinitionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, definitionBody: ParseTreeNode, isPublic: bool) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.definitionBody = definitionBody
        self.isPublic = isPublic
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitStructDefinitionNode(self)
    
    def isStructDefinitionNode(self) -> bool:
        return True
    
class ParseTreeEnumDefinitionNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ParseTreeNode, baseTypeExpression: ParseTreeNode, valuesExpression: ParseTreeNode, isPublic: bool) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.baseTypeExpression = baseTypeExpression
        self.valuesExpression = valuesExpression
        self.isPublic = isPublic
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitEnumDefinitionNode(self)
    
    def isEnumDefinitionNode(self) -> bool:
        return True
    
class ParseTreeLoadFileOnceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, pathExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.pathExpression = pathExpression
        
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLoadFileOnceNode(self)
    
    def isLoadFileOnceNode(self) -> bool:
        return True
    

class ParseTreeSequentialVisitor(ParseTreeVisitor):
    def visitErrorNode(self, node: ParseTreeErrorNode):
        self.visitNodes(node.innerNodes)

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        self.visitNode(node.functional)
        self.visitNodes(node.arguments)

    def visitArgumentDefinitionNode(self, node: ParseTreeArgumentDefinitionNode):
        self.visitOptionalNode(node.typeExpression)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        self.visitNode(node.store)
        self.visitNode(node.value)

    def visitAssertNode(self, node: ParseTreeAssertNode):
        self.visitNode(node.expression)

    def visitAssociationNode(self, node: ParseTreeAssociationNode):
        self.visitNode(node.key)
        self.visitOptionalNode(node.value)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        self.visitNodes(node.elements)

    def visitFunctionTypeNode(self, node: ParseTreeFunctionTypeNode):
        self.visitNodes(node.argumentDefinitions)
        self.visitOptionalNode(node.resultTypeExpression)

    def visitFunctionNode(self, node: ParseTreeFunctionNode):
        self.visitNode(node.functionType)
        self.visitNode(node.body)

    def visitCascadeMessageNode(self, node: ParseTreeCascadedMessageNode):
        self.visitNode(node.selector)
        self.visitNodes(node.arguments)

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        self.visitNodes(node.elements)

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        pass

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        self.visitNode(node.body)

    def visitLiteralNode(self, node: ParseTreeLiteralNode):
        pass

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        self.visitLiteralNode(node)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        self.visitLiteralNode(node)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        self.visitLiteralNode(node)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        self.visitLiteralNode(node)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        self.visitLiteralNode(node)

    def visitLiteralValueNode(self, node: ParseTreeLiteralValueNode):
        self.visitLiteralNode(node)

    def visitMessageCascadeNode(self, node: ParseTreeMessageCascadeNode):
        self.visitNode(node.receiver)
        self.visitNodes(node.messages)

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        self.visitOptionalNode(node.receiver)
        self.visitNode(node.selector)
        self.visitNodes(node.arguments)

    def visitQuoteNode(self, node: ParseTreeQuoteNode):
        self.visitNode(node.term)

    def visitQuasiQuoteNode(self, node: ParseTreeQuasiQuoteNode):
        self.visitNode(node.term)

    def visitQuasiUnquoteNode(self, node: ParseTreeQuasiUnquoteNode):
        self.visitNode(node.term)

    def visitRuntimeErrorNode(self, node: ParseTreeRuntimeErrorNode):
        self.visitNode(node.messageExpression)
    
    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        self.visitNodes(node.elements)

    def visitSpliceNode(self, node: ParseTreeSpliceNode):
        self.visitNode(node.term)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        self.visitNodes(node.elements)

    def visitVariableDefinitionNode(self, node: ParseTreeVariableDefinitionNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.typeExpression)
        self.visitOptionalNode(node.initialValue)

    def visitIfSelectionNode(self, node: ParseTreeIfSelectionNode):
        self.visitNode(node.condition)
        self.visitOptionalNode(node.trueExpression)
        self.visitOptionalNode(node.falseExpression)
    
    def visitSwitchSelectionNode(self ,node: ParseTreeSwitchSelectionNode):
        self.visitNode(node.valueExpression)
        self.visitNode(node.cases)

    def visitReturnNode(self ,node: ParseTreeReturnNode):
        self.visitNode(node.valueExpression)

    def visitWhileDoNode(self, node: ParseTreeWhileDoNode):
        self.visitOptionalNode(node.condition)
        self.visitOptionalNode(node.bodyExpression)
        self.visitOptionalNode(node.continueExpression)

    def visitDoWhileNode(self, node: ParseTreeDoWhileNode):
        self.visitOptionalNode(node.bodyExpression)
        self.visitOptionalNode(node.continueExpression)
        self.visitOptionalNode(node.condition)

    def visitNamespaceNode(self, node: ParseTreeNamespaceNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.definitionBody)

    def visitClassDefinitionNode(self, node: ParseTreeClassDefinitionNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.superclassExpression)
        self.visitOptionalNode(node.definitionBody)

    def visitStructDefinitionNode(self, node: ParseTreeStructDefinitionNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.definitionBody)

    def visitEnumDefinitionNode(self, node: ParseTreeEnumDefinitionNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.baseTypeExpression)
        self.visitOptionalNode(node.valuesExpression)

    def visitFieldDefinitionNode(self, node: ParseTreeFieldDefinitionNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.typeExpression)

    def visitLoadFileOnceNode(self, node: ParseTreeLoadFileOnceNode):
        self.visitNode(node.pathExpression)

class ParseTreeErrorVisitor(ParseTreeSequentialVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.errorNodes: list[ParseTreeErrorNode] = []
    
    def visitErrorNode(self, node: ParseTreeErrorNode):
        self.errorNodes.append(node)
        super().visitErrorNode(node)

    def checkAndPrintErrors(self, node: ParseTreeNode):
        self.visitNode(node)
        for errorNode in self.errorNodes:
            sys.stderr.write('%s: %s\n' % (str(errorNode.sourcePosition), errorNode.message))
        return len(self.errorNodes) == 0
    
    def checkPrintErrorsAndRaiseException(self, node):
        self.visitNode(node)
        for errorNode in self.errorNodes:
            sys.stderr.write('%s: %s\n' % (str(errorNode.sourcePosition), errorNode.message))
        if len(self.errorNodes) != 0:
            raise RuntimeError("Parse errors found")
