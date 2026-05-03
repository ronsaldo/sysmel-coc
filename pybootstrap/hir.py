from parsetree import SourcePosition
from abc import ABC, abstractmethod

class HIRVisitor(ABC):
    def visitValue(self, value):
        pass

class HIRValue(ABC):
    def __init__(self, sourcePosition: SourcePosition):
        self.sourcePosition = sourcePosition
    
    def accept(self, visitor: HIRVisitor):
        return visitor.visitValue(self)
    
    @abstractmethod
    def getType(self):
        pass
    
    def isType(self):
        return False

    def isNominalType(self):
        return False

    def isDynamicType(self):
        return False

    def isUniverseType(self):
        return False

class HIRType(HIRValue):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(sourcePosition)
        self.coreTypes = coreTypes

    def getType(self):
        return self.coreTypes.getUniverseAtLevel(0)
    
    def isType(self):
        return True

class HIRNominalType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isNominalType(self):
        return True
 

class HIRDynamicType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isDynamicType(self):
        return True

class HIRUniverseType(HIRType):
    def __init__(self, name: str, coreTypes, level: int):
        super().__init__(coreTypes, None)
        self.level = level
        self.name = name

    def getName(self):
        return self.name

    def getType(self):
        return self.coreTypes.getUniverseAtLevel(self.level + 1)

    def isUniverseType(self):
        return True

class HIRPackage(HIRValue):
    def __init__(self, name: str):
        self.name = name
        self.usedPackages = []
        self.children = []
        self.publicSymbolTable = {}
        self.coreTypes = None

    def addCoreTypes(self, coreTypes):
        self.coreTypes = coreTypes
        for type in coreTypes.coreTypeList:
            typeName = type.getName()
            self.addSymbolWithBinding(typeName, type)

    def addSymbolWithBinding(self, symbol: str, binding: HIRValue):
        self.children.append(binding)
        self.publicSymbolTable[symbol] = binding

    def getType(self):
        return self.coreTypes.packageType

    def lookupSymbolRecursivelyOrNone(self, symbol: str):
        if symbol in self.publicSymbolTable:
            return self.publicSymbolTable[symbol]
        
        for usedPackage in self.usedPackages:
            usedSymbol = usedPackage.lookupSymbolRecursivelyOrNone(symbol)
            if usedSymbol is not None:
                return usedSymbol
                    
        return None

    def usePackage(self, package):
        if package not in self.usedPackages:
            self.usedPackages.append(package)

class HIRCoreTypes:
    def __init__(self):
        self.pointerSize = 8
        self.pointerAlignment = 8

        self.integerType   = HIRNominalType('Integer', self, None);
        self.characterType = HIRNominalType('Character', self, None);
        self.floatType     = HIRNominalType('Float', self, None);
        self.booleanType   = HIRNominalType('Boolean', self, None);
        self.stringType    = HIRNominalType('String', self, None);
        self.symbolType    = HIRNominalType('Symbol', self, None);
        self.voidType      = HIRNominalType('Void', self, None);
        self.undefinedType = HIRNominalType('Undefined', self, None);
        
        self.dynamicType = HIRDynamicType('Dynamic', self, None)

        self.packageType = HIRNominalType('Package', self, None)

        self.prop = HIRUniverseType('Prop', self, 0);
        self.type = HIRUniverseType('Type', self, 1);
        self.universeLevels = {
            0: self.prop,
            1: self.type,
        }

        self.coreTypeList = [
            self.integerType,
            self.characterType,
            self.floatType,
            self.booleanType,
            self.stringType,
            self.symbolType,
            self.voidType,
            self.undefinedType,

            self.dynamicType,

            self.prop,
            self.type,
        ]
        self.coreValueList = [
            
        ]
    
    def getUniverseAtLevel(self, level):
        if level in self.universeLevels:
            return self.universeLevels[level]
        newLevel = HIRUniverseType(None, self, level)
        self.universeLevels[level] = newLevel
        return newLevel

class HIRContext:
    def __init__(self):
        self.coreTypes = HIRCoreTypes()
        self.corePackage = HIRPackage('CoreLib')
        self.corePackage.addCoreTypes(self.coreTypes)
        self.currentPackage = self.corePackage
