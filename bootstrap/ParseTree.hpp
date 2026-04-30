#ifndef SYSMEL_PARSE_TREE_HPP
#define SYSMEL_PARSE_TREE_HPP

#include "SourceCode.hpp"
#include <memory>
#include <stdint.h>
#include <vector>

typedef std::shared_ptr<struct ParseTreeNode> ParseTreeNodePtr;
typedef std::shared_ptr<struct ParseTreeParseErrorNode> ParseTreeParseErrorNodePtr;

struct ParseTreeNode : std::enable_shared_from_this<ParseTreeNode>
{
    SourcePositionPtr sourcePosition;
    
    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out)
    {
        (void)out;
    }
    
    std::vector<ParseTreeParseErrorNodePtr> collectParseErrorNodes()
    {
        std::vector<ParseTreeParseErrorNodePtr> errors;
        collectParseErrorNodesIn(errors);
        return errors;
    }

};

struct ParseTreeParseErrorNode : ParseTreeNode
{
    std::string errorMessage;
    ParseTreeNodePtr innerNode;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        out.push_back(std::static_pointer_cast<ParseTreeParseErrorNode> (shared_from_this()));
        if(innerNode)
            innerNode->collectParseErrorNodesIn(out);
    }
};

struct ParseTreeLiteralIntegerNode : ParseTreeNode
{
    int64_t value;
};

struct ParseTreeLiteralCharacterNode : ParseTreeNode
{
    uint32_t value;
};

struct ParseTreeLiteralFloatNode : ParseTreeNode
{
    double value;
};

struct ParseTreeLiteralStringNode : ParseTreeNode
{
    std::string value;
};

struct ParseTreeLiteralSymbolNode : ParseTreeNode
{
    std::string value;
};

struct ParseTreeSequenceNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> elements;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        for(auto &element : elements)
            element->collectParseErrorNodesIn(out);
    }
};

struct ParseTreeTupleNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> elements;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        for(auto &element : elements)
            element->collectParseErrorNodesIn(out);
    }
};

#endif //SYSMEL_PARSE_TREE_HPP