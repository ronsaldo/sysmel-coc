#ifndef SYSMEL_SOURCE_CODE_HPP
#define SYSMEL_SOURCE_CODE_HPP

#include <memory>
#include <string>

typedef std::shared_ptr<struct SourceCode> SourceCodePtr;
typedef std::shared_ptr<struct SourcePosition> SourcePositionPtr;

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

    std::string getText()
    {
        return sourceCode->text.substr(startIndex, endIndex - startIndex);
    }
};

#endif //SYSMEL_META_MODEL_H