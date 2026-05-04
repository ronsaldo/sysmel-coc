from parsetree import *
from parser import parseSourceString, parseFileNamed
from analysisAndEvaluation import *
from hir import *
import sys

class FrontEndDriver:
    def __init__(self):
        self.context = HIRContext()
        self.package = HIRPackage('Main')
        self.package.usePackage(self.context.corePackage)
        self.context.currentPackage = self.package
    
    def parseSourceStringWithoutErrors(self, string: str) -> ParseTreeNode:
        ast = parseSourceString(string)
        ParseTreeErrorVisitor().checkPrintErrorsAndRaiseException(ast)
        return ast
    
    def evaluateTopLevelSourceString(self, string: str):
        ast = self.parseSourceStringWithoutErrors(string)
        evaluationContext = self.context.createTopLevelEvaluationContext(ast.sourcePosition.sourceCode)
        return AnalysisAndEvaluationPass(evaluationContext).visitDecayedNode(ast)

    def evaluateAndPrintSource(self, string: str):
        result = self.evaluateTopLevelSourceString(string)
        print(result)

    def evaluateSourceFile(self, filename):
        ast = parseFileNamed(filename)
        ParseTreeErrorVisitor().checkPrintErrorsAndRaiseException(ast)
            
        evaluationContext = self.context.createTopLevelEvaluationContext(ast.sourcePosition.sourceCode)
        return AnalysisAndEvaluationPass(evaluationContext).visitDecayedNode(ast)

    def main(self, argv):
        try: 
            i = 1
            while i < len(argv):
                arg = argv[i]
                if arg[0] == '-':
                    if arg == '-print-eval':
                        i += 1
                        evalSource = argv[i]
                        self.evaluateAndPrintSource(evalSource)
                else:
                    self.evaluateSourceFile(arg)
                i += 1
        except RuntimeError as error:
            print(error)
            return False

        return True
    
if __name__ == "__main__":
    if not FrontEndDriver().main(sys.argv):
        sys.exit(1)
