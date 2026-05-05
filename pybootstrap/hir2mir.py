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
        self.setCoreTypeMappings()

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

    def makeNominalTypeWithMethods(self, type: HIRNominalType):
        typeWithMethodDictionary = MirTypeWithMethodDictionary(type.name, type)
        self.currentMirPackage.addElement(typeWithMethodDictionary)
        for method in type.childrenMethods:
            translatedMethod = self.translateValue(method)
            if translatedMethod is not None:
                typeWithMethodDictionary.withSelectorAddMethod(method.selector, translatedMethod)

        return typeWithMethodDictionary

    def visitNextValue(self, value: HIRValue):
        return value.accept(self)

    def visitValue(self, value):
        assert False

    def visitType(self, value):
        assert False

    def visitNominalType(self, type: HIRNominalType):
        mirType = self.coreTypeMappings.get(type, self.context.gcPointerType)
        self.valueMap[type] = mirType

        self.makeNominalTypeWithMethods(type)
        return mirType

    def visitDynamicType(self, type: HIRDynamicType):
        return self.context.gcPointerType

    def visitVoidType(self, type: HIRVoidType):
        return self.context.voidType

    def visitControlFlowEscapeType(self, type: HIRControlFlowEscapeType):
        return self.context.voidType

    def visitUniverseType(self, type: HIRUniverseType):
        return self.context.gcPointerType

    def visitAssociationType(self, type: HIRAssociationType):
        return self.context.gcPointerType

    def visitDictionaryType(self, type: HIRDictionaryType):
        assert False

    def visitEnumType(self, type: HIREnumType):
        assert False

    def visitBehavior(self, type: HIRBehavior):
        assert False

    def visitClass(self, type: HIRClass):
        mirType = self.context.gcPointerType
        self.valueMap[type] = mirType

        self.makeNominalTypeWithMethods(type)
        return mirType

    def visitMetaclass(self, type: HIRMetaclass):
        assert False
        return self.context.gcPointerType

    def visitStructType(self, type: HIRStructType):
        assert False

    def visitTupleType(self, type: HIRTupleType):
        assert False

    def visitDerivedType(self, type: HIRDerivedType):
        assert False

    def visitPointerLikeType(self, type: HIRPointerLikeType):
        # TODO: inspect the base type to determine the corrent pointer type
        return self.context.gcPointerType

    def visitPointerType(self, type: HIRPointerType):
        return self.visitPointerLikeType(type)

    def visitReferenceType(self, type: HIRReferenceType):
        return self.visitPointerLikeType(type)

    def visitMutableValueBoxType(self, type: HIRMutableValueBoxType):
        return self.context.gcPointerType

    def visitSimpleFunctionType(self, type: HIRSimpleFunctionType):
        return self.context.gcPointerType
    
    def visitDependentFunctionType(self, type: HIRDependentFunctionType):
        return self.context.gcPointerType
    
    def visitConstantLiteralBooleanValue(self, value):
        return MirInlineConstant(value.value, self.context.boolean8Type)
    
    def visitConstantLiteralVoidValue(self, value):
        return MirInlineConstant(None, self.context.voidType)

    def visitConstantLiteralNilValue(self, value):
        return MirInlineConstant(None, self.context.pointerType)
    
    def visitMetaBuilderFactory(self, value):
        return None
    
    def visitPrimitiveFunction(self, primitiveFunction):
        runtimeFunctionName = self.context.getPrimitiveRuntimeFunctionNameFor(primitiveFunction.name)
        return self.currentMirPackage.getOrCreateRuntimePrimitiveNamed(runtimeFunctionName)

    def visitPrimitiveMacro(self, value):
        return None

    def visitPackage(self, package: HIRPackage):
        if package in self.valueMap:
            return self.valueMap[package]
        
        # Start translating the package.
        oldCurrentPackage = self.currentMirPackage
        mirPackage = MirPackage(self.context, package.name)
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
        #mirPackage.dumpToConsole()
        return mirPackage

class HirFunction2Mir(HIRVisitor):
    def __init__(self):
        super().__init__()