#include "common.h"

RuntimeRoots sysmel_RuntimeRoots = {
    .classes = {
#define SysmelClassDefinitionNoSuper(className) \
    .className ## _Class = &className ## _Class, \
    .className ## _Metaclass = &className ## _Metaclass, \

#define SysmelClassDefinition(className, superClassName) SysmelClassDefinitionNoSuper(className)
#include "classDefinitions.inc"
#undef SysmelClassDefinition
#undef SysmelClassDefinitionNoSuper
    }
};