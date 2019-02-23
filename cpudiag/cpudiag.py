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

import emulator_8080
import sys
import os

'''Verifies the correctness of emulator_8080 via the cpudiag.bin
    test program'''

# Diagnostic should be loaded at 0x0100 but file starts at 0x00
with open("cpudiag.bin", 'rb') as input_file:
    emulator_8080.load_program(input_file.read(), 0x0100)
# Insert first instruction to jump to beginning of diagnostic code
emulator_8080.state.set_memory_byte(0xc3, 0, 0) # JMP to:
emulator_8080.state.set_memory_byte(0x01, 0, 2) # 0x0100
# Code calls 0x0005 to print messages, needs to be able to return
emulator_8080.state.set_memory_byte(0xc9, 0, 6) # Return
# Stack pointer address didn't include correct initial offset
emulator_8080.state.set_memory_byte(0x07, 0x01, 0x70)
# Skip DAA tests
emulator_8080.state.set_memory_byte(0xc3, 0x05, 0x9c) # JMP to:
emulator_8080.state.set_memory_byte(0xc2, 0x05, 0x9d) # lo c2
emulator_8080.state.set_memory_byte(0x05, 0x05, 0x9e) # hi 05

instruction_count = 0

def get_membyte(address):
    return emulator_8080.state.get_memory_by_address(address)

# Begin test
while instruction_count < 620:
    print("{:<8}".format(instruction_count) 
       + "0x{:04x}".format(emulator_8080.state.get_register_value('pc'))
        + "\t", end = '')
    opcode = emulator_8080.emulate_operation()
    if opcode == 0xcd: # call
        if (5 == emulator_8080.state.get_register_value('pc')):
            # If we jump to address 5, print the relevant message
            address = emulator_8080.state.get_register_value('d') << 8
            address += emulator_8080.state.get_register_value('e')
            address += 3
            line = ">"
            while get_membyte(address) != ord("$"):
                line += chr(get_membyte(address))
                address += 1
            print(line)
            print(emulator_8080.state.summarize())
            input("enter to continue")
        elif (0 == emulator_8080.state.get_register_value('pc')):
            # If we jump to address 0, the test has ended
            print("> Exit called")
            sys.exit()
    instruction_count += 1
    if instruction_count % 10 == 0:# or instruction_count >= 600:
        print(emulator_8080.state.summarize())

