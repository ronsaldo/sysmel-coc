#include "message.h"
#include "dict.h"
#include <stdio.h>

SYSMEL_RUNTIME_EXPORT sysmel_messageLookupResult_t
sysmel_oop_lookupSelector(SymbolRef selector, Oop receiver)
{
    TypeRef receiverType = sysmel_oop_getType(receiver);
    TypeRef currentType = receiverType;
    while (currentType)
    {
        NativeMethodRef foundMethod = (NativeMethodRef)sysmel_MethodDictionary_atOrNil(currentType->methodDictionary, selector);
        if(foundMethod)
        {
            assert(foundMethod->super.super.super.__type__ == &NativeMethod_Class.super.super.super);
            return foundMethod->nativeFunction;
        }
        currentType = currentType->supertype;
    }

    fprintf(stderr, "Does not understand: #%.*s\n", (int)sysmel_symbol_getSize(selector), selector->__elements__);
    abort();
}