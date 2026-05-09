#include "numbers.h"
#include <assert.h>
#include <stdio.h>

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
__sysmel_integer_negated(Oop operand)
{
    intptr_t operandInteger = __sysmel_decodeInteger(operand);
    return __sysmel_encodeInteger(-operandInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_add(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger + rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_sub(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger - rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_mul(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger * rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_div(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger / rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_mod(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger % rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_and(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger & rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_or(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger | rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_xor(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger ^ rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_shiftLeft(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger << rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_shiftRight(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return __sysmel_encodeInteger(leftInteger >> rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_equals(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return sysmel_oop_encodeBoolean(leftInteger == rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_notEquals(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return sysmel_oop_encodeBoolean(leftInteger != rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_hash(Oop operand)
{
    intptr_t integer = __sysmel_decodeInteger(operand);
    return __sysmel_encodeInteger(integer * 1664525);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_lessThan(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return sysmel_oop_encodeBoolean(leftInteger < rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_lessOrEquals(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return sysmel_oop_encodeBoolean(leftInteger <= rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_greaterThan(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return sysmel_oop_encodeBoolean(leftInteger > rightInteger);
}

SYSMEL_RUNTIME_EXPORT Oop
__sysmel_integer_greaterOrEquals(Oop left, Oop right)
{
    intptr_t leftInteger = __sysmel_decodeInteger(left);
    intptr_t rightInteger = __sysmel_decodeInteger(right);
    return sysmel_oop_encodeBoolean(leftInteger >= rightInteger);
}

SYSMEL_RUNTIME_EXPORT int32_t
__sysmel_integer_asInt32(Oop value)
{
    return (int32_t)__sysmel_decodeInteger(value);
}

SYSMEL_RUNTIME_EXPORT StringRef
__sysmel_integer_printString(Oop value)
{
    char buffer[64];
    intptr_t decoded = __sysmel_decodeInteger(value);
    snprintf(buffer, sizeof(buffer), "%lld", (long long)decoded);
    return sysmel_string_fromCString(buffer);
}

void
sysmel_initializeNumberPrimitives(void)
{
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "negated", 1, __sysmel_integer_negated);
    
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "+",  2, __sysmel_integer_add);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "-",  2, __sysmel_integer_sub);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "*",  2, __sysmel_integer_mul);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "//", 2, __sysmel_integer_div);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "%",  2, __sysmel_integer_mod);

    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "&",  2, __sysmel_integer_and);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "|",  2, __sysmel_integer_or);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "^",  2, __sysmel_integer_xor);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "<<", 2, __sysmel_integer_shiftLeft);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, ">>", 2, __sysmel_integer_shiftRight);

    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "=",  2, __sysmel_integer_equals);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "~=", 2, __sysmel_integer_notEquals);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "hash",  1, __sysmel_integer_hash);

    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "<",  2, __sysmel_integer_lessThan);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "<=", 2, __sysmel_integer_lessOrEquals);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, ">",  2, __sysmel_integer_greaterThan);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, ">=", 2, __sysmel_integer_greaterOrEquals);

    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "asString", 1, __sysmel_integer_printString);
    sysmel_type_addPrimitive(&Integer_Class.super.super.super, "printString", 1, __sysmel_integer_printString);
}
