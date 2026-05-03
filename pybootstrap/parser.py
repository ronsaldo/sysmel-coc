from scanner import Token, TokenKind, scanSourceString, scanFileNamed
from parsetree import *
import copy

C_ESCAPE_TABLE = {
    'r': '\r',
    'n': '\n',
    't': '\t',
}

class ParserState:
    def __init__(self, sourceCode: SourceCode, tokens: list[Token]) -> None:
        self.sourceCode = sourceCode
        self.tokens = tokens
        self.position = 0

    def atEnd(self) -> bool:
        return self.position >= len(self.tokens) or self.peekKind() == TokenKind.END_OF_SOURCE

    def peekKind(self, offset: int = 0) -> TokenKind:
        peekPosition = self.position + offset
        if peekPosition < len(self.tokens):
            return self.tokens[peekPosition].kind
        else:
            return TokenKind.END_OF_SOURCE

    def peek(self, offset: int = 0) -> Token:
        peekPosition = self.position + offset
        if peekPosition < len(self.tokens):
            return self.tokens[peekPosition]
        else:
            return None
        
    def advance(self) -> None:
        assert self.position < len(self.tokens)
        self.position += 1

    def next(self) -> Token:
        token = self.tokens[self.position]
        self.position += 1
        return token

    def expectAddingErrorToNode(self, expectedKind: TokenKind, node: ParseTreeNode) -> ParseTreeNode:
        if self.peekKind() == expectedKind:
            self.advance()
            return node
        
        errorPosition = self.currentSourcePosition()
        errorNode = ParseTreeErrorNode(errorPosition, "Expected token of kind %s." % str(expectedKind))
        return ParseTreeSequenceNode(node.sourcePosition.to(errorPosition), [node, errorNode])

    def currentSourcePosition(self) -> SourcePosition:
        if self.position < len(self.tokens):
            return self.tokens[self.position].sourcePosition

        assert self.tokens[-1].kind == TokenKind.END_OF_SOURCE 
        return self.tokens[-1].sourcePosition

    def previousSourcePosition(self) -> SourcePosition:
        assert self.position > 0
        return self.tokens[self.position - 1].sourcePosition

    def sourcePositionFrom(self, startingPosition: int) -> SourcePosition:
        assert startingPosition < len(self.tokens)
        startSourcePosition = self.tokens[startingPosition].sourcePosition
        if self.position > 0:
            endSourcePosition = self.previousSourcePosition()
            return startSourcePosition.to(endSourcePosition)
        else:
            endSourcePosition = self.currentSourcePosition()
            return startSourcePosition.until(endSourcePosition)
    
    def advanceWithExpectedError(self, message: str):
        if self.peekKind() == TokenKind.ERROR:
            errorToken = self.next()
            return self, ParseTreeErrorNode(errorToken.sourcePosition, errorToken.errorMessage)
        elif self.atEnd():
            return self, ParseTreeErrorNode(self.currentSourcePosition(), message)
        else:
            errorPosition = self.currentSourcePosition()
            self.advance()
            return self, ParseTreeErrorNode(errorPosition, message)
        
    def memento(self):
        return self.position

    def restore(self, memento):
        self.position = memento

def parseCEscapedString(string: str) -> str:
    unescaped = ''
    i = 0
    while i < len(string):
        c = string[i]
        if c == '\\':
            i += 1
            c = string[i]
            c = C_ESCAPE_TABLE.get(c, c)
        unescaped += c
        i += 1
    return unescaped

def parseIntegerConstant(string: str) -> str:
    if b'r' in string:
        radixIndex = string.index(b'r')
    elif b'R' in string:
        radixIndex = string.index(b'R')
    else:
        return int(string)
    
    radix = int(string[0:radixIndex])
    assert radix >= 0
    radixedInteger = int(string[radixIndex + 1:], abs(radix))
    return radixedInteger
    
def parseLiteralInteger(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.NAT
    return state, ParseTreeLiteralIntegerNode(token.sourcePosition, parseIntegerConstant(token.getValue()))

def parseLiteralFloat(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.FLOAT
    return state, ParseTreeLiteralFloatNode(token.sourcePosition, float(token.getValue()))

def parseLiteralString(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.STRING
    return state, ParseTreeLiteralStringNode(token.sourcePosition, parseCEscapedString(token.getStringValue()[1:-1]))

def parseLiteralCharacter(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.CHARACTER
    return state, ParseTreeLiteralCharacterNode(token.sourcePosition, ord(parseCEscapedString(token.getStringValue()[1:-1])[0]))

def parseLiteralSymbol(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.SYMBOL
    symbolValue = token.getStringValue()[1:]
    if symbolValue[0] == '"':
        assert symbolValue[0] == '"' and symbolValue[-1] == '"'
        symbolValue = parseCEscapedString(symbolValue[1:-1])
    return state, ParseTreeLiteralSymbolNode(token.sourcePosition, symbolValue)

def parseLiteral(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.NAT: return parseLiteralInteger(state)
    elif state.peekKind() == TokenKind.FLOAT: return parseLiteralFloat(state)
    elif state.peekKind() == TokenKind.STRING: return parseLiteralString(state)
    elif state.peekKind() == TokenKind.CHARACTER: return parseLiteralCharacter(state)
    elif state.peekKind() == TokenKind.SYMBOL: return parseLiteralSymbol(state)
    else: return state.advanceWithExpectedError('Expected a literal.')

def parseIdentifier(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.IDENTIFIER
    return state, ParseTreeIdentifierReferenceNode(token.sourcePosition, token.getStringValue())

def parseQuote(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUOTE
    state, term = parseUnaryPrefixExpression(state)
    return state, ParseTreeQuoteNode(state.sourcePositionFrom(startPosition), term)

def parseQuasiQuote(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUASI_QUOTE
    state, term = parseUnaryPrefixExpression(state)
    return state, ParseTreeQuasiQuoteNode(state.sourcePositionFrom(startPosition), term)

def parseQuasiUnquote(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUASI_UNQUOTE
    state, term = parseUnaryPrefixExpression(state)
    return state, ParseTreeQuasiUnquoteNode(state.sourcePositionFrom(startPosition), term)

def parseSplice(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.SPLICE
    state, term = parseUnaryPrefixExpression(state)
    return state, ParseTreeSpliceNode(state.sourcePositionFrom(startPosition), term)

def parseTerm(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.IDENTIFIER: return parseIdentifier(state)
    elif state.peekKind() == TokenKind.LEFT_PARENT: return parseParenthesis(state)
    elif state.peekKind() == TokenKind.LEFT_CURLY_BRACKET: return parseBlock(state)
    elif state.peekKind() == TokenKind.DICTIONARY_START: return parseDictionary(state)
    else: return parseLiteral(state)

def parseOptionalParenthesis(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.LEFT_PARENT:
        return parseParenthesis(state)
    else:
        return state, None

def parseNameExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.IDENTIFIER:
        token = state.next()
        return state, ParseTreeLiteralSymbolNode(token.sourcePosition, token.getStringValue())
    else:
        return state, ParseTreeErrorNode(state.currentSourcePosition(), 'Expected a bindable name.')

def parseOptionalBindableNameType(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.LEFT_BRACKET:
        state.advance()
        state, typeExpression  = parseExpression(state)
        typeExpression = state.expectAddingErrorToNode(TokenKind.RIGHT_BRACKET, typeExpression)
        return True, state, typeExpression
    elif state.peekKind() == TokenKind.LEFT_PARENT:
        state.advance()
        state, typeExpression = parseExpression(state)
        typeExpression = state.expectAddingErrorToNode(TokenKind.RIGHT_PARENT, typeExpression)
        return False, state, typeExpression
    return False, state, None

def parseParenthesis(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # (
    startPosition = state.position
    assert state.peekKind() == TokenKind.LEFT_PARENT
    state.advance()

    if isBinaryExpressionOperator(state.peekKind()) and state.peekKind(1) == TokenKind.RIGHT_PARENT:
        token = state.next()
        state.advance()
        return state, ParseTreeIdentifierReferenceNode(token.sourcePosition, token.getStringValue())

    if state.peekKind() == TokenKind.RIGHT_PARENT:
        state.advance()
        return state, ParseTreeTupleNode(state.sourcePositionFrom(startPosition), [])
    
    state, expression = parseSequenceUntilEndOrDelimiter(state, TokenKind.RIGHT_PARENT)

    # )
    expression = state.expectAddingErrorToNode(TokenKind.RIGHT_PARENT, expression)
    return state, expression

def parseBlockArgument(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.peekKind() == TokenKind.COLON
    state.advance()

    typeExpression = None
    if state.peekKind() == TokenKind.LEFT_PARENT:
        state, typeExpression = parseParenthesis(state)

    optionalName = None
    if state.peekKind() == TokenKind.IDENTIFIER:
        token = state.next()
        optionalName = token.getStringValue()

    return state, ParseTreeArgumentDefinitionNode(state.sourcePositionFrom(startPosition), optionalName, typeExpression)

def parseBlockType(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    shouldEmitHeader = False
    argumentDefinitions = []
    resultTypeExpression = None

    ## Arguments
    while state.peekKind() == TokenKind.COLON:
        state, argumentDefinition = parseBlockArgument(state)
        argumentDefinitions.append(argumentDefinition)
        shouldEmitHeader = True

    ## Result type
    if state.peekKind() == TokenKind.COLON_COLON:
        state.advance()
        state, resultTypeExpression = parseUnaryPrefixExpression(state)
        shouldEmitHeader = True

    ## Separating bar
    if state.peekKind() == TokenKind.BAR:
        shouldEmitHeader = True

    if not shouldEmitHeader:
        return state, None
    
    return state, ParseTreeFunctionTypeNode(state.sourcePositionFrom(startPosition), argumentDefinitions, resultTypeExpression)

def parseBlock(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # {
    startPosition = state.position
    assert state.peekKind() == TokenKind.LEFT_CURLY_BRACKET
    state.advance()

    state, blockType = parseBlockType(state)

    shouldEmitFunction = False
    if state.peekKind() == TokenKind.BAR:
        state.advance()
        shouldEmitFunction = True

    if blockType is not None:
        if shouldEmitFunction:
            state, body = parseSequenceUntilEndOrDelimiter(state, TokenKind.RIGHT_CURLY_BRACKET)
            body = state.expectAddingErrorToNode(TokenKind.RIGHT_CURLY_BRACKET, body)
            return state, ParseTreeFunctionNode(state.sourcePositionFrom(startPosition), None, blockType, body, False)
        else:
            blockType = state.expectAddingErrorToNode(TokenKind.RIGHT_CURLY_BRACKET, blockType)
            return state, blockType
    else:
        state, body = parseSequenceUntilEndOrDelimiter(state, TokenKind.RIGHT_CURLY_BRACKET)
        body = state.expectAddingErrorToNode(TokenKind.RIGHT_CURLY_BRACKET, body)
        return state, ParseTreeLexicalBlockNode(state.sourcePositionFrom(startPosition), body)
    # }

    body = state.expectAddingErrorToNode(TokenKind.RIGHT_CURLY_BRACKET, body)
    if blockHeader is None:
        return state, ParseTreeLexicalBlockNode(state.sourcePositionFrom(startPosition), body)
    else:
        return state, ParseTreeFunctionNode(state.sourcePositionFrom(startPosition), None, blockHeader.argumentDefinitions, blockHeader.resultTypeExpression, body, blockHeader.isPublic)

def parseDictionaryAssociation(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    value = None
    if state.peekKind() == TokenKind.KEYWORD:
        keyToken = state.next()
        key = ParseTreeLiteralSymbolNode(keyToken.sourcePosition, keyToken.getStringValue()[:-1])

        if state.peekKind() not in [TokenKind.DOT, TokenKind.RIGHT_CURLY_BRACKET]:
            state, value = parseAssociationExpression(state)
    else:
        state, key = parseBinaryExpressionSequence(state)
        if state.peekKind() == TokenKind.COLON:
            state.advance()
            state, value = parseAssociationExpression(state)

    return state, ParseTreeAssociationNode(state.sourcePositionFrom(startPosition), key, value)

def parseDictionary(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # #{
    startPosition = state.position
    assert state.peekKind() == TokenKind.DICTIONARY_START
    state.advance()

    # Chop the initial dots
    while state.peekKind() == TokenKind.DOT:
        state.advance()

    # Parse the next expression
    expectsExpression = True
    elements = []
    while not state.atEnd() and state.peekKind() != TokenKind.RIGHT_CURLY_BRACKET:
        if not expectsExpression:
            elements.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected dot before association."))

        state, expression = parseDictionaryAssociation(state)
        elements.append(expression)

        expectsExpression = False
        # Chop the next dot sequence
        while state.peekKind() == TokenKind.DOT:
            expectsExpression = True
            state.advance()

    # }
    if state.peekKind() == TokenKind.RIGHT_CURLY_BRACKET:
        state.advance()
    else:
        elements.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected a right curly brack (})."))

    return state, ParseTreeDictionaryNode(state.sourcePositionFrom(startPosition), elements)

def parseUnaryPostfixExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, receiver = parseTerm(state)
    while state.peekKind() in [TokenKind.IDENTIFIER, TokenKind.LEFT_PARENT, TokenKind.LEFT_BRACKET, TokenKind.LEFT_CURLY_BRACKET, TokenKind.BYTE_ARRAY_START, TokenKind.DICTIONARY_START]:
        token = state.peek()
        if token.kind == TokenKind.IDENTIFIER:
            state.advance()
            selector = ParseTreeLiteralSymbolNode(token.sourcePosition, token.getStringValue())
            receiver = ParseTreeMessageSendNode(receiver.sourcePosition.to(selector.sourcePosition), receiver, selector, [])
        elif token.kind == TokenKind.LEFT_PARENT:
            state.advance()
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_PARENT)
            if state.peekKind() == TokenKind.RIGHT_PARENT:
                state.advance()
            else:
                arguments.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected right parenthesis."))
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments, ParseTreeApplicationNode.Normal)
        elif token.kind == TokenKind.LEFT_BRACKET:
            state.advance()
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_BRACKET)
            if state.peekKind() == TokenKind.RIGHT_BRACKET:
                state.advance()
            else:
                arguments.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected right bracket."))
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments, ParseTreeApplicationNode.Bracket)
        elif token.kind == TokenKind.BYTE_ARRAY_START:
            state.advance()
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_BRACKET)
            if state.peekKind() == TokenKind.RIGHT_BRACKET:
                state.advance()
            else:
                arguments.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected right bracket."))
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments, ParseTreeApplicationNode.ByteArrayStart)
        elif token.kind == TokenKind.LEFT_CURLY_BRACKET:
            state, argument = parseBlock(state)
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, [argument], ParseTreeApplicationNode.Block)
        elif token.kind == TokenKind.DICTIONARY_START:
            state, argument = parseDictionary(state)
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, [argument], ParseTreeApplicationNode.Dictionary)
    return state, receiver

def parseUnaryPrefixExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.QUOTE: return parseQuote(state)
    elif state.peekKind() == TokenKind.QUASI_QUOTE: return parseQuasiQuote(state)
    elif state.peekKind() == TokenKind.QUASI_UNQUOTE: return parseQuasiUnquote(state)
    elif state.peekKind() == TokenKind.SPLICE: return parseSplice(state)
    else: return parseUnaryPostfixExpression(state)

def isBinaryExpressionOperator(kind: TokenKind) -> bool:
    return kind in [TokenKind.OPERATOR, TokenKind.STAR, TokenKind.LESS_THAN, TokenKind.GREATER_THAN, TokenKind.BAR]

def parseBinaryExpressionSequence(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, operand = parseUnaryPrefixExpression(state)
    if not isBinaryExpressionOperator(state.peekKind()):
        return state, operand
    
    elements = [operand]
    while isBinaryExpressionOperator(state.peekKind()):
        operatorToken = state.next()
        operator = ParseTreeLiteralSymbolNode(operatorToken.sourcePosition, operatorToken.getStringValue())
        elements.append(operator)

        state, operand = parseUnaryPostfixExpression(state)
        elements.append(operand)

    return state, ParseTreeBinaryExpressionSequenceNode(state.sourcePositionFrom(startPosition), elements)

def parseAssociationExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, key = parseBinaryExpressionSequence(state)

    if state.peekKind() != TokenKind.COLON:
        return state, key
    
    state.advance()
    state, value = parseAssociationExpression(state)
    return state, ParseTreeAssociationNode(state.sourcePositionFrom(startPosition), key, value)
    
def parseKeywordApplication(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    assert state.peekKind() == TokenKind.KEYWORD
    startPosition = state.position

    symbolValue = ""
    arguments = []
    firstKeywordSourcePosition = state.peek(0).sourcePosition
    lastKeywordSourcePosition = firstKeywordSourcePosition
    while state.peekKind() == TokenKind.KEYWORD:
        keywordToken = state.next()
        lastKeywordSourcePosition = keywordToken.sourcePosition
        symbolValue += keywordToken.getStringValue()
        
        state, argument = parseAssociationExpression(state)
        arguments.append(argument)

    functionIdentifier = ParseTreeIdentifierReferenceNode(firstKeywordSourcePosition.to(lastKeywordSourcePosition), symbolValue)
    
    return state, ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), functionIdentifier, arguments, ParseTreeApplicationNode.Normal)

def parseKeywordMessageSend(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, receiver = parseAssociationExpression(state)
    if state.peekKind() != TokenKind.KEYWORD:
        return state, receiver

    symbolValue = ""
    arguments = []
    firstKeywordSourcePosition = state.peek(0).sourcePosition
    lastKeywordSourcePosition = firstKeywordSourcePosition
    while state.peekKind() == TokenKind.KEYWORD:
        keywordToken = state.next()
        lastKeywordSourcePosition = keywordToken.sourcePosition
        symbolValue += keywordToken.getStringValue()
        
        state, argument = parseAssociationExpression(state)
        arguments.append(argument)

    selector = ParseTreeLiteralSymbolNode(firstKeywordSourcePosition.to(lastKeywordSourcePosition), symbolValue)
    return state, ParseTreeMessageSendNode(state.sourcePositionFrom(startPosition), receiver, selector, arguments)

def parseCascadedMessage(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    token = state.peek()
    if state.peekKind() == TokenKind.IDENTIFIER:
        state.advance()
        selector = ParseTreeLiteralSymbolNode(token.sourcePosition, token.getStringValue())
        return state, ParseTreeCascadedMessageNode(state.sourcePositionFrom(startPosition), selector, [])
    elif state.peekKind() == TokenKind.KEYWORD:
        symbolValue = ""
        arguments = []
        firstKeywordSourcePosition = state.peek(0).sourcePosition
        lastKeywordSourcePosition = firstKeywordSourcePosition
        while state.peekKind() == TokenKind.KEYWORD:
            keywordToken = state.next()
            lastKeywordSourcePosition = keywordToken.sourcePosition
            symbolValue += keywordToken.getStringValue()
            
            state, argument = parseBinaryExpressionSequence(state)
            arguments.append(argument)

        selector = ParseTreeLiteralSymbolNode(firstKeywordSourcePosition.to(lastKeywordSourcePosition), symbolValue)
        return state, ParseTreeCascadedMessageNode(state.sourcePositionFrom(startPosition), selector, arguments)
    elif isBinaryExpressionOperator(state.peekKind()):
        state.advance()
        selector = ParseTreeLiteralSymbolNode(token.sourcePosition, token.getStringValue())
        state, argument = parseUnaryPostfixExpression(state)
        return state, ParseTreeCascadedMessageNode(state.sourcePositionFrom(startPosition), selector, [argument])
    else:
        return state, ParseTreeErrorNode(state.currentSourcePosition(), 'Expected a cascaded message send.')

def parseMessageCascade(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, firstMessage = parseKeywordMessageSend(state)
    if state.peekKind() != TokenKind.SEMICOLON:
        return state, firstMessage
    
    cascadeReceiver, firstCascadedMessage = firstMessage.asMessageSendCascadeReceiverAndFirstMessage()
    cascadedMessages = []
    if firstCascadedMessage is not None:
        cascadedMessages.append(firstCascadedMessage)

    while state.peekKind() == TokenKind.SEMICOLON:
        state.advance()
        state, cascadedMessage = parseCascadedMessage(state)
        cascadedMessages.append(cascadedMessage)
    return state, ParseTreeMessageCascadeNode(state.sourcePositionFrom(startPosition), cascadeReceiver, cascadedMessages)

def parseChainExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.KEYWORD:
        return parseKeywordApplication(state)
    return parseMessageCascade(state)

def parseLowPrecedenceExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # Low precedence binary operators
    startPosition = state.position
    state, receiver = parseChainExpression(state)
    while state.peekKind() == TokenKind.LOW_PRECEDENCE_OPERATOR:
        operatorToken = state.next()
        operatorSelector = operatorToken.getStringValue()[2:]
        
        selectorNode = ParseTreeLiteralSymbolNode(operatorToken.sourcePosition, operatorSelector)
        state, argument = parseChainExpression(state)

        receiver = ParseTreeMessageSendNode(state.sourcePositionFrom(startPosition), receiver, selectorNode, [argument])

    return state, receiver

def parseAssignmentExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, assignedStore = parseLowPrecedenceExpression(state)
    if state.peekKind() == TokenKind.ASSIGNMENT:
        operatorToken = state.next()
        state, assignedValue = parseAssignmentExpression(state)
        return state, ParseTreeAssignmentNode(state.sourcePositionFrom(startPosition), assignedStore, assignedValue)
    else:
        return state, assignedStore

def parseCommaExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, element = parseAssignmentExpression(state)
    if state.peekKind() != TokenKind.COMMA:
        return state, element
    
    elements = [element]
    while state.peekKind() == TokenKind.COMMA:
        state.advance()
        memento = state.memento()
        state, element = parseAssignmentExpression(state)
        if element.isErrorNode():
            state.restore(memento)
            break
        elements.append(element)
    
    return state, ParseTreeTupleNode(state.sourcePositionFrom(startPosition), elements)

def parseExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    return parseCommaExpression(state)

def parseExpressionListUntilEndOrDelimiter(state: ParserState, delimiter: TokenKind) -> tuple[ParserState, list[ParseTreeNode]]:
    elements = []

    # Chop the initial dots
    while state.peekKind() == TokenKind.DOT:
        state.advance()

    # Parse the next expression
    expectsExpression = True
    while not state.atEnd() and state.peekKind() != delimiter:
        if not expectsExpression:
            elements.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected dot before expression."))

        state, expression = parseExpression(state)
        elements.append(expression)

        expectsExpression = False
        # Chop the next dot sequence
        while state.peekKind() == TokenKind.DOT:
            expectsExpression = True
            state.advance()

    return state, elements

def parseSequenceUntilEndOrDelimiter(state: ParserState, delimiter: TokenKind) -> tuple[ParserState, ParseTreeNode]:
    initialPosition = state.position
    state, elements = parseExpressionListUntilEndOrDelimiter(state, delimiter)
    if len(elements) == 1:
        return state, elements[0]
    return state, ParseTreeSequenceNode(state.sourcePositionFrom(initialPosition), elements)

def parseTopLevelExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    state, node = parseSequenceUntilEndOrDelimiter(state, TokenKind.END_OF_SOURCE)
    return node

def parseSourceString(sourceText: str, sourceName: str = '<string>') -> ParseTreeNode:
    sourceCode, tokens = scanSourceString(sourceText, sourceName)
    state = ParserState(sourceCode, tokens)
    return parseTopLevelExpression(state)

def parseFileNamed(fileName: str) -> ParseTreeNode:
    sourceCode, tokens = scanFileNamed(fileName)
    state = ParserState(sourceCode, tokens)
    return parseTopLevelExpression(state)
    