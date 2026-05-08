#include "common.h"
#include "memory.h"
#include <string.h>

SymbolRef
sysmel_symbol_internCString(const char *string)
{
    return sysmel_symbol_internStringData(strlen(string), string);
}

SymbolRef
sysmel_symbol_internStringData(size_t stringSize, const char *string)
{
    SymbolRef symbol = SysmelClassAllocateWithByteVariableSizedData(Symbol, stringSize);
    symbol->super.super.super.super.super.super.__identityHash__ = sysmel_string_computeHash(stringSize, string);
    memcpy(symbol->__elements__, string, stringSize);
    return symbol;
}

bool sysmel_symbol_equals(SymbolRef left, SymbolRef right)
{
    if(left == right)
        return true;

    // Compare the hashes
    if(left->super.super.super.super.super.super.__identityHash__ != right->super.super.super.super.super.super.__identityHash__)
        return false;

    // Compare the size
    if(left->super.super.super.super.super.super.__byteSize__ != right->super.super.super.super.super.super.__byteSize__)
        return false;

    // Compare the data
    return memcmp(left->__elements__, right->__elements__, left->super.super.super.super.super.super.__byteSize__) == 0;
}
