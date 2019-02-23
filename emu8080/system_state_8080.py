''' Python 8080, an 8080 emulator designed for arcade games.
    Copyright (C) 2019  Jacob Gray

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from data.precalculated import packed_monochrome_to_24_bit
from data.precalculated import parity_dict
import time

'''Store all CPU state information'''
_memory = [0] * (2**16) # 16 address bits of memory
#memory_mirror = [0] * (2**16) # not sure what this is for yet
_flags = {
    'z' : False, # Zero
    's' : False, # Sign
    'p' : False, # Parity
    'cy': False, # Carry
    'ac': False,  # Auxilliary carry (unimplemented)
    'interrupt_enabled' : False
    # pad : 3 ????
}

_registers = {
    'a' : 0,
    'b' : 0,
    'c' : 0,
    'd' : 0,
    'e' : 0,
    'h' : 0,
    'l' : 0,
    'sp': 0,
    'pc': 0
}

def summarize(do_memdump = False):
    '''Return all state info on separate lines, 
            optionally dumping memory to disk'''
            
    output = "******** Registers ********\n"
    output += "a  : " + "0x{:02x}".format(_registers['a']) + "\n"
    output += "b  : " + "0x{:02x}".format(_registers['b']) + "\n"
    output += "c  : " + "0x{:02x}".format(_registers['c']) + "\n"
    output += "d  : " + "0x{:02x}".format(_registers['d']) + "\n"
    output += "e  : " + "0x{:02x}".format(_registers['e']) + "\n"
    output += "h  : " + "0x{:02x}".format(_registers['h']) + "\n"
    output += "l  : " + "0x{:02x}".format(_registers['l']) + "\n"
    output += "sp : " + "0x{:04x}".format(_registers['sp']) + "\n"
    output += "pc : " + "0x{:04x}".format(_registers['pc']) + "\n"
    output += "\n"
    output += "********** Flags **********\n"
    output += "z  : " + str(_flags['z']) + "\n"
    output += "s  : " + str(_flags['s']) + "\n"
    output += "p  : " + str(_flags['p']) + "\n"
    output += "cy : " + str(_flags['cy']) + "\n"
    output += "ac : " + str(_flags['ac']) + "\n"
    
    if do_memdump:
        with open("./memdump", "w") as o:
            for element in _memory:
                o.write("%02x\n" % element)
            output += "Memory dump saved to ./memdump\n\n"
    return output


def get_int_TC(value, max_size = 0xff):
    '''Returns value converted to a signed integer in the specified
        range in two's complement, converting negative values and
        dropping any information greater than max_size. If not 
        provided, 8-bit int is assumed (max_size of 0xff)'''
    if value < 0:
        value = -(abs(value) & max_size)
    return value % (max_size+1)

def load_program(binary_data, address):
    '''Load binary blob into memory block starting at specified
        address'''
    for i in range(0, len(binary_data)):
        _memory[address] = get_int_TC(binary_data[i])
        address += 1

def get_register_value(register_name):
    '''Returns the numeric value stored in a register'''
    return _registers[register_name]

def set_register_copy(register_to, register_from):
    '''Sets the value of to to the value of from'''
    _registers[register_to] = _registers[register_from]

def set_register_value(register_name, value):
    '''Stores value in the named register, provided as a 
        discrete value or register name'''
    if type(value) is str:
        raise ValueError("passed register where value was expected")
    if register_name == 'pc' or register_name == 'sp':
        _registers[register_name] = get_int_TC(value, 0xffff)
    else:
        _registers[register_name]= get_int_TC(value)

def get_register_pair_value(register_high, register_low):
    '''Returns the contents of the named registers as a 16-bit value'''
    return _registers[register_high] << 8 | _registers[register_low]

def set_register_pair_value(value, register_high, register_low):
    '''Stores a 16-bit value into a register pair'''
    _registers[register_high] = get_int_TC((value & 0xff00) >> 8)
    _registers[register_low] = get_int_TC(value & 0x00ff)

def get_current_opcode():
    '''Returns the byte in memory specified by PC'''
    return _memory[_registers['pc']]

def get_stack_top():
    '''Returns the byte at the address specified by SP'''
    return _memory[_registers['sp']]

def get_memory_by_registers(register_high, register_low):
    '''Returns a byte from memory specified by the provided
        8-bit register pair'''
    return _memory[(_registers[register_high] << 8) \
                        | _registers[register_low]]

def get_memory_by_address(address):
    '''Returns a byte from memory at the specified 16-bit 
        discrete address'''
    return _memory[address]

def get_memory_word_immediate():
    '''Returns a 16-bit value from memory immediately following
        the current PC address'''
    current_pc = _registers['pc']
    return (_memory[current_pc+2] << 8) | _memory[current_pc+1]

def set_memory_by_registers(value, register_high, register_low):
    '''Stores a byte in memory at the address specified by the 
        provided 8-bit register pair'''
    _memory[(_registers[register_high] << 8) \
                    | _registers[register_low]] = get_int_TC(value)

def set_memory_by_address(value, address):
    '''Stores a byte in memory at the address specified'''
    _memory[address] = get_int_TC(value)

def store_register_at_address(register, address):
    '''Stores the value of register at the specified address'''
    _memory[address] = _registers[register]

def set_stack_top(value):
    '''Stores a byte at the top of the stack'''
    _memory[_registers['sp']] = get_int_TC(value)

def set_memory_byte(value, high_address, low_address = None):
    '''Stores a byte at the specified memory address, all values
        may be provided via register or discrete value. If low_address
        is not set, attempt to read high_address as a 16-bit register
        (i.e. SP or PC, NOT as a discrete value!)'''
    true_address = 0
    if type(high_address) is str: # then it's a register
        if low_address == None:
            true_address = _registers[high_address]
        else:
            true_address = _registers[high_address] << 8 \
                            | _registers[low_address]
    else:
        true_address = (high_address << 8) | low_address
    if type(value) is str: # then it's a register
        value = _registers[value]
    _memory[true_address] = get_int_TC(value)

def get_memory_by_offset(offset):
    '''Returns a memory byte by offset from current pc'''
    address = _registers['pc'] + offset
    return _memory[address]

def set_flags(value, target_flags):
    '''Updates _flags based on provided discrete value'''
    if type(value) is str:
        '''Could error here, we don't want to check against the stored
            register value because the 8-bit value loses data we need
            to set some of these flags'''
        #value = _registers[value]
    if 'z' in target_flags:
        _flags['z'] = (value & 0xff) == 0
    if 's' in target_flags:
        _flags['s'] = (value & 128) != 0 # check if sign bit is set
    if 'p' in target_flags:
        _flags['p'] = has_even_parity(value)
    if 'cy' in target_flags:
        _flags['cy'] = value > 0xff
    #_flags['ac'] = ?? TODO later, it's not part of Space Invaders
    return

def set_single_flag(target_flag, value):
    '''Sets the target flag to the boolean of the provided value'''
    _flags[target_flag] = (value == True) or (value != 0)

def get_flag(name):
    '''Returns the value of the named flag'''
    return _flags[name]

def has_even_parity(value):
    '''Returns 1/True if even parity, 0/False if odd parity'''
    value = get_int_TC(value)
    # 8080 parity is opposite of the standard definition, hence 'not'
    return not parity_dict.get(value)

def increment_register(name):
    _registers[name] += 1

def decrement_register(name):
    _registers[name] -= 1

def increase_pc(amount):
    '''Increases the program counter (PC) by amount, or 1 if not set'''
    _registers['pc'] += amount

def get_bytes_from_int(value, pad_to = 0):
    '''Returns a little-endian bytearray of an arbitrarily large 
        positive input value. If pad_to is set, array will be padded
        with empty bytes up to that minimum size'''
    if type(value) is not int or value < 0: 
    # Current implementation would cause unpredictable behavior
        raise ValueError("Unexpected value: " + str(value))
        return None
    if value == 0 and pad_to == 0:
        return [0]
    output = []
    while value > 0 or pad_to > 0:
        output.append(value & 0xff)
        value >>= 8
        pad_to -= 1
    return output

def inflate_monochrome_byte_to_24b(value):
    '''Convert a single byte of 1-bit color values to an array of
        24-bit color values, one byte per index'''
    if type(value) is not int or value < 0:
    # Current implementation would cause unpredictable behavior if so
        raise ValueError("Unexpected value: " + str(value))
        return None
    output = []
    for i in range(0, 8):
        if value & 1:
            output += [0xff, 0xff, 0xff]
        else:
            output += [0x00, 0x00, 0x00]
        value >>= 1
    output.reverse()
    return output

def get_bitmap_from_memory(address_start, address_end, width, height):
    '''Returns a section of memory as a 24-bit bitmap image
        that is understandable on modern machines'''
    '''Original memory provides a 1-bit white/black bitmap,
        this needs to be upconverted'''
    bit_depth = 24
    bytes_per_pixel = bit_depth // 8
    data_length = address_end - address_start
    padding = 4 - ((data_length * bit_depth) % 4) # 4-byte alignment
    total_length = 0x36 + (data_length * bit_depth) + padding
    # start header info
    bmp_output = [0x42, 0x4d]     # BM type image
    bmp_output += get_bytes_from_int(total_length, 4) # total size
    bmp_output += [   0, 0, 0, 0] # Unused bytes
    bmp_output += [0x36, 0, 0, 0] # offset of bmp data
    bmp_output += [0x28, 0, 0, 0] # Remaining bytes in header
    bmp_output += get_bytes_from_int(width, 4)
    bmp_output += get_bytes_from_int(height, 4)
    bmp_output += [0x01, 0]       # number of color planes
    bmp_output += get_bytes_from_int(bit_depth, 2) # bits per pixel
    bmp_output += [0, 0, 0, 0]    # compression information (none)
                                  # length of pixel data in bytes
    bmp_output += get_bytes_from_int((data_length * bytes_per_pixel) 
                                                    + padding, 4)
    bmp_output += [1, 0, 0, 0]    # print info, pixels per meter width
    bmp_output += [1, 0, 0, 0]    # print info, pixels per meter height
    bmp_output += [0, 0, 0, 0]    # colors in palette (none)
    bmp_output += [0, 0, 0, 0]    # important colors (all)
    # end header info, start pixel data
    for byte in _memory[address_start:address_end+1]:
        bmp_output += packed_monochrome_to_24_bit.get(byte)
    # pad to 4-byte alignment
    for i in range(0, padding):
        bmp_output += [0xfe]
    return bytes(bmp_output)

def get_memory_slice(address_start, address_end):
    '''Returns a section of memory as list'''
    return _memory[address_start:address_end+1]

def get_stringbuffer_from_memory(address_start, address_end):
    '''Returns a section of memory as a string compatible with
        pygame's 24-bit RGB Surface string buffer'''
    output = []
    for byte in _memory[address_start:address_end+1]:
        '''Using this precalculated dict rather than calculating the
            bytes on the fly dropped process time from 0.03s/frame to
            0.002s/frame! Neat.'''
        output += packed_monochrome_to_24_bit.get(byte)
    return bytes(output)
