SysmelClassDefinitionNoSuper(ProtoObject);
    SysmelClassDefinition(Object, ProtoObject);

SysmelClassDefinition(Type, Object);
    SysmelClassDefinition(TypeUniverse, Type);
    SysmelClassDefinition(NominalType, Type);
        SysmelClassDefinition(Behavior, NominalType);
            SysmelClassDefinition(Class, Behavior);
            SysmelClassDefinition(Metaclass, Behavior);

SysmelClassDefinition(Boolean, Object);
    SysmelClassDefinition(True, Boolean);
    SysmelClassDefinition(False, Boolean);

SysmelClassDefinition(Magnitude, Object);
    SysmelClassDefinition(Character, Magnitude);
    SysmelClassDefinition(Number, Magnitude);
        SysmelClassDefinition(Float, Number);
            SysmelClassDefinition(BoxedFloat, Float);
            SysmelClassDefinition(SmallFloat, Float);
        SysmelClassDefinition(Integer, Number);
            SysmelClassDefinition(SmallInteger, Integer);

SysmelClassDefinition(Collection, Object);
    SysmelClassDefinition(SequenceableCollection, Collection);
    SysmelClassDefinition(ArrayedCollection, SequenceableCollection);
        SysmelClassDefinition(String, ArrayedCollection);
        SysmelClassDefinition(Symbol, ArrayedCollection);
