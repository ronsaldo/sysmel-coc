#ifndef SYSMEL_HIR_HPP
#define SYSMEL_HIR_HPP

#include "Value.hpp"

typedef std::shared_ptr<struct HIRValue> HIRValuePtr;

struct HIRValue : Value
{
    virtual TypePtr getTypeInContext(const EvaluationContextPtr &context);
};

#endif //SYSMEL_HIR_HPP