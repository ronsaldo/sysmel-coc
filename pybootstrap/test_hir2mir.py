import unittest
from parsetree import *
from parser import parseSourceString
from analysisAndEvaluation import AnalysisAndEvaluationPass
from hir import *
from hir2mir import *

class HIR2MIRTest(unittest.TestCase):
    def setUp(self):
        self.context = HIRContext()
        self.package = HIRPackage('Test')
        self.package.usePackage(self.context.corePackage)
        self.context.currentPackage = self.package

        self.mirContext = MirContext()
        self.mirPackage = None

        return super().setUp()
    
    def tearDown(self):
        self.context.finishPendingAnalysis()
        return super().tearDown()
    
    def parseSourceStringWithoutErrors(self, string: str) -> ParseTreeNode:
        ast = parseSourceString(string)
        self.assertTrue(ParseTreeErrorVisitor().checkAndPrintErrors(ast))
        return ast
    
    def evaluateTopLevelSourceString(self, string: str):
        ast = self.parseSourceStringWithoutErrors(string)
        evaluationContext = self.context.createTopLevelEvaluationContext(ast.sourcePosition.sourceCode)
        return AnalysisAndEvaluationPass(evaluationContext).visitDecayedNode(ast)
    
    def compilePackageToMir(self):
        self.context.finishPendingAnalysis()
        self.mirPackage = HirPackage2Mir(self.context.coreTypes, self.mirContext).translateHirPackage2Mir(self.package, )
        return self.mirPackage
    
    def testEmpty(self):
        self.evaluateTopLevelSourceString('')
        mirPackage = self.compilePackageToMir()
        self.assertTrue(len(mirPackage.elementTable) == 0)

    #def testFunction(self):
    #    topLevelResult = self.evaluateTopLevelSourceString('public function add(x: Integer. y: Integer) => Integer := x + y')
    #    self.assertTrue(topLevelResult.isFunction())

    #    mirPackage = self.compilePackageToMir()
    #    self.assertTrue(len(mirPackage.elementTable) == 1)

if __name__ == '__main__':
    unittest.main()