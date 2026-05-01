#ifndef SYSMEL_VALUE_HPP
#define SYSMEL_VALUE_HPP

#include <memory>
#include <ostream>
#include <sstream>
#include <unordered_map>

typedef std::shared_ptr<struct Value> ValuePtr;
typedef std::shared_ptr<struct Type> TypePtr;
typedef std::shared_ptr<struct NominalType> NominalTypePtr;
typedef std::shared_ptr<struct Package> PackagePtr;
typedef std::shared_ptr<struct Environment> EnvironmentPtr;
typedef std::shared_ptr<struct LexicalEnvironment> LexicalEnvironmentPtr;
typedef std::shared_ptr<struct CoreTypes> CoreTypesPtr;
typedef std::shared_ptr<struct EvaluationContext> EvaluationContextPtr;

struct Value : std::enable_shared_from_this<Value>
{
    virtual ValuePtr analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
    {
        (void)context;
        return shared_from_this();
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
};

struct NominalType : Type
{
    NominalType(const std::string &initName, size_t initValueSize, size_t initValueAlignment)
        : name(initName), valueSize(initValueSize), valueAlignment(initValueAlignment) {}

    virtual void dump(std::ostream &out) override
    {
        out << name;
    }

    std::string name;
    size_t valueSize;
    size_t valueAlignment;
};

struct PrimitiveValue : Value
{
    TypePtr type;
};

struct VoidValue : PrimitiveValue
{
    virtual void dump(std::ostream &out) override
    {
        out << "void";
    }
};

struct BooleanValue : PrimitiveValue
{
    bool value = false;

    virtual void dump(std::ostream &out) override
    {
        out << "BooleanValue(" << value << ")";
    }
};

struct IntegerValue : PrimitiveValue
{
    int64_t value;

    virtual void dump(std::ostream &out) override
    {
        out << "IntegerValue(" << value << ")";
    }
};

struct FloatValue : PrimitiveValue
{
    double value;

    virtual void dump(std::ostream &out) override
    {
        out << "FloatValue(" << value << ")";
    }
};

struct NilValue : PrimitiveValue
{
    virtual void dump(std::ostream &out) override
    {
        out << "NilValue()";
    }
};

struct Package : Value
{
    std::string name;
    std::unordered_map<std::string, ValuePtr> packageSymbolTable;

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
    virtual void dump(std::ostream &out) override
    {
        out << "Environment()";
    }
};

struct EmptyEnvironment : Value
{
};

struct PackageEnvironment : Value
{
    EnvironmentPtr parent;
    PackagePtr package;
};

struct LexicalEnvironment : Value
{
    EnvironmentPtr parent;
    std::unordered_map<std::string, ValuePtr> symbolTable;
};

struct CoreTypes : Value
{
    CoreTypes();

    void registerInPackage(PackagePtr package);

    virtual void dump(std::ostream &out) override
    {
        out << "CoreTypes()";
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

    std::shared_ptr<VoidValue> voidValue;
    std::shared_ptr<BooleanValue> falseValue;
    std::shared_ptr<BooleanValue> trueValue;
    std::shared_ptr<NilValue> nilValue;
};

struct EvaluationContext : Value
{
    virtual void dump(std::ostream &out) override
    {
        out << "EvaluationContext()";
    }

    PackagePtr package;
    CoreTypesPtr coreTypes;
    LexicalEnvironmentPtr lexicalEnvironment;
};

#endif //SYSMEL_VALUE_HPP
