import unittest
from lir import *
from unicorn import *
from unicorn.x86_const import *

SimulationAddress    = 0x1000000
SimulationMemorySize = 0x200000

class LirX64Test(unittest.TestCase):
    def setUp(self):
        self.lirModule = LirModule()
        self.lirModule.name = "TestModule"
        return super().setUp()
    
    def runModule(self):
        segment = self.lirModule.makeSingleSegmentRelocatedToAddress(SimulationAddress)

        mu = Uc(UC_ARCH_X86, UC_MODE_64)
        mu.mem_map(SimulationAddress, SimulationMemorySize)
        mu.mem_write(SimulationAddress, bytes(segment))
        mu.reg_write(UC_X86_REG_RSP, SimulationAddress + SimulationMemorySize)

        exitResult = []
        def hookSyscall(mu: Uc, userData):
            rax = mu.reg_read(UC_X86_REG_RAX)
            if rax == 60:
                exitResult.append(mu.reg_read(UC_X86_REG_RDI))
            mu.emu_stop()

        mu.hook_add(UC_HOOK_INSN, hookSyscall, None, 1, 0, UC_X86_INS_SYSCALL)

        mu.emu_start(SimulationAddress, SimulationAddress + len(segment))
        return exitResult
    
    def testEmptyModule(self):
        encodedModule = self.lirModule.encodeModuleObject()
        decodedModule = LirModule().decodeModuleObject(encodedModule)
        self.assertEqual(decodedModule.name, "TestModule")
        self.assertEqual(0, len(decodedModule.sections))
        self.assertEqual(0, len(decodedModule.symbolTable))

    def testEmptyTextSection(self):
        self.lirModule.getOrCreateNullSection()
        self.lirModule.getOrCreateTextSection()
        self.assertEqual(2, len(self.lirModule.symbolTable))
        self.assertEqual(2, len(self.lirModule.sections))
        self.assertEqual('', self.lirModule.sections[0].name)
        self.assertEqual('.text', self.lirModule.sections[1].name)

        encodedModule = self.lirModule.encodeModuleObject()
        ##print(encodedModule)

        decodedModule = LirModule().decodeModuleObject(encodedModule)
        self.assertEqual(decodedModule.name, "TestModule")
        self.assertEqual(2, len(decodedModule.sections))
        self.assertEqual(2, len(decodedModule.symbolTable))
        self.assertEqual('', decodedModule.sections[0].name)
        self.assertEqual('.text', decodedModule.sections[1].name)

    def testTextSectionFunctionCalls(self):
        self.lirModule.getOrCreateNullSection()
        self.lirModule.getOrCreateTextSection()

        asm = LirAssembler(self.lirModule)
        asm.textSection()

        add = asm.makeGlobalFunctionSymbol('add')
        main = asm.makeGlobalFunctionSymbol('main')

        asm.x86_entryPointForGsv(main)

        asm.setSymbolHere(main)
        asm.x86_endbr64()
        asm.x86_mov32RegImm32(X86_EDI, 1)
        asm.x86_mov32RegImm32(X86_ESI, 2)
        asm.x86_callGsv(add)
        asm.x86_ret()
        asm.endFunctionSymbolHere(main)

        asm.setSymbolHere(add)
        asm.x86_endbr64()
        asm.x86_mov32RegReg(X86_EAX, X86_EDI)
        asm.x86_add32RegReg(X86_EAX, X86_ESI)
        asm.x86_ret()
        asm.endFunctionSymbolHere(add)

        ##self.lirModule.saveModuleToFile('testSectionReturnFunction.smo')
        encodedModule = self.lirModule.encodeModuleObject()
        ##print(encodedModule)

        decodedModule = LirModule().decodeModuleObject(encodedModule)
        self.assertEqual(decodedModule.name, "TestModule")
        self.assertEqual(2, len(decodedModule.sections))
        self.assertEqual(5, len(decodedModule.symbolTable))
        self.assertEqual('', decodedModule.sections[0].name)
        self.assertEqual('.text', decodedModule.sections[1].name)

        ## Run the module
        result = self.runModule()
        self.assertEqual(3, result[0])


if __name__ == '__main__':
    unittest.main()
