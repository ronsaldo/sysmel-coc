#ifndef SYSMEL_PARSE_TREE_HPP
#define SYSMEL_PARSE_TREE_HPP

#include "SourceCode.hpp"
#include "Value.hpp"
#include <stdint.h>
#include <vector>
#include <assert.h>

typedef std::shared_ptr<struct ParseTreeNode> ParseTreeNodePtr;
typedef std::shared_ptr<struct ParseTreeParseErrorNode> ParseTreeParseErrorNodePtr;
typedef std::shared_ptr<struct ParseTreeArgumentDefinitionNode> ParseTreeArgumentDefinitionNodePtr;
typedef std::shared_ptr<struct ParseTreeFunctionTypeNode> ParseTreeFunctionTypeNodePtr;
typedef std::shared_ptr<struct ParseTreeFunctionNode> ParseTreeFunctionNodePtr;

struct ParseTreeNode : Value
{
    SourcePositionPtr sourcePosition;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
    {
        (void)context;
        fprintf(stderr, "analyzeAndEvaluateInContext not implemented in %s\n", dumpAsString().c_str());
        abort();
    }
    
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

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        return context->coreTypes->parseTreeNodeType;
    }

    virtual void splitMessageCascadeFirstMessage(ParseTreeNodePtr *outReceiver, ParseTreeNodePtr *outFirstMessage)
    {
        *outReceiver = std::static_pointer_cast<ParseTreeNode> (shared_from_this());
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

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto evaluatedValue = std::make_shared<IntegerValue> (context->coreTypes->integerType);
        evaluatedValue->value = value;
        return evaluatedValue;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralIntegerNode(" << value << ")";
    }
};

struct ParseTreeLiteralCharacterNode : ParseTreeNode
{
    uint32_t value;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto evaluatedValue = std::make_shared<CharacterValue> (context->coreTypes->characterType);
        evaluatedValue->value = value;
        return evaluatedValue;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralCharacterNode(" << value << ")";
    }
};

struct ParseTreeLiteralFloatNode : ParseTreeNode
{
    double value;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto evaluatedValue = std::make_shared<FloatValue> (context->coreTypes->floatType);
        evaluatedValue->value = value;
        return evaluatedValue;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralFloatNode(" << value << ")";
    }
};

struct ParseTreeLiteralStringNode : ParseTreeNode
{
    std::string value;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto evaluatedValue = std::make_shared<StringValue> (context->coreTypes->stringType);
        evaluatedValue->value = value;
        return evaluatedValue;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralStringNode(\"" << value << "\")";
    }
};

struct ParseTreeLiteralSymbolNode : ParseTreeNode
{
    std::string value;
    
    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto evaluatedValue = std::make_shared<SymbolValue> (context->coreTypes->symbolType);
        evaluatedValue->value = value;
        return evaluatedValue;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeLiteralSymbolNode(\"" << value << "\")";
    }
};

struct ParseTreeIdentifierReferenceNode : ParseTreeNode
{
    std::string value;
    
    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto binding = context->lexicalEnvironment->lookupSymbolRecursively(value);
        if(!binding)
        {
            sourcePosition->printOn(stderr);
            fprintf(stderr, ": Binding for symbol #%s is not available.\n", value.c_str());
            abort();
        }

        return binding->analyzeAndEvaluateIdentifierReferenceNodeInContext(std::static_pointer_cast<ParseTreeIdentifierReferenceNode> (shared_from_this()), context);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeIdentifierReferenceNode(" << value << ")";
    }
};

struct ParseTreeSequenceNode : ParseTreeNode
{
    std::vector<ParseTreeNodePtr> pragmas;
    std::vector<ParseTreeNodePtr> elements;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        ValuePtr result = context->coreTypes->voidValue;
        for(const auto &element : elements)
            result = context->visitExpression(element);
        return result;
    }

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

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        std::vector<ValuePtr> tupleValues;
        std::vector<TypePtr> tupleTypes;
        bool hasOnlyTypes = true;

        for(const auto &element : elements)
        {
            auto elementValue = context->visitDecayedExpression(element);
            tupleValues.push_back(elementValue);

            if(!elementValue->isType())
                hasOnlyTypes = false;
            
            auto elementType = elementValue->getTypeInContext(context);
            tupleTypes.push_back(elementType);
        }

        if(hasOnlyTypes && !tupleValues.empty())
        {
            std::vector<TypePtr> tupleValuesAsTypes;
            for(const auto &element : tupleValues)
                tupleValuesAsTypes.push_back(std::static_pointer_cast<Type> (element));

            auto tupleType = context->package->getOrCreateTupleType(tupleValuesAsTypes);
            return tupleType;
        }
        else
        {
            auto tupleType = context->package->getOrCreateTupleType(tupleTypes);

            auto tuple = std::make_shared<TupleValue> ();
            tuple->elements.swap(tupleValues);
            tuple->type = tupleType;
            return tuple;
        }
        
    }

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

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        ValuePtr keyValue = context->visitDecayedExpression(key);
        ValuePtr valueValue = context->coreTypes->nilValue;
        if(value)
            valueValue = context->visitDecayedExpression(value);

        bool hasOnlyTypes = keyValue->isType() && valueValue->isType();
        if(hasOnlyTypes)
        {
            auto keyType = std::static_pointer_cast<Type> (keyValue);
            auto valueType = std::static_pointer_cast<Type> (valueValue);
            return context->package->getOrCreateAssociationType(keyType, valueType);
        }
        else
        {
            auto keyType = keyValue->getTypeInContext(context);
            auto valueType = valueValue->getTypeInContext(context);
            
            auto associationType = context->package->getOrCreateAssociationType(keyType, valueType);
            auto association = std::make_shared<AssociationValue> ();
            association->key = keyValue;
            association->value = valueValue;
            return association;
        }
    }

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
    
    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override;
    
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
    
    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto bodyEnvironment = std::make_shared<LexicalEnvironment> (context->lexicalEnvironment);
        auto bodyContext = context->clone();
        bodyContext->lexicalEnvironment = bodyEnvironment;
        return bodyContext->visitExpression(body);
    }

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

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto functionalValue = context->visitDecayedExpression(functional);
        return functionalValue->analyzeAndEvaluateFunctionApplicationNodeInContext(std::static_pointer_cast<ParseTreeFunctionApplicationNode> (shared_from_this()), context);
    }

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

struct ParseTreeVariableDefinitionNode : ParseTreeNode
{
    ParseTreeNodePtr nameExpression;
    ParseTreeNodePtr typeExpression;
    ParseTreeNodePtr initialValue;
    bool isMutable = false;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        auto name = context->visitOptionalSymbolNode(nameExpression);
        TypePtr typeValue;
        if(typeExpression)
            typeValue = context->visitNodeExpectingType(typeExpression);

        ValuePtr initial;
        if(initialValue)
            initial = context->visitNodeWithExpectedType(initialValue, typeValue);

        if(!initial)
        {
            if (!typeValue)
            {
                sourcePosition->printOn(stderr);
                fprintf(stderr, ": At least a type or an initial value must be specified.\n");
                abort();
            }

            initial = typeValue->getOrCreateDefaultValue();
        }

        if(isMutable)
        {
            fprintf(stderr, "TODO: mutable ParseTreeVariableDefinitionNode::analyzeAndEvaluateInContext\n");
            abort();
        }
        else
        {
            if(!name.empty())
            {
                if(context->lexicalEnvironment->hasSymbolBinding(name))
                {
                    sourcePosition->printOn(stderr);
                    fprintf(stderr, ": symbol %s is already bound.\n", name.c_str());
                    abort();

                }

                context->lexicalEnvironment->setSymbolBinding(name, initial);
            }

            return initial;
        }
    }

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        if(nameExpression)
            nameExpression->collectParseErrorNodesIn(out);
        if(typeExpression)
            typeExpression->collectParseErrorNodesIn(out);
        if(initialValue)
            initialValue->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeVariableDefinitionNode(";
        if(nameExpression)
            nameExpression->dump(out);

        if(typeExpression)
        {
            out << ", ";
            typeExpression->dump(out);
        }
        
        if(initialValue)
        {
            out << ", ";
            initialValue->dump(out);
        }

        if(isMutable)
            out << "mutable";

        out << ")";
    }
};

struct ParseTreeIfExpressionNode : ParseTreeNode
{
    ParseTreeNodePtr condition;
    ParseTreeNodePtr trueExpression;
    ParseTreeNodePtr falseExpression;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        if(context->visitBooleanCondition(condition))
        {
            if(trueExpression)
                return context->visitExpression(trueExpression);
        }
        else
        {
            if(falseExpression)
                return context->visitExpression(falseExpression);
        }

        return context->coreTypes->voidValue;
    }

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        condition->collectParseErrorNodesIn(out);
        if(trueExpression)
            trueExpression->collectParseErrorNodesIn(out);
        if(falseExpression)
            falseExpression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeIfExpressionNode(";
        condition->dump(out);
        if(trueExpression)
        {
            out << ", ";
            trueExpression->dump(out);
        }
        
        if(falseExpression)
        {
            out << ", ";
            falseExpression->dump(out);
        }

        out << ")";
    }
};

struct ParseTreeWhileExpressionNode : ParseTreeNode
{
    ParseTreeNodePtr condition;
    ParseTreeNodePtr bodyExpresssion;
    ParseTreeNodePtr continueExpression;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        while(!condition || context->visitBooleanCondition(condition))
        {
            if(bodyExpresssion)
                return context->visitExpression(bodyExpresssion);
            if(continueExpression)
                return context->visitExpression(continueExpression);
        }
        
        return context->coreTypes->voidValue;
    }

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        if(condition)
            condition->collectParseErrorNodesIn(out);
        if(bodyExpresssion)
            bodyExpresssion->collectParseErrorNodesIn(out);
        if(continueExpression)
            continueExpression->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeWhileExpressionNode(";
        condition->dump(out);
        if(bodyExpresssion)
        {
            out << ", ";
            bodyExpresssion->dump(out);
        }
        
        if(continueExpression)
        {
            out << ", ";
            continueExpression->dump(out);
        }

        out << ")";
    }
};

struct ParseTreeDoWhileExpressionNode : ParseTreeNode
{
    ParseTreeNodePtr bodyExpresssion;
    ParseTreeNodePtr continueExpression;
    ParseTreeNodePtr condition;

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context) override
    {
        do 
        {
            if(bodyExpresssion)
                return context->visitExpression(bodyExpresssion);
            if(continueExpression)
                return context->visitExpression(continueExpression);
        } while(!condition || context->visitBooleanCondition(condition));

        return context->coreTypes->voidValue;
    }

    virtual void collectParseErrorNodesIn(std::vector<ParseTreeParseErrorNodePtr> &out) override
    {
        if(bodyExpresssion)
            bodyExpresssion->collectParseErrorNodesIn(out);
        if(continueExpression)
            continueExpression->collectParseErrorNodesIn(out);
        if(condition)
            condition->collectParseErrorNodesIn(out);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ParseTreeDoWhileExpressionNode(";
        if(bodyExpresssion)
        {
            bodyExpresssion->dump(out);
        }
        
        if(continueExpression)
        {
            out << ", ";
            continueExpression->dump(out);
        }

        out << ", ";
        condition->dump(out);

        out << ")";
    }
};
#endif //SYSMEL_PARSE_TREE_HPP