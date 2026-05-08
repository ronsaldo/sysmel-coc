#ifndef SYSMEL_DICT_H
#define SYSMEL_DICT_H

#include "common.h"

SYSMEL_RUNTIME_EXPORT MethodDictionaryRef sysmel_MethodDictionary_new(void);
SYSMEL_RUNTIME_EXPORT Oop sysmel_MethodDictionary_atOrNil(MethodDictionaryRef self, SymbolRef selector);
SYSMEL_RUNTIME_EXPORT void sysmel_MethodDictionary_atPut(MethodDictionaryRef self, SymbolRef selector, Oop value);

#endif //SYSMEL_DICT_H
