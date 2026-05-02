#ifndef SYSMEL_VALUE_HPP
#define SYSMEL_VALUE_HPP

#include <memory>
#include <ostream>
#include <sstream>
#include <unordered_map>
#include <functional>
#include "SourceCode.hpp"

typedef std::shared_ptr<struct Value> ValuePtr;
typedef std::shared_ptr<struct Type> TypePtr;

typedef std::shared_ptr<struct HIRValue> HIRValuePtr;
typedef std::shared_ptr<struct HIRTypeExpression> HIRTypeExpressionPtr;
typedef std::shared_ptr<struct HIRFunction> HIRFunctionPtr;
typedef std::shared_ptr<struct HIRBuilder> HIRBuilderPtr;

typedef std::shared_ptr<struct ParseTreeNode> ParseTreeNodePtr;
typedef std::shared_ptr<struct ParseTreeIdentifierReferenceNode> ParseTreeIdentifierReferenceNodePtr;
typedef std::shared_ptr<struct ParseTreeFunctionApplicationNode> ParseTreeFunctionApplicationNodePtr;
typedef std::shared_ptr<struct ParseTreeAssignmentNode> ParseTreeAssignmentNodePtr;

typedef std::shared_ptr<struct NominalType> NominalTypePtr;
typedef std::shared_ptr<struct DynamicType> DynamicTypePtr;
typedef std::shared_ptr<struct UniverseType> UniverseTypePtr;

typedef std::shared_ptr<struct DerivedType> DerivedTypePtr;
typedef std::shared_ptr<struct PointerLikeType> PointerLikeTypePtr;
typedef std::shared_ptr<struct PointerType> PointerTypePtr;
typedef std::shared_ptr<struct ReferenceType> ReferenceTypePtr;
typedef std::shared_ptr<struct MutableValueBoxType> MutableValueBoxTypePtr;

typedef std::shared_ptr<struct SimpleFunctionType> SimpleFunctionTypePtr;
typedef std::shared_ptr<struct TupleType> TupleTypePtr;
typedef std::shared_ptr<struct AssociationType> AssociationTypePtr;

typedef std::shared_ptr<struct ArgumentDefinitionValue> ArgumentDefinitionValuePtr;
typedef std::shared_ptr<struct DependentFunctionType> DependentFunctionTypePtr;


typedef std::shared_ptr<struct Package> PackagePtr;
typedef std::shared_ptr<struct MacroContext> MacroContextPtr;
typedef std::shared_ptr<struct Environment> EnvironmentPtr;
typedef std::shared_ptr<struct LexicalEnvironment> LexicalEnvironmentPtr;
typedef std::shared_ptr<struct FunctionalSignatureAnalysisEnvironment> FunctionalSignatureAnalysisEnvironmentPtr;

typedef std::shared_ptr<struct CoreTypeAndMacros> CoreTypeAndMacrosPtr;
typedef std::shared_ptr<struct EvaluationContext> EvaluationContextPtr;
typedef std::shared_ptr<struct BuildContext> BuildContextPtr;

struct Value : std::enable_shared_from_this<Value>
{
    virtual ~Value() {}

    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
    {
        (void)context;
        return shared_from_this();
    }

    virtual ValuePtr analyzeAndEvaluateIdentifierReferenceNodeInContext(const ParseTreeIdentifierReferenceNodePtr &identifierNode, const EvaluationContextPtr &context)
    {
        (void)identifierNode;
        (void)context;
        return shared_from_this();
    }

    virtual HIRValuePtr analyzeAndBuildIdentifierReferenceNodeInContext(const ParseTreeIdentifierReferenceNodePtr &identifierNode, const BuildContextPtr &context)
    {
        (void)identifierNode;
        return analyzeAndBuildWithContext(context);
    }

    virtual ValuePtr analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context);
    virtual ValuePtr analyzeAndEvaluateAssignmentNodeInContext(const ParseTreeAssignmentNodePtr &assignmentNode, const EvaluationContextPtr &context);

    virtual HIRValuePtr analyzeAndBuildWithContext(const BuildContextPtr &context);

    virtual void enqueuePendingAnalysis(const PackagePtr &package);
    virtual void ensureAnalysis()
    {
        // By default do nothin
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) = 0;

    virtual bool isType() const
    {
        return false;
    }

    virtual bool isArgumentDefinitionValue() const
    {
        return false;
    }
    
    virtual bool isDependentFunctionType() const
    {
        return false;
    }

    virtual bool isBooleanValue() const
    {
        return false;
    }

    virtual bool isStringValue() const
    {
        return false;
    }

    virtual bool isSymbolValue() const
    {
        return false;
    }

    virtual void dump(std::ostream &out) = 0;

    std::string dumpAsString()
    {
        std::ostringstream out;
        dump(out);
        return out.str();
    }

    virtual ValuePtr loadValueWithFieldIndex(int fieldIndex)
    {
        (void)fieldIndex;
        fprintf(stderr, "Value %s does not have fields that can be loaded.\n", dumpAsString().c_str());
        abort();
    }

    virtual void storeValueWithFieldIndex(const ValuePtr &valueToStore, int fieldIndex)
    {
        (void)valueToStore;
        (void)fieldIndex;
        fprintf(stderr, "Value %s does not have fields that can be mutated.\n", dumpAsString().c_str());
        abort();
    }
    
    virtual bool isReferenceValue() const
    {
        return false;
    }
};

struct Type : Value
{
    virtual ValuePtr getOrCreateDefaultValue()
    {
        fprintf(stderr, "Type %s does not have a default value.\n", dumpAsString().c_str());
        abort();
    }

    virtual std::vector<ValuePtr> analyzeAndEvaluationFunctionApplicationArgumentsInContext(const ParseTreeFunctionApplicationNodePtr &application, const EvaluationContextPtr &context)
    {
        (void)application;
        (void)context;
        fprintf(stderr, "Type %s is not functional.\n", dumpAsString().c_str());
        abort();
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) = 0;

    virtual bool isSatisfiedByValue(const ValuePtr &value, const EvaluationContextPtr &context) const;
    virtual bool isSatisfiedByType(const TypePtr &otherType) const;

    virtual bool isType() const override
    {
        return true;
    }
};

struct NominalType : Type
{
    NominalType(const std::string &initName, size_t initValueSize, size_t initValueAlignment)
        : name(initName), valueSize(initValueSize), valueAlignment(initValueAlignment) {}

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << name;
    }

    virtual ValuePtr getOrCreateDefaultValue() override
    {
        return defaultValue;
    }

    ValuePtr defaultValue;

    std::string name;
    size_t valueSize;
    size_t valueAlignment;
};

struct DynamicType : Type
{
    DynamicType(const std::string &initName, size_t initValueSize, size_t initValueAlignment)
        : name(initName), valueSize(initValueSize), valueAlignment(initValueAlignment) {}

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << name;
    }

    virtual ValuePtr getOrCreateDefaultValue() override
    {
        return defaultValue;
    }

    ValuePtr defaultValue;

    std::string name;
    size_t valueSize;
    size_t valueAlignment;
};


struct UniverseType : Type
{
    UniverseType(const std::string &initName, size_t initLevel)
        : name(initName), level(initLevel) {}
    
    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << name;
    }

    std::string name;
    size_t level;
    UniverseTypePtr type;
};

struct DerivedType : Type
{
    DerivedType(const TypePtr &initBaseType)
        : baseType(initBaseType) {}
    
    TypePtr baseType;
};

struct PointerLikeType : DerivedType
{
    PointerLikeType(const TypePtr &initBaseType)
        : DerivedType(initBaseType) {}
};

struct PointerType : PointerLikeType
{
    PointerType(const TypePtr &initBaseType)
        : PointerLikeType(initBaseType) {}

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "PointerType(";
        baseType->dump(out);
        out << ")";
    }
};

struct ReferenceType : PointerLikeType
{
    ReferenceType(const TypePtr &initBaseType)
        : PointerLikeType(initBaseType) {}

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "ReferenceType(";
        baseType->dump(out);
        out << ")";
    }
};

struct MutableValueBoxType : DerivedType
{
    MutableValueBoxType(const TypePtr &initBaseType)
        : DerivedType(initBaseType) {}

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "MutableValueBoxType(";
        baseType->dump(out);
        out << ")";
    }
};

struct ArgumentDefinitionValue : Value
{
    SourcePositionPtr sourcePosition;
    std::string name;
    ValuePtr typeExpression;
    int index = 0;
    bool hasDependentUsers = false;

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    virtual bool isArgumentDefinitionValue() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ArgumentDefinitionValue(" << name;
        out << ", ";
        typeExpression->dump(out);
        out << ")";
    }
};

struct DependentFunctionType : Type
{
    std::vector<ArgumentDefinitionValuePtr> arguments;
    ValuePtr resultTypeExpression;
    bool hasDependentArgs = false;

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    TypePtr simplify();

    virtual bool isDependentFunctionType() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "DependentFunctionType([";
        for(size_t i = 0; i < arguments.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            arguments[i]->dump(out);
        }
        out << "], ";
        resultTypeExpression->dump(out);
        out << ", hasDependentArgs = " << hasDependentArgs << ")";
    }
};

struct SimpleFunctionType : Type
{
    std::vector<TypePtr> argumentTypes;
    TypePtr resultType;

    virtual std::vector<ValuePtr> analyzeAndEvaluationFunctionApplicationArgumentsInContext(const ParseTreeFunctionApplicationNodePtr &application, const EvaluationContextPtr &context) override;
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "SimpleFunctionType([";
        for(size_t i = 0; i < argumentTypes.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            argumentTypes[i]->dump(out);
        }
        out << "], ";
        resultType->dump(out);
        out << ")";
    }
};

struct TupleType : Type
{
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "TupleType(";
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << ")";
    }

    std::vector<TypePtr> elements;
};

struct AssociationType : Type
{
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;
    
    HIRTypeExpressionPtr hirTypeCache;
    virtual HIRTypeExpressionPtr asHIRTypeWithContext(const BuildContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "AssociationType(";
        keyType->dump(out);
        out << ", ";
        valueType->dump(out);
        out << ")";
    }

    TypePtr keyType;
    TypePtr valueType;
};

struct PrimitiveValue : Value
{
    PrimitiveValue(const TypePtr initType)
        : type(initType) {}

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return type;
    }

    TypePtr type;
};

struct VoidValue : PrimitiveValue
{
    VoidValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    virtual void dump(std::ostream &out) override
    {
        out << "void";
    }
};

struct BooleanValue : PrimitiveValue
{
    BooleanValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    bool value = false;
    
    virtual bool isBooleanValue() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "BooleanValue(" << value << ")";
    }
};

struct IntegerValue : PrimitiveValue
{
    IntegerValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    int64_t value = 0;

    virtual void dump(std::ostream &out) override
    {
        out << "IntegerValue(" << value << ")";
    }
};

struct CharacterValue : PrimitiveValue
{
    CharacterValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    uint32_t value = 0;

    virtual void dump(std::ostream &out) override
    {
        out << "CharacterValue(" << value << ")";
    }
};

struct FloatValue : PrimitiveValue
{
    FloatValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    double value = 0.0;

    virtual void dump(std::ostream &out) override
    {
        out << "FloatValue(" << value << ")";
    }
};

struct NilValue : PrimitiveValue
{
    NilValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    virtual void dump(std::ostream &out) override
    {
        out << "NilValue()";
    }
};

struct StringValue : PrimitiveValue
{
    StringValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    StringValue(const TypePtr initType, const std::string &initValue)
        : PrimitiveValue(initType), value(initValue) {}

    std::string value;

    virtual bool isStringValue() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "StringValue(" << value << ")";
    }
};

struct SymbolValue : PrimitiveValue
{
    SymbolValue(const TypePtr initType)
        : PrimitiveValue(initType) {}

    std::string value;

    virtual bool isSymbolValue() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "SymbolValue(" << value << ")";
    }
};


struct FunctionValue : Value
{
    SourcePositionPtr sourcePosition;
    DependentFunctionTypePtr dependentFunctionType;
    TypePtr functionType;
    ParseTreeNodePtr body;
    EvaluationContextPtr definitionContext;
    bool isMethod = false;
    bool isPublic = false;
    bool isMacro = false;
    bool isCompileTime = false;
    bool isTemplate = false;
    std::string name;
    std::string primitiveName;

    HIRFunctionPtr hirFunction;

    virtual ValuePtr analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context) override;
    virtual void ensureAnalysis() override;
    
    ValuePtr evaluateWithArgumentsAndCaptures(const std::vector<ValuePtr> &arguments, const std::vector<ValuePtr> &captures);
    ValuePtr evaluateWithArgumentsViaParseTree(const std::vector<ValuePtr> &arguments);
    ValuePtr evaluateWithArguments(const std::vector<ValuePtr> &arguments);

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return functionType;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "FunctionValue(";
        functionType->dump(out);
        out << ")";
    }
};

struct MutableValueBox : Value
{
    ValuePtr boxedValue;
    TypePtr type;

    virtual void dump(std::ostream &out) override
    {
        out << "MutableValueBox()";
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return type;
    }
    
    virtual ValuePtr loadValueWithFieldIndex(int fieldIndex) override
    {
        (void)fieldIndex;
        return boxedValue;
    }

    virtual void storeValueWithFieldIndex(const ValuePtr &valueToStore, int fieldIndex) override
    {
        (void)fieldIndex;
        boxedValue = valueToStore;
    }
};

struct PointerLikeValue : Value
{
    ValuePtr storage;
    PointerLikeTypePtr type;
    int fieldIndex = 0;

    virtual void dump(std::ostream &out) override
    {
        out << "PointerLikeValue()";
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return type;
    }

    virtual ValuePtr loadValue()
    {
        return storage->loadValueWithFieldIndex(fieldIndex);
    }

    virtual void storeValue(const ValuePtr &valueToStore)
    {
        storage->storeValueWithFieldIndex(valueToStore, fieldIndex);
    }
};

struct ReferenceValue : PointerLikeValue
{
    virtual bool isReferenceValue() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "ReferenceValue()";
    }
    
    virtual ValuePtr analyzeAndEvaluateAssignmentNodeInContext(const ParseTreeAssignmentNodePtr &assignmentNode, const EvaluationContextPtr &context) override;
};

struct TupleValue : Value
{
    std::vector<ValuePtr> elements;
    TypePtr type;

    virtual void dump(std::ostream &out) override
    {
        out << "TupleValue(";
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << ")";
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return type;
    }
};

struct AssociationValue : Value
{
    ValuePtr key;
    ValuePtr value;
    TypePtr type;

    virtual void dump(std::ostream &out) override
    {
        out << "AssociationValue(";
        key->dump(out);
        out << ", ";
        value->dump(out);
        out << ")";
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return type;
    }
};

struct Package : Value
{
    std::string name;
    std::unordered_map<std::string, ValuePtr> packageSymbolTable;
    std::vector<ValuePtr> packageChildren;
    std::vector<ValuePtr> pendingAnalysisQueue;

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    TupleTypePtr getOrCreateTupleType(const std::vector<TypePtr> &elements);
    AssociationTypePtr getOrCreateAssociationType(const TypePtr &keyType, const TypePtr &valueType);

    PointerTypePtr getOrCreatePointerType(const TypePtr &baseType);
    ReferenceTypePtr getOrCreateReferenceType(const TypePtr &baseType);
    MutableValueBoxTypePtr getOrCreateMutableValueBoxType(const TypePtr &baseType);

    void setSymbolBinding(std::string symbol, ValuePtr binding)
    {
        packageSymbolTable[symbol] = binding;
        packageChildren.push_back(binding);
    }

    virtual void dump(std::ostream &out) override
    {
        out << "Package(" << name << ")";
    }
};

struct Environment : Value
{
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    virtual ValuePtr lookupSymbolRecursively(const std::string &symbol) = 0;

    virtual void dump(std::ostream &out) override
    {
        out << "Environment()";
    }
};

struct EmptyEnvironment : Environment
{
    virtual ValuePtr lookupSymbolRecursively(const std::string &symbol) override
    {
        (void)symbol;
        return nullptr;
    }
};

struct PackageEnvironment : Environment
{
    EnvironmentPtr parent;
    PackagePtr package;

    PackageEnvironment(const EnvironmentPtr &initParent, const PackagePtr &initPackage)
        : parent(initParent), package(initPackage) {}

    virtual ValuePtr lookupSymbolRecursively(const std::string &symbol) override
    {
        auto it = package->packageSymbolTable.find(symbol);
        if(it != package->packageSymbolTable.end())
            return it->second;

        return parent->lookupSymbolRecursively(symbol);
    }
};

struct LexicalEnvironment : Environment
{
    LexicalEnvironment(const EnvironmentPtr &initParent)
        : parent(initParent) {}

    EnvironmentPtr parent;
    std::unordered_map<std::string, ValuePtr> symbolTable;

    bool hasSymbolBinding(std::string symbol) const
    {
        return symbolTable.find(symbol) != symbolTable.end();
    }

    void setSymbolBinding(std::string symbol, ValuePtr binding)
    {
        symbolTable[symbol] = binding;
    }

    virtual ValuePtr lookupSymbolRecursively(const std::string &symbol) override
    {
        auto it = symbolTable.find(symbol);
        if(it != symbolTable.end())
            return it->second;

        return parent->lookupSymbolRecursively(symbol);
    }
};

struct FunctionalActivationEnvironment : LexicalEnvironment
{
    FunctionalActivationEnvironment(const EnvironmentPtr &initParent)
        : LexicalEnvironment(initParent) {}

};

struct FunctionalAnalysisEnvironment: LexicalEnvironment
{
    FunctionalAnalysisEnvironment(const EnvironmentPtr &initParent)
        : LexicalEnvironment(initParent) {}

};

struct FunctionalSignatureAnalysisEnvironment : LexicalEnvironment
{
    FunctionalSignatureAnalysisEnvironment(const EnvironmentPtr &initParent)
        : LexicalEnvironment(initParent) {}

    std::vector<ArgumentDefinitionValuePtr> argumentList;
    std::vector<ArgumentDefinitionValuePtr> dependentArguments;

    void addArgument(const ArgumentDefinitionValuePtr &argument)
    {
        if(!argument->name.empty())
            symbolTable[argument->name] = argument;
        argumentList.push_back(argument);
    }

    void markUsedArgumentDefinition(const ArgumentDefinitionValuePtr &argument)
    {
        if(argument->hasDependentUsers)
            return;

        argument->hasDependentUsers = true;
        dependentArguments.push_back(argument);
    }

    virtual ValuePtr lookupSymbolRecursively(const std::string &symbol) override
    {
        auto it = symbolTable.find(symbol);
        if(it != symbolTable.end())
        {
            auto localSymbol = it->second;
            if(localSymbol->isArgumentDefinitionValue())
                markUsedArgumentDefinition(std::static_pointer_cast<ArgumentDefinitionValue> (localSymbol));

            return localSymbol;
        }

        return parent->lookupSymbolRecursively(symbol);
    }
};

struct MacroContext : Value
{
    SourcePositionPtr sourcePosition;

    virtual void dump(std::ostream &out) override
    {
        out << "MacroContext()";
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;
};

struct PrimitiveMacro : Value
{
    template<typename FT>
    PrimitiveMacro(size_t initArgumentCount, FT &&initFunction)
        : argumentCount(initArgumentCount), function(initFunction) {}

    virtual ValuePtr analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << "PrimitiveMacro()";
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    size_t argumentCount = 0;
    std::function<ParseTreeNodePtr (const MacroContextPtr &context, const std::vector<ParseTreeNodePtr> arguments)> function;
};

struct CoreTypeAndMacros : Value
{
    CoreTypeAndMacros();

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        (void)context;
        return coreTypesType;
    }

    void registerInPackage(PackagePtr package);

    virtual void dump(std::ostream &out) override
    {
        out << "CoreTypeAndMacros()";
    }

    size_t pointerSize;
    size_t pointerAlignment;

    NominalTypePtr integerType;
    NominalTypePtr characterType;
    NominalTypePtr floatType;
    NominalTypePtr booleanType;
    NominalTypePtr stringType;
    NominalTypePtr symbolType;
    NominalTypePtr voidType;
    NominalTypePtr undefinedType;
    
    DynamicTypePtr dynamicType;

    NominalTypePtr parseTreeNodeType;
    NominalTypePtr coreTypesType;
    NominalTypePtr argumentDefinitionValue;
    NominalTypePtr evaluationContextType;
    NominalTypePtr buildContextType;
    NominalTypePtr environmentType;
    NominalTypePtr packageType;
    NominalTypePtr hirValueType;

    NominalTypePtr primitiveMacroType;
    NominalTypePtr macroContextType;

    UniverseTypePtr propType;
    UniverseTypePtr typeType;

    std::shared_ptr<VoidValue> voidValue;
    std::shared_ptr<BooleanValue> falseValue;
    std::shared_ptr<BooleanValue> trueValue;
    std::shared_ptr<NilValue> nilValue;
};

struct EvaluationContext : Value
{
    ValuePtr visitExpression(const ParseTreeNodePtr &parseNode);
    ValuePtr visitDecayedExpression(const ParseTreeNodePtr &parseNode);

    std::string visitOptionalSymbolNode(const ParseTreeNodePtr &parseNode);
    std::string visitStringNode(const ParseTreeNodePtr &parseNode);
    bool visitBooleanCondition(const ParseTreeNodePtr &parseNode);

    TypePtr visitNodeExpectingType(const ParseTreeNodePtr &parseNode);
    ValuePtr visitNodeWithExpectedType(const ParseTreeNodePtr &parseNode, const TypePtr &expectedType);

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        return context->coreTypes->evaluationContextType;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "EvaluationContext()";
    }

    EvaluationContextPtr clone() const
    {
        auto cloned = std::make_shared<EvaluationContext> ();
        cloned->package = package;
        cloned->coreTypes = coreTypes;
        cloned->lexicalEnvironment = lexicalEnvironment;
        return cloned;
    }

    PackagePtr package;
    CoreTypeAndMacrosPtr coreTypes;
    LexicalEnvironmentPtr lexicalEnvironment;
};

struct BuildContext : Value
{
    HIRValuePtr visitExpression(const ParseTreeNodePtr &parseNode);
    HIRValuePtr visitDecayedExpression(const ParseTreeNodePtr &parseNode);
    HIRValuePtr visitNodeWithExpectedType(const ParseTreeNodePtr &parseNode, const HIRTypeExpressionPtr &expectedType);

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override
    {
        return context->coreTypes->buildContextType;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "BuildContext()";
    }

    EvaluationContextPtr asEvaluationContext() const
    {
        auto context = std::make_shared<EvaluationContext> ();
        context->package = package;
        context->coreTypes = coreTypes;
        context->lexicalEnvironment = lexicalEnvironment;
        return context;
    }

    static BuildContextPtr fromEvaluationContext(const EvaluationContextPtr &evalContext)
    {
        auto buildContext = std::make_shared<BuildContext> ();
        buildContext->package = evalContext->package;
        buildContext->coreTypes = evalContext->coreTypes;
        buildContext->lexicalEnvironment = evalContext->lexicalEnvironment;
        return buildContext;
    }

    BuildContextPtr clone() const
    {
        auto cloned = std::make_shared<BuildContext> ();
        cloned->package = package;
        cloned->coreTypes = coreTypes;
        cloned->lexicalEnvironment = lexicalEnvironment;
        cloned->builder = builder;
        return cloned;
    }

    PackagePtr package;
    CoreTypeAndMacrosPtr coreTypes;
    LexicalEnvironmentPtr lexicalEnvironment;
    HIRBuilderPtr builder;
};

#endif //SYSMEL_VALUE_HPP
