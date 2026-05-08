#ifndef SYSMEL_MESSAGE_H
#define SYSMEL_MESSAGE_H

#include "common.h"

typedef Oop (*sysmel_messageLookupResult_t)(...);

SYSMEL_RUNTIME_EXPORT sysmel_messageLookupResult_t sysmel_oop_lookupSelector(SymbolRef selector, Oop receiver);

#endif //SYSMEL_MESSAGE_H