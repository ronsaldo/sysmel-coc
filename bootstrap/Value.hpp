#ifndef SYSMEL_VALUE_HPP
#define SYSMEL_VALUE_HPP

#include <memory>
#include <ostream>
#include <sstream>
#include <unordered_map>
#include <functional>

typedef std::shared_ptr<struct Value> ValuePtr;
typedef std::shared_ptr<struct Type> TypePtr;
typedef std::shared_ptr<struct ParseTreeNode> ParseTreeNodePtr;
typedef std::shared_ptr<struct ParseTreeIdentifierReferenceNode> ParseTreeIdentifierReferenceNodePtr;
typedef std::shared_ptr<struct ParseTreeFunctionApplicationNode> ParseTreeFunctionApplicationNodePtr;
typedef std::shared_ptr<struct NominalType> NominalTypePtr;
typedef std::shared_ptr<struct UniverseType> UniverseTypePtr;
typedef std::shared_ptr<struct TupleType> TupleTypePtr;
typedef std::shared_ptr<struct AssociationType> AssociationTypePtr;
typedef std::shared_ptr<struct Package> PackagePtr;
typedef std::shared_ptr<struct MacroContext> MacroContextPtr;
typedef std::shared_ptr<struct Environment> EnvironmentPtr;
typedef std::shared_ptr<struct LexicalEnvironment> LexicalEnvironmentPtr;
typedef std::shared_ptr<struct CoreTypeAndMacros> CoreTypesPtr;
typedef std::shared_ptr<struct EvaluationContext> EvaluationContextPtr;

struct Value : std::enable_shared_from_this<Value>
{
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

    virtual ValuePtr analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context);

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) = 0;

    virtual bool isType() const
    {
        return false;
    }

    virtual bool isBooleanValue() const
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
};

struct Type : Value
{
    virtual ValuePtr getOrCreateDefaultValue()
    {
        fprintf(stderr, "Type %s does not have a default value.", dumpAsString().c_str());
        abort();
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

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

    virtual void dump(std::ostream &out) override
    {
        out << name;
    }

    virtual ValuePtr getOrCreateDefaultValue()
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
    
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    virtual void dump(std::ostream &out) override
    {
        out << name;
    }

    std::string name;
    size_t level;
    UniverseTypePtr type;
};

struct TupleType : Type
{
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

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
    
    virtual bool isBooleanValue() const
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

    std::string value;

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

    virtual bool isSymbolValue() const
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "SymbolValue(" << value << ")";
    }
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

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context) override;

    TupleTypePtr getOrCreateTupleType(const std::vector<TypePtr> &elements);
    AssociationTypePtr getOrCreateAssociationType(const TypePtr &keyType, const TypePtr &valueType);

    void setSymbolBinding(std::string symbol, ValuePtr binding)
    {
        packageSymbolTable[symbol] = binding;
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

    virtual ValuePtr analyzeAndEvaluateFunctionApplicationNodeInContext(const ParseTreeFunctionApplicationNodePtr &applicationNode, const EvaluationContextPtr &context);

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

    NominalTypePtr parseTreeNodeType;
    NominalTypePtr coreTypesType;
    NominalTypePtr evaluationContextType;
    NominalTypePtr environmentType;
    NominalTypePtr packageType;

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

    EvaluationContextPtr clone()
    {
        auto cloned = std::make_shared<EvaluationContext> ();
        cloned->package = package;
        cloned->coreTypes = coreTypes;
        cloned->lexicalEnvironment = lexicalEnvironment;
        return cloned;
    }

    PackagePtr package;
    CoreTypesPtr coreTypes;
    LexicalEnvironmentPtr lexicalEnvironment;
};

#endif //SYSMEL_VALUE_HPP
