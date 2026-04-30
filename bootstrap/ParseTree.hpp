#ifndef SYSMEL_PARSE_TREE_HPP
#define SYSMEL_PARSE_TREE_HPP

#include "SourceCode.hpp"
#include <memory>

typedef std::shared_ptr<struct ParseTreeNode> ParseTreeNodePtr;

struct ParseTreeNode
{
    SourcePositionPtr sourcePosition;
};

struct ParseTreeErrorNode : ParseTreeNode
{
    std::string errorMessage;
};


#endif //SYSMEL_PARSE_TREE_HPP