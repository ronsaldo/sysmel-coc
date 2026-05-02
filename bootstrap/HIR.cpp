#include "HIR.hpp"

TypePtr HIRValue::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->hirValueType;
}

void HIRDependentFunctionType::dump(std::ostream &out)
{
    out << "HIRDependentFunctionType([";
    for(size_t i = 0; i < arguments.size(); ++i)
    {
        if(i > 0)
            out << ", ";
        arguments[i]->dump(out);
    }
    out << "], ";
    resultType->dump(out);
    out << ")";
}

void
HIRFunction::addBasicBlock(const HIRBasicBlockPtr &basicBlock)
{
    if(lastBasicBlock)
    {
        lastBasicBlock->nextBasicBlock = basicBlock;
        basicBlock->previousBasicBlock = lastBasicBlock;
        lastBasicBlock = basicBlock;
    }
    else
    {
        firstBasicBlock = lastBasicBlock = basicBlock;
    }
}

void HIRFunction::dump(std::ostream &out)
{
    out << "HIRFunction(\n  " << name;
    dependentFunctionType->dump(out);

    out << "\n";
    auto basicBlock = firstBasicBlock;
    while (basicBlock)
    {
        basicBlock->dump(out);
        basicBlock = basicBlock->nextBasicBlock;
    }
    
    out << ")";
}
    
void
HIRBasicBlock::addInstruction(const HIRInstructionPtr &instruction)
{
    if(lastInstruction)
    {
        lastInstruction->nextInstruction = instruction;
        instruction->previousInstruction = lastInstruction;
        lastInstruction = instruction;
    }
    else
    {
        firstInstruction = lastInstruction = instruction;
    }
}

void
HIRBasicBlock::dump(std::ostream &out)
{
    out << "@" << index << "<" << name << ">:\n";
    auto instruction = firstInstruction;
    while(instruction)
    {
        out << "  ";
        instruction->dump(out);
        instruction = instruction->nextInstruction;
    }
}
