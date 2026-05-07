from parsetree import *
from parser import parseSourceString, parseFileNamed
from analysisAndEvaluation import *
from hir import *
from hir2mir import *
from mir2lir_x64 import *
import sys

class FrontEndDriver:
    def __init__(self):
        self.context = HIRContext()
        self.package = HIRPackage('Main')
        self.package.usePackage(self.context.corePackage)
        self.context.currentPackage = self.package
    
        self.mirContext = MirContext()
        self.mirPackage = None

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
        outputFile = None
        printHir = False
        printMir = False

        try: 
            i = 1
            while i < len(argv):
                arg = argv[i]
                if arg[0] == '-':
                    if arg == '-o':
                        i += 1
                        outputFile = argv[i]
                    elif arg == '-print-eval':
                        i += 1
                        evalSource = argv[i]
                        self.evaluateAndPrintSource(evalSource)
                    elif arg == '-print-hir':
                        printHir = True
                    elif arg == '-print-mir':
                        printMir = True
                else:
                    self.evaluateSourceFile(arg)
                i += 1
        except RuntimeError as error:
            print(error)
            return False

        ## HIR Finalizaton
        self.context.finishPendingAnalysis()

        if printHir:
            self.package.dumpToConsole()
        
        # HIR2MIR
        if outputFile is None and not printMir:
            return True

        self.mirPackage = HirPackage2Mir(self.context.coreTypes, self.mirContext).translateHirPackage2Mir(self.package)
        if printMir:
            self.mirPackage.dumpToConsole()
            return True
        
        ## MIR2Lir
        self.lirModule = MirPackage2LirX64(self.mirContext).translateMirPackage(self.mirPackage)
        self.lirModule.saveModuleToFile(outputFile)
        return True
    
if __name__ == "__main__":
    if not FrontEndDriver().main(sys.argv):
        sys.exit(1)
