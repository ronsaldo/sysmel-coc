#ifndef SYSMEL_HIR_HPP
#define SYSMEL_HIR_HPP

#include "Value.hpp"

typedef std::shared_ptr<struct HIRValue> HIRValuePtr;

typedef std::shared_ptr<struct HIRTypeExpression> HIRTypeExpressionPtr;

typedef std::shared_ptr<struct HIRConstant> HIRConstantPtr;
typedef std::shared_ptr<struct HIRConstantLiteralValue> HIRConstantLiteralValuePtr;
typedef std::shared_ptr<struct HIRFunction> HIRFunctionPtr;
typedef std::shared_ptr<struct HIRFunctionClosure> HIRFunctionClosurePtr;

typedef std::shared_ptr<struct HIRFunctionLocalValue> HIRFunctionLocalValuePtr;
typedef std::shared_ptr<struct HIRArgument> HIRArgumentPtr;
typedef std::shared_ptr<struct HIRCapture> HIRCapturePtr;
typedef std::shared_ptr<struct HIRBasicBlock> HIRBasicBlockPtr;
typedef std::shared_ptr<struct HIRInstruction> HIRInstructionPtr;

struct HIRValue : Value
{
    virtual HIRValuePtr analyzeAndBuildWithContext(const BuildContextPtr &context)
    {
        (void)context;
        return std::static_pointer_cast<HIRValue> (shared_from_this());
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context);
};

struct HIRTypeExpression : HIRValue
{
};

struct HIRConstant : HIRValue
{
};

struct HIRConstantLiteralValue : HIRConstant
{
    ValuePtr value;

    virtual void dump(std::ostream &out) override
    {
        out << "HIRConstantLiteralValue(";
        value->dump(out);
        out << ")";
    }
};

struct HIRFunction : HIRConstant
{
    std::vector<HIRArgumentPtr> arguments;
    std::vector<HIRCapturePtr> captures;
    HIRBasicBlockPtr firstBasicBlock;
    HIRBasicBlockPtr lastBasicBlock;

    void addBasicBlock(const HIRBasicBlockPtr &basicBlock);
};

struct HIRFunctionClosure : HIRConstant
{
};

struct HIRFunctionLocalValue : HIRValue
{
    std::string name;
    int32_t index = -1;
};

struct HIRArgument : HIRFunctionLocalValue
{
};

struct HIRCapture : HIRFunctionLocalValue
{
};

struct HIRBasicBlock : HIRFunctionLocalValue
{
    HIRBasicBlockPtr previousBasicBlock;
    HIRBasicBlockPtr nextBasicBlock;
    HIRInstructionPtr firstInstruction;
    HIRInstructionPtr lastInstruction;

    void addInstruction(const HIRInstructionPtr &instruction);
};

struct HIRInstruction : HIRFunctionLocalValue
{
    HIRInstructionPtr previousInstruction;
    HIRInstructionPtr nextInstruction;
};

struct HIRBuilder
{
    HIRBuilderPtr allocaBuilder;
    HIRFunctionPtr function;
    HIRBasicBlockPtr basicBlock;
};

#endif //SYSMEL_HIR_HPP