from hir import *
from mirContext import *
from mir import *

class HirPackage2Mir(HIRVisitor):
    def __init__(self, context: MirContext):
        super().__init__()
        self.context = context
    
    def translateHirPackage2Mir(self, hirPackage: HIRPackage, mirPackage: MirPackage):
        
        return mirPackage

class HirFunction2Mir(HIRVisitor):
    def __init__(self):
        super().__init__()