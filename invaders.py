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

''' Holds the I/O code and specific hardware operations for 
    the Space Invaders arcade machine on the 8080 '''
from sys import exit
import emu8080.emulator_8080 as emulator_8080
import pygame
import time
from functools import partial
from multiprocessing import Process
from data.precalculated import packed_monochrome_to_palette
from emu8080.io_abstract import IOAbstract

class ShiftRegister():
    '''16-bit shift register from the Space Invaders spec'''
    def __init__(self):
        '''Stored values intialize to 0'''
        self._stored_value = 0
        self._offset = 0
    
    def __str__(self):
        '''Returns stored values as a string'''
        return "value: " + str(self._stored_value) + ", offset: " \
                                                 + str(self._offset)

    def set_and_swap_bytes(self, value): # write port 4
        '''Sets the input value and swaps the high byte with 
            the low byte.'''
        #print("setting to " + "{:0x}".format(value))
        self._stored_value >>= 8
        self._stored_value += value << 8
    
    def set_offset(self, offset): # write port 2
        '''Sets the left-justified offset for an 8-bit value to be
            read from the stored value'''
        #print("set offset to " + "{:0x}".format(offset))
        self._offset = offset & 0x7 # only bits 0,1,2 are used
    
    def get_value(self): # read port 3
        '''Returns an 8-bit value offset from the left of the stored
            16-bit value by the specified amount'''
        mask = 0xff << (8 - self._offset)
        output = self._stored_value & mask
        output >>= (8 - self._offset)
        #print("got " + "{:>4x}".format(output) + " " + str(self))
        return output

class SpaceInvaders(IOAbstract):
    shift = ShiftRegister()

    system_info = {
        'orig_width'    : 256,
        'orig_height'   : 224,
        'rotate_ccw_deg': 90,
        'target_width'  : 896, # Note: Scaling occurs after rotation
        'target_height' : 1024, #  the values here should reflect that
        'vram_start'    : 0x2400,
        'vram_end'      : 0x3fff,
        'framerate'     : 1.0/60.0,
        'palette'       : [(0,0,0), (255,255,255)],
        'mid_vblank'    : True,
        'vblank_op'     : 0xcf,
        'mid_vblank_op' : 0xd7
    }
    
    binary_dict = {
        0x0000 : "bin/invaders/invaders.h",
        0x0800 : "bin/invaders/invaders.g",
        0x1000 : "bin/invaders/invaders.f",
        0x1800 : "bin/invaders/invaders.e"
    }

    ''' Read ports:
        Port 0
            bit 0 DIP4 (Seems to be self-test-request read at power up)
            bit 1 Always 1
            bit 2 Always 1
            bit 3 Always 1
            bit 4 Fire
            bit 5 Left
            bit 6 Right
            bit 7 ? tied to demux port 7 ?
        Port 1
            bit 0 = CREDIT (1 if deposit)
            bit 1 = 2P start (1 if pressed)
            bit 2 = 1P start (1 if pressed)
            bit 3 = Always 1
            bit 4 = 1P shot (1 if pressed)
            bit 5 = 1P left (1 if pressed)
            bit 6 = 1P right (1 if pressed)
            bit 7 = Not connected
        Port 2
            bit 0 = DIP3 00 = 3 ships  10 = 5 ships
            bit 1 = DIP5 01 = 4 ships  11 = 6 ships
            bit 2 = Tilt
            bit 3 = DIP6 0 = extra ship at 1500, 1 = extra ship at 1000
            bit 4 = P2 shot (1 if pressed)
            bit 5 = P2 left (1 if pressed)
            bit 6 = P2 right (1 if pressed)
            bit 7 = DIP7 Coin info displayed in demo screen 0=ON
        Port 3
            bit 0-7 Shift register data
    '''
    read_ports = {
        0 : 0xe, # mapped but never read, bits 1,2,3 are always 1
        1 : 0x8, # bit 3 is always 1.
        2 : 0,
        #3 : mapped to shift register's get function upstream
    }

    keymap = {
        pygame.K_a     : (1, 0x20), # p1 left
        pygame.K_d     : (1, 0x40), # p1 right
        pygame.K_w     : (1, 0x10), # p1 shoot
        pygame.K_LEFT  : (2, 0x20), # p2 left
        pygame.K_RIGHT : (2, 0x40), # p2 right
        pygame.K_UP    : (2, 0x10), # p2 shoot
        pygame.K_c     : (1, 0x01), # coin
        pygame.K_1     : (1, 0x04), # 1P start
        pygame.K_2     : (1, 0x02)  # 2P start
    }

    ''' Sound triggers:
        port 3:
            bit 0 = UFO (repeats)        SX0
            bit 1 = Shot                 SX1
            bit 2 = Flash (player die)   SX2
            bit 3 = Invader die          SX3
            bit 4 = Extended play        SX4
            bit 5 = AMP enable           SX5
        port 5: 
            bit 0 = Fleet movement 1     SX6
            bit 1 = Fleet movement 2     SX7
            bit 2 = Fleet movement 3     SX8
            bit 3 = Fleet movement 4     SX9
            bit 4 = UFO Hit              SX10
            bit 5 = NC (Cocktail mode control to flip screen) TODO?
    '''
    write_ports = {
        3 : 0,
        5 : 0
    }

    '''Filenames specified here are loaded into this dict as pygame
        Sound objects at runtime'''
    sound_dict = {
        'playerdie'     : 'sounds/invaders/explosion.wav',
        'invaderdie'    : 'sounds/invaders/invaderkilled.wav',
        'ufo'           : 'sounds/invaders/ufo_lowpitch.wav',
        'ufohit'        : 'sounds/invaders/ufo_highpitch.wav',
        'shot'          : 'sounds/invaders/shoot.wav',
        'fleet1'        : 'sounds/invaders/fastinvader1.wav',
        'fleet2'        : 'sounds/invaders/fastinvader2.wav',
        'fleet3'        : 'sounds/invaders/fastinvader3.wav',
        'fleet4'        : 'sounds/invaders/fastinvader4.wav'
    }

    def __init__(self):
        ''' Assign local configuration to class variables that
            the super code can see, then initialize super '''
        '''This feels clunky, I don't expect python actually
            needs this conversion but I can't find info on a 
            better way to make this work'''
        self._system_info = self.system_info
        self._binary_dict = self.binary_dict
        self._read_ports  = self.read_ports
        self._write_ports = self.write_ports
        self._sound_dict =  self.sound_dict
        self._keymap      = self.keymap
        super().__init__()

    def set_sounds(self, port, new_data):
        '''Plays sound files according to output bit signals'''
        old_data = self.write_ports[port]
        if old_data != new_data:
            '''All sound files start only when their relevant bit
                changes from 0 to 1'''
            if port == 3:
                if (new_data & 0x01) and not (old_data & 0x01):
                    # UFO sound loops, starting if 0 changes to 1
                    self._sound_dict['ufo'].play(-1)
                elif (not new_data & 0x01) and (old_data & 0x01):
                    # UFO sound stops when 1 changes to 0
                    self._sound_dict['ufo'].stop() # .fadeout()
                if (new_data & 0x02) and not (old_data & 0x02):
                    self._sound_dict['shot'].play()
                if (new_data & 0x04) and not (old_data & 0x04):
                    self._sound_dict['playerdie'].play()
                if (new_data & 0x08) and not (old_data & 0x08):
                    self._sound_dict['invaderdie'].play()
            elif port == 5:
                if (new_data & 0x01) and not (old_data & 0x01):
                    self._sound_dict['fleet1'].play()
                if (new_data & 0x02) and not (old_data & 0x02):
                    self._sound_dict['fleet2'].play()
                if (new_data & 0x04) and not (old_data & 0x04):
                    self._sound_dict['fleet3'].play()
                if (new_data & 0x08) and not (old_data & 0x08):
                    self._sound_dict['fleet4'].play()
                if (new_data & 0x10) and not (old_data & 0x10):
                    self._sound_dict['ufohit'].play()
            self.write_ports[port] = new_data
        
    def write_device(self, port_num):
        '''Takes output from the program and simulates the 
            appropriate hardware interaction'''
        data = emulator_8080.get_write_data()
        if port_num == 2:
            self.shift.set_offset(data)
        elif port_num == 3:
            self.set_sounds(3, data)
        elif port_num == 4:
            self.shift.set_and_swap_bytes(data)
        elif port_num == 5:
            self.set_sounds(5, data)
        elif port_num == 6:
            None # ignore this port
        #    strange 'debug' port? eg. it writes to this port when    
        #        it writes text to the screen (0=a,1=b,2=c, etc)
        else:
            print("Attempted to write to invalid port " + \
                                                 str(port_num))

    def read_device(self, port_num):
        '''Passes I/O data into emulator state'''
        if port_num == 3: # read shift register
            data = self.shift.get_value()
        else:              # read other I/O
            data = self.read_ports.get(port_num)
        emulator_8080.apply_read_data(data)

game = SpaceInvaders()
game.run()
