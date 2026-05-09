#include "common.h"

extern Oop SysmelMain(void);

void sysmel_initializeNumberPrimitives(void);
void sysmel_initializeObjectPrimitives(void);
void sysmel_initializeStringPrimitives(void);
void sysmel_initializeSymbolPrimitives(void);

void
sysmel_initializePrimitives(void)
{
    sysmel_initializeNumberPrimitives();
    sysmel_initializeStringPrimitives();
    sysmel_initializeSymbolPrimitives();
}

void
sysmel_initializeRuntime(void)
{
    sysmel_initializeClasses();
    sysmel_initializePrimitives();
}

int main(int argc, const char *argv[])
{
    (void)argc;
    (void)argv;
    printf("Class_Class size %zu\n", sizeof(Class_Class));
    printf("Metaclass_Class size %zu\n", sizeof(Metaclass_Class));

    sysmel_initializeRuntime();
    return SysmelMain();
}
