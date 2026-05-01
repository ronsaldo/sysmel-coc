#include "Value.hpp"
#include "ParseTree.hpp"

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

    package->setSymbolBinding("void", voidValue);
    package->setSymbolBinding("false", falseValue);
    package->setSymbolBinding("true", trueValue);
    package->setSymbolBinding("nil", nilValue);
}

ValuePtr EvaluationContext::visitParseNode(const ParseTreeNodePtr &parseNode)
{
    return parseNode->analyzeAndEvaluateInContext(std::static_pointer_cast<EvaluationContext> (shared_from_this()));
}
