#include "Scanner.hpp"
#include <stdio.h>

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

void
evaluateSourceCode(const SourceCodePtr &sourceCode)
{
    auto scannedTokens = SysmelScanSourceCode(sourceCode);
    for(auto &token : scannedTokens)
    {
        printf("Token kind %s\n", SysmelTokenKind_toString(token->kind));
    }
}

void
evaluateCommandLineString(const std::string &cliString)
{
    auto sourceCode = std::make_shared<SourceCode> ();
    sourceCode->name = "<cli>";
    sourceCode->text = cliString;
    return evaluateSourceCode(sourceCode);

}

int main(int argc, const char *argv[])
{
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
                evaluateCommandLineString(arg);
            }
        }
        else
        {

        }
    }

    return 0;
}
