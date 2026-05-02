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

ValuePtr
ParseTreeArgumentDefinitionNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    ValuePtr typeValue;
    if(typeExpression)
        typeValue = context->visitNodeExpectingType(typeExpression);
    if(!typeValue)
        typeValue = context->coreTypes->dynamicType;

    auto argumentDefinitionValue = std::make_shared<ArgumentDefinitionValue> ();
    argumentDefinitionValue->name = name;
    argumentDefinitionValue->typeExpression = typeValue;
    return argumentDefinitionValue;
}

ValuePtr
ParseTreeFunctionTypeNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    auto signatureAnalysisEnvironment = std::make_shared<FunctionalSignatureAnalysisEnvironment> (context->lexicalEnvironment);
    auto analysisContext = context->clone();
    analysisContext->lexicalEnvironment = signatureAnalysisEnvironment;

    // Arguments.
    std::vector<ArgumentDefinitionValuePtr> argumentValues;
    argumentValues.reserve(argumentDefinitions.size());
    for(size_t i = 0; i < argumentDefinitions.size(); ++i)
    {
        auto argumentDefinitionValue = analysisContext->visitExpression(argumentDefinitions[i]);
        assert(argumentDefinitionValue->isArgumentDefinitionValue());

        auto argumentValue = std::static_pointer_cast<ArgumentDefinitionValue> (argumentDefinitionValue);
        argumentValue->index = i;
        
        signatureAnalysisEnvironment->addArgument(argumentValue);
        argumentValues.push_back(argumentValue);
    }

    // Result type.
    ValuePtr resultType = context->coreTypes->dynamicType;
    if(resultTypeExpression)
        resultType = context->visitNodeExpectingType(resultTypeExpression);

    auto functionType = std::make_shared<DependentFunctionType> ();
    functionType->arguments = argumentValues;
    functionType->resultTypeExpression = resultType;
    functionType->hasDependentArgs = !signatureAnalysisEnvironment->dependentArguments.empty();
    return functionType;
}

ValuePtr
ParseTreeFunctionNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    auto functionTypeValue = context->visitExpression(functionType);
    printf("TODO: ParseTreeFunctionNode\n");
    abort();
}

ValuePtr
ParseTreeLoadFileNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
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
