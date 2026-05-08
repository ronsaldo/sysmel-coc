#ifndef SYSMEL_RUNTIME_H
#define SYSMEL_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

typedef enum sysmel_ImmediateObjectTagBits_e {
    ImmediateObjectTag_BitCount = 3,
    ImmediateObjectTag_BitMask = (1<<ImmediateObjectTag_BitCount) - 1,
    ImmediateObjectTag_SmallInteger = 1,
    ImmediateObjectTag_Character = 2,
    ImmediateObjectTag_SmallFloat = 4,
} sysmel_ImmediateObjectTagBits_t;

typedef intptr_t Oop;

typedef struct ObjectHeader ObjectHeader;

// Declare the classes.
#define SysmelClassDefinitionNoSuper(className) \
    typedef struct className className; \
    extern struct Class className ## _Class; \
    extern struct Metaclass className ## _Metaclass;

#define SysmelClassDefinition(className, superClassName) SysmelClassDefinitionNoSuper(className)
#include "classDefinitions.inc"
#undef SysmelClassDefinition
#undef SysmelClassDefinitionNoSuper

// Define the structs
struct ObjectHeader
{
    Type *__type__;
    size_t __byteSize__;
    uint8_t __gcColor__;
    uint32_t __identityHash__;
};

struct ProtoObject
{
    ObjectHeader super;
};

struct Object
{
    ProtoObject super;
};

// Type system
struct Type
{
    Object super;
};

struct DerivedType
{
    Type super;
    Type *baseType;
};

struct PointerLikeType
{
    DerivedType super;
};

struct PointerType
{
    PointerLikeType super;
};

struct ReferenceType
{
    PointerLikeType super;
};

struct DynamicType
{
    Type super;
};

struct NominalType
{
    Type super;
    MethodDictionary *methodDictionary;
};

struct PrimitiveType
{
    NominalType super;
};

struct TypeUniverse
{
    Type super;
};

struct Behavior
{
    NominalType super;
    Behavior *superclass;
    size_t instanceAlignment;
    size_t instanceSize;
};

struct Class
{
    Behavior super;
    Symbol *name;
};

struct Metaclass
{
    Behavior super;
    Class *thisClass;
};

// Boolean
struct Boolean
{
    Object super;
};

struct True
{
    Boolean super;
};

struct False
{
    Boolean super;
};

struct Magnitude
{
    Object super;
};

struct Character
{
    Magnitude super;
};

struct Number
{
    Magnitude super;
};

struct Float
{
    Number super;
};

struct BoxedFloat
{
    Float super;
    double value;
};

struct SmallFloat
{
    Float super;
};

struct Integer
{
    Number super;
};

struct SmallInteger
{
    Integer super;
};

struct Collection
{
    Object super;
};

struct SequenceableCollection
{
    Collection super;
};

struct ArrayedCollection
{
    SequenceableCollection super;
};

struct Array
{
    SequenceableCollection ArrayedCollection;
    Oop __elements__[];
};

struct String
{
    SequenceableCollection ArrayedCollection;
    char __elements__[];
};

struct Symbol
{
    SequenceableCollection ArrayedCollection;
    char __elements__[];
};

struct HashedCollection
{
    Collection super;
    Oop tally;
    Array *array;
};

struct InternedSymbolSet
{
    HashedCollection super;
};

struct MethodDictionary
{
    HashedCollection super;
};

Symbol *sysmel_internCString(const char *string);
void sysmel_initializeClasses(void);
void sysmel_initializeRuntime(void);

#endif //SYSMEL_RUNTIME_H
