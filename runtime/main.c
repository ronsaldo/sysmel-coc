#include "common.h"

extern Oop SysmelMain(void);

void
sysmel_initializeRuntime(void)
{
    sysmel_initializeClasses()
}

int main(int argc, const char *argv[])
{
    (void)argc;
    (void)argv;
    return SysmelMain();
}
