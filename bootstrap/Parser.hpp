#ifndef SYSMEL_PARSER_HPP
#define SYSMEL_PARSER_HPP

#include "ParseTree.hpp"
#include "Scanner.hpp"

ParseTreeNodePtr SysmelParseTokenSequence(const std::vector<SysmelTokenPtr> &tokens);

#endif //SYSMEL_PARSER_HPP
