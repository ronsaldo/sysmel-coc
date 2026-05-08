#include "common.h"

#define SysmelClassDefinition(className) \
    struct Class className ## _Class = {}; \
    struct Metaclass className ## _Metaclass = {};
#include "classDefinitions.inc"
#undef SysmelClassDefinition

void sysmel_initializeClasses(void)
{
    
}