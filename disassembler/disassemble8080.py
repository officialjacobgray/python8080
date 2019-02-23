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
from instruction_info_8080 import mnemonics
from instruction_info_8080 import special_sizes

testinput = [0x00, 0x00, 0x00, 0xc3, 0xd4, 0x18]
CHUNKSIZE_DEFAULT = 2**23 # ~8 MB max
INFILE_DEFAULT = "./cpudiag.bin"
OUTFILE_DEFAULT = "./cpudiag.dissassembled"

def LoadFile(filename=INFILE_DEFAULT, chunksize=CHUNKSIZE_DEFAULT):
    '''Loads [chunksize] bytes of the specified file into memory and returns the object'''
    data = None
    with open(filename, "rb") as infile:
        data = infile.read(chunksize)
    return data

def Dissassemble(blob, show_address = False):
    '''Takes a binary blob and converts it to a string of assembly mnemonics, one per line'''
    output = ""
    index = 0
    while index < len(blob):
        line = ""
        instr = blob[index]
        if show_address:
            line += str("%04x  " % index)
        descriptor = mnemonics[instr]
        line += PadString(descriptor)
        if instr in special_sizes:
            data = []
            for c in range(1,special_sizes[instr]):
                index += 1
                data.append(blob[index])
            data.reverse() # 8080 is little-endian, reverse address bytes for display
            for c in data:
                line += str("%02x " % c)
        line += "\n"
        output += line
        index += 1
    return output

def PadString(line, width = 12):
    for c in range(len(line), width+1):
        line += " "
    return line

def Main():
    infile = LoadFile()
    if infile is None:
        print("Couldn't load the file, or empty file")
        return 10;
    output = Dissassemble(infile, True)
    outfile = open(OUTFILE_DEFAULT, "w")
    outfile.write(output)
    outfile.close()
    print("Success!")
    return 0;

Main()
