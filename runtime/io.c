#include "common.h"
#include <stdio.h>

void __sysmel_io_print(Oop receiver)
{
    StringRef string = sysmel_object_printString(receiver);
    printf("%.*s", (int)sysmel_string_getSize(string), string->__elements__);
}

void __sysmel_io_printLine(Oop receiver)
{
    StringRef string = sysmel_object_printString(receiver);
    printf("%.*s\n", (int)sysmel_string_getSize(string), string->__elements__);
}

void __sysmel_io_writeLine(Oop oop)
{
    StringRef string = sysmel_object_asString(oop);
    printf("%.*s\n", (int)sysmel_string_getSize(string), string->__elements__);
}
