#ifndef SYSMEL_MEMORY_H
#define SYSMEL_MEMORY_H

#include "common.h"

typedef struct sysmel_ObjectAllocationHeader_s
{
    struct sysmel_ObjectAllocationHeader_s *previousObject;
    struct sysmel_ObjectAllocationHeader_s *nextObject;
} sysmel_ObjectAllocationHeader_t;

Oop sysmel_behavior_allocateWithByteVariableSizedData(BehaviorRef behavior, size_t variableSizedData);
Oop sysmel_behavior_allocate(BehaviorRef behavior);

void sysmel_memory_safePoint(void);
void sysmel_gc_cycle(void);

#define SysmelClassAllocateWithByteVariableSizedData(className, variableSizedData) \
    (className*)sysmel_behavior_allocateWithByteVariableSizedData(&className ##_Class.super, variableSizedData)

#define SysmelClassAllocateWithSlotVariableSizedData(className, variableSizedData) \
    SysmelClassAllocateWithByteVariableSizedData(className, (variableSizedData)*sizeof(Oop))

#define SysmelClassAllocate(className) \
    SysmelClassAllocateWithByteVariableSizedData(className, 0)


#endif //SYSMEL_MEMORY_H