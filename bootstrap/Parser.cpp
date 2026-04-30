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

static ParseTreeNodePtr
sysmel_parser_parseLiteral(sysmel_ParserState_t *state)
{
    switch (sysmel_parserState_peekKind(state, 0))
    {
    case SysmelTokenKind_Nat:
        return sysmel_parser_parseLiteralInteger(state);
    case SysmelTokenKind_Float:
        return sysmel_parser_parseLiteralFloat(state);
    /*case SysmelTokenKind_Character:
        return sysmel_parser_parseLiteralCharacter(state);
    case SysmelTokenKind_String:
        return sysmel_parser_parseLiteralString(state);
    case SysmelTokenKind_Symbol:
        return sysmel_parser_parseLiteralSymbol(state);*/
    case SysmelTokenKind_Error:
        return sysmel_parser_parseLexicalError(state);
    default:
        return sysmel_parserState_advanceWithExpectedError(state, "Expected a literal");
    }
}

static ParseTreeNodePtr
sysmel_parser_parseAssignmentExpression(sysmel_ParserState_t *state)
{
    return sysmel_parser_parseLiteral(state);
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

static ParseTreeNodePtr
sysmel_parser_parseSequenceUntilEndOrDelimiter(sysmel_ParserState_t *state, SysmelTokenKind_t delimiter)
{
    size_t startingPosition = state->position;
    auto expressions = sysmel_parser_parseExpressionListUntilEndOrDelimiter(state, delimiter);
    if(expressions.size() == 1)
        return expressions[0];

    auto sequence = std::make_shared<ParseTreeSequenceNode> ();
    sequence->sourcePosition = sysmel_parserState_sourcePositionFrom(state, startingPosition);
    sequence->elements = expressions;
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
