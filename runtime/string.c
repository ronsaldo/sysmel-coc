#include "common.h"
#include "memory.h"
#include "message.h"
#include <string.h>

uint32_t
sysmel_string_computeHash(size_t stringSize, const char *string)
{
    uint32_t hash = stringSize*1664525;
    for(size_t i = 0; i < stringSize; ++i)
        hash = (hash + string[i])*1664525;
    return hash;
}

StringRef
sysmel_string_fromCString(const char *string)
{
    return sysmel_string_formStringData(strlen(string), string);
}

StringRef
sysmel_string_formStringData(size_t stringSize, const char *string)
{
    StringRef stringObject = SysmelClassAllocateWithByteVariableSizedData(String, stringSize);
    stringObject->super.super.super.super.super.super.__identityHash__ = sysmel_string_computeHash(stringSize, string);
    memcpy(stringObject->__elements__, string, stringSize);
    return stringObject;
}

size_t
sysmel_string_getSize(StringRef string)
{
    return sysmel_oop_getVariableByteSize((Oop)string);
}

StringRef
sysmel_object_asString(Oop receiver)
{
    return (StringRef)sysmel_oop_lookupSelector(sysmel_symbol_internCString("asString"), receiver)(receiver);
}

StringRef
sysmel_object_printString(Oop receiver)
{
    return (StringRef)sysmel_oop_lookupSelector(sysmel_symbol_internCString("printString"), receiver)(receiver);
}
