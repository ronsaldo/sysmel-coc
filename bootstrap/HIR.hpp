#ifndef SYSMEL_HIR_HPP
#define SYSMEL_HIR_HPP

#include "Value.hpp"
#include <assert.h>

typedef std::shared_ptr<struct HIRValue> HIRValuePtr;

typedef std::shared_ptr<struct HIRTypeExpression> HIRTypeExpressionPtr;
typedef std::shared_ptr<struct HIRNominalType> HIRNominalTypePtr;
typedef std::shared_ptr<struct HIRDynamicType> HIRDynamicTypePtr;
typedef std::shared_ptr<struct HIRUniverseType> HIRUniverseTypePtr;

typedef std::shared_ptr<struct HIRDerivedType> HIRDerivedTypePtr;
typedef std::shared_ptr<struct HIRPointerLikeType> HIRPointerLikeTypePtr;
typedef std::shared_ptr<struct HIRPointerType> HIRPointerTypePtr;
typedef std::shared_ptr<struct HIRReferenceType> HIRReferenceTypePtr;
typedef std::shared_ptr<struct HIRMutableValueBoxType> HIRMutableValueBoxTypePtr;

typedef std::shared_ptr<struct HIRAssociationType> HIRAssociationTypePtr;
typedef std::shared_ptr<struct HIRTupleType> HIRTupleTypePtr;

typedef std::shared_ptr<struct HIRSimpleFunctionType> HIRSimpleFunctionTypePtr;
typedef std::shared_ptr<struct HIRDependentFunctionType> HIRDependentFunctionTypePtr;

typedef std::shared_ptr<struct HIRConstant> HIRConstantPtr;
typedef std::shared_ptr<struct HIRConstantLiteralValue> HIRConstantLiteralValuePtr;
typedef std::shared_ptr<struct HIRFunction> HIRFunctionPtr;
typedef std::shared_ptr<struct HIRFunctionClosure> HIRFunctionClosurePtr;

typedef std::shared_ptr<struct HIRFunctionLocalValue> HIRFunctionLocalValuePtr;
typedef std::shared_ptr<struct HIRArgument> HIRArgumentPtr;
typedef std::shared_ptr<struct HIRCapture> HIRCapturePtr;
typedef std::shared_ptr<struct HIRBasicBlock> HIRBasicBlockPtr;

typedef std::shared_ptr<struct HIRInstruction> HIRInstructionPtr;
typedef std::shared_ptr<struct HIRBranchInstruction> HIRBranchInstructionPtr;
typedef std::shared_ptr<struct HIRReturnInstruction> HIRReturnInstructionPtr;
typedef std::shared_ptr<struct HIRReturnVoidInstruction> HIRReturnVoidInstructionPtr;
typedef std::shared_ptr<struct HIRUnreachableInstruction> HIRUnreachableInstructionPtr;

typedef std::shared_ptr<struct HIRBuilder> HIRBuilderPtr;

struct HIRValue : Value
{
    SourcePositionPtr sourcePosition;

    virtual std::string asString()
    {
        return dumpAsString();
    }

    virtual HIRValuePtr analyzeAndBuildWithContext(const BuildContextPtr &context)
    {
        (void)context;
        return std::static_pointer_cast<HIRValue> (shared_from_this());
    }

    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context);
    virtual HIRTypeExpressionPtr getHirType() = 0;
};

struct HIRTypeExpression : HIRValue
{
    HIRUniverseTypePtr universeType;
    
    virtual HIRTypeExpressionPtr getHirType() override;
};

struct HIRNominalType : HIRTypeExpression
{
    NominalTypePtr nominalType;

    virtual void dump(std::ostream &out) override
    {
        nominalType->dump(out);
    }

};

struct HIRDynamicType : HIRTypeExpression
{
    DynamicTypePtr dynamicType;
    
    virtual void dump(std::ostream &out) override
    {
        out << "HIRDynamicType";
    }
};

struct HIRUniverseType : HIRTypeExpression
{
    UniverseTypePtr universe;
    size_t level = 0;
    
    virtual void dump(std::ostream &out) override
    {
        out << "HIRUniverseType(" << level << ")";
    }
};

struct HIRDerivedType : HIRTypeExpression
{
    HIRTypeExpressionPtr baseType;
};

struct HIRPointerLikeType : HIRDerivedType
{
};

struct HIRPointerType : HIRPointerLikeType
{
    PointerTypePtr pointerType;
    virtual void dump(std::ostream &out) override
    {
        out << "HIRPointerType(";
        baseType->dump(out);
        out << ")";
    }
};

struct HIRReferenceType : HIRPointerLikeType
{
    ReferenceTypePtr referenceType;

    virtual void dump(std::ostream &out) override
    {
        out << "HIRReferenceType(";
        baseType->dump(out);
        out << ")";
    }
};

struct HIRMutableValueBoxType : HIRDerivedType
{
    MutableValueBoxTypePtr boxType;

    virtual void dump(std::ostream &out) override
    {
        out << "HIRMutableValueBoxType(";
        baseType->dump(out);
        out << ")";
    }
};

struct HIRTupleType : HIRTypeExpression
{
    std::vector<HIRTypeExpressionPtr> elements;
    TupleTypePtr tupleType;

    virtual void dump(std::ostream &out) override
    {
        out << "HIRTupleType(";
        for(size_t i = 0; i < elements.size(); ++i)
        {
            if(i > 0)
                out << ", ";
            elements[i]->dump(out);
        }
        out << ")";
    }
};

struct HIRAssociationType : HIRTypeExpression
{
    HIRTypeExpressionPtr keyType;
    HIRTypeExpressionPtr valueType;
    AssociationTypePtr associationType;

    virtual void dump(std::ostream &out) override
    {
        out << "HIRAssociationType(";
        keyType->dump(out);
        out << ", ";
        valueType->dump(out);
        out << ")";
    }
};

struct HIRSimpleFunctionType : HIRTypeExpression
{
    std::vector<HIRTypeExpressionPtr> argumentTypes;
    HIRTypeExpressionPtr resultType;
    SimpleFunctionTypePtr simpleFunctionType;

    virtual void dump(std::ostream &out) override
    {
        out << "HIRSimpleFunctionType([";
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

struct HIRDependentFunctionType : HIRTypeExpression
{
    std::vector<HIRArgumentPtr> arguments;
    HIRTypeExpressionPtr resultType;

    virtual void dump(std::ostream &out) override;
};

struct HIRConstant : HIRValue
{
};

struct HIRConstantLiteralValue : HIRConstant
{
    HIRTypeExpressionPtr type;
    ValuePtr value;

    virtual HIRTypeExpressionPtr getHirType() override
    {
        return type;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "HIRConstantLiteralValue(";
        value->dump(out);
        out << ")";
    }
};

struct HIRFunction : HIRConstant
{
    std::string name;
    HIRDependentFunctionTypePtr dependentFunctionType;
    std::vector<HIRCapturePtr> captures;
    HIRBasicBlockPtr firstBasicBlock;
    HIRBasicBlockPtr lastBasicBlock;

    virtual HIRTypeExpressionPtr getHirType() override
    {
        return dependentFunctionType;
    }

    void addBasicBlock(const HIRBasicBlockPtr &basicBlock);
    virtual void dump(std::ostream &out) override;

    void enumerateInstructions();
    std::vector<HIRFunctionLocalValuePtr> enumeratedInstructions;
};

struct HIRFunctionClosure : HIRConstant
{
};

struct HIRFunctionLocalValue : HIRValue
{
    std::string name;
    int32_t index = -1;

    virtual std::string asString() override
    {
        std::ostringstream out;
        out << '$' << index;
        return out.str();
    }
};

struct HIRArgument : HIRFunctionLocalValue
{
    HIRTypeExpressionPtr type;

    virtual HIRTypeExpressionPtr getHirType() override
    {
        return type;
    }

    virtual void dump(std::ostream &out) override
    {
        out << index << " := argument " << name << " :: ";
        type->dump(out);
    }
};

struct HIRCapture : HIRFunctionLocalValue
{
    HIRTypeExpressionPtr type;

    virtual HIRTypeExpressionPtr getHirType() override
    {
        return type;
    }

    virtual void dump(std::ostream &out) override
    {
        out << index << " := capture " << name << " :: ";
        type->dump(out);
    }
};

struct HIRBasicBlock : HIRFunctionLocalValue
{
    HIRBasicBlockPtr previousBasicBlock;
    HIRBasicBlockPtr nextBasicBlock;
    HIRInstructionPtr firstInstruction;
    HIRInstructionPtr lastInstruction;

    virtual HIRTypeExpressionPtr getHirType() override
    {
        //TODO: add a type to the basic block
        return nullptr;
    }

    void addInstruction(const HIRInstructionPtr &instruction);
   
    virtual void dump(std::ostream &out) override;
};

struct HIRInstruction : HIRFunctionLocalValue
{
    HIRInstructionPtr previousInstruction;
    HIRInstructionPtr nextInstruction;

    virtual bool isTerminator() const
    {
        return false;
    }
};

struct HIRBranchInstruction : HIRInstruction
{
    HIRBasicBlockPtr destination;

    virtual HIRTypeExpressionPtr getHirType() override
    {
        //TODO: add a type to the basic block
        return nullptr;
    }

    virtual bool isTerminator() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "branch " << destination->asString();
    }
};

struct HIRReturnInstruction : HIRInstruction
{
    HIRValuePtr returnValue;

    virtual bool isTerminator() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "return " << returnValue->asString();
    }

    virtual HIRTypeExpressionPtr getHirType() override
    {
        //TODO: add a type to the basic block
        return nullptr;
    }
};

struct HIRReturnVoidInstruction : HIRInstruction
{
    virtual bool isTerminator() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "returnVoid";
    }

    virtual HIRTypeExpressionPtr getHirType() override
    {
        //TODO: add a type to the basic block
        return nullptr;
    }
};

struct HIRUnreachableInstruction : HIRInstruction
{
    virtual bool isTerminator() const override
    {
        return true;
    }

    virtual void dump(std::ostream &out) override
    {
        out << "unreachable";
    }
    
    virtual HIRTypeExpressionPtr getHirType() override
    {
        //TODO: add a type to the basic block
        return nullptr;
    }
};

struct HIRBuilder
{
    HIRBuilderPtr allocaBuilder;
    HIRFunctionPtr function;
    HIRBasicBlockPtr basicBlock;

    bool isLastTerminator() const
    {
        return basicBlock && basicBlock->lastInstruction && basicBlock->lastInstruction->isTerminator();
    }

    HIRBranchInstructionPtr branch(const HIRBasicBlockPtr &destination, const SourcePositionPtr &sourcePosition)
    {
        auto instruction = std::make_shared<HIRBranchInstruction> ();
        instruction->sourcePosition = sourcePosition;
        instruction->destination = destination;
        basicBlock->addInstruction(instruction);
        return instruction;
    }

    HIRReturnInstructionPtr returnValue(const HIRValuePtr &value, const SourcePositionPtr &sourcePosition)
    {
        auto instruction = std::make_shared<HIRReturnInstruction> ();
        instruction->returnValue = value;
        instruction->sourcePosition = sourcePosition;
        basicBlock->addInstruction(instruction);
        return instruction;
    }

    HIRReturnVoidInstructionPtr returnVoid(const SourcePositionPtr &sourcePosition)
    {
        auto instruction = std::make_shared<HIRReturnVoidInstruction> ();
        instruction->sourcePosition = sourcePosition;
        basicBlock->addInstruction(instruction);
        return instruction;
    }

    HIRUnreachableInstructionPtr unreachable(const SourcePositionPtr &sourcePosition)
    {
        auto instruction = std::make_shared<HIRUnreachableInstruction> ();
        instruction->sourcePosition = sourcePosition;
        basicBlock->addInstruction(instruction);
        return instruction;
    }

};

#endif //SYSMEL_HIR_HPP