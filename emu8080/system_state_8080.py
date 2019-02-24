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

from data.precalculated import packed_monochrome_to_24_bit
from data.precalculated import parity_dict
import time

def _get_int_TC(value, max_size = 0xff):
    '''Returns value converted to a signed integer in the specified
        range in two's complement, converting negative values and
        dropping any information greater than max_size. If not 
        provided, 8-bit int is assumed (max_size of 0xff)'''
    if value < 0:
        value = -(abs(value) & max_size)
    return value % (max_size+1)

def has_even_parity(value):
    '''Returns 1/True if even parity, 0/False if odd parity'''
    value = _get_int_TC(value)
    # 8080 parity is opposite the standard definition, hence 'not'
    return not parity_dict.get(value)

    def get_bytes_from_int(value, pad_to = 0):
        '''Returns a little-endian bytearray of an arbitrarily large 
            positive input value. If pad_to is set, array will be
            padded with empty bytes up to that minimum size'''
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
        # Current implementation would cause unpredictable behavior
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




class SystemState:
    '''Store all CPU state information'''
    _memory = [0] * (2**16) # 16 address bits of memory
    _flags = {
        'z' : False, # Zero
        's' : False, # Sign
        'p' : False, # Parity
        'cy': False, # Carry
        'ac': False,  # Auxilliary carry (unimplemented)
        'interrupt_enabled' : False
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

    def summarize(self, do_memdump = False):
        '''Return all state info on separate lines, 
                optionally dumping memory to disk'''
                
        output = "******** Registers ********\n"
        output +="a  : "+"0x{:02x}".format(self._registers['a']) + "\n"
        output +="b  : "+"0x{:02x}".format(self._registers['b']) + "\n"
        output +="c  : "+"0x{:02x}".format(self._registers['c']) + "\n"
        output +="d  : "+"0x{:02x}".format(self._registers['d']) + "\n"
        output +="e  : "+"0x{:02x}".format(self._registers['e']) + "\n"
        output +="h  : "+"0x{:02x}".format(self._registers['h']) + "\n"
        output +="l  : "+"0x{:02x}".format(self._registers['l']) + "\n"
        output +="sp : "+"0x{:04x}".format(self._registers['sp'])+ "\n"
        output +="pc : "+"0x{:04x}".format(self._registers['pc'])+ "\n"
        output +="\n"
        output +="********** Flags **********\n"
        output +="z  : " + str(self._flags['z']) + "\n"
        output +="s  : " + str(self._flags['s']) + "\n"
        output +="p  : " + str(self._flags['p']) + "\n"
        output +="cy : " + str(self._flags['cy']) + "\n"
        output +="ac : " + str(self._flags['ac']) + "\n"
        
        if do_memdump:
            with open("./memdump", "w") as o:
                for element in _memory:
                    o.write("%02x\n" % element)
                output += "Memory dump saved to ./memdump\n\n"
        return output

    def load_program(self, binary_data, address):
        '''Load binary blob into memory block starting at specified
            address'''
        for i in range(0, len(binary_data)):
            self._memory[address] = _get_int_TC(binary_data[i])
            address += 1

    def get_register_value(self, register_name):
        '''Returns the numeric value stored in a register'''
        return self._registers[register_name]

    def set_register_copy(self, register_to, register_from):
        '''Sets the value of to to the value of from'''
        self._registers[register_to] = self._registers[register_from]

    def set_register_value(self, register_name, value):
        '''Stores value in the named register, provided as a 
            discrete value or register name'''
        if type(value) is str:
            raise ValueError("Register given where value was expected")
        if register_name == 'pc' or register_name == 'sp':
            self._registers[register_name] = _get_int_TC(value, 0xffff)
        else:
            self._registers[register_name]= _get_int_TC(value)

    def get_register_pair_value(self, register_hi, register_lo):
        '''Returns the contents of the named registers as a
            16-bit value'''
        return self._registers[register_hi] << 8 \
                        | self._registers[register_lo]

    def set_register_pair_value(self, value, register_hi, register_lo):
        '''Stores a 16-bit value into a register pair'''
        self._registers[register_hi]=_get_int_TC((value & 0xff00) >> 8)
        self._registers[register_lo]=_get_int_TC(value & 0x00ff)

    def get_current_opcode(self):
        '''Returns the byte in memory specified by PC'''
        return self._memory[self._registers['pc']]

    def get_stack_top(self):
        '''Returns the byte at the address specified by SP'''
        return self._memory[self._registers['sp']]

    def get_memory_by_registers(self, register_hi, register_lo):
        '''Returns a byte from memory specified by the provided
            8-bit register pair'''
        return self._memory[(self._registers[register_hi] << 8) \
                            | self._registers[register_lo]]

    def get_memory_by_address(self, address):
        '''Returns a byte from memory at the specified 16-bit 
            discrete address'''
        return self._memory[address]

    def get_memory_word_immediate(self):
        '''Returns a 16-bit value from memory immediately following
            the current PC address'''
        current_pc = self._registers['pc']
        return (self._memory[current_pc+2] << 8) \
                    | self._memory[current_pc+1]

    def set_memory_by_registers(self, value, register_hi, register_lo):
        '''Stores a byte in memory at the address specified by the 
            provided 8-bit register pair'''
        self._memory[(self._registers[register_hi] << 8) \
                    | self._registers[register_lo]] \
                    = _get_int_TC(value)

    def set_memory_by_address(self, value, address):
        '''Stores a byte in memory at the address specified'''
        self._memory[address] = _get_int_TC(value)

    def store_register_at_address(self, register, address):
        '''Stores the value of register at the specified address'''
        self._memory[address] = self._registers[register]

    def set_stack_top(self, value):
        '''Stores a byte at the top of the stack'''
        self._memory[self._registers['sp']] = _get_int_TC(value)

    def get_memory_by_offset(self, offset):
        '''Returns a memory byte by offset from current pc'''
        address = self._registers['pc'] + offset
        return self._memory[address]

    def set_flags(self, value, target_flags):
        '''Updates _flags based on provided discrete value'''
        if 'z' in target_flags: # Zero
            self._flags['z'] = (value & 0xff) == 0
        if 's' in target_flags: # Sign
            self._flags['s'] = (value & 128) != 0 
        if 'p' in target_flags: # Parity
            self._flags['p'] = has_even_parity(value)
        if 'cy' in target_flags: # Carry
            self._flags['cy'] = value > 0xff
        #_flags['ac'] = ?? TODO later, it's not part of Space Invaders
        return

    def set_single_flag(self, target_flag, value):
        '''Sets the target flag to the boolean of the provided value'''
        self._flags[target_flag] = (value == True) or (value != 0)

    def get_flag(self, name):
        '''Returns the value of the named flag'''
        return self._flags[name]

    def increment_register(self, name):
        self._registers[name] += 1

    def decrement_register(self, name):
        self._registers[name] -= 1

    def increase_pc(self, amount):
        '''Increases the program counter (PC) by the given amount'''
        self._registers['pc'] += amount

    def get_bitmap_from_memory(self, address_start, address_end,
                                        width, height):
        '''Returns a section of memory as a 24-bit bitmap image
            that is understandable on modern machines'''
        '''Original memory provides a 1-bit white/black bitmap,
            this needs to be upconverted'''
        bit_depth = 24
        bytes_per_pixel = bit_depth // 8
        data_length = address_end - address_start
        padding = 4 - ((data_length * bit_depth) % 4) # 4b alignment
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
        bmp_output += get_bytes_from_int((data_length * \
                                     bytes_per_pixel)   \
                                     + padding, 4)
        bmp_output += [1, 0, 0, 0]    # print info, pix/meter width
        bmp_output += [1, 0, 0, 0]    # print info, pix/meter height
        bmp_output += [0, 0, 0, 0]    # colors in palette (none)
        bmp_output += [0, 0, 0, 0]    # important colors (all)
        # end header info, start pixel data
        for byte in self._memory[address_start:address_end+1]:
            bmp_output += packed_monochrome_to_24_bit.get(byte)
        # pad to 4-byte alignment
        for i in range(0, padding):
            bmp_output += [0xfe]
        return bytes(bmp_output)

    def get_memory_slice(self, address_start, address_end):
        '''Returns a section of memory as list'''
        return self._memory[address_start:address_end+1]

    def get_stringbuffer_from_memory(self, address_start, address_end):
        '''Returns a section of memory as a string compatible with
            pygame's 24-bit RGB Surface string buffer'''
        output = []
        for byte in self._memory[address_start:address_end+1]:
            '''Using this precalculated dict rather than calculating
                the bytes on the fly dropped process time from 
                0.03s/frame to 0.002s/frame! Neat.'''
            output += packed_monochrome_to_24_bit.get(byte)
        return bytes(output)
