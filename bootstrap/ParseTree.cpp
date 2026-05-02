#include "ParseTree.hpp"
#include "SourceCode.hpp"
#include "Utility.hpp"

ValuePtr
ParseTreeBinaryExpressionSequenceNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    assert(elements.size() >= 1);
    auto previous = elements[0];

    for(size_t i = 1; i < elements.size(); i += 2)
    {
        auto operatorSymbol = elements[i];
        auto operand = elements[i + 1];

        auto send = std::make_shared<ParseTreeMessageSendNode> ();
        send->sourcePosition = sourcePosition;
        send->receiver = previous;
        send->selector = operatorSymbol;
        send->arguments.push_back(operand);
        previous = send;
    }

    return context->visitExpression(previous);
}

ValuePtr ParseTreeLoadFileNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    auto fileNameValue = context->visitStringNode(fileName);
    
    auto fileDirBinding = context->lexicalEnvironment->lookupSymbolRecursively("__FileDir__");
    assert(fileDirBinding->isStringValue());

    auto dirname = std::static_pointer_cast<StringValue> (fileDirBinding)->value;

    auto filePath = path_join(dirname, fileNameValue);

    auto sourceCode = sourceCode_createForFileNamed(filePath);
    if(!sourceCode)
    {
        sourcePosition->printOn(stderr);
        fprintf(stderr, " Failed to open source file '%s'.\n", filePath.c_str());
        abort();
    }

    sourceCode_evaluate(sourceCode, context->coreTypes, context->package, false);
    return context->coreTypes->voidValue;
}

ValuePtr
ParseTreeAddMethodNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    auto ownerValue = context->visitDecayedExpression(owner);
    if(!ownerValue->isType())
    {
        sourcePosition->printOn(stderr);
        fprintf(stderr, " Expected a type or template for adding a method.\n");
        abort();
    }

    TypePtr ownerValueType = std::static_pointer_cast<Type> (ownerValue);
    auto methodNode = method->copyWithSelfType(ownerValueType);

    printf("TODO: ParseTreeAddMethodNode::analyzeAndEvaluateInContext\n");
    abort();
}
