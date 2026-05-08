#include "common.h"

#define SysmelClassDefinition(className) \
    struct Class className ## _Class = { \
        .super.super.super.super.super = { \
            .__byteSize__ = sizeof(Class), \
            .__type__ = &className ## _Metaclass.super.super.super \
        } \
    }; \
    struct Metaclass className ## _Metaclass = {\
        .super.super.super.super.super = { \
            .__byteSize__ = sizeof(Metaclass), \
            .__type__ = &Metaclass_Class.super.super.super \
        } \
    };
#include "classDefinitions.inc"
#undef SysmelClassDefinition

void sysmel_initializeClasses(void)
{
    // Short circuit
    ProtoObject_Metaclass.super.superclass = &Class_Class.super;
    
}