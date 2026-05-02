#include "SourceCode.hpp"
#include "Scanner.hpp"
#include "Parser.hpp"
#include "Utility.hpp"
#include <stdio.h>

bool
sourceCode_printParseTree(const SourceCodePtr &sourceCode)
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

    printf("%s\n", parseTree->dumpAsString().c_str());
    return true;
}


bool
sourceCode_evaluate(const SourceCodePtr &sourceCode, const CoreTypeAndMacrosPtr &coreTypes, const PackagePtr &package, bool printResult)
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
    evaluationContext->package = package;
    evaluationContext->lexicalEnvironment = std::make_shared<LexicalEnvironment> (
        std::make_shared<PackageEnvironment> (std::make_shared<EmptyEnvironment> (), package)
    );

    evaluationContext->lexicalEnvironment->setSymbolBinding("__FileDir__", std::make_shared<StringValue> (coreTypes->stringType, sourceCode->directory));
    evaluationContext->lexicalEnvironment->setSymbolBinding("__FileName__", std::make_shared<StringValue> (coreTypes->stringType, sourceCode->name));

    auto value = parseTree->analyzeAndEvaluateInContext(evaluationContext);
    if(printResult)
        printf("%s\n", value->dumpAsString().c_str());

    return true;
}

SourceCodePtr
sourceCode_createForFileNamed(const std::string &filename)
{
    auto sourceCode = std::make_shared<SourceCode> ();

    FILE *sourceFile = fopen(filename.c_str(), "rb");
    if(!sourceFile)
    {
        perror("Failed to open file.");
        return nullptr;
    }

    // Get the file size.
    fseek(sourceFile, 0, SEEK_END);
    size_t sourceFileSize = ftell(sourceFile);
    fseek(sourceFile, 0, SEEK_SET);

    sourceCode->text.resize(sourceFileSize);

    char *textBuffer = (char*)malloc(sourceFileSize);

    if(fread(textBuffer, sourceFileSize, 1, sourceFile) != 1)
    {
        fclose(sourceFile);
        free(textBuffer);
        perror("Failed to read file.");
        return nullptr;
    }

    fclose(sourceFile);

    sourceCode->directory = path_dirname(filename);
    sourceCode->name = path_basename(filename);
    sourceCode->text = std::string(textBuffer, textBuffer + sourceFileSize);
    free(textBuffer);

    return sourceCode;
}
