#include "Scanner.hpp"
#include "Parser.hpp"
#include <stdio.h>

static CoreTypeAndMacrosPtr coreTypes;
static PackagePtr corePackage;

void
printHelp()
{
    printf("sysmelb <options> <scriptToEvaluate>");
}

void
printVersion()
{
    printf("sysmelb 0.1");
}

bool
evaluateCommandLineString(const std::string &cliString, bool printResult)
{
    auto sourceCode = std::make_shared<SourceCode> ();
    sourceCode->name = "<cli>";
    sourceCode->text = cliString;
    return sourceCode_evaluate(sourceCode, coreTypes, corePackage, printResult);
}

bool
evaluateSourceFileNamed(const std::string &sourceFileName)
{
    auto sourceCode = sourceCode_createForFileNamed(sourceFileName);
    return sourceCode_evaluate(sourceCode, coreTypes, corePackage, false);
}

int main(int argc, const char *argv[])
{
    corePackage = std::make_shared<Package> ();
    corePackage->name = "SysmelCore";

    coreTypes = std::make_shared<CoreTypeAndMacros> ();
    coreTypes->registerInPackage(corePackage);

    for(int i = 1; i < argc; ++i)
    {
        std::string arg = argv[i];
        if(arg[0] == '-')
        {
            if(arg == "-help")
            {
                printHelp();
            }
            else if(arg == "-version")
            {
                printVersion();
            }
            else if(arg == "-eval")
            {
                arg = argv[++i];
                evaluateCommandLineString(arg, false);
            }
            else if(arg == "-print-eval")
            {
                arg = argv[++i];
                evaluateCommandLineString(arg, true);
            }
        }
        else
        {
            evaluateSourceFileNamed(arg);
        }
    }

    return 0;
}
