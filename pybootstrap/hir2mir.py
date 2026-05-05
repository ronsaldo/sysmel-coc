from hir import *
from mirContext import *
from mir import *

class HirPackage2Mir(HIRVisitor):
    def __init__(self, coreTypes: HIRCoreTypes, context: MirContext):
        super().__init__()
        self.hirCoreTypes = coreTypes
        self.context = context
        self.valueMap = {}
        self.packageList = []
        self.currentMirPackage = None

    def setCoreTypeMappings(self):
        self.coreTypeMappings = {
            self.hirCoreTypes.booleanType : self.context.boolean8Type
        }

    def translateHirPackage2Mir(self, hirPackage: HIRPackage):
        return self.translateValue(hirPackage)
    
    def translateValue(self, value: HIRValue):
        if value in self.valueMap:
            return self.valueMap[value]
        
        assert not value.isFunctionLocalValue()
        translatedValue = self.visitNextValue(value)
        self.valueMap[value] = translatedValue
        return translatedValue


    def visitNextValue(self, value: HIRValue):
        return value.accept(self)

    def visitValue(self, value):
        assert False

    def visitType(self, value):
        assert False

    def visitNominalType(self, type):
        return self.context.gcPointerType

    def visitDynamicType(self, type):
        return self.context.gcPointerType

    def visitVoidType(self, type):
        return self.context.voidType

    def visitControlFlowEscapeType(self, type):
        return self.context.voidType

    def visitUniverseType(self, type):
        return self.context.gcPointerType

    def visitAssociationType(self, type):
        return self.context.gcPointerType

    def visitDictionaryType(self, type):
        assert False

    def visitEnumType(self, type):
        assert False

    def visitBehavior(self, type):
        assert False

    def visitClass(self, type):
        assert False

    def visitMetaclass(self, type):
        assert False

    def visitStructType(self, type):
        assert False

    def visitTupleType(self, type):
        assert False

    def visitDerivedType(self, type):
        assert False

    def visitPointerLikeType(self, type):
        return self.context.pointerType

    def visitPointerType(self, type):
        return self.context.pointerType

    def visitReferenceType(self, type):
        return self.context.pointerType

    def visitMutableValueBoxType(self, type):
        return self.context.gcPointerType

    def visitSimpleFunctionType(self, type):
        return self.context.gcPointerType
    
    def visitDependentFunctionType(self, type):
        return self.context.gcPointerType

    def visitPackage(self, package: HIRPackage):
        if package in self.valueMap:
            return self.valueMap[package]
        
        # Start translating the package.
        oldCurrentPackage = self.currentMirPackage
        mirPackage = MirPackage(package.name)
        self.valueMap[package] = mirPackage
        self.currentMirPackage = mirPackage

        # Translate the used packages.
        for usedPackage in package.usedPackages:
            self.translateValue(usedPackage)
            
        # Translate the children
        package.finishPendingAnalysis()
        for child in package.children:
            self.translateValue(child)

        self.currentMirPackage = oldCurrentPackage
        return mirPackage

class HirFunction2Mir(HIRVisitor):
    def __init__(self):
        super().__init__()