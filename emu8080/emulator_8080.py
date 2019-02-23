''' 
    python8080, an 8080 emulator designed for arcade games.
    Copyright (C) 2019  Jacob Gray

    This program is free software: you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation, either version 3 of
    the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  
    If not, see <https://www.gnu.org/licenses/>.
'''

from functools import partial
import emu8080.system_state_8080 as state
from sys import exit

_debug_mode = 'none' # options are 'print' or 'write'
_debug_file = "./debug_file"

def unimplemented_instruction(opcode):
    '''Prints failed instruction info'''
    print("\n\n")
    print("Unimplemented instruction: " + str("0x%02x" % opcode))
    print("Dumping and exiting.\n\n")
    #print(state.summarize())
    exit()

def emulate_operation():
    '''Parse current instruction and call the relevant code, 
        increasing the PC as appropriate for that instruction'''
    opcode = state.get_current_opcode()
    # opcodes in dict that are yet to be defined exist as strings,
    # which will crash the program (string cannot be executed error)
    '''Pulling the instruction from dict as an index rather than
        with dict.get() will crash if an invalid value is submitted
        but benchmarking suggests performance increases up to 40%'''
    operation = instruction_dict_8080[opcode]
    #print("{:04x}\t".format(state.get_register_value('pc')) \
    #    + "{:02x}\t".format(opcode), end=' ')
    # call the function or partial from the instruction dictionary
    instruction_length = operation()
    '''The return value for some functions defines whether to
        increment the PC at this point, because e.g. a True JMP_IF
        shouldn't increase it (it affects the downstream value 
        incorrectly) but a false JMP_IF should change. The correct
        increase is returned by each operation to be used here'''
    state.increase_pc(instruction_length)
    return opcode

def hexform(value):
    '''Return numbers as hex strings, or return string back if
        a different type is provided'''
    if type(value) is int:
        if value < 0xff:
            return ".{:02x}".format(value)
        else:
            return ".{:04x}".format(value)
    else:
        return str(value)

def dlog(*messages):
    '''Print or write debug log according to debug_mode flag'''
    if _debug_mode == 'print':
        print(messages[0], end='')
        for msg in messages[1:]:
            print(hexform(msg), end=" ")
        print()
    #elif _debug_mode == 'write':
        #with open(_debug_file, 'a') as o:
        #    o.write(messages + '\n')
    return

def load_program(binary_data, start_address = 0):
    '''Loads a program into memory from binary data, starting at 
        start_address if provided'''
    state.load_program(binary_data, start_address)

def impl_count():
    '''Provides a count of implemented and unimplemented instructions
        in the instruction dict'''
    done = 0
    notdone = 0
    for element in instruction_dict_8080.values():
        if type(element) is str:
            done += 1
        else:
            notdone += 1
    print("Blank instructions    : " + str(done))
    print("Existing instructions : " + str(notdone))

def get_high_byte(data):
    '''Returns the high byte of a 16-bit value'''
    return (data & 0xff00) >> 8

def get_low_byte(data):
    '''Returns the low byte of a 16-bit value'''
    return data & 0x00ff

def get_16_bit_from_byte_pair(high_byte, low_byte):
    '''Returns a 16-bit number constructed from two bytes'''
    return (high_byte << 8) | low_byte


'''
***********************************************************************
                       Instruction set functions
***********************************************************************
'''

''' Each instruction returns the amount to increase the PC following
    that operation'''

def nop():
    '''No operation'''
    dlog("NOP\t")
    return 1

def mov(register_to, register_from):
    '''Move stored value from register2 to register1'''
    dlog("MOV\t\t", register_to, "<-", register_from)
    state.set_register_copy(register_to, register_from)
    return 1

def mov_m(register_to):
    '''Move stored value from register2 to register1'''
    value = state.get_memory_by_registers('h', 'l')
    dlog("MOV M\t\t", register_to, "<-", value)
    state.set_register_value(register_to, value)
    return 1

def mov_to_m(target_register):
    '''Move target register into memory address specified by HL'''
    dlog("MOV TO M\t", target_register)
    value = state.get_register_value(target_register)
    state.set_memory_by_registers(value, 'h', 'l')
    return 1

def lxi(high_target, low_target):
    '''Load Pair Immediate into specified register pair'''
    high_data = state.get_memory_by_offset(2)
    low_data = state.get_memory_by_offset(1)
    dlog("LXI\t\t", high_target, low_target, high_data, low_data)
    state.set_register_value(high_target, high_data)
    state.set_register_value(low_target, low_data)
    return 3

def lxi_sp():
    '''Load Pair Immediate into Stack Pointer'''
    high_data = state.get_memory_by_offset(2)
    low_data = state.get_memory_by_offset(1)
    dlog("LXI SP\t\t", high_data, low_data)
    state.set_register_value('sp', \
        get_16_bit_from_byte_pair(high_data, low_data))
    return 3

def add(register_to, register_from):
    '''Add a register value to defined register, updating flags.
        If read_carry is passed as True, the carry bit will be added
        in the operation.'''
    dlog("ADD\t\t", register_to, register_from)
    result = state.get_register_value(register_to) \
            + state.get_register_value(register_from)
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','cy','ac'])
    return 1

def add_m(register_to):
    '''Add memory byte stored at HL to the provided register,
        updating flags'''
    dlog("ADD M\t\t", register_to)
    result = state.get_register_value(register_to) \
            + state.get_memory_by_registers('h', 'l')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','cy','ac'])
    return 1

def adc(register_to, register_from):
    '''Add from register value to register_to, including the value
        of the carry bit, and updates flags based on the result'''
    dlog("ADC\t\t", register_to, register_from)
    result = state.get_register_value(register_to)    \
            + state.get_register_value(register_from) \
            + state.get_flag('cy')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','cy','ac'])
    return 1

def adc_m(register_to):
    '''Add memory byte stored at HL to the provided register,
        updating flags'''
    dlog("ADC M\t\t", register_to)
    result = state.get_register_value(register_to)    \
            + state.get_memory_by_registers('h', 'l') \
            + state.get_flag('cy')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','cy','ac'])
    return 1

def adi(register_to):
    '''Add immediate byte to the specified register, 
        updating flags.'''
    byte = state.get_memory_by_offset(1)
    dlog("ADI\t\t", byte)
    result = state.get_register_value(register_to) + byte
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','cy','ac'])
    return 2

def aci(register_to):
    '''Add immediate byte to the specified register, as well as the
        value of the carry bit, and update flags.'''
    byte = state.get_memory_by_offset(1)
    dlog("ADI\t\t", byte)
    result = state.get_register_value(register_to) \
                + byte                             \
                + state.get_flag('cy')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','cy','ac'])
    return 2

def sub(register_to, register_from):
    '''Subtract - Store difference of to and from into register_to'''
    dlog("SUB\t\t", register_to, register_from)
    if register_from == 'm':
        subtrahend = state.get_memory_by_registers('h', 'l')
    else:
        subtrahend = state.get_register_value(register_from)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) + subtrahend
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 1

def sub_m(register_to):
    '''Subtract from memory - Store difference of to and memory byte
        at HL into regsiter_to'''
    subtrahend = state.get_memory_by_registers('h', 'l')
    dlog("SUB M\t\t", register_to, subtrahend)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) + subtrahend
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 1

def sbb(register_to, register_from):
    '''Subtract with borrow - Store difference of to and from into
        register_to, including the carry bit as a borrow'''
    #TODO I don't think this is correct for new carry when borrowing
    dlog("SBB\t\t", register_to, register_from)
    subtrahend = state.get_register_value(register_from)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) \
                + subtrahend                       \
                - state.get_flag('cy')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 1

def sbb_m(register_to):
    '''Subtractfrom memory with borrow - Store difference of to and
        memory byte at HL into regsiter_to, including the carry bit
        as a borrow''' 
    #TODO I don't think this is correct for new carry when borrowing
    subtrahend = state.get_memory_by_registers('h', 'l')
    dlog("SBB M\t\t", register_to, subtrahend)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) \
                + subtrahend                       \
                - state.get_flag('cy')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 1

def sui(register_to):
    '''Subtract Immedate - Stores difference of register_to and
        immediate byte in register_to, updating flags'''
    subtrahend = state.get_memory_by_offset(1)
    dlog("SUI\t\t", register_to, subtrahend)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) + subtrahend
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 2

def sbi(register_to):
    '''Subtract Immediate with Borrow - Stores difference of 
        register_to and immediate byte in register_to, including
        the value of the carry bit as a borrow and updating flags'''
    subtrahend = state.get_memory_by_offset(1)
    dlog("SBI\t\t", register_to, subtrahend)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) \
                + subtrahend                       \
                - state.get_flag('cy')
    state.set_register_value(register_to, result)
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 2

def cmp(register_to, register_from):
    '''Compare, sets flags based on (to - from). If from is not
        set, use immediate byte instead'''
    subtrahend = state.get_register_value(register_from)
    dlog("CMP\t\t", register_to, register_from, subtrahend)
    carry = subtrahend > state.get_register_value(register_to)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register_to) + subtrahend
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 1

def cmp_m(register):
    '''Compare to memory, sets flags based on 
        (register - memory at HL)'''
    subtrahend = state.get_memory_by_registers('h', 'l')
    dlog("CMP M\t\t", register, subtrahend)
    carry = subtrahend > state.get_register_value(register)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register) + subtrahend
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 1
        

def cmi(register):
    '''Compare to immediate - sets flags based on 
        (register - immediate byte)'''
    subtrahend = state.get_memory_by_offset(1)
    dlog("CMI\t\t", register, subtrahend)
    carry = subtrahend > state.get_register_value(register)
    subtrahend = -subtrahend & 0xff
    result = state.get_register_value(register) + subtrahend
    state.set_flags(result, ['z','s','p','ac'])
    state.set_single_flag('cy', carry)
    return 2

def save(register_from, register_high, register_low):
    '''Saves data value to the address specified by the 
        provided 8-bit registerpair '''
    dlog("SAVE\t\t", register_from, register_high, register_low)
    value = state.get_register_value(register_from)
    state.set_memory_by_registers(value, register_high, register_low)
    return 1

def load_r(target_register, high_byte, low_byte):
    '''Loads 16-bit data into target register from register pair'''
    dlog("LOAD R\t\t", target_register, high_byte, low_byte)
    value = (state.get_register_value(high_byte) << 8) \
            | state.get_register_value(low_byte)
    state.set_register_value(target_register, value)
    if target_register == 'pc':
        return 0
    else:
        return 1

def load_m(target_register, high_byte, low_byte):
    '''Loads data into the target register from a memory address, 
        provided as register pair'''
    dlog("LOAD M\t\t", target_register, high_byte, low_byte)
    state.set_register_value(target_register, \
                state.get_memory_by_registers(high_byte, low_byte))
    if target_register == 'pc':
        return 0
    else:
        return 1

def inr(target_register):
    '''Increment Register or Memory'''
    if target_register == 'm':
        inr_m()
        return 1
    dlog("INR\t\t", target_register)
    result = state.get_register_value(target_register) + 1
    state.set_register_value(target_register, result)
    state.set_flags(result, ['z','s','p','ac'])
    return 1

def inr_m():
    '''Increment Memory stored at address described by HL. Not
        intended to be called directly, call inr("m") instead'''
    dlog("INR M\t\t")
    result = state.get_memory_by_registers('h', 'l')
    result += 1
    state.set_memory_by_registers(result, 'h', 'l')
    state.set_flags(result, ['z','s','p','ac'])
    return 1

def dcr(target_register):
    '''Decrement Register'''
    dlog("DCR\t\t", target_register)
    state.decrement_register(target_register)
    # NOTE: inaccurate, does not handle 0-- correctly for flags
    state.set_flags(state.get_register_value(target_register), \
                                             ['z','s','p','ac'])
    return 1

def dcr_m():
    '''Decrement Memory stored at address described by HL'''
    dlog("DCR M\t\t")
    result = state.get_memory_by_registers('h', 'l')
    result -= 1
    state.set_memory_by_registers(result, 'h', 'l')
    state.set_flags(result, ['z', 's', 'p', 'ac'])
    return 1

def mvi(target_register):
    '''Loads immediate byte into the target register'''
    byte = state.get_memory_by_offset(1)
    dlog("MVI\t\t", target_register, byte)
    state.set_register_value(target_register, byte)
    return 2

def mvi_m():
    '''Loads immediate byte to the memory address indicated by HL'''
    byte = state.get_memory_by_offset(1)
    dlog("MVI_M\t\t", byte)
    state.set_memory_by_registers(byte, 'h', 'l')
    return 2

def jmp(address = None):
    '''Jump to immediate address, or arg address if provided'''
    address = state.get_memory_word_immediate()
    dlog("JMP\t\t", address)
    state.set_register_value('pc', address)
    return 0

def jmp_flag(condition):
    '''Jump to immediate address if flag is True'''
    dlog("JMP IF\t\t", condition)
    if state.get_flag(condition):
        address = state.get_memory_word_immediate()
        state.set_register_value('pc', address)
        return 0
    else:
        return 3

def jmp_not_flag(condition):
    '''Jump to immediate address if flag is False'''
    dlog("JMP IFN\t\t", condition)
    if not state.get_flag(condition):
        address = state.get_memory_word_immediate()
        state.set_register_value('pc', address)
        return 0
    else:
        return 3

def push(high_byte, low_byte):
    '''Push register values onto the stack'''
    dlog("PUSH\t\t", high_byte, low_byte)
    if type(high_byte) is str: # Then it's a register, convert
        high_byte = state.get_register_value(high_byte)
        low_byte = state.get_register_value(low_byte)
    state.decrement_register('sp')
    state.set_stack_top(high_byte)
    state.decrement_register('sp')
    state.set_stack_top(low_byte)
    return 1

def push_psw():
    '''Push ACC and flags onto the stack'''
    dlog("PUSH PSW\t")
    high_byte = state.get_register_value('a')
    low_byte = 0b10 # Spec declares format thusly: s z 0 ac 0 p 1 cy
    low_byte ^= state.get_flag('cy') << 0
    low_byte ^= state.get_flag('p')  << 2
    low_byte ^= state.get_flag('ac') << 4
    low_byte ^= state.get_flag('z')  << 6
    low_byte ^= state.get_flag('s')  << 7
    push(high_byte, low_byte)
    return 1

def pop(high_target, low_target):
    '''Pop values from the stack to the given target registers'''
    dlog("POP\t\t", high_target, low_target)
    state.set_register_value(low_target, state.get_stack_top())
    state.increment_register('sp')
    state.set_register_value(high_target, state.get_stack_top())
    state.increment_register('sp')
    return 1

def pop_psw():
    '''Pop values from the stack into ACC and state flags'''
    dlog("POP PSW\t")
    flags_byte = state.get_stack_top() #format: s z 0 ac 0 p 1 cy
    state.increment_register('sp')
    state.set_register_value('a', state.get_stack_top())
    state.increment_register('sp')
    state.set_single_flag('cy', flags_byte & (1<<0))
    state.set_single_flag('p',  flags_byte & (1<<2))
    state.set_single_flag('ac', flags_byte & (1<<4))
    state.set_single_flag('z',  flags_byte & (1<<6))
    state.set_single_flag('s',  flags_byte & (1<<7))
    return 1

def call():
    '''Push pc+3 onto stack, jump to immediate address'''
    target = state.get_memory_word_immediate()
    dlog("CALL\t\t", target)
    state.increase_pc(3)
    high_byte = get_high_byte(state.get_register_value('pc'))
    low_byte = get_low_byte(state.get_register_value('pc'))
    push(high_byte, low_byte)
    state.set_register_value('pc', target)
    return 0

def ret():
    '''Pop address from the stack, store it in pc'''
    low_data = state.get_stack_top()
    state.increment_register('sp')
    high_data = state.get_stack_top()
    state.increment_register('sp')
    dlog("RET\t\t", high_data, low_data)
    true_data = get_16_bit_from_byte_pair(high_data, low_data)
    state.set_register_value('pc', true_data)
    return 0

def call_flag(condition):
    '''Call if condition is True'''
    dlog("CALL IF\t\t", condition)
    if state.get_flag(condition):
        call()
        return 0
    else:
        return 3

def call_not_flag(condition):
    '''Call if condition is False'''
    dlog("CALL IFN\t\t", condition)
    if not state.get_flag(condition):
        call()
        return 0
    else:
        return 3

def ret_flag(condition):
    '''Return if condition is True'''
    dlog("RET IF\t\t", condition)
    if state.get_flag(condition):
        ret()
        return 0
    else:
        return 1

def ret_not_flag(condition):
    '''Return if condition is False'''
    dlog("RET IFN\t\t", condition)
    if not state.get_flag(condition):
        ret()
        return 0
    else:
        return 1

def rst(target):
    '''Reset (interrupt) - stores the current PC on the stack and
        jumps to the target memory location'''
    dlog("RST\t\t", target)
    high_byte = get_high_byte(state.get_register_value('pc'))
    low_byte = get_low_byte(state.get_register_value('pc'))
    push(high_byte, low_byte)
    state.set_register_value('pc', target)
    return 0

'''The following logical operation methods could probably be
    condensed through some trickery, but I'm not sure what yet
    and it works fine as is. It just seems like a lot of repetition'''

def ana(register_from):
    '''Logical AND, stores A & register_from -> A'''
    dlog("ANA\t\t", register_from)
    result = state.get_register_value('a')
    if register_from == 'm':
        result &= state.get_memory_by_registers('h', 'l')
    else:
        result &= state.get_register_value(register_from)
    state.set_register_value('a', result)
    state.set_flags(result, ['z', 's', 'p', 'cy', 'ac'])
    return 1

def ani():
    '''Logical AND Immediate, stores A & immediate byte ->A'''
    byte = state.get_memory_by_offset(1)
    dlog("ANI\t\t", byte)
    result = state.get_register_value('a')
    result &= byte
    state.set_register_value('a', result)
    state.set_flags(result, ['z', 's', 'p'])
    state.set_single_flag('cy', False) # According to the spec
    return 2

def xra(register_from):
    '''Logical XOR, stores A ^ register_from -> A'''
    dlog("XRA\t\t", register_from)
    result = state.get_register_value('a')
    if register_from == 'm':
        result ^= state.get_memory_by_registers('h', 'l')
    else:
        result ^= state.get_register_value(register_from)
    state.set_register_value('a', result)
    state.set_flags(result, ['z', 's', 'p', 'cy', 'ac'])
    return 1

def xri():
    '''Logical XOR, stores A ^ immediate byte -> A'''
    byte = state.get_memory_by_offset(1)
    dlog("XRI\t\t", byte)
    result = state.get_register_value('a')
    result ^= byte
    state.set_register_value('a', result)
    state.set_flags(result, ['z', 's', 'p', 'cy', 'ac'])
    return 2

def ora(register_from):
    '''Logical OR, stores A | register_from -> A'''
    dlog("ORA\t\t", register_from)
    result = state.get_register_value('a')
    if register_from == 'm':
        result |= state.get_memory_by_registers('h', 'l')
    else:
        result |= state.get_register_value(register_from)
    state.set_register_value('a', result)
    state.set_flags(result, ['z', 's', 'p', 'cy', 'ac'])
    return 1

def ori():
    '''Logical OR, stores A | immediate byte -> A'''
    byte = state.get_memory_by_offset(1)
    dlog("ORI\t\t", byte)
    result = state.get_register_value('a')
    result |= byte
    state.set_register_value('a', result)
    state.set_flags(result, ['z', 's', 'p', 'cy', 'ac'])
    return 2

def cma():
    '''Complement Accumulator, inverts the value stored in acc'''
    dlog("CMA\t")
    state.set_register_value('a', ~state.get_register_value('a'))
    return 1

def addx(high_byte, low_byte, mod_value):
    '''Add mod_value to register pair, treating it as a 16-bit value
        and storing back into original registers. For use in INX/DCX
        operations'''
    dlog("ADDX\t\t", high_byte, low_byte, mod_value)
    bigval = state.get_register_pair_value(high_byte, low_byte)
    bigval += mod_value
    state.set_register_pair_value(bigval, high_byte, low_byte)
    return 1

def addx_sp(mod_value):
    '''Add mod_value to stack pointer. For use in INXSP/DCXSP'''
    dlog("ADDX_SP\t\t", mod_value)
    result = state.get_register_value('sp') + mod_value
    state.set_register_value('sp', result)
    return 1

def rlc():
    '''Rotate Accumulator Left - the mnemonic seems backwards for
        RLC/RAL RRC/RAR but that's canonical via the manual'''
    dlog("RLC\t")
    result = state.get_register_value('a')
    bit7 = (result & 128) != 0
    result <<= 1
    result += bit7 # places bit 7 at new bit 0
    state.set_single_flag('cy', bit7)
    state.set_register_value('a', result)
    return 1

def ral():
    '''Rotate Accumulator Left through Carry'''
    dlog("RAL\t")
    result = state.get_register_value('a')
    bit7 = (result & 128) != 0
    result <<= 1
    result += state.get_flag('cy') # places carry bit at new bit 0
    state.set_single_flag('cy', bit7)
    state.set_register_value('a', result)
    return 1

def rrc():
    '''Rotate Accumulator Right'''
    dlog("RRC\t")
    result = state.get_register_value('a')
    bit0 = (result & 1) != 0
    result >>= 1
    result += bit0 * 128 # places bit 0 at new bit 7
    state.set_single_flag('cy', bit0)
    state.set_register_value('a', result)
    return 1

def rar():
    '''Rotate Accumulator Right through Carry'''
    dlog("RAR\t")
    result = state.get_register_value('a')
    bit0 = (result & 1) != 0
    result >>= 1
    result += state.get_flag('cy') * 128 # places cy bit at new bit 7
    state.set_single_flag('cy', bit0)
    state.set_register_value('a', result)
    return 1

def stc():
    '''Set Carry'''
    dlog("STC\t")
    state.set_single_flag('cy', True)
    return 1

def cmc():
    '''Complement Carry'''
    dlog("CMC\t")
    state.set_single_flag('cy', not state.get_flag('cy'))
    return 1

def set_interrupt_enabled(new_bool):
    '''Sets interrupt_enabled to the given bool'''
    dlog("SetInter\t", new_bool)
    state.set_single_flag('interrupt_enabled', new_bool)
    return 1

def dad(high_byte, low_byte):
    ''' Double Add - provided register pair is added to HL pair 
        with 16-bit math'''
    dlog("DAD\t\t", high_byte, low_byte)
    result = state.get_register_pair_value('h', 'l')
    result += state.get_register_pair_value(high_byte, low_byte)
    state.set_single_flag('cy', result > 0xffff)
    state.set_register_pair_value(result, 'h', 'l')
    return 1

def dad_sp():
    '''Double Add - the current stack pointer is added to HL as 
        a 16-bit value'''
    high_byte = get_high_byte(state.get_register_value('sp'))
    low_byte = get_low_byte(state.get_register_value('sp'))
    dlog("DAD SP\t\t", high_byte, low_byte)
    result = state.get_register_pair_value('h', 'l')
    result += state.get_register_value('sp')
    state.set_single_flag('cy', result > 0xffff)
    state.set_register_pair_value(result, 'h', 'l')
    return 1

def xchg():
    '''Exchange Registers DE and HL'''
    dlog("XCHG\t\thl <-> de")
    tmp = state.get_register_value('h')
    state.set_register_copy('h', 'd')
    state.set_register_value('d', tmp)
    tmp = state.get_register_value('l')
    state.set_register_copy('l', 'e')
    state.set_register_value('e', tmp)
    return 1

def xthl():
    '''Exchange stack values with HL'''
    dlog("XTHL\t\thl <-> stack")
    tmp_high = state.get_register_value('h')
    tmp_low = state.get_register_value('l')
    pop('h', 'l')
    push(tmp_high, tmp_low)
    return 1

def lda():
    '''Load A with data from the memory address specified by the
        next two immediate bytes'''
    address = state.get_memory_word_immediate()
    data = state.get_memory_by_address(address)
    dlog("LDA\t\t", address, ":", data)
    state.set_register_value('a', data)
    return 3

def sta():
    '''Store A at the memory address specified by the next two
        immediate bytes'''
    address = state.get_memory_word_immediate()
    dlog("STA\t\t", address)
    state.store_register_at_address('a', address)
    return 3

def lhld():
    '''Load HL Direct - loads byte from memory address specified by
        two immediate bytes into L, and the byte from the following
        address into H'''
    address = state.get_memory_word_immediate()
    dlog("LHLD\t\t", address)
    state.set_register_value('l', \
                    state.get_memory_by_address(address))
    address += 1
    state.set_register_value('h', \
                    state.get_memory_by_address(address))
    return 3

def shld():
    '''Store HL Direct - stores L at memory address specified by two
        immediate bytes, and H into the byte following that address'''
    address = state.get_memory_word_immediate()
    dlog("SHLD\t\t", address)
    state.store_register_at_address('l', address)
    address += 1
    state.store_register_at_address('h', address)
    return 3

def _pretend_read():
    '''IN placeholder for internal use - just writes a log saying
        an IN opcode was reached. actual device read should be caught
        and handled through machine-specific code externally, using the
        apply_read_data function'''
    device_id = state.get_memory_by_offset(1)
    dlog("IN\t\t", device_id)
    return 2

def apply_read_data(data):
    '''For use in IN operations, called externally to pass read data 
        into the accumulator (register A)'''
    state.set_register_value('a', data)

def _pretend_write():
    '''OUT placeholder for internal use - just writes a log saying
        an OUT opcode was reached. actual device write should be
        caught and handled through machine-specific code externally,
        using the get_write_data function'''
    device_id = state.get_memory_by_offset(1)
    dlog("OUT\t\t", device_id)
    return 2

def get_write_data():
    '''For use in OUT operations, returns data to be written out to
        the external device'''
    return state.get_register_value('a')

def interrupt(opcode):
    '''Performs the given operation, typically a RST but can
        theoretically be anything. Called externally, never from
        within the emulator'''
    dlog("INTERRUPT\t", opcode, state.get_flag("interrupt_enabled"))
    if state.get_flag("interrupt_enabled"):
        set_interrupt_enabled(False)
        operation = instruction_dict_8080.get(opcode)
        operation()

def daa(): # TODO add AC flag to relevant other ops
    '''Decimal Adjust Accumulator : Fancy decimal math that
        is not yet implemented, except for basic conversion'''
    dlog("DAA\t\t")
    result = state.get_register_value('a')
    # calculate bottom bits first
    bottom_bits = result & 0x0f
    if bottom_bits > 0x09 or state.get_flag('ac'):
        bottom_bits += 0x06
        result      += 0x06
    # If bottom_bits carries out, set AC flag, else reset AC flag
    state.set_single_flag('ac', bottom_bits & 0x10)
    # next calculate top bits, based on effects of bottom bits
    top_bits = result & 0xf0
    if top_bits > 0x90 or state.get_flag('cy'):
        top_bits += 0x60
        result   += 0x60
    state.set_register_value('a', result)
    # If top_bits carries out, set CY flag, else ignore (not reset)
    if top_bits & 0x100:
        state.set_single_flag('cy', True)
    state.set_flags(result, ['z','s','p'])
    return 1

'''Map byte instructions to functions'''
instruction_dict_8080 = { # size    flags
    0x00 : nop,                             #"NOP",
    0x01 : partial(lxi, 'b', 'c'),          #"LXI B,D16", #   
    0x02 : partial(save, 'a', 'b', 'c'),    #"STAX B",
    0x03 : partial(addx, 'b', 'c', 1),      #"INX B",
    0x04 : partial(inr, 'b'),               #"INR B",     #Z, S, P, AC
    0x05 : partial(dcr, 'b'),               #"DCR B",     #Z, S, P, AC
    0x06 : partial(mvi, 'b'),               #"MVI B,D8",  #
    0x07 : rlc,                             #"RLC",       #CY
    0x08 : nop,                             #"---",
    0x09 : partial(dad, 'b', 'c'),          #"DAD B",     #CY
    0x0a : partial(load_m, 'a', 'b', 'c'),  #"LDAX B",
    0x0b : partial(addx, 'b', 'c', -1),     #"DCX B",
    0x0c : partial(inr, 'c'),               #"INR C",     #Z, S, P, AC
    0x0d : partial(dcr, 'c'),               #"DCR C",     #Z, S, P, AC
    0x0e : partial(mvi, 'c'),               #"MVI C,D8",  #
    0x0f : rrc,                             #"RRC",       #CY
    0x10 : nop,                             #"---",
    0x11 : partial(lxi, 'd', 'e'),          #"LXI D,D16", #
    0x12 : partial(save, 'a', 'd', 'e'),    #"STAX D",
    0x13 : partial(addx, 'd', 'e', 1),      #"INX D",
    0x14 : partial(inr, 'd'),               #"INR D",     #Z, S, P, AC
    0x15 : partial(dcr, 'd'),               #"DCR D",     #Z, S, P, AC
    0x16 : partial(mvi, 'd'),               #"MVI D,D8",  #
    0x17 : ral,                             #"RAL",       #CY
    0x18 : nop,                             #"---",
    0x19 : partial(dad, 'd', 'e'),          #"DAD D",     #CY
    0x1a : partial(load_m, 'a', 'd', 'e'),  #"LDAX D",
    0x1b : partial(addx, 'd', 'e', -1),     #"DCX D",
    0x1c : partial(inr, 'e'),               #"INR E",     #Z, S, P, AC
    0x1d : partial(dcr, 'e'),               #"DCR E",     #Z, S, P, AC
    0x1e : partial(mvi, 'e'),               #"MVI E,D8",  #
    0x1f : rar,                             #"RAR",       #CY
    0x20 : "RIM",       #                       'special'
    0x21 : partial(lxi, 'h', 'l'),          #"LXI H,D16", #
    0x22 : shld,                            #"SHLD adr",  #
    0x23 : partial(addx, 'h', 'l', 1),      #"INX H",     #
    0x24 : partial(inr, 'h'),               #"INR H",     #Z, S, P, AC
    0x25 : partial(dcr, 'h'),               #"DCR H",     #Z, S, P, AC
    0x26 : partial(mvi, 'h'),               #"MVI H,D8",  #
    0x27 : daa,                             #"DAA",       #ZSPCYAC
    0x28 : nop,                             #"---",
    0x29 : partial(dad, 'h', 'l'),          #"DAD H",     #CY
    0x2a : lhld,                            #"LHLD adr",  #          
    0x2b : partial(addx, 'h', 'l', -1),     #"DCX H",
    0x2c : partial(inr, 'l'),               #"INR L",     #Z, S, P, AC
    0x2d : partial(dcr, 'l'),               #"DCR L",     #Z, S, P, AC
    0x2e : partial(mvi, 'l'),               #"MVI L,D8",  #
    0x2f : cma,                             #"CMA",
    0x30 : "SIM",
    0x31 : lxi_sp,                          #"LXI SP,D16",#
    0x32 : sta,                             #"STA adr",   #
    0x33 : partial(addx_sp, 1),             #"INX SP",    
    0x34 : partial(inr, 'm'),               #"INR M",     #Z, S, P, AC
    0x35 : dcr_m,                           #"DCR M",     #Z, S, P, AC
    0x36 : mvi_m,                           #"MVI M,D8",  #
    0x37 : stc,                             #"STC",       #CY
    0x38 : nop,                             #"---",
    0x39 : dad_sp,                          #"DAD SP",    #CY
    0x3a : lda,                             #"LDA adr",   #
    0x3b : partial(addx_sp, -1),            #"DCX SP",
    0x3c : partial(inr, 'a'),               #"INR A",     #Z, S, P, AC
    0x3d : partial(dcr, 'a'),               #"DCR A",     #Z, S, P, AC
    0x3e : partial(mvi, 'a'),               #"MVI A,D8",  #
    0x3f : cmc,                             #"CMC",       #CY
    
    0x40 : partial(mov, 'b', 'b'),          #"MOV B,B",
    0x41 : partial(mov, 'b', 'c'),          #"MOV B,C",
    0x42 : partial(mov, 'b', 'd'),          #"MOV B,D",
    0x43 : partial(mov, 'b', 'e'),          #"MOV B,E",
    0x44 : partial(mov, 'b', 'h'),          #"MOV B,H",
    0x45 : partial(mov, 'b', 'l'),          #"MOV B,L",
    0x46 : partial(mov_m, 'b'),             #"MOV B,M",
    0x47 : partial(mov, 'b', 'a'),          #"MOV B,A",
    
    0x48 : partial(mov, 'c', 'b'),          #"MOV C,B",
    0x49 : partial(mov, 'c', 'c'),          #"MOV C,C",
    0x4a : partial(mov, 'c', 'd'),          #"MOV C,D",
    0x4b : partial(mov, 'c', 'e'),          #"MOV C,E",
    0x4c : partial(mov, 'c', 'h'),          #"MOV C,H",
    0x4d : partial(mov, 'c', 'l'),          #"MOV C,L",
    0x4e : partial(mov_m, 'c'),             #"MOV C,M",
    0x4f : partial(mov, 'c', 'a'),          #"MOV C,A",
    
    0x50 : partial(mov, 'd', 'b'),          #"MOV D,B",
    0x51 : partial(mov, 'd', 'c'),          #"MOV D,C",
    0x52 : partial(mov, 'd', 'd'),          #"MOV D,D",
    0x53 : partial(mov, 'd', 'e'),          #"MOV D,E",
    0x54 : partial(mov, 'd', 'h'),          #"MOV D,H",
    0x55 : partial(mov, 'd', 'l'),          #"MOV D,L",
    0x56 : partial(mov_m, 'd'),             #"MOV D,M",
    0x57 : partial(mov, 'd', 'a'),          #"MOV D,A",
    
    0x58 : partial(mov, 'e', 'b'),          #"MOV E,B",
    0x59 : partial(mov, 'e', 'c'),          #"MOV E,C",
    0x5a : partial(mov, 'e', 'd'),          #"MOV E,D",
    0x5b : partial(mov, 'e', 'e'),          #"MOV E,E",
    0x5c : partial(mov, 'e', 'h'),          #"MOV E,H",
    0x5d : partial(mov, 'e', 'l'),          #"MOV E,L",
    0x5e : partial(mov_m, 'e'),             #"MOV E,M",
    0x5f : partial(mov, 'e', 'a'),          #"MOV E,A",
    
    0x60 : partial(mov, 'h', 'b'),          #"MOV H,B",
    0x61 : partial(mov, 'h', 'c'),          #"MOV H,C",
    0x62 : partial(mov, 'h', 'd'),          #"MOV H,D",
    0x63 : partial(mov, 'h', 'e'),          #"MOV H,E",
    0x64 : partial(mov, 'h', 'h'),          #"MOV H,H",
    0x65 : partial(mov, 'h', 'l'),          #"MOV H,L",
    0x66 : partial(mov_m, 'h'),             #"MOV H,M",
    0x67 : partial(mov, 'h', 'a'),          #"MOV H,A",
    
    0x68 : partial(mov, 'l', 'b'),          #"MOV L,B",
    0x69 : partial(mov, 'l', 'c'),          #"MOV L,C",
    0x6a : partial(mov, 'l', 'd'),          #"MOV L,D",
    0x6b : partial(mov, 'l', 'e'),          #"MOV L,E",
    0x6c : partial(mov, 'l', 'h'),          #"MOV L,H",
    0x6d : partial(mov, 'l', 'l'),          #"MOV L,L",
    0x6e : partial(mov_m, 'l'),             #"MOV L,M",
    0x6f : partial(mov, 'l', 'a'),          #"MOV L,A",
    
    0x70 : partial(mov_to_m, 'b'),          #"MOV M,B",
    0x71 : partial(mov_to_m, 'c'),          #"MOV M,C",
    0x72 : partial(mov_to_m, 'd'),          #"MOV M,D",
    0x73 : partial(mov_to_m, 'e'),          #"MOV M,E",
    0x74 : partial(mov_to_m, 'h'),          #"MOV M,H",
    0x75 : partial(mov_to_m, 'l'),          #"MOV M,L",
    0x76 : "HLT", #incr pc to next instr, CPU STOPs until interrupt
    0x77 : partial(mov_to_m, 'a'),          #"MOV M,A",
    
    0x78 : partial(mov, 'a', 'b'),          #"MOV A,B",
    0x79 : partial(mov, 'a', 'c'),          #"MOV A,C",
    0x7a : partial(mov, 'a', 'd'),          #"MOV A,D",
    0x7b : partial(mov, 'a', 'e'),          #"MOV A,E",
    0x7c : partial(mov, 'a', 'h'),          #"MOV A,H",
    0x7d : partial(mov, 'a', 'l'),          #"MOV A,L",
    0x7e : partial(mov_m, 'a'),             #"MOV A,M",
    0x7f : partial(mov, 'a', 'a'),          #"MOV A,A",
    
    0x80 : partial(add, 'a', 'b'),          #"ADD B",    #Z,S,P,CY,AC
    0x81 : partial(add, 'a', 'c'),          #"ADD C",
    0x82 : partial(add, 'a', 'd'),          #"ADD D",
    0x83 : partial(add, 'a', 'e'),          #"ADD E",
    0x84 : partial(add, 'a', 'h'),          #"ADD H",
    0x85 : partial(add, 'a', 'l'),          #"ADD L",
    0x86 : partial(add_m, 'a'),             #"ADD M",
    0x87 : partial(add, 'a', 'a'),          #"ADD A",
    
    0x88 : partial(adc, 'a', 'b'),          #"ADC B",
    0x89 : partial(adc, 'a', 'c'),          #"ADC C",
    0x8a : partial(adc, 'a', 'd'),          #"ADC D",
    0x8b : partial(adc, 'a', 'e'),          #"ADC E",
    0x8c : partial(adc, 'a', 'h'),          #"ADC H",
    0x8d : partial(adc, 'a', 'l'),          #"ADC L",
    0x8e : partial(adc_m, 'a'),             #"ADC M",
    0x8f : partial(adc, 'a', 'a'),          #"ADC A",
    
    0x90 : partial(sub, 'a', 'b'),          #"SUB B",
    0x91 : partial(sub, 'a', 'c'),          #"SUB C",
    0x92 : partial(sub, 'a', 'd'),          #"SUB D",
    0x93 : partial(sub, 'a', 'e'),          #"SUB E",
    0x94 : partial(sub, 'a', 'h'),          #"SUB H",
    0x95 : partial(sub, 'a', 'l'),          #"SUB L",
    0x96 : partial(sub_m, 'a'),             #"SUB M",
    0x97 : partial(sub, 'a', 'a'),          #"SUB A",
    
    0x98 : partial(sbb, 'a', 'b'),          #"SBB B",
    0x99 : partial(sbb, 'a', 'c'),          #"SBB C",
    0x9a : partial(sbb, 'a', 'd'),          #"SBB D",
    0x9b : partial(sbb, 'a', 'e'),          #"SBB E",
    0x9c : partial(sbb, 'a', 'h'),          #"SBB H",
    0x9d : partial(sbb, 'a', 'l'),          #"SBB L",
    0x9e : partial(sbb_m, 'a'),             #"SBB M",
    0x9f : partial(sbb, 'a', 'a'),          #"SBB A",
    
    0xa0 : partial(ana, 'b'),               #"ANA B",
    0xa1 : partial(ana, 'c'),               #"ANA C",
    0xa2 : partial(ana, 'd'),               #"ANA D",
    0xa3 : partial(ana, 'e'),               #"ANA E",
    0xa4 : partial(ana, 'h'),               #"ANA H",
    0xa5 : partial(ana, 'l'),               #"ANA L",
    0xa6 : partial(ana, 'm'),               #"ANA M",
    0xa7 : partial(ana, 'a'),               #"ANA A",
    
    0xa8 : partial(xra, 'b'),               #"XRA B",
    0xa9 : partial(xra, 'c'),               #"XRA C",
    0xaa : partial(xra, 'd'),               #"XRA D",
    0xab : partial(xra, 'e'),               #"XRA E",
    0xac : partial(xra, 'h'),               #"XRA H",
    0xad : partial(xra, 'l'),               #"XRA L",
    0xae : partial(xra, 'm'),               #"XRA M",
    0xaf : partial(xra, 'a'),               #"XRA A",
    
    0xb0 : partial(ora, 'b'),               #"ORA B",
    0xb1 : partial(ora, 'c'),               #"ORA C",
    0xb2 : partial(ora, 'd'),               #"ORA D",
    0xb3 : partial(ora, 'e'),               #"ORA E",
    0xb4 : partial(ora, 'h'),               #"ORA H",
    0xb5 : partial(ora, 'l'),               #"ORA L",
    0xb6 : partial(ora, 'm'),               #"ORA M",
    0xb7 : partial(ora, 'a'),               #"ORA A",
    
    0xb8 : partial(cmp, 'a', 'b'),          #"CMP B",
    0xb9 : partial(cmp, 'a', 'c'),          #"CMP C",
    0xba : partial(cmp, 'a', 'd'),          #"CMP D",
    0xbb : partial(cmp, 'a', 'e'),          #"CMP E",
    0xbc : partial(cmp, 'a', 'h'),          #"CMP H",
    0xbd : partial(cmp, 'a', 'l'),          #"CMP L",
    0xbe : partial(cmp_m, 'a'),             #"CMP M",
    0xbf : partial(cmp, 'a', 'a'),          #"CMP A",     #Z,S,P,CY,AC
    
    0xc0 : partial(ret_not_flag, 'z'),      #"RNZ",
    0xc1 : partial(pop, 'b', 'c'),          #"POP B",
    0xc2 : partial(jmp_not_flag, 'z'),      #"JNZ adr",   #   3
    0xc3 : jmp,                             #"JMP adr",   #   3
    0xc4 : partial(call_not_flag, 'z'),     #"CNZ adr",   #   3
    0xc5 : partial(push, 'b', 'c'),         #"PUSH B",
    0xc6 : partial(adi, 'a'),               #"ADI D8",    #Z,S,P,CY,AC
    0xc7 : partial(rst, 0x0),               #"RST 0",
    0xc8 : partial(ret_flag, 'z'),          #"RZ",
    0xc9 : ret,                             #"RET",
    0xca : partial(jmp_flag, 'z'),          #"JZ adr",    #   3
    0xcb : nop,                             #"---",
    0xcc : partial(call_flag, 'z'),         #"CZ adr",    #   3
    0xcd : call,                            #"CALL adr",  #   3
    0xce : partial(aci, 'a'),               #"ACI D8",    #Z,S,P,CY,AC
    0xcf : partial(rst, 0x8),               #"RST 1",
    0xd0 : partial(ret_not_flag, 'cy'),     #"RNC",
    0xd1 : partial(pop, 'd', 'e'),          #"POP D",
    0xd2 : partial(jmp_not_flag, 'cy'),     #"JNC adr",   #   3
    0xd3 : _pretend_write,                  #"OUT D8",    #   2
    0xd4 : partial(call_not_flag, 'cy'),    #"CNC adr",   #   3
    0xd5 : partial(push, 'd', 'e'),         #"PUSH D",
    0xd6 : partial(sui, 'a'),               #"SUI D8",    #Z,S,P,CY,AC
    0xd7 : partial(rst, 0x10),              #"RST 2",
    0xd8 : partial(ret_flag, 'cy'),         #"RC",
    0xd9 : nop,                             #"---",
    0xda : partial(jmp_flag, 'cy'),         #"JC adr",    #   3
    0xdb : _pretend_read,                   #"IN D8",     #   2
    0xdc : partial(call_flag, 'cy'),        #"CC adr",    #   3
    0xdd : nop,                             #"---",
    0xde : partial(sbi, 'a'),               #"SBI D8",    #Z,S,P,CY,AC
    0xdf : partial(rst, 0x18),              #"RST 3",
    0xe0 : partial(ret_not_flag, 'p'),      #"RPO",
    0xe1 : partial(pop, 'h', 'l'),          #"POP H",
    0xe2 : partial(jmp_not_flag, 'p'),      #"JPO adr",   #   3
    0xe3 : xthl,                            #"XTHL",
    0xe4 : partial(call_not_flag, 'p'),     #"CPO adr",   #   3
    0xe5 : partial(push, 'h', 'l'),         #"PUSH H",
    0xe6 : ani,                             #"ANI D8",    #Z,S,P,CY,AC
    0xe7 : partial(rst, 0x20),              #"RST 4",
    0xe8 : partial(ret_flag, 'p'),          #"RPE",
    0xe9 : partial(load_r, 'pc', 'h', 'l'), #"PCHL",
    0xea : partial(jmp_flag, 'p'),          #"JPE adr",   #   3
    0xeb : xchg,                            #"XCHG",
    0xec : partial(call_flag, 'p'),         #"CPE adr",   #   3
    0xed : nop,                             #"---",
    0xee : xri,                             #"XRI D8",    #Z,S,P,CY,AC
    0xef : partial(rst, 0x28),              #"RST 5:",
    0xf0 : partial(ret_not_flag, 's'),      #"RP",
    0xf1 : pop_psw,                         #"POP PSW",   
    0xf2 : partial(jmp_not_flag, 's'),      #"JP adr",    #   3
    0xf3 : partial(set_interrupt_enabled, False),#"DI",
    0xf4 : partial(call_not_flag, 's'),     #"CP adr",    #   3
    0xf5 : push_psw,                        #"PUSH PSW",
    0xf6 : ori,                             #"ORI D8",    #Z,S,P,CY,AC
    0xf7 : partial(rst, 0x30),              #"RST 6",
    0xf8 : partial(ret_flag, 's'),          #"RM",
    0xf9 : partial(load_r, 'sp', 'h', 'l'), #"SPHL",
    0xfa : partial(jmp_flag, 's'),          #"JM adr",    #   3
    0xfb : partial(set_interrupt_enabled, True),#"EI",
    0xfc : partial(call_flag, 's'),         #"CM adr",    #   3
    0xfd : nop,                             #"---",
    0xfe : partial(cmi, 'a'),               #"CPI D8",    #   2
    0xff : partial(rst, 0x38),              #"RST 7"
}

