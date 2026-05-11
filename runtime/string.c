#include "common.h"
#include "memory.h"
#include "message.h"
#include <string.h>
#include <assert.h>

StringBuilderRef
sysmel_stringBuilder_new()
{
    StringBuilderRef builder = SysmelClassAllocate(StringBuilder);
    builder->capacity = 16;
    builder->size = 0;
    builder->string = SysmelClassAllocateWithByteVariableSizedData(String, builder->capacity);
    return builder;
}

void
sysmel_stringBuilder_ensureCapacityForSize(StringBuilderRef self, size_t requiredSize)
{
    size_t requiredCapacity = self->size + requiredSize;
    if(requiredCapacity <= self->capacity)
        return;

    size_t newCapacity = self->capacity*2;
    if (newCapacity < 16)
        newCapacity = 16;
    if (newCapacity < requiredCapacity)
        newCapacity = requiredCapacity;

    StringRef oldStorage = self->string;
    StringRef newStorage = SysmelClassAllocateWithByteVariableSizedData(String, newCapacity);
    memcpy(newStorage->__elements__, oldStorage->__elements__, self->size);
    
    self->capacity = newCapacity;
    self->string = newStorage;

    assert(requiredCapacity <= self->capacity);
}

void
sysmel_stringBuilder_addCString(StringBuilderRef self, const char *cstring)
{
    size_t stringSize = strlen(cstring);
    sysmel_stringBuilder_ensureCapacityForSize(self, stringSize);
    memcpy(self->string->__elements__ + self->size, cstring, stringSize);
    self->size += stringSize;
}

void
sysmel_stringBuilder_addStringObject(StringBuilderRef self, StringRef stringObject)
{
    size_t stringSize = sysmel_string_getSize(stringObject);
    sysmel_stringBuilder_ensureCapacityForSize(self, stringSize);
    memcpy(self->string->__elements__ + self->size, stringObject->__elements__, stringSize);
    self->size += stringSize;
}

void
sysmel_stringBuilder_addSymbolObject(StringBuilderRef self, SymbolRef symbol)
{
    size_t symbolSize = sysmel_symbol_getSize(symbol);
    sysmel_stringBuilder_ensureCapacityForSize(self, symbolSize);
    memcpy(self->string->__elements__ + self->size, symbol->__elements__, symbolSize);
    self->size += symbolSize;
}

StringRef sysmel_stringBuilder_asString(StringBuilderRef builder)
{
    return sysmel_string_fromStringData(builder->size, builder->string->__elements__);
}

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
sysmel_string_fromSymbol(SymbolRef symbol)
{
    size_t size = sysmel_symbol_getSize(symbol);
    return sysmel_string_fromStringData(size, symbol->__elements__);
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

void
sysmel_object_printOn(Oop receiver, StringBuilderRef builder)
{
    sysmel_oop_lookupSelector(sysmel_symbol_internCString("printOn:"), receiver)(receiver, builder);
}

StringRef
sysmel_string_asString(StringRef receiver)
{
    return receiver;
}

Oop
sysmel_string_printOn(StringRef self, StringBuilderRef builder)
{
    sysmel_stringBuilder_addCString(builder, "\"");
    sysmel_stringBuilder_addStringObject(builder, self);
    sysmel_stringBuilder_addCString(builder, "\"");
    return sysmel_void;
}

void
sysmel_initializeStringPrimitives(void)
{
    sysmel_type_addPrimitive(&String_Class.super.super.super, "--", 2, sysmel_string_concat);

    sysmel_type_addPrimitive(&String_Class.super.super.super, "asString", 1, sysmel_string_asString);
    sysmel_type_addPrimitive(&String_Class.super.super.super, "printOn:", 2, sysmel_string_printOn);

    sysmel_type_addPrimitive(&Symbol_Class.super.super.super, "asString", 1, sysmel_string_fromSymbol);
    
}