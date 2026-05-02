#include "Value.hpp"
#include "ParseTree.hpp"
#include <sstream>

ValuePtr
Value::analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context)
{
    (void)context;
    applicationNode->sourcePosition->printOn(stderr);
    fprintf(stderr, " Cannot apply to non-functional value.\n");
    abort();
}

ValuePtr
Value::analyzeAndEvaluateAssignmentNodeInContext(const ParseTreeAssignmentNodePtr &assignmentNode, const EvaluationContextPtr &context)
{
    (void)context;
    assignmentNode->sourcePosition->printOn(stderr);
    fprintf(stderr, " Cannot assign non-assignable value.\n");
    abort();
}

void
Value::enqueuePendingAnalysis(const PackagePtr &package)
{
    package->pendingAnalysisQueue.push_back(shared_from_this());
}

TypePtr
Type::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->propType;
}

bool Type::isSatisfiedByValue(const ValuePtr &value, const EvaluationContextPtr &context) const
{
    return isSatisfiedByType(value->getTypeInContext(context));
}

bool Type::isSatisfiedByType(const TypePtr &otherType) const
{
    return this == otherType.get();
}

TypePtr
UniverseType::getTypeInContext(const EvaluationContextPtr &context)
{
    (void)context;
    if (!type)
    {
        std::ostringstream typeName;
        typeName << "Type@" << (level + 1);
        type = std::make_shared<UniverseType> (typeName.str(), level + 1);
    }
    return type;
}

ValuePtr
ReferenceValue::analyzeAndEvaluateAssignmentNodeInContext(const ParseTreeAssignmentNodePtr &assignmentNode, const EvaluationContextPtr &context)
{
    auto castedValue = context->visitNodeWithExpectedType(assignmentNode->value, type->baseType);
    storeValue(castedValue);
    return shared_from_this();
}

TypePtr
TupleType::getTypeInContext(const EvaluationContextPtr &context)
{
    // TODO: Use the max universe.
    return context->coreTypes->propType;
}

TypePtr
AssociationType::getTypeInContext(const EvaluationContextPtr &context)
{
    // TODO: Use the max universe.
    return context->coreTypes->propType;
}

TypePtr
ArgumentDefinitionValue::getTypeInContext(const EvaluationContextPtr &context)
{
    // TODO: Use the max universe.
    return context->coreTypes->argumentDefinitionValue;
}

TypePtr
DependentFunctionType::getTypeInContext(const EvaluationContextPtr &context)
{
    // TODO: Use the max universe.
    return context->coreTypes->propType;
}

TypePtr DependentFunctionType::simplify()
{
    if(!hasDependentArgs || !resultTypeExpression->isType())
    {
        std::vector<TypePtr> argumentTypes;
        argumentTypes.reserve(arguments.size());
        for(auto &arg : arguments)
        {
            if(!arg->typeExpression->isType())
                return std::static_pointer_cast<DependentFunctionType> (shared_from_this());

            argumentTypes.push_back(std::static_pointer_cast<Type> (arg->typeExpression));
        }

        auto simpleType = std::make_shared<SimpleFunctionType> ();
        simpleType->argumentTypes.swap(argumentTypes);
        simpleType->resultType = std::static_pointer_cast<Type> (resultTypeExpression);
        return simpleType;
    }

    return std::static_pointer_cast<DependentFunctionType> (shared_from_this());
}

std::vector<ValuePtr>
SimpleFunctionType::analyzeAndEvaluationFunctionApplicationArgumentsInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context)
{
    auto argumentCount = argumentTypes.size();
    if(argumentCount != applicationNode->arguments.size())
    {
        applicationNode->sourcePosition->printOn(stderr);
        fprintf(stderr, " Expected %d arguments instead of %d.\n", int(applicationNode->arguments.size()), int(argumentCount));
        abort();
    }

    std::vector<ValuePtr> typecheckedArguments;
    typecheckedArguments.reserve(argumentCount);
    for(size_t i = 0; i < argumentCount; ++i)
    {
        auto checkedArgument =context->visitNodeWithExpectedType(applicationNode->arguments[i], argumentTypes[i]);
        typecheckedArguments.push_back(checkedArgument);
    }

    return typecheckedArguments;
}

TypePtr SimpleFunctionType::getTypeInContext(const EvaluationContextPtr &context)
{
    // TODO: Use the max universe.
    return context->coreTypes->propType;
}

void
FunctionValue::ensureAnalysis()
{
    if(isAnalyzed)
        return;
    if(isTemplate)
        return;

    isAnalyzed = true;
}

ValuePtr
FunctionValue::evaluateWithArgumentsAndCaptures(const std::vector<ValuePtr> &arguments, const std::vector<ValuePtr> &captures)
{
    ensureAnalysis();

    (void)arguments;
    (void)captures;

    printf("TODO: evaluateWithArgumentsAndCaptures\n");
    abort();
}

ValuePtr FunctionValue::evaluateWithArgumentsViaParseTree(const std::vector<ValuePtr> &arguments)
{
    ensureAnalysis();

    // Make the activation context.
    auto activationEnvironment = std::make_shared<FunctionalActivationEnvironment> (definitionContext->lexicalEnvironment);
    auto activationContext = definitionContext->clone();
    activationContext->lexicalEnvironment = activationEnvironment;

    // Arguments
    assert(arguments.size() == dependentFunctionType->arguments.size());
    auto argumentCount = arguments.size();
    for(size_t i = 0; i < argumentCount; ++i)
    {
        auto argumentValue = arguments[i];
        auto argumentDefinition = dependentFunctionType->arguments[i];
        auto expectedArgumentTypeValue = argumentDefinition->typeExpression->analyzeAndEvaluateInContext(activationContext);
        if(!expectedArgumentTypeValue->isType())
        {
            sourcePosition->printOn(stderr);
            fprintf(stderr, " Expected an argument type instead of %s.\n", expectedArgumentTypeValue->dumpAsString().c_str());
            abort();
        }

        auto expectedArgumentType = std::static_pointer_cast<Type> (expectedArgumentTypeValue);
        if(!expectedArgumentType->isSatisfiedByValue(argumentValue, activationContext))
        {
            argumentDefinition->sourcePosition->printOn(stderr);
            auto argumentType = argumentValue->getTypeInContext(activationContext);
            fprintf(stderr, " Expected an argument with type %s instead of %s.\n",
                expectedArgumentTypeValue->dumpAsString().c_str(), argumentType->dumpAsString().c_str());
            abort();
        }

        if(!argumentDefinition->name.empty())
            activationEnvironment->setSymbolBinding(argumentDefinition->name, argumentValue);
    }

    // Result type computation.
    auto resultTypeValue = dependentFunctionType->resultTypeExpression->analyzeAndEvaluateInContext(activationContext);
    if(!resultTypeValue->isType())
    {
        sourcePosition->printOn(stderr);
        fprintf(stderr, " Expected a result type instead of %s.\n", resultTypeValue->dumpAsString().c_str());
        abort();
    }

    auto resultType = std::static_pointer_cast<Type> (resultTypeValue);

    // Make the body environment.
    auto bodyEnvironment = std::make_shared<LexicalEnvironment> (activationEnvironment);
    activationContext->lexicalEnvironment = bodyEnvironment;

    // Evaluate the body.
    auto bodyResult = activationContext->visitNodeWithExpectedType(body, resultType);

    // Return
    return bodyResult;
}

ValuePtr
FunctionValue::evaluateWithArguments(const std::vector<ValuePtr> &arguments)
{
    return evaluateWithArgumentsViaParseTree(arguments);
    //return evaluateWithArgumentsAndCaptures(arguments, std::vector<ValuePtr> ());
}

ValuePtr
FunctionValue::analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context)
{
    auto typecheckedArguments = functionType->analyzeAndEvaluationFunctionApplicationArgumentsInContext(applicationNode, context);
    return evaluateWithArguments(typecheckedArguments);
}

TypePtr
Package::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->packageType;
}

TupleTypePtr
Package::getOrCreateTupleType(const std::vector<TypePtr> &elements)
{
    auto tupleType = std::make_shared<TupleType> ();
    tupleType->elements = elements;
    return tupleType;
}

AssociationTypePtr
Package::getOrCreateAssociationType(const TypePtr &keyType, const TypePtr &valueType)
{
    auto associationType = std::make_shared<AssociationType> ();
    associationType->keyType = keyType;
    associationType->valueType = valueType;
    return associationType;
}

PointerTypePtr
Package::getOrCreatePointerType(const TypePtr &baseType)
{
    return std::make_shared<PointerType> (baseType);
}

ReferenceTypePtr
Package::getOrCreateReferenceType(const TypePtr &baseType)
{
    return std::make_shared<ReferenceType> (baseType);
}

MutableValueBoxTypePtr
Package::getOrCreateMutableValueBoxType(const TypePtr &baseType)
{
    return std::make_shared<MutableValueBoxType> (baseType);
}

TypePtr
Environment::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->environmentType;
}

TypePtr
MacroContext::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->macroContextType;
}

ValuePtr
PrimitiveMacro::analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context)
{
    if(argumentCount != applicationNode->arguments.size())
    {
        applicationNode->sourcePosition->printOn(stderr);
        fprintf(stderr, ": Macro expects %d arguments instead of %d.\n", int(argumentCount), int(applicationNode->arguments.size()));
        abort();
    }

    auto macroContext = std::make_shared<MacroContext> ();
    macroContext->sourcePosition = applicationNode->sourcePosition;

    auto macroResult = function(macroContext, applicationNode->arguments);
    return context->visitExpression(macroResult);
}

TypePtr
PrimitiveMacro::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->primitiveMacroType;
}

CoreTypeAndMacros::CoreTypeAndMacros()
{
    size_t pointerSize = sizeof(void*);
    size_t pointerAlignment = sizeof(void*);
    
    integerType   = std::make_shared<NominalType> ("Integer", 8, 8);
    integerType->defaultValue = std::make_shared<IntegerValue> (integerType);

    characterType = std::make_shared<NominalType> ("Character", 8, 8);
    characterType->defaultValue = std::make_shared<CharacterValue> (characterType);

    floatType     = std::make_shared<NominalType> ("Float", 8, 8);
    floatType->defaultValue = std::make_shared<FloatValue> (floatType);

    booleanType   = std::make_shared<NominalType> ("Boolean", 8, 8);

    stringType    = std::make_shared<NominalType> ("String", pointerSize, pointerAlignment);
    stringType->defaultValue = std::make_shared<StringValue> (stringType);

    symbolType    = std::make_shared<NominalType> ("Symbol", pointerSize, pointerAlignment);
    symbolType->defaultValue = std::make_shared<SymbolValue> (symbolType);

    dynamicType = std::make_shared<DynamicType> ("Dynamic", pointerSize, pointerAlignment);

    voidType      = std::make_shared<NominalType> ("Void", 0, 1);
    undefinedType = std::make_shared<NominalType> ("UndefinedObject", 0, 1);

    parseTreeNodeType     = std::make_shared<NominalType> ("ParseTreeNode", pointerSize, pointerAlignment);
    coreTypesType         = std::make_shared<NominalType> ("CoreTypeAndMacros", pointerSize, pointerAlignment);
    argumentDefinitionValue = std::make_shared<NominalType> ("ArgumentDefinitionValue", pointerSize, pointerAlignment);
    
    evaluationContextType = std::make_shared<NominalType> ("EvaluationContext", pointerSize, pointerAlignment);

    primitiveMacroType = std::make_shared<NominalType> ("PrimitiveMacro", pointerSize, pointerAlignment);
    macroContextType = std::make_shared<NominalType> ("MacroContext", pointerSize, pointerAlignment);

    propType = std::make_shared<UniverseType> ("Prop", 0);
    typeType = std::make_shared<UniverseType> ("Type", 1);
    propType->type = typeType;

    voidValue = std::make_shared<VoidValue> (voidType);
    voidValue->type = voidType;
    voidType->defaultValue = voidValue;

    falseValue = std::make_shared<BooleanValue> (booleanType);
    falseValue->type = booleanType;
    falseValue->value = false;
    booleanType->defaultValue = falseValue;

    trueValue = std::make_shared<BooleanValue> (booleanType);
    trueValue->type = booleanType;
    trueValue->value = true;

    nilValue = std::make_shared<NilValue> (undefinedType);
    nilValue->type = undefinedType;
    undefinedType->defaultValue = nilValue;
    dynamicType->defaultValue = nilValue;

}

void CoreTypeAndMacros::registerInPackage(PackagePtr package)
{
    package->setSymbolBinding("Integer", integerType);
    package->setSymbolBinding("Character", characterType);
    package->setSymbolBinding("Float", floatType);
    package->setSymbolBinding("Boolean", booleanType);
    package->setSymbolBinding("Float", floatType);
    package->setSymbolBinding("String", stringType);
    package->setSymbolBinding("Symbol", symbolType);
    package->setSymbolBinding("Void", voidType);
    package->setSymbolBinding("UndefinedObject", undefinedType);

    package->setSymbolBinding("ParseTreeNode", parseTreeNodeType);
    package->setSymbolBinding("CoreTypeAndMacros", coreTypesType);
    package->setSymbolBinding("EvaluationContext", evaluationContextType);

    package->setSymbolBinding("PrimitiveMacro", primitiveMacroType);
    package->setSymbolBinding("MacroContext", macroContextType);

    package->setSymbolBinding("Prop", propType);
    package->setSymbolBinding("Type", typeType);

    package->setSymbolBinding("void", voidValue);
    package->setSymbolBinding("false", falseValue);
    package->setSymbolBinding("true", trueValue);
    package->setSymbolBinding("nil", nilValue);

    package->setSymbolBinding("loadFileOnce:", std::make_shared<PrimitiveMacro> (1, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto loadFile = std::make_shared<ParseTreeLoadFileNode> ();
        loadFile->sourcePosition = context->sourcePosition;
        loadFile->fileName = arguments[0];
        return loadFile;
    }));

    package->setSymbolBinding("let:with:", std::make_shared<PrimitiveMacro> (2, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto letWith = std::make_shared<ParseTreeVariableDefinitionNode> ();
        letWith->sourcePosition = context->sourcePosition;
        letWith->nameExpression = arguments[0];
        letWith->initialValue = arguments[1];
        return letWith;
    }));
    package->setSymbolBinding("let:mutableWith:", std::make_shared<PrimitiveMacro> (2, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto letWith = std::make_shared<ParseTreeVariableDefinitionNode> ();
        letWith->sourcePosition = context->sourcePosition;
        letWith->nameExpression = arguments[0];
        letWith->initialValue = arguments[1];
        letWith->isMutable = true;
        return letWith;
    }));

    package->setSymbolBinding("if:then:else:", std::make_shared<PrimitiveMacro> (3, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto ifThenElse = std::make_shared<ParseTreeIfExpressionNode> ();
        ifThenElse->sourcePosition = context->sourcePosition;
        ifThenElse->condition = arguments[0];
        ifThenElse->trueExpression = arguments[1];
        ifThenElse->falseExpression = arguments[2];
        return ifThenElse;
    }));
    package->setSymbolBinding("if:then:", std::make_shared<PrimitiveMacro> (2, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto ifThen = std::make_shared<ParseTreeIfExpressionNode> ();
        ifThen->sourcePosition = context->sourcePosition;
        ifThen->condition = arguments[0];
        ifThen->trueExpression = arguments[1];
        return ifThen;
    }));
    package->setSymbolBinding("while:do:", std::make_shared<PrimitiveMacro> (2, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto whileDo = std::make_shared<ParseTreeWhileExpressionNode> ();
        whileDo->sourcePosition = context->sourcePosition;
        whileDo->condition = arguments[0];
        whileDo->bodyExpresssion = arguments[1];
        return whileDo;
    }));
    package->setSymbolBinding("while:do:continueWith:", std::make_shared<PrimitiveMacro> (3, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto whileDo = std::make_shared<ParseTreeWhileExpressionNode> ();
        whileDo->sourcePosition = context->sourcePosition;
        whileDo->condition = arguments[0];
        whileDo->bodyExpresssion = arguments[1];
        whileDo->continueExpression = arguments[2];
        return whileDo;
    }));
    package->setSymbolBinding("do:while:", std::make_shared<PrimitiveMacro> (2, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto whileDo = std::make_shared<ParseTreeWhileExpressionNode> ();
        whileDo->sourcePosition = context->sourcePosition;
        whileDo->bodyExpresssion = arguments[0];
        whileDo->condition = arguments[1];
        return whileDo;
    }));
    package->setSymbolBinding("do:continueWith:while:", std::make_shared<PrimitiveMacro> (3, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto whileDo = std::make_shared<ParseTreeWhileExpressionNode> ();
        whileDo->sourcePosition = context->sourcePosition;
        whileDo->bodyExpresssion = arguments[0];
        whileDo->continueExpression = arguments[1];
        whileDo->condition = arguments[2];
        return whileDo;
    }));
}

ValuePtr EvaluationContext::visitExpression(const ParseTreeNodePtr &parseNode)
{
    return parseNode->analyzeAndEvaluateInContext(std::static_pointer_cast<EvaluationContext> (shared_from_this()));
}

ValuePtr EvaluationContext::visitDecayedExpression(const ParseTreeNodePtr &parseNode)
{
    auto value = visitExpression(parseNode);
    if(value->isReferenceValue())
        return std::static_pointer_cast<ReferenceValue> (value)->loadValue();

    return value;
}

std::string
EvaluationContext::visitOptionalSymbolNode(const ParseTreeNodePtr &parseNode)
{
    if(!parseNode)
        return std::string();

    auto symbolValue = visitDecayedExpression(parseNode);
    if(!symbolValue->isSymbolValue())
    {
        parseNode->sourcePosition->printOn(stderr);
        fprintf(stderr, ": Expected a symbol value.\n");
        abort();
    }

    return std::static_pointer_cast<SymbolValue> (symbolValue)->value;
}

std::string
EvaluationContext::visitStringNode(const ParseTreeNodePtr &parseNode)
{
    auto stringValue = visitDecayedExpression(parseNode);
    if(!stringValue->isStringValue())
    {
        parseNode->sourcePosition->printOn(stderr);
        fprintf(stderr, ": Expected a string value.\n");
        abort();
    }

    return std::static_pointer_cast<StringValue> (stringValue)->value;
}

bool
EvaluationContext::visitBooleanCondition(const ParseTreeNodePtr &parseNode)
{
    auto booleanValue = visitDecayedExpression(parseNode);
    if(!booleanValue->isBooleanValue())
    {
        parseNode->sourcePosition->printOn(stderr);
        fprintf(stderr, ": Expected a boolean value.\n");
        abort();
    }

    return std::static_pointer_cast<BooleanValue> (booleanValue)->value;
}

TypePtr
EvaluationContext::visitNodeExpectingType(const ParseTreeNodePtr &parseNode)
{
    auto decayedValue = visitDecayedExpression(parseNode);
    if(!decayedValue->isType())
    {
        parseNode->sourcePosition->printOn(stderr);
        fprintf(stderr, ": Expected a type expression.\n");
        abort();
    }

    return std::static_pointer_cast<Type> (decayedValue);
}

ValuePtr
EvaluationContext::visitNodeWithExpectedType(const ParseTreeNodePtr &parseNode, const TypePtr &expectedType)
{
    auto value = visitDecayedExpression(parseNode);
    if(expectedType && !expectedType->isSatisfiedByValue(value, std::static_pointer_cast<EvaluationContext> (shared_from_this())))
    {
        parseNode->sourcePosition->printOn(stderr);
        fprintf(stderr, ": Expected an expression with type '%s'.\n", expectedType->dumpAsString().c_str());
        abort();
    }

    return value;
}