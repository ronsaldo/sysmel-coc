#ifndef SYSMEL_SOURCE_CODE_HPP
#define SYSMEL_SOURCE_CODE_HPP

#include <memory>
#include <string>
#include <stdio.h>

typedef std::shared_ptr<struct SourceCode> SourceCodePtr;
typedef std::shared_ptr<struct SourcePosition> SourcePositionPtr;

typedef std::shared_ptr<struct Package> PackagePtr;
typedef std::shared_ptr<struct CoreTypeAndMacros> CoreTypeAndMacrosPtr;

struct SourceCode
{
    std::string text;
    std::string name;
    std::string directory;
};

struct SourcePosition
{
    SourceCodePtr sourceCode;
    int32_t startIndex = -1;
    int32_t endIndex = -1;
    int32_t startLine = -1;
    int32_t endLine = -1;
    int32_t startColumn = -1;
    int32_t endColumn = -1;

    SourcePositionPtr to(const SourcePositionPtr &end) const
    {
        auto merged = std::make_shared<SourcePosition> ();
        merged->sourceCode = sourceCode;
        
        merged->startIndex  = startIndex;
        merged->startLine   = startLine;
        merged->startColumn = startColumn;
        merged->endIndex    = end->endIndex;
        merged->endLine     = end->endLine;
        merged->endColumn   = end->endColumn;
        return merged;
    }

    SourcePositionPtr until(const SourcePositionPtr &end) const
    {
        auto merged = std::make_shared<SourcePosition> ();
        merged->sourceCode = sourceCode;
        
        merged->startIndex  = startIndex;
        merged->startLine   = startLine;
        merged->startColumn = startColumn;
        merged->endIndex    = end->startIndex;
        merged->endLine     = end->startLine;
        merged->endColumn   = end->startColumn;
        return merged;
    }

    std::string getText()
    {
        return sourceCode->text.substr(startIndex, endIndex - startIndex);
    }

    void printOn(FILE *out)
    {
        if(!sourceCode->directory.empty())
            fprintf(out, "%s/", sourceCode->directory.c_str());
        fprintf(out, "%s:%d.%d-%d-%d:", sourceCode->name.c_str(), startLine, startColumn, endLine, endColumn);
    }
};

bool sourceCode_evaluate(const SourceCodePtr &sourceCode, const CoreTypeAndMacrosPtr &coreTypes, const PackagePtr &package, bool printResult);
SourceCodePtr sourceCode_createForFileNamed(const std::string &filename);

#endif //SYSMEL_META_MODEL_H