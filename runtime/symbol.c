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

size_t
sysmel_symbol_getSize(SymbolRef symbol)
{
    return sysmel_oop_getVariableByteSize((Oop)symbol);
}

bool sysmel_symbol_equals(SymbolRef left, SymbolRef right)
{
    if(left == right)
        return true;

    // Compare the hashes
    if(left->super.super.super.super.super.super.__identityHash__ != right->super.super.super.super.super.super.__identityHash__)
        return false;

    // Compare the size
    size_t leftSize = sysmel_symbol_getSize(left);
    size_t rightSize = sysmel_symbol_getSize(right);
    if(leftSize != rightSize)
        return false;

    // Compare the data
    return memcmp(left->__elements__, right->__elements__, leftSize) == 0;
}
