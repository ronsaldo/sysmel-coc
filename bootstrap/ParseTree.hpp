#ifndef SYSMEL_PARSE_TREE_HPP
#define SYSMEL_PARSE_TREE_HPP

#include "SourceCode.hpp"
#include <memory>
#include <stdint.h>
#include <vector>
#include <ostream>
#include <sstream>

typedef std::shared_ptr<struct ParseTreeNode> ParseTreeNodePtr;
typedef std::shared_ptr<struct ParseTreeParseErrorNode> ParseTreeParseErrorNodePtr;
typedef std::shared_ptr<struct ParseTreeArgumentDefinitionNode> ParseTreeArgumentDefinitionNodePtr;
typedef std::shared_ptr<struct ParseTreeFunctionTypeNode> ParseTreeFunctionTypeNodePtr;
typedef std::shared_ptr<struct ParseTreeFunctionNode> ParseTreeFunctionNodePtr;

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

    virtual void dump(std::ostream &out) = 0;
    std::string dumpAsString()
    {
        std::ostringstream out;
        dump(out);
        return out.str();
    }

    virtual void splitMessageCascadeFirstMessage(ParseTreeNodePtr *outReceiver, ParseTreeNodePtr *outFirstMessage)
    {
        *outReceiver = shared_from_this();
        *outFirstMessage = nullptr;
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
    
    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeParseErrorNode(" << errorMessage;
        if(innerNode)
            innerNode->dump(out);
        out << ")";
    }
};

struct ParseTreeLiteralIntegerNode : ParseTreeNode
{
    int64_t value;
    
    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralIntegerNode(" << value << ")";
    }
};

struct ParseTreeLiteralCharacterNode : ParseTreeNode
{
    uint32_t value;

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralCharacterNode(" << value << ")";
    }
};

struct ParseTreeLiteralFloatNode : ParseTreeNode
{
    double value;

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralFloatNode(" << value << ")";
    }
};

struct ParseTreeLiteralStringNode : ParseTreeNode
{
    std::string value;

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralStringNode(\"" << value << "\")";
    }
};

struct ParseTreeLiteralSymbolNode : ParseTreeNode
{
    std::string value;
    
    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralSymbolNode(\"" << value << "\")";
    }
};

struct ParseTreeIdentifierReferenceNode : ParseTreeNode
{
    std::string value;
    
    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeIdentifierReferenceNode(" << value << ")";
    }
};

struct ParseTreeSequenceNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> pragmas;
    std::vector<ParseTreeNodePtr> elements;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        for(auto &pragma : pragmas)
            pragma->collectParseErrorNodesIn(out);
        for(auto &element : elements)
            element->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeSequenceNode([";
        for(size_t i = 0; i < pragmas.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            pragmas[i]->dump(out);
        }
        out << "], [";
     
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << "])";
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

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeTupleNode(";
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << ")";
    }
};

struct ParseTreeAssignmentNode : ParseTreeNode
{
    ParseTreeNodePtr store;
    ParseTreeNodePtr value;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        store->collectParseErrorNodesIn(out);
        value->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeAssignmentNode(";
        store->dump(out);
        out << ", ";
        value->dump(out);
        out << ")";
    }
};

struct ParseTreeAssociationNode : ParseTreeNode
{
    ParseTreeNodePtr key;
    ParseTreeNodePtr value;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        key->collectParseErrorNodesIn(out);
        if(value)
            value->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeAssociationNode(";
        key->dump(out);
        out << ", ";
        if(value)
            value->dump(out);
        out << ")";
    }
};

struct ParseTreeDictionaryNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> elements;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        for(auto &element : elements)
            element->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeDictionaryNode(";
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << ")";
    }
};

struct ParseTreeBinaryExpressionSequenceNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> elements;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        for(auto &arg : elements)
            arg->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeBinaryExpressionSequenceNode(";
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << ")";
    }
};

struct ParseTreeArgumentDefinitionNode : ParseTreeNode
{
    std::string name;
    ParseTreeNodePtr typeExpression;
    bool isSelf = false;
    
    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        if(typeExpression)
            typeExpression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeArgumentDefinitionNode(" << name;
        if(typeExpression)
        {
            out << ", ";
            typeExpression->dump(out);
        }
        out << ")";
    }
};

struct ParseTreeFunctionTypeNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> argumentDefinitions;
    ParseTreeNodePtr resultTypeExpression;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        if(resultTypeExpression)
            resultTypeExpression->collectParseErrorNodesIn(out);

        for(auto &arg : argumentDefinitions)
            arg->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeFunctionTypeNode([";

        for(size_t i = 0; i < argumentDefinitions.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            argumentDefinitions[i]->dump(out);
        }

        out << "]";
        if(resultTypeExpression)
        {
            out << ", ";
            resultTypeExpression->dump(out);
        }

        out << ")";
    }
};

struct ParseTreeFunctionNode : ParseTreeNode
{
    ParseTreeNodePtr nameExpression;
    ParseTreeFunctionTypeNodePtr functionType;
    ParseTreeNodePtr body;
    bool isPublic = false;
    bool isMacro = false;
    bool isCompileTime = false;
    bool isTemplate = false;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        if(nameExpression)
            nameExpression->collectParseErrorNodesIn(out);

        functionType->collectParseErrorNodesIn(out);

        if(body)
            body->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeFunctionNode(";
        if(nameExpression)
        {
            nameExpression->dump(out);
            out << ", ";
        }
        
        functionType->dump(out);
        
        if(body)
        {
            out << ", ";
            body->dump(out);
        }

        out << ")";
    }
};

struct ParseTreeLexicalBlockNode : ParseTreeNode
{
    ParseTreeNodePtr body;
    
    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLexicalBlockNode(";
        body->dump(out);
        out << ")";
    }
};

struct ParseTreeFunctionApplicationNode : ParseTreeNode
{
    ParseTreeNodePtr functional;
    std::vector<ParseTreeNodePtr> arguments;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        functional->collectParseErrorNodesIn(out);
        for(auto &arg : arguments)
            arg->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeFunctionApplicationNode(";
        functional->dump(out);

        out << ", [";
        for(size_t i = 0; i < arguments.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            arguments[i]->dump(out);
        }
        out << "])";
    }
};

struct ParseTreePragmaNode : ParseTreeNode
{
    ParseTreeNodePtr selector;
    std::vector<ParseTreeNodePtr> arguments;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        selector->collectParseErrorNodesIn(out);
        for(auto &arg : arguments)
            arg->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreePragmaNode(";
        selector->dump(out);

        out << ", [";
        for(size_t i = 0; i < arguments.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            arguments[i]->dump(out);
        }
        out << "])";
    }
};

struct ParseTreeCascadedMessageNode : ParseTreeNode
{
    ParseTreeNodePtr selector;
    std::vector<ParseTreeNodePtr> arguments;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        selector->collectParseErrorNodesIn(out);
        for(auto &arg : arguments)
            arg->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeCascadedMessageNode(";
        selector->dump(out);

        out << ", [";
        for(size_t i = 0; i < arguments.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            arguments[i]->dump(out);
        }
        out << "])";
    }
};

struct ParseTreeMessageSendNode : ParseTreeNode
{
    ParseTreeNodePtr receiver;
    ParseTreeNodePtr selector;
    std::vector<ParseTreeNodePtr> arguments;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        receiver->collectParseErrorNodesIn(out);
        selector->collectParseErrorNodesIn(out);
        for(auto &arg : arguments)
            arg->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeMessageSendNode(";
        receiver->dump(out);
        out << ", ";
        selector->dump(out);

        out << ", [";
        for(size_t i = 0; i < arguments.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            arguments[i]->dump(out);
        }
        out << "])";
    }

    virtual void splitMessageCascadeFirstMessage(ParseTreeNodePtr *outReceiver, ParseTreeNodePtr *outFirstMessage)
    {
        auto cascadedMessage = std::make_shared<ParseTreeCascadedMessageNode> ();
        cascadedMessage->sourcePosition = sourcePosition;
        cascadedMessage->selector = selector;
        cascadedMessage->arguments = arguments;

        *outReceiver = receiver;
        *outFirstMessage = cascadedMessage;
    }
};

struct ParseTreeMessageCascadeNode : ParseTreeNode
{
    ParseTreeNodePtr receiver;
    std::vector<ParseTreeNodePtr> messages;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        receiver->collectParseErrorNodesIn(out);
        for(auto &message : messages)
            message->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeMessageCascadeNode(";
        receiver->dump(out);

        out << ", [";
        for(size_t i = 0; i < messages.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            messages[i]->dump(out);
        }
        out << "])";
    }
};

struct ParseTreeQuoteNode : ParseTreeNode
{
    ParseTreeNodePtr expression;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        expression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeQuoteNode(";
        expression->dump(out);
        out << ")";
    }
};

struct ParseTreeQuasiQuoteNode : ParseTreeNode
{
    ParseTreeNodePtr expression;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        expression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeQuasiQuoteNode(";
        expression->dump(out);
        out << ")";
    }
};

struct ParseTreeQuasiUnquoteNode : ParseTreeNode
{
    ParseTreeNodePtr expression;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        expression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeQuasiUnquoteNode(";
        expression->dump(out);
        out << ")";
    }
};

struct ParseTreeSpliceNode : ParseTreeNode
{
    ParseTreeNodePtr expression;

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        expression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeSpliceNode(";
        expression->dump(out);
        out << ")";
    }
};

#endif //SYSMEL_PARSE_TREE_HPP