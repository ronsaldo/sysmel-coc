#include "memory.h"
#include <stdlib.h>

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

static uint8_t sysmel_gc_whiteColor = 0;
static uint8_t sysmel_gc_grayColor = 1;
static uint8_t sysmel_gc_blackColor = 2;

static size_t sysmel_memory_allocatedSize = 0;
static size_t sysmel_gc_triggerLimit = 1024*4;

static sysmel_ObjectAllocationHeader_t *firstAllocatedObject;
static sysmel_ObjectAllocationHeader_t *lastAllocatedObject;

Oop sysmel_class_allocateWithByteVariableSizedData(BehaviorRef behavior, size_t byteVariableSizedData)
{
    size_t classInstanceSize = behavior->instanceSize;
    size_t objectByteSize = classInstanceSize + byteVariableSizedData;
    size_t totalByteSize = sizeof(sysmel_ObjectAllocationHeader_t) + objectByteSize;
    
    sysmel_ObjectAllocationHeader_t *allocationHeader = calloc(1, totalByteSize);
    if(!firstAllocatedObject)
    {
        firstAllocatedObject = lastAllocatedObject = allocationHeader;
    }
    else
    {
        allocationHeader->previousObject = lastAllocatedObject;
        lastAllocatedObject->nextObject = allocationHeader;
        lastAllocatedObject = allocationHeader;
    }

    ObjectHeader* objectHeader = (ObjectHeader*)(allocationHeader + 1);
    objectHeader->__gcColor__ = sysmel_gc_whiteColor;
    objectHeader->__type__ = &behavior->super.super;
    objectHeader->__byteSize__ = objectByteSize;
    sysmel_memory_allocatedSize += totalByteSize;

    return (Oop)objectHeader;
}

Oop sysmel_class_allocate(BehaviorRef behavior)
{
    return sysmel_class_allocateWithByteVariableSizedData(behavior, 0);
}

void
sysmel_memory_safePoint(void)
{
    if(sysmel_memory_allocatedSize < sysmel_gc_triggerLimit)
        return;

    // Perform a GC cycle
    sysmel_gc_cycle();

    // Duplicate the GC limit if needed.
    size_t afterGC = sysmel_memory_allocatedSize;
    if (afterGC > sysmel_gc_triggerLimit)
        sysmel_gc_triggerLimit = afterGC * 2;
}

static size_t sysmel_gc_markingStackSize = 0;
static size_t sysmel_gc_markingStackCapacity = 0;
static Oop *sysmel_gc_markingStackElements;

void
sysmel_gc_swapColors(void)
{
    uint8_t white = sysmel_gc_blackColor;
    uint8_t black = sysmel_gc_whiteColor;

    sysmel_gc_whiteColor = white;
    sysmel_gc_blackColor = black;
}

void
sysmel_gc_cycle(void)
{
    // TODO: Implement this.
    //sysmel_gc_markRoots();
    //sysmel_gc_markStackElements();
    //// TODO: Clear weak objects.
    //sysmel_gc_sweepPhase();
    sysmel_gc_swapColors();
}

void
sysmel_memory_freeAll(void)
{
    // Free the allocation list.
    sysmel_ObjectAllocationHeader_t *position = firstAllocatedObject;
    while(position)
    {
        sysmel_ObjectAllocationHeader_t *oldPosition = position;
        position = position->nextObject;
        free(oldPosition);
    }

    firstAllocatedObject = lastAllocatedObject = NULL;
    sysmel_memory_allocatedSize = 0;
    
    // Marking stack
    sysmel_gc_markingStackSize = 0;
    sysmel_gc_markingStackCapacity = 0;
    free(sysmel_gc_markingStackElements);
}