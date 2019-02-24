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
from instruction_info_8080 import mnemonics
from instruction_info_8080 import special_sizes
import sys

testinput = [0x00, 0x00, 0x00, 0xc3, 0xd4, 0x18]
CHUNKSIZE_DEFAULT = 2**23 # ~8 MB max

def load_file(filename, chunksize=CHUNKSIZE_DEFAULT):
    '''Loads [chunksize] bytes of the specified file into memory and returns the object'''
    data = None
    with open(filename, "rb") as infile:
        data = infile.read(chunksize)
    return data

def dissassemble(blob, show_address = False):
    '''Takes a binary blob and converts it to a string of assembly
        mnemonics, one per line. If show_address is true, the
        instruction address is printed at the beginning of each line'''
    output = ""
    index = 0
    while index < len(blob):
        line = ""
        instr = blob[index]
        if show_address:
            line += str("%04x  " % index)
        descriptor = mnemonics[instr]
        line += "{:<12}".format(descriptor)
        if instr in special_sizes:
            data = []
            for c in range(1,special_sizes[instr]):
                index += 1
                data.append(blob[index])
            data.reverse() 
            # 8080 is little-endian, reverse address bytes for display
            for c in data:
                line += str("%02x " % c)
        line += "\n"
        output += line
        index += 1
    return output

def main(filename):
    infile = load_file(filename)
    if infile is None:
        print("Couldn't load the file, or empty file")
        sys.exit()
    output = dissassemble(infile, True)
    outfile_name = filename + ".disassembled"
    outfile = open(outfile_name, "w")
    outfile.write(output)
    outfile.close()
    print("Success!")
    return 0;

main(sys.argv[1])
