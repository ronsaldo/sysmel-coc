#include "numbers.h"
#include <assert.h>

intptr_t
__sysmel_decodeInteger(Oop integer)
{
    assert(sysmel_oop_isImmediate(integer));
    return sysmel_oop_decodeSmallInteger(integer);
}

Oop
__sysmel_encodeInteger(intptr_t integer)
{
    // TODO: Check the range.
    return sysmel_oop_encodeSmallInteger(integer);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_add(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger + rightInteger);
}

SYSMEL_RUNTIME_EXPORT int32_t
__sysmel_integer_asInt32(Oop value)
{
    return (int32_t)__sysmel_decodeInteger(value);
}