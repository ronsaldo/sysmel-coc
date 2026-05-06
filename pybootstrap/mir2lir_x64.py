from mir import *
from lir import *

class MirPackage2LirX64(MirVisitor):
    def __init__(self, context: MirContext):
        super().__init__()
        self.context = context
        self.lirModule: LirModule = None

    def translateMirPackage(self, mirPackage: MirPackage):
        self.lirModule = LirModule()
        self.lirModule.name = mirPackage.name
        return self.lirModule
        
