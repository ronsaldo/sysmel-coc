#include "Scanner.hpp"
#include <assert.h>

static const char *SysmelTokenKind_stringTable[] = {
#define TokenKindName(name) #name,
#   include "TokenKind.inc"
#undef TokenKindName
};

const char *
SysmelTokenKind_toString(SysmelTokenKind_t kind)
{
    return SysmelTokenKind_stringTable[kind];
}

typedef struct SysmelScannerState_s
{
    SourceCodePtr sourceCode;
    size_t position;
    size_t size;
    size_t line;
    size_t column;
    bool isPreviousCR;
} SysmelScannerState_t;

static SysmelScannerState_t
sysmel_scannerState_newForSourceCode(const SourceCodePtr &sourceCode)
{
    SysmelScannerState_t state = {};
    state.sourceCode = sourceCode;
    state.position = 0;
    state.size = sourceCode->text.size();
    state.line = 1;
    state.column = 1;
    return state;
}

static bool
sysmel_scanner_isDigit(int character)
{
    return '0' <= character && character <= '9';
}

static bool
sysmel_scanner_isIdentifierStart(int character)
{
    return
        ('A' <= character && character <= 'Z') ||
        ('a' <= character && character <= 'z') ||
        (character == '_')
        ;
}

static bool
sysmel_scanner_isIdentifierMiddle(int character)
{
    return sysmel_scanner_isIdentifierStart(character) || sysmel_scanner_isDigit(character);
}

static bool
sysmel_scanner_isOperatorCharacter(int character)
{
    const char *charset = "+-/\\*~<>=@%|&?!^";
    while(*charset != 0)
    {
        if(*charset == character)
            return true;
        ++charset;
    }
    return false;
}

static bool
sysmel_scannerState_atEnd(SysmelScannerState_t *state)
{
    return state->position >= state->size;
}

static int
sysmel_scannerState_peek(SysmelScannerState_t *state, int peekOffset)
{
    size_t peekPosition = state->position + peekOffset;
    if(peekPosition < state->size)
        return state->sourceCode->text[peekPosition];
    else
        return -1;
}

static void
sysmel_scannerState_advanceSinglePosition(SysmelScannerState_t *state)
{
    assert(!sysmel_scannerState_atEnd(state));
    char c = state->sourceCode->text[state->position];
    ++state->position;
    switch(c)
    {
    case '\r':
        ++state->line;
        state->column = 1;
        state->isPreviousCR = true;
        break;
    case '\n':
        if (!state->isPreviousCR)
        {
            ++state->line;
            state->column = 1;
        }
        state->isPreviousCR = false;
        break;
    case '\t':
        state->column = (state->column + 4) % 4 * 4 + 1;
        state->isPreviousCR = false;
        break;
    default:
        ++state->column;
        state->isPreviousCR = false;
        break;
    }
}

void
sysmel_scannerState_advance(SysmelScannerState_t *state, int count)
{
    for(int i = 0; i < count; ++i)
        sysmel_scannerState_advanceSinglePosition(state);
}

static SysmelTokenPtr
sysmel_scannerState_makeToken(SysmelScannerState_t *state, SysmelTokenKind_t kind)
{
    auto sourcePosition = std::make_shared<SourcePosition> ();
    sourcePosition->sourceCode = state->sourceCode;
    sourcePosition->startIndex = state->position;
    sourcePosition->startLine = state->line;
    sourcePosition->startColumn = state->column;
    sourcePosition->endIndex = state->position;
    sourcePosition->endLine = state->line;
    sourcePosition->endColumn = state->column;

    auto token = std::make_shared<SysmelToken> ();
    token->kind = kind;
    token->sourcePosition = sourcePosition;
    return token;
}

static SysmelTokenPtr
sysmel_scannerState_makeTokenStartingFrom(SysmelScannerState_t *state, SysmelTokenKind_t kind, SysmelScannerState_t *initialState)
{
    auto sourcePosition = std::make_shared<SourcePosition> ();
    sourcePosition->sourceCode = initialState->sourceCode;
    sourcePosition->startIndex = initialState->position;
    sourcePosition->startLine = initialState->line;
    sourcePosition->startColumn = initialState->column;
    
    sourcePosition->endIndex = state->position;
    sourcePosition->endLine = state->line;
    sourcePosition->endColumn = state->column;

    auto token = std::make_shared<SysmelToken> ();
    token->kind = kind;
    token->sourcePosition = sourcePosition;
    return token;
}

static SysmelTokenPtr
sysmel_scannerState_makeErrorTokenStartingFrom(SysmelScannerState_t *state, const char *errorMessage, SysmelScannerState_t *initialState)
{
    auto sourcePosition = std::make_shared<SourcePosition> ();
    sourcePosition->sourceCode = initialState->sourceCode;
    sourcePosition->startIndex = initialState->position;
    sourcePosition->startLine = initialState->line;
    sourcePosition->startColumn = initialState->column;
    
    sourcePosition->endIndex = state->position;
    sourcePosition->endLine = state->line;
    sourcePosition->endColumn = state->column;

    auto token = std::make_shared<SysmelToken> ();
    token->kind = SysmelTokenKind_Error;
    token->sourcePosition = sourcePosition;
    token->errorMessage = errorMessage;
    return token;
}

static SysmelTokenPtr
sysmel_scanner_skipWhite(SysmelScannerState_t *state)
{
    bool hasSeenComment = false;
    
    do
    {
        hasSeenComment = false;
        while (!sysmel_scannerState_atEnd(state) && sysmel_scannerState_peek(state, 0) <= ' ')
            sysmel_scannerState_advance(state, 1);

        if(sysmel_scannerState_peek(state, 0) == '#')
        {
            // Single line comment.
            if(sysmel_scannerState_peek(state, 1) == '#')
            {
                sysmel_scannerState_advance(state, 2);

                while (!sysmel_scannerState_atEnd(state))
                {
                    if (sysmel_scannerState_peek(state, 0) == '\r' || sysmel_scannerState_peek(state, 0) == '\n')
                        break;
                    sysmel_scannerState_advance(state, 1);
                }
                hasSeenComment = true;
            }
            else if(sysmel_scannerState_peek(state, 1) == '*')
            {
                SysmelScannerState_t commentInitialState = *state;
                sysmel_scannerState_advance(state, 2);
                bool hasCommentEnd = false;
                while (!sysmel_scannerState_atEnd(state))
                {
                    hasCommentEnd = sysmel_scannerState_peek(state, 0) == '*' &&  sysmel_scannerState_peek(state, 1) == '#';
                    if (hasCommentEnd)
                    {
                        sysmel_scannerState_advance(state, 2);
                        break;
                    }
                    else
                    {
                        sysmel_scannerState_advance(state, 1); 
                    }
                }

                if (!hasCommentEnd)
                {
                    return sysmel_scannerState_makeErrorTokenStartingFrom(state, "Incomplete multiline comment.", &commentInitialState);
                }
                hasSeenComment = true;
            }
        }
    } while (hasSeenComment);

    return nullptr;
}

bool
sysmel_scanner_advanceKeyword(SysmelScannerState_t *state)
{
    if(!sysmel_scanner_isIdentifierStart(sysmel_scannerState_peek(state, 0)))
        return false;

    SysmelScannerState_t initialState = *state;
    while (sysmel_scanner_isIdentifierMiddle(sysmel_scannerState_peek(state, 0)))
        sysmel_scannerState_advance(state, 1);

    if(sysmel_scannerState_peek(state, 0) == ':')
    {
        sysmel_scannerState_advance(state, 1);
    }
    else
    {
        *state = initialState;
        return false;
    }
    
    return true;
}

static SysmelTokenPtr
sysmel_scanner_scanSingleToken(SysmelScannerState_t *state)
{
    // Skip white and comments.
    SysmelTokenPtr whiteToken = sysmel_scanner_skipWhite(state);
    if(whiteToken)
        return whiteToken;

    // End of file.
    if(sysmel_scannerState_atEnd(state))
        return sysmel_scannerState_makeToken(state, SysmelTokenKind_EndOfSource);

    // Specific tokens.
    SysmelScannerState_t initialState = *state;
    int c = sysmel_scannerState_peek(state, 0);

    // Identifiers, keywords and multi-keywords
    if(sysmel_scanner_isIdentifierStart(c))
    {
        sysmel_scannerState_advance(state, 1);
        while (sysmel_scanner_isIdentifierMiddle(sysmel_scannerState_peek(state, 0)))
            sysmel_scannerState_advance(state, 1);

        if(sysmel_scannerState_peek(state, 0) == ':')
        {
            sysmel_scannerState_advance(state, 1);
            bool isMultiKeyword = false;
            bool hasAdvanced = true;
            while(hasAdvanced)
            {
                hasAdvanced = sysmel_scanner_advanceKeyword(state);
                isMultiKeyword = isMultiKeyword || hasAdvanced;
            }

            if(isMultiKeyword)
                return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_MultiKeyword, &initialState);
            else
                return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Keyword, &initialState);
        }

        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Identifier, &initialState);
    }

    // Numbers
    if(sysmel_scanner_isDigit(c))
    {
        sysmel_scannerState_advance(state, 1);
        while(sysmel_scanner_isDigit(sysmel_scannerState_peek(state, 0)))
            sysmel_scannerState_advance(state, 1);

        // Parse the radix
        if(sysmel_scannerState_peek(state, 0) == 'r')
        {
            sysmel_scannerState_advance(state, 1);
            while(sysmel_scanner_isIdentifierMiddle(sysmel_scannerState_peek(state, 0)))
                sysmel_scannerState_advance(state, 1);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Nat, &initialState);
        }

        // Parse the decimal point
        if(sysmel_scannerState_peek(state, 0) == '.' && sysmel_scanner_isDigit(sysmel_scannerState_peek(state, 1)))
        {
            sysmel_scannerState_advance(state, 2);
            while(sysmel_scanner_isDigit(sysmel_scannerState_peek(state, 0)))
                sysmel_scannerState_advance(state, 1);

            // Parse the exponent
            if(sysmel_scannerState_peek(state, 0) == 'e' || sysmel_scannerState_peek(state, 0) == 'E')
            {
                if(sysmel_scanner_isDigit(sysmel_scannerState_peek(state, 1)) ||
                ((sysmel_scannerState_peek(state, 1) == '+' || sysmel_scannerState_peek(state, 1) == '-') && sysmel_scanner_isDigit(sysmel_scannerState_peek(state, 2) )))
                {
                    sysmel_scannerState_advance(state, 2);
                    while(sysmel_scanner_isDigit(sysmel_scannerState_peek(state, 0)))
                        sysmel_scannerState_advance(state, 1);
                }
            }

            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Float, &initialState);
        }

        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Nat, &initialState);
    }

    // Symbols
    if(c == '#')
    {
        int c1 = sysmel_scannerState_peek(state, 1);
        if(sysmel_scanner_isIdentifierStart(c1))
        {
            sysmel_scannerState_advance(state, 2);
            while (sysmel_scanner_isIdentifierMiddle(sysmel_scannerState_peek(state, 0)))
                sysmel_scannerState_advance(state, 1);


            if (sysmel_scannerState_peek(state, 0) == ':')
            {
                sysmel_scannerState_advance(state, 1);
                bool hasAdvanced = true;
                while(hasAdvanced)
                {
                    hasAdvanced = sysmel_scanner_advanceKeyword(state);
                }

                return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Symbol, &initialState); 
            }
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Symbol, &initialState); 
        }
        else if(sysmel_scanner_isOperatorCharacter(c1))
        {
            sysmel_scannerState_advance(state, 2);
            while(sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
                sysmel_scannerState_advance(state, 1);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Symbol, &initialState);
        }
        else if(c1 == '"')
        {
            sysmel_scannerState_advance(state, 2);
            while (!sysmel_scannerState_atEnd(state) && sysmel_scannerState_peek(state, 0) != '"')
            {
                if(sysmel_scannerState_peek(state, 0) == '\\' && sysmel_scannerState_peek(state, 1) > 0)
                    sysmel_scannerState_advance(state, 2);
                else
                    sysmel_scannerState_advance(state, 1);
            }

            if (sysmel_scannerState_peek(state, 0) != '"')
                return sysmel_scannerState_makeErrorTokenStartingFrom(state, "Incomplete symbol string literal.", &initialState);
            
            sysmel_scannerState_advance(state, 1);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Symbol, &initialState);
        }
        else if (c1 == '[')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_ByteArrayStart, &initialState);
        }
        else if (c1 == '{')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_DictionaryStart, &initialState);
        }
        else if (c1 == '(')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_LiteralArrayStart, &initialState);
        }
    }


    // Strings
    if(c == '"')
    {
        sysmel_scannerState_advance(state, 1);
        while (!sysmel_scannerState_atEnd(state) && sysmel_scannerState_peek(state, 0) != '"')
        {
            if(sysmel_scannerState_peek(state, 0) == '\\' && sysmel_scannerState_peek(state, 1) > 0)
                sysmel_scannerState_advance(state, 2);
            else
                sysmel_scannerState_advance(state, 1);
        }

        if (sysmel_scannerState_peek(state, 0) != '"')
            return sysmel_scannerState_makeErrorTokenStartingFrom(state, "Incomplete string literal.", &initialState);
        
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_String, &initialState);
    }

    // Character
    if(c == '\'')
    {
        sysmel_scannerState_advance(state, 1);
        while (!sysmel_scannerState_atEnd(state) && sysmel_scannerState_peek(state, 0) != '\'')
        {
            if(sysmel_scannerState_peek(state, 0) == '\\' && sysmel_scannerState_peek(state, 1) > 0)
                sysmel_scannerState_advance(state, 2);
            else
                sysmel_scannerState_advance(state, 1);
        }

        if (sysmel_scannerState_peek(state, 0) != '\'')
            return sysmel_scannerState_makeErrorTokenStartingFrom(state, "Incomplete character literal.", &initialState);
        
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Character, &initialState);
    }

    // Punctuations
    switch(c)
    {
    case '(':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_LeftParent, &initialState);
    case ')':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_RightParent, &initialState);
    case '[':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_LeftBracket, &initialState);
    case ']':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_RightBracket, &initialState);
    case '{':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_LeftCurlyBracket, &initialState);
    case '}':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_RightCurlyBracket, &initialState);
    case ';':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Semicolon, &initialState);
    case ',':
        sysmel_scannerState_advance(state, 1);
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Comma, &initialState);
    case '.':
        sysmel_scannerState_advance(state, 1);
        if(sysmel_scannerState_peek(state, 0) == '.' && sysmel_scannerState_peek(state, 1) == '.')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Ellipsis, &initialState);
        }
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Dot, &initialState);
    case ':':
        sysmel_scannerState_advance(state, 1);
        if(sysmel_scannerState_peek(state, 0) == ':')
        {
            sysmel_scannerState_advance(state, 1);
            if(sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
            {
                while (sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
                    sysmel_scannerState_advance(state, 1);
                return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_LowPrecedenceOperator, &initialState);    
            }
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_ColonColon, &initialState);
        }
        else if(sysmel_scannerState_peek(state, 0) == '=')
        {
            sysmel_scannerState_advance(state, 1);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Assignment, &initialState);
        }
        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Colon, &initialState);
    case '`':
        if (sysmel_scannerState_peek(state, 1) == '\'')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Quote, &initialState);
        }
        else if (sysmel_scannerState_peek(state, 1) == '`')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_QuasiQuote, &initialState);
        }
        else if (sysmel_scannerState_peek(state, 1) == ',')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_QuasiUnquote, &initialState);
        }
        else if (sysmel_scannerState_peek(state, 1) == '@')
        {
            sysmel_scannerState_advance(state, 2);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Splice, &initialState);
        }
        break;
    case '|':
        sysmel_scannerState_advance(state, 1);
        if (sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
        {
            while(sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
                sysmel_scannerState_advance(state, 1);
            return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Operator, &initialState);
        }

        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Bar, &initialState);
    default:
        break;
    }

    // Binary operators
    if(sysmel_scanner_isOperatorCharacter(c))
    {
        sysmel_scannerState_advance(state, 1);
        if(!sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
        {
            switch(c)
            {
            case '<':
                return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_LessThan, &initialState);
            case '>':
                return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_GreaterThan, &initialState);
            default:
                // Generic character, do nothing.
                break;
            }
        }

        while(sysmel_scanner_isOperatorCharacter(sysmel_scannerState_peek(state, 0)))
            sysmel_scannerState_advance(state, 1);

        return sysmel_scannerState_makeTokenStartingFrom(state, SysmelTokenKind_Operator, &initialState);
    }

    // Unsupported character
    sysmel_scannerState_advance(state, 1);
    return sysmel_scannerState_makeErrorTokenStartingFrom(state, "Unknown character", &initialState);
}


std::vector<SysmelTokenPtr> SysmelScanSourceCode(SourceCodePtr sourceCode)
{
    std::vector<SysmelTokenPtr> tokens;
    SysmelScannerState_t scannerState = sysmel_scannerState_newForSourceCode(sourceCode);
    SysmelTokenPtr scannedToken = NULL;

    do
    {
        scannedToken = sysmel_scanner_scanSingleToken(&scannerState);
        if(scannedToken->kind != SysmelTokenKind_NullToken)
            tokens.push_back(scannedToken);
    } while(scannedToken->kind != SysmelTokenKind_EndOfSource);
    return tokens;
}