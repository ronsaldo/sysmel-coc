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

// Declare the classes.
#define SysmelClassDefinition(className) \
    typedef struct className className; \
    extern struct Class className ## _Class; \
    extern struct Metaclass className ## _Metaclass;
#include "classDefinitions.inc"
#undef SysmelClassDefinition

// Define the structs
struct ProtoObject
{
    Type *__type__;
    size_t __byteSize__;
    uint8_t __gcColor__;
    uint32_t __identityHash__;
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

struct NominalType
{
    Type super;
};

struct TypeUniverse
{
    Type super;
};

struct Behavior
{
    NominalType super;
};

struct Class
{
    Behavior super;
};

struct Metaclass
{
    Behavior super;
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

struct String
{
    SequenceableCollection ArrayedCollection;
};

struct Symbol
{
    SequenceableCollection ArrayedCollection;
};

void sysmel_initializeClasses(void);
void sysmel_initializeRuntime(void);

#endif //SYSMEL_RUNTIME_H
