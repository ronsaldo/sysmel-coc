#include "common.h"
#include "dict.h"
#include "memory.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

extern struct GCSmallLayout Class_GCLayout;

True  sysmel_trueValue;
False sysmel_falseValue;
Void  sysmel_voidValue;

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
                .gcLayout = (GCLayout*)&className ## _GCLayout, \
                .instanceAlignment = 16, \
                .instanceSize = sizeof(className), \
            },\
        }, \
    }; \
    struct Metaclass className ## _Metaclass = {\
        .super = { \
            .super.super = { \
                .super.super.super = { \
                    .__byteSize__ = sizeof(Metaclass), \
                    .__type__ = &Metaclass_Class.super.super.super \
                }, \
                .gcLayout = (GCLayout*)&Class_GCLayout, \
                .instanceSize = sizeof(Class), \
            }, \
        },\
        .thisClass = &className ## _Class, \
    };
#define SysmelClassDefinition(className, superclass) \
    SysmelClassDefinitionNoSuper(className)
#include "classDefinitions.inc"
#undef SysmelClassDefinition
#undef SysmelClassDefinitionNoSuper

uint32_t
sysmel_oop_getIdentityHash(Oop object)
{
    if(!sysmel_oop_isImmediate(object))
        return ((ObjectHeader*)object)->__identityHash__;

    return (uint32_t)(object *1664525);
}

TypeRef
sysmel_oop_getType(Oop object)
{
    if(!sysmel_oop_isImmediate(object))
        return ((ObjectHeader*)object)->__type__;
    
    Oop tag = object & ImmediateObjectTag_BitMask;
    switch(tag)
    {
    case 0: return &UndefinedObject_Class.super.super.super;
    case ImmediateObjectTag_SmallInteger: return &SmallInteger_Class.super.super.super;
    case ImmediateObjectTag_Character: return &Character_Class.super.super.super;
    case ImmediateObjectTag_SmallFloat: return &SmallFloat_Class.super.super.super;
    default: abort();
    }
}

size_t
sysmel_oop_getVariableByteSize(Oop value)
{
    if(sysmel_oop_isImmediate(value))
        return 0;

    ObjectHeader* header = (ObjectHeader*)value;
    assert(header->__byteSize__ >= header->__type__->instanceSize);
    return header->__byteSize__ - header->__type__->instanceSize;
}

size_t
sysmel_oop_getVariablePointerSize(Oop object)
{
    return sysmel_oop_getVariableByteSize(object) / sizeof(Oop);
}

void
sysmel_SmallGCLayout_setSlotType(GCSmallLayout *layout, size_t offset, sysmel_SlotType_t slotType)
{
    size_t slotIndex = offset / sizeof(Oop);

    size_t wordIndex = slotIndex / 16;
    size_t bitIndex = (slotIndex % 16) * 2;
    assert(wordIndex < GCSmallLayoutSize);
    layout->__elements__[wordIndex] |= slotType << bitIndex;
}

void
sysmel_initializeClasses(void)
{
    // Name, Superclasses and method dict
#define SysmelClassDefinitionNoSuper(className)
#define SysmelClassDefinition(className, superclassName) \
    className ## _Class.super.super.super.methodDictionary = sysmel_MethodDictionary_new(); \
    className ## _Class.name = sysmel_symbol_internCString(#className); \
    className ## _Class.super.super.super.supertype = &superclassName##_Class.super.super.super; \
    className ## _Metaclass.super.super.super.methodDictionary = sysmel_MethodDictionary_new(); \
    className ## _Metaclass.super.super.super.supertype = &superclassName##_Metaclass.super.super.super;

#include "classDefinitions.inc"

#undef SysmelClassDefinitionNoSuper
#undef SysmelClassDefinition

    // Proto object
    ProtoObject_Class.super.super.super.methodDictionary = sysmel_MethodDictionary_new();
    ProtoObject_Metaclass.super.super.super.methodDictionary = sysmel_MethodDictionary_new();

    ProtoObject_Metaclass.super.super.super.supertype = &Class_Class.super.super.super;

    // Class layouts
    GCSmallLayout *currentLayout;

#define SysmelBeginClassLayout(className, superClassName) \
    className ## _GCLayout = superClassName ## _GCLayout; \
    currentLayout = &className ## _GCLayout

#define GCLayoutAddField(className, fieldName, slotType) \
    sysmel_SmallGCLayout_setSlotType(currentLayout, offsetof(className, fieldName), slotType)

    sysmel_SmallGCLayout_setSlotType(&ProtoObject_GCLayout, offsetof(ObjectHeader, __type__), SlotType_StrongRef);
    ProtoObject_Class.super.super.super.methodDictionary = sysmel_MethodDictionary_new();

    SysmelBeginClassLayout(Object, ProtoObject);

    SysmelBeginClassLayout(GCLayout, Object);
    SysmelBeginClassLayout(Type, Object);
        GCLayoutAddField(Type, gcLayout, SlotType_StrongRef);
        GCLayoutAddField(Type, methodDictionary, SlotType_StrongRef);
        GCLayoutAddField(Type, supertype, SlotType_StrongRef);
        
        SysmelBeginClassLayout(TypeUniverse, Type);

        SysmelBeginClassLayout(DerivedType, Type);
            GCLayoutAddField(DerivedType, baseType, SlotType_StrongRef);

            SysmelBeginClassLayout(PointerLikeType, DerivedType);

                SysmelBeginClassLayout(PointerType, PointerLikeType);

                SysmelBeginClassLayout(ReferenceType, PointerLikeType);

        SysmelBeginClassLayout(DynamicType, Type);
        
        SysmelBeginClassLayout(NominalType, Type);
            
            SysmelBeginClassLayout(PrimitiveType, NominalType);
            SysmelBeginClassLayout(Behavior, NominalType);
                
                SysmelBeginClassLayout(Class, Behavior);
                GCLayoutAddField(Class, name, SlotType_StrongRef);

                SysmelBeginClassLayout(Metaclass, Behavior);
                GCLayoutAddField(Metaclass, thisClass, SlotType_StrongRef);

    SysmelBeginClassLayout(NativeMethod, Object);

    SysmelBeginClassLayout(Boolean, Object);
    SysmelBeginClassLayout(True, Boolean);
    SysmelBeginClassLayout(False, Boolean);

    SysmelBeginClassLayout(UndefinedObject, Object);
    SysmelBeginClassLayout(Void, Object);

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

    SysmelBeginClassLayout(StringBuilder, Object);
        GCLayoutAddField(StringBuilder, string, SlotType_StrongRef);

#undef SysmelBeginClassLayout
#undef GCLayoutAddField
}

void
sysmel_type_addPrimitive(Type *type, const char *selector, uint32_t argumentCount, void* primitiveImplementation)
{
    SymbolRef selectorSymbol = sysmel_symbol_internCString(selector);
    NativeMethodRef nativeMethod = SysmelClassAllocate(NativeMethod);
    nativeMethod->argumentCount = argumentCount;
    nativeMethod->nativeFunction = primitiveImplementation;
    sysmel_MethodDictionary_atPut(type->methodDictionary, selectorSymbol, (Oop)nativeMethod);
}


Oop
sysmel_object_printOn_primitive(ObjectRef object, StringBuilderRef builder)
{
    sysmel_stringBuilder_addCString(builder, "A ");

    TypeRef objectClass = sysmel_oop_getType((Oop)object);
    sysmel_object_printOn((Oop)objectClass, builder);

    return sysmel_void;
}

Oop
sysmel_class_printOn_primitive(ClassRef clazz, StringBuilderRef builder)
{
    if(clazz->name)
        sysmel_stringBuilder_addSymbolObject(builder, clazz->name);
    else
        sysmel_stringBuilder_addCString(builder, "An anonymous class");

    return sysmel_void;
}

StringRef
sysmel_object_asString_primitive(Oop self)
{
    return sysmel_object_printString(self);
}

StringRef
sysmel_object_printString_primitive(Oop object)
{
    StringBuilderRef builder = sysmel_stringBuilder_new();
    sysmel_object_printOn(object, builder);
    return sysmel_stringBuilder_asString(builder);
}

void
sysmel_initializeObjectPrimitives(void)
{
    sysmel_type_addPrimitive(&Object_Class.super.super.super, "asString", 1, sysmel_object_asString_primitive);
    sysmel_type_addPrimitive(&Object_Class.super.super.super, "printString", 1, sysmel_object_printString_primitive);
    sysmel_type_addPrimitive(&Object_Class.super.super.super, "printOn:", 2, sysmel_object_printOn_primitive);
    sysmel_type_addPrimitive(&Class_Class.super.super.super, "printOn:", 2, sysmel_class_printOn_primitive);
}
