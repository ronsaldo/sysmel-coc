#include "HIR.hpp"

TypePtr HIRValue::getTypeInContext(const EvaluationContextPtr &context)
{
    return context->coreTypes->hirValueType;
}