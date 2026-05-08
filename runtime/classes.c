#include "common.h"
#include <assert.h>

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

void sysmel_SmallGCLayout_setSlotType(GCSmallLayout *layout, size_t offset, sysmel_SlotType_t slotType)
{
    size_t wordIndex = offset / 16;
    size_t bitIndex = (offset % 16) * 2;
    assert(wordIndex < GCSmallLayoutSize);
    layout->__elements__[wordIndex] |= slotType << bitIndex;
}

void
sysmel_initializeClasses(void)
{
    // Name and Superclasses
#define SysmelClassDefinitionNoSuper(className)
#define SysmelClassDefinition(className, superclassName) \
    className ## _Class.name = sysmel_internCString(#className); \
    className ## _Class.super.superclass = &superclassName##_Class.super; \
    className ## _Metaclass.super.superclass = &superclassName##_Metaclass.super;

#include "classDefinitions.inc"

#undef SysmelClassDefinitionNoSuper
#undef SysmelClassDefinition

    // Short circuit
    ProtoObject_Metaclass.super.superclass = &Class_Class.super;

    // Class layouts
    GCSmallLayout *currentLayout;

#define SysmelBeginClassLayout(className, superClassName) \
    className ## _GCLayout = superClassName ## _GCLayout; \
    currentLayout = &className ## _GCLayout

#define GCLayoutAddField(className, fieldName, slotType) \
    sysmel_SmallGCLayout_setSlotType(currentLayout, offsetof(className, fieldName), slotType)

    SysmelBeginClassLayout(Object, ProtoObject);
    sysmel_SmallGCLayout_setSlotType(currentLayout, offsetof(ObjectHeader, __type__), SlotType_StrongRef);

    SysmelBeginClassLayout(GCLayout, Object);
    SysmelBeginClassLayout(Type, Object);
        GCLayoutAddField(Type, gcLayout, SlotType_StrongRef);
        
        SysmelBeginClassLayout(TypeUniverse, Type);

        SysmelBeginClassLayout(DerivedType, Type);
            GCLayoutAddField(DerivedType, baseType, SlotType_StrongRef);

            SysmelBeginClassLayout(PointerLikeType, DerivedType);

                SysmelBeginClassLayout(PointerType, PointerLikeType);

                SysmelBeginClassLayout(ReferenceType, PointerLikeType);

        SysmelBeginClassLayout(DynamicType, Type);
        
        SysmelBeginClassLayout(NominalType, Type);
            GCLayoutAddField(NominalType, methodDictionary, SlotType_StrongRef);
            
            SysmelBeginClassLayout(PrimitiveType, NominalType);
            SysmelBeginClassLayout(Behavior, NominalType);
                GCLayoutAddField(Behavior, superclass, SlotType_StrongRef);
                
                SysmelBeginClassLayout(Class, Behavior);
                GCLayoutAddField(Class, name, SlotType_StrongRef);

                SysmelBeginClassLayout(Metaclass, Behavior);
                GCLayoutAddField(Metaclass, thisClass, SlotType_StrongRef);

    SysmelBeginClassLayout(Boolean, Object);
    SysmelBeginClassLayout(True, Boolean);
    SysmelBeginClassLayout(False, Boolean);

SysmelBeginClassLayout(Magnitude, Object);
    SysmelBeginClassLayout(Character, Magnitude);
    SysmelBeginClassLayout(Number, Magnitude);
        SysmelBeginClassLayout(Float, Number);
            SysmelBeginClassLayout(BoxedFloat, Float);
            SysmelBeginClassLayout(SmallFloat, Float);
        SysmelBeginClassLayout(Integer, Number);
            SysmelBeginClassLayout(SmallInteger, Integer);

SysmelBeginClassLayout(Collection, Object);
    SysmelBeginClassLayout(SequenceableCollection, Collection);
    SysmelBeginClassLayout(ArrayedCollection, SequenceableCollection);
        
        SysmelBeginClassLayout(Array, ArrayedCollection);
        currentLayout->variableDataFormat = SlotType_StrongRef;
        
        SysmelBeginClassLayout(String, ArrayedCollection);
        
        SysmelBeginClassLayout(Symbol, ArrayedCollection);

    SysmelBeginClassLayout(HashedCollection, Collection);
        GCLayoutAddField(HashedCollection, array, SlotType_StrongRef);
        
        SysmelBeginClassLayout(InternedSymbolSet, HashedCollection);
        SysmelBeginClassLayout(MethodDictionary, HashedCollection);

#undef SysmelBeginClassLayout
#undef GCLayoutAddField
}