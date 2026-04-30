#include "Scanner.hpp"

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

std::vector<SysmelTokenPtr> SysmelScanSourceCode(SourceCodePtr sourceCode)
{
    std::vector<SysmelTokenPtr> tokens;
    return tokens;
}