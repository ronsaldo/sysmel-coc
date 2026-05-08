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
    memcpy(symbol->__elements__, string, stringSize);
    return symbol;
}
