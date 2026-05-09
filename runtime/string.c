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
    return sysmel_string_fromStringData(strlen(string), string);
}

StringRef
sysmel_string_fromStringData(size_t stringSize, const char *string)
{
    StringRef stringObject = SysmelClassAllocateWithByteVariableSizedData(String, stringSize);
    stringObject->super.super.super.super.super.super.__identityHash__ = sysmel_string_computeHash(stringSize, string);
    memcpy(stringObject->__elements__, string, stringSize);
    return stringObject;
}

StringRef
sysmel_string_concat(StringRef left, StringRef right)
{
    size_t leftSize = sysmel_string_getSize(left);
    size_t rightSize = sysmel_string_getSize(right);
    size_t resultSize = leftSize + rightSize;

    StringRef stringObject = SysmelClassAllocateWithByteVariableSizedData(String, resultSize);
    memcpy(stringObject->__elements__, left->__elements__, leftSize);
    memcpy(stringObject->__elements__ + leftSize, right->__elements__, rightSize);
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

StringRef
sysmel_string_asString(StringRef receiver)
{
    return receiver;
}

StringRef
sysmel_string_printString(StringRef receiver)
{
    return sysmel_string_concat(sysmel_string_concat(sysmel_string_fromCString("\""), receiver), sysmel_string_fromCString("\""));
}

void
sysmel_initializeStringPrimitives(void)
{
    sysmel_type_addPrimitive(&String_Class.super.super.super, "--", 2, sysmel_string_concat);

    sysmel_type_addPrimitive(&String_Class.super.super.super, "asString", 1, sysmel_string_asString);
    sysmel_type_addPrimitive(&String_Class.super.super.super, "printString", 1, sysmel_string_printString);
}