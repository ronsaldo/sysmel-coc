#include "common.h"
#include "memory.h"

MethodDictionaryRef
sysmel_MethodDictionary_new(void)
{
    MethodDictionaryRef dictionary = SysmelClassAllocate(MethodDictionary);
    dictionary->super.array = SysmelClassAllocateWithSlotVariableSizedData(Array, 16);
    return dictionary;
}

intptr_t
sysmel_MethodDictionary_scanFor(MethodDictionaryRef self, SymbolRef selector)
{
    ArrayRef array = self->super.array;
    size_t capacity = sysmel_oop_getVariablePointerSize((Oop)array) / 2;
    size_t identityHash = selector->super.super.super.super.super.super.__identityHash__;
    size_t naturalIndex = identityHash % capacity;

    for(size_t i = naturalIndex; i < capacity; ++i)
    {
        Oop key = array->__elements__[i*2];
        if(key == sysmel_nil || sysmel_symbol_equals((SymbolRef)key, selector))
            return i;
    }

    for(size_t i = 0; i < naturalIndex; ++i)
    {
        Oop key = array->__elements__[i*2];
        if(key == sysmel_nil || sysmel_symbol_equals((SymbolRef)key, selector))
            return i;
    }

    return -1;
}

void
sysmel_MethodDictionary_increaseCapacity(MethodDictionaryRef self)
{
    (void)self;
    abort();
}

Oop
sysmel_MethodDictionary_atOrNil(MethodDictionaryRef self, SymbolRef selector)
{
    intptr_t index = sysmel_MethodDictionary_scanFor(self, selector);
    if(index < 0)
        return sysmel_nil;

    ArrayRef array = self->super.array;
    return array->__elements__[index*2 + 1];
}

void
sysmel_MethodDictionary_atPut(MethodDictionaryRef self, SymbolRef selector, Oop binding)
{
    intptr_t index = sysmel_MethodDictionary_scanFor(self, selector);
    if(index < 0)
    {
        sysmel_MethodDictionary_increaseCapacity(self);
        index = sysmel_MethodDictionary_scanFor(self, selector);
    };

    ArrayRef array = self->super.array;
    if(array->__elements__[index*2] == sysmel_nil)
    {
        array->__elements__[index*2] = (Oop)selector;
        array->__elements__[index*2 + 1] = binding;
        ++self->super.tally;

        size_t capacity = sysmel_oop_getVariablePointerSize((Oop)array) / 2;
        size_t targetCapacity = capacity*80/100;
        if(self->super.tally >= targetCapacity)
            sysmel_MethodDictionary_increaseCapacity(self);
    }
    else
    {
        array->__elements__[index*2 + 1] = binding;
    }
}
