#include "HIR.hpp"

TypePtr HIRValue::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->hirValueType;
}

void HIRFunction::addBasicBlock(const HIRBasicBlockPtr &basicBlock)
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

void HIRBasicBlock::addInstruction(const HIRInstructionPtr &instruction)
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
