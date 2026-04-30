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

    virtual void dump(FILE *out) = 0;
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
    
    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeParseErrorNode(%s", errorMessage.c_str());
        if(innerNode)
            innerNode->dump(out);
        fprintf(out, ")");
    }
};

struct ParseTreeLiteralIntegerNode : ParseTreeNode
{
    int64_t value;
    
    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeLiteralIntegerNode(%lld)", (long long int)value);
    }
};

struct ParseTreeLiteralCharacterNode : ParseTreeNode
{
    uint32_t value;

    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeLiteralCharacterNode(%c)", value);
    }
};

struct ParseTreeLiteralFloatNode : ParseTreeNode
{
    double value;

    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeLiteralFloatNode(%f)", value);
    }
};

struct ParseTreeLiteralStringNode : ParseTreeNode
{
    std::string value;

    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeLiteralStringNode(\"%s\")", value.c_str());
    }
};

struct ParseTreeLiteralSymbolNode : ParseTreeNode
{
    std::string value;
    
    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeLiteralSymbolNode(\"%s\")", value.c_str());
    }
};

struct ParseTreeSequenceNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> elements;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        for(auto &element : elements)
            element->collectParseErrorNodesIn(out);
    }

    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeSequenceNode(");
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                fprintf(out, ", ");
            elements[i]->dump(out);
        }
        fprintf(out, ")");
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

    virtual void dump(FILE *out) override
    {
        fprintf(out, "ParseTreeTupleNode(");
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                fprintf(out, ", ");
            elements[i]->dump(out);
        }
        fprintf(out, ")");
    }
};

#endif //SYSMEL_PARSE_TREE_HPP