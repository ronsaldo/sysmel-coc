#include "Parser.hpp"
#include <assert.h>
#include <stdlib.h>

typedef struct sysmel_ParserState_s
{
    size_t tokenCount;
    const SysmelTokenPtr *tokens;
    size_t position;
}sysmel_ParserState_t;

static SourcePositionPtr sysmel_parserState_currentSourcePosition(sysmel_ParserState_t *state);
static ParseTreeNodePtr sysmel_parser_parseAssociationExpression(sysmel_ParserState_t *state);
static ParseTreeNodePtr sysmel_parser_parseBinaryExpressionSequence(sysmel_ParserState_t *state);
static ParseTreeNodePtr sysmel_parser_parseSequenceUntilEndOrDelimiter(sysmel_ParserState_t *state, SysmelTokenKind_t delimiter);
static ParseTreeNodePtr sysmel_parser_parseUnaryPrefixExpression(sysmel_ParserState_t *state);
static std::vector<ParseTreeNodePtr> sysmel_parser_parseExpressionListUntilEndOrDelimiter(sysmel_ParserState_t *state, SysmelTokenKind_t delimiter);

static bool
sysmel_parserState_atEnd(sysmel_ParserState_t *state)
{
    return state->position >= state->tokenCount;
}

static SysmelTokenKind_t
sysmel_parserState_peekKind(sysmel_ParserState_t *state, int offset)
{
    size_t peekPosition = state->position + offset;
    if (peekPosition < state->tokenCount)
        return state->tokens[peekPosition]->kind;
    else
        return SysmelTokenKind_EndOfSource;
}

static SysmelTokenPtr 
sysmel_parserState_peek(sysmel_ParserState_t *state, int offset)
{
    size_t peekPosition = state->position + offset;
    if (peekPosition < state->tokenCount)
        return state->tokens[peekPosition];
    else
        return nullptr;
}

static void
sysmel_parserState_advance(sysmel_ParserState_t *state)
{
    assert(state->position < state->tokenCount);
    ++state->position;
}

static SysmelTokenPtr
sysmel_parserState_next(sysmel_ParserState_t *state)
{
    assert(state->position < state->tokenCount);
    auto token = state->tokens[state->position];
    ++state->position;
    return token;
}

ParseTreeNodePtr
sysmel_parserState_advanceWithExpectedError(sysmel_ParserState_t *state, const char *message)
{
    if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Error)
    {
        SysmelTokenPtr errorToken = sysmel_parserState_next(state);
        auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
        errorNode->sourcePosition = errorToken->sourcePosition;
        errorNode->errorMessage = errorToken->errorMessage;
        return errorNode;
    }
    else if (sysmel_parserState_atEnd(state))
    {
        auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
        errorNode->sourcePosition = sysmel_parserState_currentSourcePosition(state);
        errorNode->errorMessage = message;
        return errorNode;
    }
    else
    {
        auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
        sysmel_parserState_advance(state);
        errorNode->sourcePosition = sysmel_parserState_currentSourcePosition(state);
        errorNode->errorMessage = message;
        return errorNode;
    }
}

static SourcePositionPtr
sysmel_parserState_previousSourcePosition(sysmel_ParserState_t *state)
{
    assert(state->position > 0);
    return state->tokens[state->position - 1]->sourcePosition;
}

static SourcePositionPtr
sysmel_parserState_currentSourcePosition(sysmel_ParserState_t *state)
{
    if (state->position < state->tokenCount)
        return state->tokens[state->position]->sourcePosition;

    assert(state->tokenCount > 0);
    // assert(!tokens->at(tokens->size() - 1)->kind == TokenKind::EndOfSource);
    return state->tokens[state->tokenCount - 1]->sourcePosition;
}

static SourcePositionPtr
sysmel_parserState_sourcePositionFrom(sysmel_ParserState_t *state, size_t startingPosition)
{
    assert(startingPosition < state->tokenCount);
    SourcePositionPtr startSourcePosition = state->tokens[startingPosition]->sourcePosition;
    if (state->position > 0)
    {
        SourcePositionPtr endSourcePosition = sysmel_parserState_previousSourcePosition(state);
        return startSourcePosition->to(endSourcePosition);
    }
    else
    {
        SourcePositionPtr endSourcePosition = sysmel_parserState_currentSourcePosition(state);
        return startSourcePosition->until(endSourcePosition);
    }
}

static ParseTreeNodePtr
sysmel_parserState_makeErrorAtCurrentSourcePosition(sysmel_ParserState_t *state, const char *errorMessage)
{
    auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
    errorNode->sourcePosition = sysmel_parserState_currentSourcePosition(state);
    errorNode->errorMessage = errorMessage;
    return errorNode;
}

static ParseTreeNodePtr
sysmel_parserState_expectAddingErrorToNode(sysmel_ParserState_t *state, SysmelTokenKind_t expectedKind, const ParseTreeNodePtr &node)
{
    if (sysmel_parserState_peekKind(state, 0) == expectedKind)
    {
        sysmel_parserState_advance(state);
        return node;
    }

    auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
    errorNode->sourcePosition = sysmel_parserState_currentSourcePosition(state);
    errorNode->errorMessage = "Expected a specific token kind.";
    errorNode->innerNode = node;
    return errorNode;
}

static int64_t
parseIntegerConstant(const std::string &string)
{
    // TODO: Support large integers.
    int64_t result = 0;
    int64_t radix = 10;
    bool hasSeenRadix = false;

    for (size_t i = 0; i < string.size(); ++i)
    {
        char c = string[i];
        if (!hasSeenRadix && (c == 'r' || c == 'R'))
        {
            hasSeenRadix = true;
            radix = result;
            result = 0;
        }
        else
        {
            if ('0' <= c && c <= '9')
                result = result * radix + (int64_t)(c - '0');
            else if ('A' <= c && c <= 'Z')
                result = result * radix + (int64_t)(c - 'A' + 10);
            else if ('a' <= c && c <= 'z')
                result = result * radix + (int64_t)(c - 'a' + 10);
        }
    }
    return result;
}

static ParseTreeNodePtr
sysmel_parser_parseLiteralInteger(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_Nat);

    intptr_t integer = parseIntegerConstant(token->sourcePosition->getText());

    auto node = std::make_shared<ParseTreeLiteralIntegerNode> ();
    node->sourcePosition = token->sourcePosition;
    node->value = integer;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseLiteralFloat(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_Float);

    double value = atof(token->sourcePosition->getText().c_str());

    auto node = std::make_shared<ParseTreeLiteralFloatNode> ();
    node->sourcePosition = token->sourcePosition;
    node->value = value;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseLexicalError(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_Error);

    auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
    errorNode->sourcePosition = token->sourcePosition;
    errorNode->errorMessage = token->errorMessage;
    return errorNode;
}

static std::string
sysmel_parseCEscapedString(const std::string &string)
{
    std::string result;
    
    for (size_t i = 0; i < string.size(); ++i)
    {
        char c = string[i];
        if (c == '\\')
        {
            char c1 = string[++i];
            switch (c1)
            {
            case 'n':
                result.push_back('\n');
                break;
            case 'r':
                result.push_back('\r');
                break;
            case 't':
                result.push_back('\t');
                break;
            default:
                result.push_back(c1);
                break;
            }
        }
        else
        {
            result.push_back(c);
        }
    }

    return result;
}

static ParseTreeNodePtr
sysmel_parser_parseLiteralCharacter(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_Character);

    auto tokenText = token->sourcePosition->getText();
    auto parsedString = sysmel_parseCEscapedString(tokenText.substr(1, tokenText.size() - 2));
    if(parsedString.empty())
    {
        auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
        errorNode->sourcePosition = token->sourcePosition;
        errorNode->errorMessage = "Character literal cannot be empty.";
        return errorNode;
    }

    // TODO: Decode the UTF-8 character.

    auto node = std::make_shared<ParseTreeLiteralCharacterNode> ();
    node->sourcePosition = token->sourcePosition;
    node->value = parsedString[0];
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseLiteralString(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_String);

    auto tokenText = token->sourcePosition->getText();
    auto parsedString = sysmel_parseCEscapedString(tokenText.substr(1, tokenText.size() - 2));

    auto node = std::make_shared<ParseTreeLiteralStringNode> ();
    node->sourcePosition = token->sourcePosition;
    node->value = parsedString;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseLiteralSymbol(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_Symbol);

    auto tokenText = token->sourcePosition->getText();
    std::string parsedString;
    if(tokenText.size() >= 3 && tokenText[1] == '"')
    {
        parsedString = sysmel_parseCEscapedString(tokenText.substr(2, tokenText.size() - 3));
    }
    else
    {
        parsedString = tokenText.substr(1);
    }

    auto node = std::make_shared<ParseTreeLiteralSymbolNode> ();
    node->sourcePosition = token->sourcePosition;
    node->value = parsedString;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseLiteral(sysmel_ParserState_t *state)
{
    switch (sysmel_parserState_peekKind(state, 0))
    {
    case SysmelTokenKind_Nat:
        return sysmel_parser_parseLiteralInteger(state);
    case SysmelTokenKind_Float:
        return sysmel_parser_parseLiteralFloat(state);
    case SysmelTokenKind_Character:
        return sysmel_parser_parseLiteralCharacter(state);
    case SysmelTokenKind_String:
        return sysmel_parser_parseLiteralString(state);
    case SysmelTokenKind_Symbol:
        return sysmel_parser_parseLiteralSymbol(state);
    case SysmelTokenKind_Error:
        return sysmel_parser_parseLexicalError(state);
    default:
        return sysmel_parserState_advanceWithExpectedError(state, "Expected a literal");
    }
}

static bool
sysmel_parser_isBinaryExpressionOperator(SysmelTokenKind_t kind)
{
    switch (kind)
    {
    case SysmelTokenKind_Operator:
    case SysmelTokenKind_LessThan:
    case SysmelTokenKind_GreaterThan:
    case SysmelTokenKind_Bang:
    case SysmelTokenKind_Bar:
        return true;
    default:
        return false;
    }
}

static ParseTreeNodePtr
sysmel_parser_parseParenthesis(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LeftParent);
    sysmel_parserState_advance(state);

    if (sysmel_parser_isBinaryExpressionOperator(sysmel_parserState_peekKind(state, 0)) && sysmel_parserState_peekKind(state, 1) == SysmelTokenKind_RightParent)
    {
        auto token = sysmel_parserState_next(state);
        sysmel_parserState_advance(state);

        auto symbol = token->sourcePosition->getText();

        auto node = std::make_shared<ParseTreeIdentifierReferenceNode> ();
        node->sourcePosition = token->sourcePosition;
        node->value = symbol;
        return node;
    }

    if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_RightParent)
    {
        sysmel_parserState_advance(state);
        auto node = std::make_shared<ParseTreeTupleNode> ();
        node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        return node;
    }

    auto expression = sysmel_parser_parseSequenceUntilEndOrDelimiter(state, SysmelTokenKind_RightParent);
    expression = sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_RightParent, expression);
    return expression;
}

static ParseTreeNodePtr
sysmel_parser_parseIdentifier(sysmel_ParserState_t *state)
{
    auto token = sysmel_parserState_next(state);
    assert(token->kind == SysmelTokenKind_Identifier);

    auto symbol = token->sourcePosition->getText();

    auto node = std::make_shared<ParseTreeIdentifierReferenceNode> ();
    node->sourcePosition = token->sourcePosition;
    node->value = symbol;
    return node;
}

static ParseTreeArgumentDefinitionNodePtr
sysmel_parser_parseBlockArgument(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Colon);
    sysmel_parserState_advance(state);

    ParseTreeNodePtr typeExpression = NULL;
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LeftParent)
        typeExpression = sysmel_parser_parseParenthesis(state);

    std::string name;
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Identifier)
    {
        auto token = sysmel_parserState_next(state);
        name = token->sourcePosition->getText();
    }

    auto argument = std::make_shared<ParseTreeArgumentDefinitionNode> ();
    argument->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    argument->typeExpression = typeExpression;
    argument->name = name;
    return argument;
}

static ParseTreeFunctionTypeNodePtr
sysmel_parser_parseBlockType(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    bool shouldEmitType = false;
    std::vector<ParseTreeArgumentDefinitionNodePtr> argumentDefinitions;
    ParseTreeNodePtr resultTypeExpression = nullptr;

    while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Colon)
    {
        auto argumentDefinition = sysmel_parser_parseBlockArgument(state);
        argumentDefinitions.push_back(argumentDefinition);
        shouldEmitType = true;

    }

    // Result type
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_ColonColon)
    {
        sysmel_parserState_advance(state);
        shouldEmitType = true;
        resultTypeExpression = sysmel_parser_parseUnaryPrefixExpression(state);
    }

    // Separating bar
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Bar)
        shouldEmitType = true;

    if(!shouldEmitType)
        return nullptr;

    auto functionType = std::make_shared<ParseTreeFunctionTypeNode> ();
    functionType->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    functionType->argumentDefinitions.swap(argumentDefinitions);
    functionType->resultTypeExpression = resultTypeExpression;
    return functionType;
}

static ParseTreeNodePtr
sysmel_parser_parseBlock(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LeftCurlyBracket);
    sysmel_parserState_advance(state);

    auto blockType = sysmel_parser_parseBlockType(state);

    // Separating bar
    bool shouldEmitFunction = false;
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Bar)
    {
        sysmel_parserState_advance(state);
        shouldEmitFunction = true;
    }
 
    if(blockType)
    {
        if(shouldEmitFunction)
        {
            auto bodySequence = sysmel_parser_parseSequenceUntilEndOrDelimiter(state, SysmelTokenKind_RightCurlyBracket);
            bodySequence = sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_RightCurlyBracket, bodySequence);

            auto function = std::make_shared<ParseTreeFunctionNode> ();
            function->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
            function->functionType = blockType;
            function->body = bodySequence;
            return function;
        }
        else
        {
            return sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_RightCurlyBracket, blockType);
        }
    }
    else
    {
        auto bodySequence = sysmel_parser_parseSequenceUntilEndOrDelimiter(state, SysmelTokenKind_RightCurlyBracket);
        bodySequence = sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_RightCurlyBracket, bodySequence);

        auto lexicalBlock = std::make_shared<ParseTreeLexicalBlockNode> ();;
        lexicalBlock->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        lexicalBlock->body = bodySequence;
        return lexicalBlock;
    }
}

static ParseTreeNodePtr
sysmel_parser_parseDictionaryAssociation(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    ParseTreeNodePtr key;
    ParseTreeNodePtr value;

    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
    {
        // Key symbol parsing
        auto token = sysmel_parserState_next(state);
        auto tokenText = token->sourcePosition->getText();
        auto symbol = tokenText.substr(0, tokenText.size() - 1);
        
        auto literalSymbol = std::make_shared<ParseTreeLiteralSymbolNode> (); 
        literalSymbol->sourcePosition = token->sourcePosition;
        literalSymbol->value = symbol;
        key = literalSymbol;

        if(sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_Dot && sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_RightCurlyBracket)
            value = sysmel_parser_parseAssociationExpression(state);
    }
    else
    {
        key = sysmel_parser_parseBinaryExpressionSequence(state);
        if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Colon)
        {
            sysmel_parserState_advance(state);
            value = sysmel_parser_parseAssociationExpression(state);
        }
    }

    auto association = std::make_shared<ParseTreeAssociationNode> (); 
    association->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    association->key = key;
    association->value = value;
    return association;
}

static ParseTreeNodePtr
sysmel_parser_parseDictionary(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_DictionaryStart);
    sysmel_parserState_advance(state);

    // Chop the initial dots
    while (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Dot)
        sysmel_parserState_advance(state);

    
    // Parse the next expressions
    bool expectsExpression = true;
    std::vector<ParseTreeNodePtr> elements;

    while (!sysmel_parserState_atEnd(state) && sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_RightCurlyBracket)
    {
        if (!expectsExpression)
        {
            auto errorNode = sysmel_parserState_makeErrorAtCurrentSourcePosition(state, "Expected a dot before expression.");
            elements.push_back(errorNode);
        }

        auto expression = sysmel_parser_parseDictionaryAssociation(state);
        elements.push_back(expression);
        expectsExpression = false;

        // Chop the next dots
        while (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Dot)
        {
            expectsExpression = true;
            sysmel_parserState_advance(state);
        }

    }

    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_RightCurlyBracket)
    {
        sysmel_parserState_advance(state);
    }
    else
    {
        auto errorNode = sysmel_parserState_makeErrorAtCurrentSourcePosition(state, "Expected a right curly brack (}).");
        elements.push_back(errorNode);
    }

    auto dictionaryNode = std::make_shared<ParseTreeDictionaryNode> (); 
    dictionaryNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    dictionaryNode->elements.swap(elements);
    return dictionaryNode;
}

static ParseTreeArgumentDefinitionNodePtr
sysmel_parser_parseMethodArgument(sysmel_ParserState_t *state)
{
    ParseTreeNodePtr argumentTypeExpression;
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LeftParent)
        argumentTypeExpression = sysmel_parser_parseParenthesis(state);

    auto token = sysmel_parserState_next(state);
    auto argumentDefinition = std::make_shared<ParseTreeArgumentDefinitionNode> ();
    argumentDefinition->sourcePosition = token->sourcePosition;
    argumentDefinition->typeExpression = argumentTypeExpression;
    argumentDefinition->name = token->sourcePosition->getText();
    return argumentDefinition;
}

static ParseTreeFunctionTypeNodePtr
sysmel_parser_parseMethodHeader(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    std::vector<ParseTreeArgumentDefinitionNodePtr> argumentDefinitions;
    ParseTreeNodePtr resultTypeExpression = nullptr;
    std::string selector;

    // Self implicit argument.
    {
        auto selfArgument = std::make_shared<ParseTreeArgumentDefinitionNode> ();
        selfArgument->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        selfArgument->name = "self";
        argumentDefinitions.push_back(selfArgument);
    }

    // Remaining explicit arguments.
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Identifier)
    {
        auto token = sysmel_parserState_next(state);
        selector = token->sourcePosition->getText();
    }
    else if(sysmel_parser_isBinaryExpressionOperator(sysmel_parserState_peekKind(state, 0)))
    {
        auto token = sysmel_parserState_next(state);
        selector = token->sourcePosition->getText();

        auto argument = sysmel_parser_parseMethodArgument(state);
        argumentDefinitions.push_back(argument);
    }
    else if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
    {
        while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
        {
            auto token = sysmel_parserState_next(state);
            selector += token->sourcePosition->getText();

            auto argument = sysmel_parser_parseMethodArgument(state);
            argumentDefinitions.push_back(argument);
        }
    }

    // Result type
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_ColonColon)
    {
        sysmel_parserState_advance(state);
        resultTypeExpression = sysmel_parser_parseUnaryPrefixExpression(state);
    }

    // Dot separator.
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Dot)
        sysmel_parserState_advance(state);

    auto selectorLiteral = std::make_shared<ParseTreeLiteralSymbolNode> ();
    selectorLiteral->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    selectorLiteral->value = selector;

    auto functionType = std::make_shared<ParseTreeFunctionTypeNode> ();
    functionType->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    functionType->argumentDefinitions.swap(argumentDefinitions);
    functionType->resultTypeExpression = resultTypeExpression;
    functionType->nameExpression = selectorLiteral;
    return functionType;
}

static ParseTreeFunctionNodePtr
sysmel_parser_parseMethod(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_MethodStart);
    sysmel_parserState_advance(state);

    auto methodHeader = sysmel_parser_parseMethodHeader(state);

    auto bodySequence = sysmel_parser_parseSequenceUntilEndOrDelimiter(state, SysmelTokenKind_RightCurlyBracket);
    bodySequence = sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_RightCurlyBracket, bodySequence);

    auto function = std::make_shared<ParseTreeFunctionNode> ();
    function->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    function->nameExpression = methodHeader->nameExpression;
    function->functionType = methodHeader;
    function->body = bodySequence;
    function->isMethod = true;
    return function;
}

static ParseTreeNodePtr
sysmel_parser_parseTerm(sysmel_ParserState_t *state)
{
    switch (sysmel_parserState_peekKind(state, 0))
    {
    case SysmelTokenKind_Identifier:
        return sysmel_parser_parseIdentifier(state);
    case SysmelTokenKind_LeftParent:
        return sysmel_parser_parseParenthesis(state);
    case SysmelTokenKind_LeftCurlyBracket:
        return sysmel_parser_parseBlock(state);
    case SysmelTokenKind_DictionaryStart:
        return sysmel_parser_parseDictionary(state);
    case SysmelTokenKind_MethodStart:
        return sysmel_parser_parseMethod(state);
    default:
        return sysmel_parser_parseLiteral(state);
    }
}
static bool sysmel_parser_isUnaryPostfixExpressionOperator(SysmelTokenKind_t kind)
{
    switch(kind)
    {
    case SysmelTokenKind_Identifier:
    case SysmelTokenKind_LeftParent:
    case SysmelTokenKind_MethodStart:
        return true;
    default: return false;
    }
}

static ParseTreeNodePtr
sysmel_parser_parseUnaryPostfixExpression(sysmel_ParserState_t *state)
{   
    size_t startPosition = state->position;
    auto receiver = sysmel_parser_parseTerm(state);
    while(sysmel_parser_isUnaryPostfixExpressionOperator(sysmel_parserState_peekKind(state, 0)))
    {
        auto token = sysmel_parserState_peek(state, 0);
        if(token->kind == SysmelTokenKind_Identifier)
        {
            sysmel_parserState_advance(state);

            auto tokenText = token->sourcePosition->getText();

            auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
            selectorNode->sourcePosition = token->sourcePosition;
            selectorNode->value = tokenText;

            auto sendNode = std::make_shared<ParseTreeMessageSendNode> ();
            sendNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
            sendNode->receiver = receiver;
            sendNode->selector = selectorNode;
            
            receiver = sendNode;
        }
        else if(token->kind == SysmelTokenKind_LeftParent)
        {
            sysmel_parserState_advance(state);
            auto arguments = sysmel_parser_parseExpressionListUntilEndOrDelimiter(state, SysmelTokenKind_RightParent);
            if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_RightParent)
            {
                sysmel_parserState_advance(state);
            }
            else
            {
                auto errorNode = sysmel_parserState_makeErrorAtCurrentSourcePosition(state, "Expected right parenthesis.");
                arguments.push_back(errorNode);
            }

            // Function application
            auto applicationNode = std::make_shared<ParseTreeFunctionApplicationNode> ();
            applicationNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
            applicationNode->functional = receiver;
            applicationNode->arguments = arguments;

            receiver = applicationNode;
        }
        else if(token->kind == SysmelTokenKind_MethodStart)
        {
            auto method = sysmel_parser_parseMethod(state);
            auto addMethod = std::make_shared<ParseTreeAddMethodNode> ();
            addMethod->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
            addMethod->owner = receiver;
            addMethod->method = method;
            receiver = addMethod;
        }
        else
        {
            abort();
        }

    }
    return receiver;
}

static ParseTreeNodePtr
sysmel_parser_parseQuote(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Quote);
    sysmel_parserState_advance(state);

    auto term = sysmel_parser_parseUnaryPrefixExpression(state);

    auto node = std::make_shared<ParseTreeQuoteNode>();
    node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    node->expression = term;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseQuasiQuote(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_QuasiQuote);
    sysmel_parserState_advance(state);

    auto term = sysmel_parser_parseUnaryPrefixExpression(state);

    auto node = std::make_shared<ParseTreeQuasiQuoteNode>();
    node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    node->expression = term;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseQuasiUnquote(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_QuasiUnquote);
    sysmel_parserState_advance(state);

    auto term = sysmel_parser_parseUnaryPrefixExpression(state);

    auto node = std::make_shared<ParseTreeQuasiUnquoteNode>();
    node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    node->expression = term;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseSplice(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Splice);
    sysmel_parserState_advance(state);

    auto term = sysmel_parser_parseUnaryPrefixExpression(state);

    auto node = std::make_shared<ParseTreeSpliceNode>();
    node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    node->expression = term;
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseUnaryPrefixExpression(sysmel_ParserState_t *state)
{
    switch (sysmel_parserState_peekKind(state, 0))
    {
    case SysmelTokenKind_Quote:
        return sysmel_parser_parseQuote(state);
    case SysmelTokenKind_QuasiQuote:
        return sysmel_parser_parseQuasiQuote(state);
    case SysmelTokenKind_QuasiUnquote:
        return sysmel_parser_parseQuasiUnquote(state);
    case SysmelTokenKind_Splice:
        return sysmel_parser_parseSplice(state);
    default:
        return sysmel_parser_parseUnaryPostfixExpression(state);
    }
}

static ParseTreeNodePtr
sysmel_parser_parseBinaryExpressionSequence(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    auto operand = sysmel_parser_parseUnaryPrefixExpression(state);
    if(!sysmel_parser_isBinaryExpressionOperator(sysmel_parserState_peekKind(state, 0)))
        return operand;
    
    std::vector<ParseTreeNodePtr> elements;
    elements.push_back(operand);

    while(sysmel_parser_isBinaryExpressionOperator(sysmel_parserState_peekKind(state, 0)))
    {
        // Parse the selector.
        auto operatorToken = sysmel_parserState_next(state);

        auto operatorText = operatorToken->sourcePosition->getText();

        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
        selectorNode->sourcePosition = operatorToken->sourcePosition;
        selectorNode->value = operatorText;
        elements.push_back(selectorNode);

        // Operand
        auto operand = sysmel_parser_parseUnaryPrefixExpression(state);
        elements.push_back(operand);
    }

    auto sequence = std::make_shared<ParseTreeBinaryExpressionSequenceNode> ();
    sequence->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    sequence->elements.swap(elements);

    return sequence;
}

static ParseTreeNodePtr
sysmel_parser_parseAssociationExpression(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    auto key = sysmel_parser_parseBinaryExpressionSequence(state);
    if(sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_Colon)
        return key;

    sysmel_parserState_advance(state);
    auto value = sysmel_parser_parseAssociationExpression(state);

    // Make the association node
    auto association = std::make_shared<ParseTreeAssociationNode> ();
    association->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    association->key = key;
    association->value = value;

    return association;
}

static ParseTreeNodePtr
sysmel_parser_parseKeywordApplication(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    std::string symbolText;
    std::vector<ParseTreeNodePtr> arguments;

    while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
    {
        auto keywordToken = sysmel_parserState_next(state);

        auto tokenText = keywordToken->sourcePosition->getText();
        symbolText += tokenText;

        auto argument = sysmel_parser_parseAssociationExpression(state);
        arguments.push_back(argument);
    }

    // Function identifier.
    auto identifierNode = std::make_shared<ParseTreeIdentifierReferenceNode>();
    identifierNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    identifierNode->value = symbolText;

    // Function application
    auto applicationNode = std::make_shared<ParseTreeFunctionApplicationNode> ();
    applicationNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    applicationNode->functional = identifierNode;
    applicationNode->arguments.swap(arguments);
    return applicationNode;
}

static ParseTreeNodePtr
sysmel_parser_parseKeywordMessageSend(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    auto receiver = sysmel_parser_parseAssociationExpression(state);
    if(sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_Keyword)
        return receiver;

    std::string selector;
    std::vector<ParseTreeNodePtr> arguments;

    while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
    {
        auto keywordToken = sysmel_parserState_next(state);

        auto tokenText = keywordToken->sourcePosition->getText();
        selector += tokenText;
        
        auto argument = sysmel_parser_parseAssociationExpression(state);
        arguments.push_back(argument);
    }

    // Selector
    auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
    selectorNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    selectorNode->value = selector;

    // Message send
    auto sendNode = std::make_shared<ParseTreeMessageSendNode> ();
    sendNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    sendNode->receiver = receiver;
    sendNode->selector = selectorNode;
    sendNode->arguments.swap(arguments);

    return sendNode;
}

static ParseTreeNodePtr
sysmel_parser_parseCascadedMessage(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Identifier)
    {
        auto token = sysmel_parserState_next(state);
       
        auto symbol = token->sourcePosition->getText();

        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode>();
        selectorNode->sourcePosition = token->sourcePosition;
        selectorNode->value = symbol;

        auto messageNode = std::make_shared<ParseTreeCascadedMessageNode> ();
        messageNode->sourcePosition = token->sourcePosition;
        messageNode->selector = selectorNode;
        return messageNode;
    }
    else if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
    {
        std::string selector;
        std::vector<ParseTreeNodePtr> arguments;

        while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
        {
            auto keywordToken = sysmel_parserState_next(state);
            auto tokenText = keywordToken->sourcePosition->getText();

            selector += tokenText;

            auto argument = sysmel_parser_parseAssociationExpression(state);
            arguments.push_back(argument);
        }

        // Selector
        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
        selectorNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        selectorNode->value = selector;

        // Message send
        auto cascadeNode = std::make_shared<ParseTreeCascadedMessageNode> ();
        cascadeNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        cascadeNode->selector = selectorNode;
        cascadeNode->arguments.swap(arguments);
        return cascadeNode;
    }
    else if(sysmel_parser_isBinaryExpressionOperator(sysmel_parserState_peekKind(state, 0)))
    {
        auto token = sysmel_parserState_next(state);
        
        auto symbol = token->sourcePosition->getText();

        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
        selectorNode->sourcePosition = token->sourcePosition;
        selectorNode->value = symbol;

        auto argument = sysmel_parser_parseUnaryPostfixExpression(state);

        auto messageNode = std::make_shared<ParseTreeCascadedMessageNode> ();
        messageNode->sourcePosition = token->sourcePosition;
        messageNode->selector = selectorNode;
        messageNode->arguments.push_back(argument);
        return messageNode;
    }
    else
    {
        auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
        errorNode->sourcePosition = sysmel_parserState_currentSourcePosition(state);
        errorNode->errorMessage = "Expected a cascaded message send.";
        return errorNode;
    }
}

static ParseTreeNodePtr
sysmel_parser_parseMessageCascade(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    auto firstMessageNodeOrReceiver = sysmel_parser_parseKeywordMessageSend(state);
    if(sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_Semicolon)
        return firstMessageNodeOrReceiver;

    ParseTreeNodePtr receiver;
    ParseTreeNodePtr firstMessage;
    firstMessageNodeOrReceiver->splitMessageCascadeFirstMessage(&receiver, &firstMessage);

    std::vector<ParseTreeNodePtr> messages;
    if(firstMessage)
        messages.push_back(firstMessage);

    while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Semicolon)
    {
        sysmel_parserState_advance(state);
        auto cascadedMessage = sysmel_parser_parseCascadedMessage(state);
        messages.push_back(cascadedMessage);
    }

    // Message cascade
    auto cascadeNode = std::make_shared<ParseTreeMessageCascadeNode> ();
    cascadeNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
    cascadeNode->receiver = receiver;
    cascadeNode->messages.swap(messages);

    return cascadeNode;
}

static ParseTreeNodePtr
sysmel_parser_parseChainExpression(sysmel_ParserState_t *state)
{
    if(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
        return sysmel_parser_parseKeywordApplication(state);
    return sysmel_parser_parseMessageCascade(state);
}

static ParseTreeNodePtr
sysmel_parser_parseLowPrecedenceExpression(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    auto receiver = sysmel_parser_parseChainExpression(state);
    while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LowPrecedenceOperator)
    {
        // Parse the selector.
        auto operatorToken = sysmel_parserState_next(state);

        auto selectorText = operatorToken->sourcePosition->getText();
        auto selectorValue = selectorText.substr(2);

        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
        selectorNode->sourcePosition = operatorToken->sourcePosition;
        selectorNode->value = selectorValue;

        // Parse the argument.
        auto argument = sysmel_parser_parseChainExpression(state);

        // Make the message send
        auto send = std::make_shared<ParseTreeMessageSendNode> ();
        send->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        send->receiver = receiver;
        send->selector = selectorNode;
        send->arguments.push_back(argument);

        receiver = send;
    }
    
    return receiver;
}

static ParseTreeNodePtr
sysmel_parser_parseAssignmentExpression(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    auto assignedStore = sysmel_parser_parseLowPrecedenceExpression(state);
    if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Assignment)
    {
        sysmel_parserState_advance(state);
        auto assignedValue = sysmel_parser_parseAssignmentExpression(state);

        auto node = std::make_shared<ParseTreeAssignmentNode> ();
        node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        node->store = assignedStore;
        node->value = assignedValue;
        return node;
    }
    else
    {
        return assignedStore;
    }
}

static ParseTreeNodePtr
sysmel_parser_parseCommaExpression(sysmel_ParserState_t *state)
{
    size_t startingPosition = state->position;
    auto element = sysmel_parser_parseAssignmentExpression(state);

    if (sysmel_parserState_peekKind(state, 0) != SysmelTokenKind_Comma)
        return element;
        
    std::vector<ParseTreeNodePtr> elements;
    elements.push_back(element);
    while (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Comma)
    {
        sysmel_parserState_advance(state);
        auto element = sysmel_parser_parseAssignmentExpression(state);
        elements.push_back(element);
    }

    auto node = std::make_shared<ParseTreeTupleNode> ();
    node->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startingPosition);
    node->elements.swap(elements);
    return node;
}

static ParseTreeNodePtr
sysmel_parser_parseExpression(sysmel_ParserState_t *state)
{
    return sysmel_parser_parseCommaExpression(state);
}

static std::vector<ParseTreeNodePtr>
sysmel_parser_parseExpressionListUntilEndOrDelimiter(sysmel_ParserState_t *state, SysmelTokenKind_t delimiter)
{
    std::vector<ParseTreeNodePtr> elements;

    // Leading dots.
    while (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Dot)
        sysmel_parserState_advance(state);

    bool expectsExpression = true;

    while (!sysmel_parserState_atEnd(state) && sysmel_parserState_peekKind(state, 0) != delimiter)
    {
        if (!expectsExpression)
        {
            auto errorNode = sysmel_parserState_makeErrorAtCurrentSourcePosition(state, "Expected dot before expression.");
            elements.push_back(errorNode);
        }

        auto expression = sysmel_parser_parseExpression(state);
        elements.push_back(expression);

        // Trailing dots.
        expectsExpression = false;
        while (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Dot)
        {
            expectsExpression = true;
            sysmel_parserState_advance(state);
        }
    }

    return elements;
}

static ParseTreeNodePtr sysmel_parser_parsePragma(sysmel_ParserState_t *state)
{
    size_t startPosition = state->position;
    assert(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LessThan);
    sysmel_parserState_advance(state);

    if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Identifier)
    {
        auto token = sysmel_parserState_next(state);
       
        auto symbol = token->sourcePosition->getText();

        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode>();
        selectorNode->sourcePosition = token->sourcePosition;
        selectorNode->value = symbol;

        auto pragmaNode = std::make_shared<ParseTreePragmaNode> ();
        pragmaNode->sourcePosition = token->sourcePosition;
        pragmaNode->selector = selectorNode;
        return sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_GreaterThan, pragmaNode);
    }
    else if (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
    {
        std::string selector;
        std::vector<ParseTreeNodePtr> arguments;

        while(sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_Keyword)
        {
            auto keywordToken = sysmel_parserState_next(state);
            auto tokenText = keywordToken->sourcePosition->getText();

            selector += tokenText;

            auto argument = sysmel_parser_parseUnaryPrefixExpression(state);
            arguments.push_back(argument);
        }

        // Selector
        auto selectorNode = std::make_shared<ParseTreeLiteralSymbolNode> ();
        selectorNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        selectorNode->value = selector;

        // Pragma
        auto pragmaNode = std::make_shared<ParseTreePragmaNode> ();
        pragmaNode->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startPosition);
        pragmaNode->selector = selectorNode;
        pragmaNode->arguments.swap(arguments);
        return sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_GreaterThan, pragmaNode);
    }
    else
    {
        auto errorNode = std::make_shared<ParseTreeParseErrorNode> ();
        errorNode->sourcePosition = sysmel_parserState_currentSourcePosition(state);
        errorNode->errorMessage = "Expected a pragma message send.";
        return sysmel_parserState_expectAddingErrorToNode(state, SysmelTokenKind_GreaterThan, errorNode);
    }
}

static std::vector<ParseTreeNodePtr> sysmel_parser_parsePragmaList(sysmel_ParserState_t *state)
{
    std::vector<ParseTreeNodePtr> pragmas;
    while (sysmel_parserState_peekKind(state, 0) == SysmelTokenKind_LessThan)
    {
        auto pragma = sysmel_parser_parsePragma(state);
        pragmas.push_back(pragma);
    }
    
    return pragmas;
}

static ParseTreeNodePtr
sysmel_parser_parseSequenceUntilEndOrDelimiter(sysmel_ParserState_t *state, SysmelTokenKind_t delimiter)
{
    size_t startingPosition = state->position;
    auto pragmas = sysmel_parser_parsePragmaList(state);
    auto expressions = sysmel_parser_parseExpressionListUntilEndOrDelimiter(state, delimiter);
    if(expressions.size() == 1)
        return expressions[0];

    auto sequence = std::make_shared<ParseTreeSequenceNode> ();
    sequence->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startingPosition);
    sequence->pragmas.swap(pragmas);
    sequence->elements.swap(expressions);
    return sequence;
}

static ParseTreeNodePtr
sysmel_parser_parseTopLevelExpressions(sysmel_ParserState_t *state)
{
    return sysmel_parser_parseSequenceUntilEndOrDelimiter(state, SysmelTokenKind_EndOfSource);
}

ParseTreeNodePtr SysmelParseTokenSequence(const std::vector<SysmelTokenPtr> &tokens)
{
    sysmel_ParserState_t state = {};
    state.tokenCount = tokens.size();
    state.tokens = tokens.data();
    state.position = 0;
    return sysmel_parser_parseTopLevelExpressions(&state);
}
