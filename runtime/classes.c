#include "common.h"

extern struct GCSmallLayout Class_GCLayout;

#define SysmelClassDefinitionNoSuper(className) \
    struct GCSmallLayout className ## _GCLayout = { \
        .super.super.super = { \
            .__byteSize__ = sizeof(GCSmallLayout), \
            .__type__ = &GCLayout_Class.super.super.super \
        }, \
    }; \
    struct Class className ## _Class = { \
        .super = { \
            .super.super = { \
                .super.super.super = { \
                    .__byteSize__ = sizeof(Class), \
                    .__type__ = &className ## _Metaclass.super.super.super \
                }, \
                .gcLayout = (GCLayout*)&className ## _GCLayout\
            },\
            .instanceAlignment = 16, \
            .instanceSize = sizeof(className), \
        }, \
    }; \
    struct Metaclass className ## _Metaclass = {\
        .super = { \
            .super.super = { \
                .super.super.super = { \
                    .__byteSize__ = sizeof(Metaclass), \
                    .__type__ = &Metaclass_Class.super.super.super \
                }, \
                .gcLayout = (GCLayout*)&Class_GCLayout\
            }, \
            .instanceSize = sizeof(Class), \
        },\
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