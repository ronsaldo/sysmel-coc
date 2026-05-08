#include "common.h"
#include "memory.h"
#include <string.h>

StringRef
sysmel_string_fromCString(const char *string)
{
    return sysmel_string_formStringData(strlen(string), string);
}

StringRef
sysmel_string_formStringData(size_t stringSize, const char *string)
{
    StringRef stringObject = SysmelClassAllocateWithByteVariableSizedData(String, stringSize);
    memcpy(stringObject->__elements__, string, stringSize);
    return stringObject;
}

size_t
sysmel_string_getSize(StringRef string)
{
    return string->super.super.super.super.super.super.__byteSize__;
}

StringRef
sysmel_object_asString(Oop receiver)
{
    return sysmel_string_fromCString("TODO: object asString");
}

StringRef
sysmel_object_printString(Oop receiver)
{
    return sysmel_string_fromCString("TODO: object printString");
}
