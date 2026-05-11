#ifndef SYSMEL_RUNTIME_H
#define SYSMEL_RUNTIME_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define SYSMEL_RUNTIME_EXPORT

typedef enum sysmel_ImmediateObjectTagBits_e {
    ImmediateObjectTag_BitCount = 3,
    ImmediateObjectTag_BitMask = (1<<ImmediateObjectTag_BitCount) - 1,
    ImmediateObjectTag_SmallInteger = 1,
    ImmediateObjectTag_Character = 2,
    ImmediateObjectTag_SmallFloat = 4,
} sysmel_ImmediateObjectTagBits_t;

typedef enum sysmel_SlotType_e {
    SlotType_Data = 0,
    SlotType_StrongRef = 1,
    SlotType_WeakRef = 2,
} sysmel_SlotType_t;

typedef intptr_t Oop;

typedef struct ObjectHeader ObjectHeader;
typedef struct GCSmallLayout GCSmallLayout;

// Declare the classes.
#define SysmelClassDefinitionNoSuper(className) \
    typedef struct className className; \
    typedef struct className * className ## Ref; \
    extern struct Class className ## _Class; \
    extern struct Metaclass className ## _Metaclass;

#define SysmelClassDefinition(className, superClassName) SysmelClassDefinitionNoSuper(className)
#include "classDefinitions.inc"
#undef SysmelClassDefinition
#undef SysmelClassDefinitionNoSuper

extern True  sysmel_trueValue;
extern False sysmel_falseValue;
extern Void  sysmel_voidValue;

typedef Oop (*sysmel_NativeMethodFunction_t)(...);

uint32_t sysmel_oop_getIdentityHash(Oop object);
TypeRef sysmel_oop_getType(Oop object);

static inline bool
sysmel_oop_isImmediate(Oop object)
{
    return object == 0 || (object & ImmediateObjectTag_BitMask) != 0;
}

#define sysmel_nil   ((Oop)0)
#define sysmel_true  ((Oop)&sysmel_trueValue)
#define sysmel_false ((Oop)&sysmel_falseValue)
#define sysmel_void  ((Oop)&sysmel_voidValue)

static inline Oop sysmel_oop_encodeBoolean(bool value)
{
    return value ? sysmel_true : sysmel_false;
}

static inline Oop sysmel_oop_encodeSmallInteger(intptr_t value)
{
    return (value << ImmediateObjectTag_BitCount) | ImmediateObjectTag_SmallInteger;
}

static inline intptr_t sysmel_oop_decodeSmallInteger(Oop value)
{
    return value >> ImmediateObjectTag_BitCount;
}

static inline Oop sysmel_encodeCharacter(uint32_t value)
{
    return ((Oop)value << ImmediateObjectTag_BitCount) | ImmediateObjectTag_Character;
}

static inline uint32_t sysmel_oop_decodeCharacter(Oop value)
{
    return (uint32_t)(value >> ImmediateObjectTag_BitCount);
}

static inline Oop sysmel_oop_encodeInt32(int32_t value)
{
    return sysmel_oop_encodeSmallInteger(value);
}

static inline Oop sysmel_oop_encodeUInt32(uint32_t value)
{
    return sysmel_oop_encodeSmallInteger(value);
}

size_t
sysmel_oop_getVariableByteSize(Oop object);
size_t
sysmel_oop_getVariablePointerSize(Oop object);

// Define the structs
struct ObjectHeader
{
    TypeRef __type__;
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
struct GCLayout
{
    Object super;
    uint8_t variableDataFormat;
    uint32_t __elements__[];
};

#define GCSmallLayoutSize 2 
struct GCSmallLayout
{
    Object super;
    uint8_t variableDataFormat;
    uint32_t __elements__[GCSmallLayoutSize];
};

struct Type
{
    Object super;
    GCLayoutRef gcLayout;
    MethodDictionaryRef methodDictionary;
    TypeRef supertype;
    size_t instanceAlignment;
    size_t instanceSize;
};

struct DerivedType
{
    Type super;
    TypeRef baseType;
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
};

struct Class
{
    Behavior super;
    SymbolRef name;
};

struct Metaclass
{
    Behavior super;
    ClassRef thisClass;
};
// Native method.
struct NativeMethod
{
    Object super;
    uint32_t argumentCount;
    sysmel_NativeMethodFunction_t nativeFunction;
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

struct UndefinedObject
{
    Object super;
};

// Void
struct Void
{
    Object super;
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
    ArrayedCollection super;
    Oop __elements__[];
};

struct String
{
    ArrayedCollection super;
    char __elements__[];
};

struct Symbol
{
    ArrayedCollection super;
    char __elements__[];
};

struct HashedCollection
{
    Collection super;
    size_t tally;
    ArrayRef array;
};

struct InternedSymbolSet
{
    HashedCollection super;
};

struct MethodDictionary
{
    HashedCollection super;
};

struct StringBuilder
{
    Object super;
    StringRef string;
    size_t capacity;
    size_t size;
};

typedef struct RuntimeClasses
{
#define SysmelClassDefinitionNoSuper(className) \
    struct Class *className ## _Class; \
    struct Metaclass *className ## _Metaclass;

#define SysmelClassDefinition(className, superClassName) SysmelClassDefinitionNoSuper(className)
#include "classDefinitions.inc"
#undef SysmelClassDefinition
#undef SysmelClassDefinitionNoSuper
} RuntimeClasses;

typedef struct RuntimeRoots
{
    RuntimeClasses classes;
} RuntimeRoots;

extern RuntimeRoots sysmel_RuntimeRoots;

SYSMEL_RUNTIME_EXPORT StringBuilderRef sysmel_stringBuilder_new();
SYSMEL_RUNTIME_EXPORT void sysmel_stringBuilder_addCString(StringBuilderRef builder, const char *cstring);
SYSMEL_RUNTIME_EXPORT void sysmel_stringBuilder_addStringObject(StringBuilderRef builder, StringRef stringObject);
SYSMEL_RUNTIME_EXPORT void sysmel_stringBuilder_addSymbolObject(StringBuilderRef builder, SymbolRef symbol);
SYSMEL_RUNTIME_EXPORT StringRef sysmel_stringBuilder_asString(StringBuilderRef builder);

SYSMEL_RUNTIME_EXPORT uint32_t sysmel_string_computeHash(size_t stringSize, const char *string);

SYSMEL_RUNTIME_EXPORT StringRef sysmel_string_fromCString(const char *string);
SYSMEL_RUNTIME_EXPORT StringRef sysmel_string_fromStringData(size_t stringSize, const char *string);
SYSMEL_RUNTIME_EXPORT StringRef sysmel_string_fromSymbol(SymbolRef symbol);
SYSMEL_RUNTIME_EXPORT StringRef sysmel_string_concat(StringRef left, StringRef right);
SYSMEL_RUNTIME_EXPORT size_t sysmel_string_getSize(StringRef string);

SYSMEL_RUNTIME_EXPORT StringRef sysmel_object_asString(Oop receiver);
SYSMEL_RUNTIME_EXPORT StringRef sysmel_object_printString(Oop receiver);
SYSMEL_RUNTIME_EXPORT void sysmel_object_printOn(Oop receiver, StringBuilderRef builder);

SYSMEL_RUNTIME_EXPORT SymbolRef sysmel_symbol_internCString(const char *string);
SYSMEL_RUNTIME_EXPORT SymbolRef sysmel_symbol_internStringData(size_t stringSize, const char *string);
SYSMEL_RUNTIME_EXPORT size_t sysmel_symbol_getSize(SymbolRef string);

SYSMEL_RUNTIME_EXPORT bool sysmel_symbol_equals(SymbolRef left, SymbolRef right);

SYSMEL_RUNTIME_EXPORT void sysmel_type_addPrimitive(Type *type, const char *selector, uint32_t argumentCount, void* primitiveImplementation);

SYSMEL_RUNTIME_EXPORT void sysmel_initializeClasses(void);
SYSMEL_RUNTIME_EXPORT void sysmel_initializeRuntime(void);

#endif //SYSMEL_RUNTIME_H
