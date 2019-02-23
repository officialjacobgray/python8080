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

'''map hex values to assembly mnemonic'''
mnemonics = { # size    flags
    0x00 : "NOP",
    0x01 : "LXI B,D16", #   3
    0x02 : "STAX B",
    0x03 : "INX B",
    0x04 : "INR B",     #           Z, S, P, AC
    0x05 : "DCR B",     #           Z, S, P, AC
    0x06 : "MVI B,D8",  #   2
    0x07 : "RLC",       #           CY
    0x08 : "---",
    0x09 : "DAD B",     #           CY
    0x0a : "LDAX B",
    0x0b : "DCX B",
    0x0c : "INR C",     #           Z, S, P, AC
    0x0d : "DCR C",     #           Z, S, P, AC
    0x0e : "MVI C,D8",  #   2
    0x0f : "RRC",       #           CY
    0x10 : "---",
    0x11 : "LXI D,D16", #   3
    0x12 : "STAX D",
    0x13 : "INX D",
    0x14 : "INR D",     #           Z, S, P, AC
    0x15 : "DCR D",     #           Z, S, P, AC
    0x16 : "MVI D,D8",  #   2
    0x17 : "RAL",       #           CY
    0x18 : "---",
    0x19 : "DAD D",     #           CY
    0x1a : "LDAX D",
    0x1b : "DCX D",
    0x1c : "INR E",     #           Z, S, P, AC
    0x1d : "DCR E",     #           Z, S, P, AC
    0x1e : "MVI E,D8",  #   2
    0x1f : "RAR",       #           CY
    0x20 : "RIM",       #                       'special'
    0x21 : "LXI H,D16", #   3
    0x22 : "SHLD adr",  #   3
    0x23 : "INX H",     #
    0x24 : "INR H",     #           Z, S, P, AC
    0x25 : "DCR H",     #           Z, S, P, AC
    0x26 : "MVI H,D8",  #   2
    0x27 : "DAA",       #                       'special'
    0x28 : "---",
    0x29 : "DAD H",     #           CY
    0x2a : "LHLD adr",  #   3
    0x2b : "DCX H",
    0x2c : "INR L",     #           Z, S, P, AC
    0x2d : "DCR L",     #           Z, S< P, AC
    0x2e : "MVI L,D8",  #   2
    0x2f : "CMA",
    0x30 : "SIM",
    0x31 : "LXI SP,D16",#   3
    0x32 : "STA adr",   #   3
    0x33 : "INX SP",    
    0x34 : "INR M",     #           Z, S, P, AC
    0x35 : "DCR M",     #           Z, S, P, AC
    0x36 : "MVI M,D8",  #   2
    0x37 : "STC",       #           CY
    0x38 : "---",
    0x39 : "DAD SP",    #           CY
    0x3a : "LDA adr",   #   3
    0x3b : "DCX SP",
    0x3c : "INR A",     #           Z, S, P, AC
    0x3d : "DCR A",     #           Z, S, P, AC
    0x3e : "MVI A,D8",  #   2
    0x3f : "CMC",       #           CY
    
    0x40 : "MOV B,B",
    0x41 : "MOV B,C",
    0x42 : "MOV B,D",
    0x43 : "MOV B,E",
    0x44 : "MOV B,H",
    0x45 : "MOV B,L",
    0x46 : "MOV B,M",
    0x47 : "MOV B,A",
    
    0x48 : "MOV C,B",
    0x49 : "MOV C,C",
    0x4a : "MOV C,D",
    0x4b : "MOV C,E",
    0x4c : "MOV C,H",
    0x4d : "MOV C,L",
    0x4e : "MOV C,M",
    0x4f : "MOV C,A",
    
    0x50 : "MOV D,B",
    0x51 : "MOV D,C",
    0x52 : "MOV D,D",
    0x53 : "MOV D,E",
    0x54 : "MOV D,H",
    0x55 : "MOV D,L",
    0x56 : "MOV D,M",
    0x57 : "MOV D,A",
    
    0x58 : "MOV E,B",
    0x59 : "MOV E,C",
    0x5a : "MOV E,D",
    0x5b : "MOV E,E",
    0x5c : "MOV E,H",
    0x5d : "MOV E,L",
    0x5e : "MOV E,M",
    0x5f : "MOV E,A",
    
    0x60 : "MOV H,B",
    0x61 : "MOV H,C",
    0x62 : "MOV H,D",
    0x63 : "MOV H,E",
    0x64 : "MOV H,H",
    0x65 : "MOV H,L",
    0x66 : "MOV H,M",
    0x67 : "MOV H,A",
    
    0x68 : "MOV L,B",
    0x69 : "MOV L,C",
    0x6a : "MOV L,D",
    0x6b : "MOV L,E",
    0x6c : "MOV L,H",
    0x6d : "MOV L,L",
    0x6e : "MOV L,M",
    0x6f : "MOV L,A",
    
    0x70 : "MOV M,B",
    0x71 : "MOV M,C",
    0x72 : "MOV M,D",
    0x73 : "MOV M,E",
    0x74 : "MOV M,H",
    0x75 : "MOV M,L",
    0x76 : "HLT",
    0x77 : "MOV M,A",
    
    0x78 : "MOV A,B",
    0x79 : "MOV A,C",
    0x7a : "MOV A,D",
    0x7b : "MOV A,E",
    0x7c : "MOV A,H",
    0x7d : "MOV A,L",
    0x7e : "MOV A,M",
    0x7f : "MOV A,A",
    
    0x80 : "ADD B",     #           Z, S, P, CY, AC
    0x81 : "ADD C",
    0x82 : "ADD D",
    0x83 : "ADD E",
    0x84 : "ADD H",
    0x85 : "ADD L",
    0x86 : "ADD M",
    0x87 : "ADD A",
    
    0x88 : "ADC B",
    0x89 : "ADC C",
    0x8a : "ADC D",
    0x8b : "ADC E",
    0x8c : "ADC H",
    0x8d : "ADC L",
    0x8e : "ADC M",
    0x8f : "ADC A",
    
    0x90 : "SUB B",
    0x91 : "SUB C",
    0x92 : "SUB D",
    0x93 : "SUB E",
    0x94 : "SUB H",
    0x95 : "SUB L",
    0x96 : "SUB M",
    0x97 : "SUB A",
    
    0x98 : "SBB B",
    0x99 : "SBB C",
    0x9a : "SBB D",
    0x9b : "SBB E",
    0x9c : "SBB H",
    0x9d : "SBB L",
    0x9e : "SBB M",
    0x9f : "SBB A",
    
    0xa0 : "ANA B",
    0xa1 : "ANA C",
    0xa2 : "ANA D",
    0xa3 : "ANA E",
    0xa4 : "ANA H",
    0xa5 : "ANA L",
    0xa6 : "ANA M",
    0xa7 : "ANA A",
    
    0xa8 : "XRA B",
    0xa9 : "XRA C",
    0xaa : "XRA D",
    0xab : "XRA E",
    0xac : "XRA H",
    0xad : "XRA L",
    0xae : "XRA M",
    0xaf : "XRA A",
    
    0xb0 : "ORA B",
    0xb1 : "ORA C",
    0xb2 : "ORA D",
    0xb3 : "ORA E",
    0xb4 : "ORA H",
    0xb5 : "ORA L",
    0xb6 : "ORA M",
    0xb7 : "ORA A",
    
    0xb8 : "CMP B",
    0xb9 : "CMP C",
    0xba : "CMP D",
    0xbb : "CMP E",
    0xbc : "CMP H",
    0xbd : "CMP L",
    0xbe : "CMP M",
    0xbf : "CMP A",     #           Z, S, P, CY, AC
    
    0xc0 : "RNZ",
    0xc1 : "POP B",
    0xc2 : "JNZ adr",   #   3
    0xc3 : "JMP adr",   #   3
    0xc4 : "CNZ adr",   #   3
    0xc5 : "PUSH B",
    0xc6 : "ADI D8",    #   2       Z, S, P, CY, AC
    0xc7 : "RST 0",
    0xc8 : "RZ",
    0xc9 : "RET",
    0xca : "JZ adr",    #   3
    0xcb : "---",
    0xcc : "CZ adr",    #   3
    0xcd : "CALL adr",  #   3
    0xce : "ACI D8",    #   2       Z, S, P, CY, AC
    0xcf : "RST 1",
    0xd0 : "RNC",
    0xd1 : "POP D",
    0xd2 : "JNC adr",   #   3
    0xd3 : "OUT D8",    #   2
    0xd4 : "CNC adr",   #   3
    0xd5 : "PUSH D",
    0xd6 : "SUI D8",    #   2       Z, S, P, CY, AC
    0xd7 : "RST 2",
    0xd8 : "RC",
    0xd9 : "---",
    0xda : "JC adr",    #   3
    0xdb : "IN D8",     #   2
    0xdc : "CC adr",    #   3
    0xdd : "---",
    0xde : "SBI D8",    #   2       Z, S, P, CY, AC
    0xdf : "RST 3",
    0xe0 : "RPO",
    0xe1 : "POP H",
    0xe2 : "JPO adr",   #   3
    0xe3 : "XTHL",
    0xe4 : "CPO adr",   #   3
    0xe5 : "PUSH H",
    0xe6 : "ANI D8",    #   2       Z, S, P, CY, AC
    0xe7 : "RST 4",
    0xe8 : "RPE",
    0xe9 : "PCHL",
    0xea : "JPE adr",   #   3
    0xeb : "XCHG",
    0xec : "CPE adr",   #   3
    0xed : "---",
    0xee : "XRI D8",    #   2       Z, S< P, CY, AC
    0xef : "RST 5:",
    0xf0 : "RP",
    0xf1 : "POP PSW",   
    0xf2 : "JP adr",    #   3
    0xf3 : "DI",
    0xf4 : "CP adr",    #   3
    0xf5 : "PUSH PSW",
    0xf6 : "ORI D8",    #   2       Z, S, P, CY, AC
    0xf7 : "RST 6",
    0xf8 : "RM",
    0xf9 : "SPHL",
    0xfa : "JM adr",    #   3
    0xfb : "EI",
    0xfc : "CM adr",    #   3
    0xfd : "---",
    0xfe : "CPI D8",    #   2
    0xff : "RST 7"
    }

'''most instructions are 1 byte, exceptions (instructions with
    immediate arguments) are in this dict'''
special_sizes = {
    0x01 : 3,
    0x06 : 2,
    0x0e : 2,
    0x11 : 3,
    0x16 : 2,
    0x1e : 2,
    0x21 : 3,
    0x22 : 3,
    0x26 : 2,
    0x2a : 3,
    0x2e : 2,
    0x31 : 3,
    0x32 : 3,
    0x36 : 2,
    0x3a : 3,
    0x3e : 2,
    0xc2 : 3,
    0xc3 : 3,
    0xc4 : 3,
    0xc6 : 2,
    0xca : 3,
    0xcc : 3,
    0xcd : 3,
    0xce : 2,
    0xd2 : 3,
    0xd3 : 2,
    0xd4 : 3,
    0xd6 : 2,
    0xda : 3,
    0xdb : 2,
    0xdc : 3,
    0xde : 2,
    0xe2 : 3,
    0xe4 : 3,
    0xe6 : 2,
    0xea : 3,
    0xec : 3,
    0xee : 2,
    0xf2 : 3,
    0xf4 : 3,
    0xf6 : 2,
    0xfa : 3,
    0xfc : 3,
    0xfe : 2
}

