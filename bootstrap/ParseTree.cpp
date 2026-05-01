#include "ParseTree.hpp"

ValuePtr
ParseTreeBinaryExpressionSequenceNode::analyzeAndEvaluateInContext(const EvaluationContextPtr &context)
{
    assert(elements.size() >= 1);
    auto previous = elements[0];

    for(size_t i = 1; i < elements.size(); i += 2)
    {
        auto operatorSymbol = elements[i];
        auto operand = elements[i + 1];

        auto send = std::make_shared<ParseTreeMessageSendNode> ();
        send->receiver = previous;
        send->selector = operand;
        send->arguments.push_back(operand);
        previous = send;
    }

    return context->visitExpression(previous);
}
