#ifndef SYSMEL_SCANNER_HPP
#define SYSMEL_SCANNER_HPP

#include "SourceCode.hpp"
#include <vector>

typedef enum SysmelTokenKind_e
{
#define TokenKindName(name) SysmelTokenKind_ ## name,
#   include "TokenKind.inc"
#undef TokenKindName
} SysmelTokenKind_t;

typedef std::shared_ptr<struct SysmelToken> SysmelTokenPtr;

struct SysmelToken
{
    SourcePositionPtr sourcePosition;
    SysmelTokenKind_t kind;
    std::string errorMessage;
};

const char *SysmelTokenKind_toString(SysmelTokenKind_t kind);
std::vector<SysmelTokenPtr> SysmelScanSourceCode(SourceCodePtr sourceCode);

#endif //SYSMEL_SCANNER_HPP