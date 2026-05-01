#include "Value.hpp"
#include "ParseTree.hpp"
#include <sstream>

ValuePtr Value::analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context)
{
    (void)context;
    applicationNode->sourcePosition->printOn(stderr);
    fprintf(stderr, ": Cannot apply to non-functional value.\n");
    abort();
}

TypePtr
Type::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->propType;
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
    characterType = std::make_shared<NominalType> ("Character", 8, 8);
    floatType     = std::make_shared<NominalType> ("Float", 8, 8);
    booleanType   = std::make_shared<NominalType> ("Boolean", 8, 8);
    stringType    = std::make_shared<NominalType> ("String", pointerSize, pointerAlignment);
    symbolType    = std::make_shared<NominalType> ("Symbol", pointerSize, pointerAlignment);
    voidType      = std::make_shared<NominalType> ("Void", 0, 1);
    undefinedType = std::make_shared<NominalType> ("UndefinedObject", 0, 1);

    parseTreeNodeType     = std::make_shared<NominalType> ("ParseTreeNode", pointerSize, pointerAlignment);;
    coreTypesType         = std::make_shared<NominalType> ("CoreTypeAndMacros", pointerSize, pointerAlignment);;
    evaluationContextType = std::make_shared<NominalType> ("EvaluationContext", pointerSize, pointerAlignment);;

    primitiveMacroType = std::make_shared<NominalType> ("PrimitiveMacro", pointerSize, pointerAlignment);;
    macroContextType = std::make_shared<NominalType> ("MacroContext", pointerSize, pointerAlignment);;

    propType = std::make_shared<UniverseType> ("Prop", 0);
    typeType = std::make_shared<UniverseType> ("Type", 1);
    propType->type = typeType;

    voidValue = std::make_shared<VoidValue> ();
    voidValue->type = voidType;

    falseValue = std::make_shared<BooleanValue> ();
    falseValue->type = booleanType;
    falseValue->value = false;

    trueValue = std::make_shared<BooleanValue> ();
    trueValue->type = booleanType;
    trueValue->value = true;

    nilValue = std::make_shared<NilValue> ();
    nilValue->type = undefinedType;

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

    package->setSymbolBinding("if:then:else:", std::make_shared<PrimitiveMacro> (3, [](const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> &arguments) {
        auto ifThenElse = std::make_shared<ParseTreeIfExpressionNode> ();
        ifThenElse->sourcePosition = context->sourcePosition;
        ifThenElse->condition = arguments[0];
        ifThenElse->trueExpression = arguments[1];
        ifThenElse->falseExpression = arguments[2];
        return ifThenElse;
    }));
}

ValuePtr EvaluationContext::visitExpression(const ParseTreeNodePtr &parseNode)
{
    return parseNode->analyzeAndEvaluateInContext(std::static_pointer_cast<EvaluationContext> (shared_from_this()));
}

ValuePtr EvaluationContext::visitDecayedExpression(const ParseTreeNodePtr &parseNode)
{
    return visitExpression(parseNode);
}

