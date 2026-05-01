#include "Scanner.hpp"
#include "Parser.hpp"
#include <stdio.h>

static CoreTypesPtr coreTypes;
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
evaluateSourceCode(const SourceCodePtr &sourceCode)
{
    // Scan the source code.
    auto scannedTokens = SysmelScanSourceCode(sourceCode);
    if(!checkScannedTokensForErrors(scannedTokens))
        return false;

    // Parse and check syntax errors.
    auto parseTree = SysmelParseTokenSequence(scannedTokens);
    auto parseTreeErrorNodes = parseTree->collectParseErrorNodes();
    for(auto &errorNode : parseTreeErrorNodes)
    {
        errorNode->sourcePosition->printOn(stderr);
        fprintf(stderr, " %s\n", errorNode->errorMessage.c_str());
    }

    if(!parseTreeErrorNodes.empty())
        return false;

    //printf("%s\n", parseTree->dumpAsString().c_str());

    auto evaluationContext = std::make_shared<EvaluationContext> ();
    evaluationContext->coreTypes = coreTypes;
    evaluationContext->package = corePackage;

    auto value = parseTree->analyzeAndEvaluateInContext(evaluationContext);
    printf("%s\n", value->dumpAsString().c_str());

    return true;
}

bool
evaluateCommandLineString(const std::string &cliString)
{
    auto sourceCode = std::make_shared<SourceCode> ();
    sourceCode->name = "<cli>";
    sourceCode->text = cliString;
    return evaluateSourceCode(sourceCode);
}

int main(int argc, const char *argv[])
{
    corePackage = std::make_shared<Package> ();
    corePackage->name = "SysmelCore";

    coreTypes = std::make_shared<CoreTypes> ();
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
                evaluateCommandLineString(arg);
            }
        }
        else
        {

        }
    }

    return 0;
}
