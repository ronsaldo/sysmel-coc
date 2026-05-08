#include "common.h"

#define SysmelClassDefinitionNoSuper(className) \
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
        }, \
        .thisClass = &className ## _Class, \
    };
#define SysmelClassDefinition(className, superclass) \
    SysmelClassDefinitionNoSuper(className)
#include "classDefinitions.inc"
#undef SysmelClassDefinition
#undef SysmelClassDefinitionNoSuper

void sysmel_initializeClasses(void)
{
    // Superclasses
#define SysmelClassDefinitionNoSuper(className)
#define SysmelClassDefinition(className, superclassName) \
    className ## _Class.super.superclass = &superclassName##_Class.super; \
    className ## _Metaclass.super.superclass = &superclassName##_Metaclass.super; \

#include "classDefinitions.inc"

#undef SysmelClassDefinitionNoSuper
#undef SysmelClassDefinition

    // Short circuit
    ProtoObject_Metaclass.super.superclass = &Class_Class.super;

}