#include "Value.hpp"
#include "ParseTree.hpp"
#include <sstream>

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

CoreTypes::CoreTypes()
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
    coreTypesType         = std::make_shared<NominalType> ("CoreTypes", pointerSize, pointerAlignment);;
    evaluationContextType = std::make_shared<NominalType> ("EvaluationContext", pointerSize, pointerAlignment);;

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

void CoreTypes::registerInPackage(PackagePtr package)
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
    package->setSymbolBinding("CoreTypes", coreTypesType);
    package->setSymbolBinding("EvaluationContext", evaluationContextType);

    package->setSymbolBinding("Prop", propType);
    package->setSymbolBinding("Type", typeType);

    package->setSymbolBinding("void", voidValue);
    package->setSymbolBinding("false", falseValue);
    package->setSymbolBinding("true", trueValue);
    package->setSymbolBinding("nil", nilValue);
}

ValuePtr EvaluationContext::visitExpression(const ParseTreeNodePtr &parseNode)
{
    return parseNode->analyzeAndEvaluateInContext(std::static_pointer_cast<EvaluationContext> (shared_from_this()));
}

ValuePtr EvaluationContext::visitDecayedExpression(const ParseTreeNodePtr &parseNode)
{
    return visitExpression(parseNode);
}
