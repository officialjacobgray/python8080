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

import abc
import pygame
import emu8080.emulator_8080 as emulator
from sys import exit
from time import process_time
from functools import partial
from multiprocessing import Process
from data.precalculated import packed_monochrome_to_palette

class IOAbstract():
    ''' Generic interface for creating a machine that can run on the
        emulator. These aspects must be defined for a functional 
        implementation:
        _system_info
        _binary_dict
        _read_ports
        _write_ports
        _keymap
        write_device()
        read_device()
    '''

    ''' Contains configuration info about this hardware '''
    _system_info = { # sample data:
        #'orig_width'    : 256,
        #'orig_height'   : 224,
        #'rotate_ccw_deg': 90,
        #'target_width'  : 448, # Note: Scaling occurs after rotation
        #'target_height' : 512, #  the values here should reflect that
        #'vram_start'    : 0x2400,
        #'vram_end'      : 0x3fff,
        #'framerate'     : 1.0/60.0,
        #'palette'       : [(0,0,0), (255,255,255)],
        #'mid_vblank'    : True,
        #'vblank_op'     : 0xcf,
        #'mid_vblank_op' : 0xd7
    }
    
    ''' Dict with one entry for each program file to load into 
        memory at program init. The key should be the beginning
        memory address, and the value should be the file path. '''
    _binary_dict = { # sample data:
        #0x0000 : "bin/invaders/invaders.h",
        #0x0800 : "bin/invaders/invaders.g",
        #0x1000 : "bin/invaders/invaders.f",
        #0x1800 : "bin/invaders/invaders.e"
    }
    
    _read_ports = {
    }
    
    _write_ports = {
    }

    def set_read_bit(self, port, mask, new_state):
        ''' Sets bits at the specified port according to the 
            given mask to the boolean value new_state'''
        if new_state:
            self._read_ports[port] = self._read_ports[port] | mask
        else:
            self._read_ports[port] = self._read_ports[port] & ~mask
    
    ''' Dict defining bits to set for keypresses. Each key should
        be mapped to a tuple of the format (readport, bitmask) '''
    _keymap = { # sample data, mappings are from Space Invaders:
        #pygame.K_a      : (1, 0x20), # p1 left
        #pygame.K_d      : (1, 0x40), # p1 right
        #pygame.K_w      : (1, 0x10), # p1 shoot
        #pygame.K_LEFT   : (2, 0x20), # p2 left
        #pygame.K_RIGHT  : (2, 0x40), # p2 right
        #pygame.K_SPACE  : (2, 0x10), # p2 shoot
        #pygame.K_c      : (1, 0x01), # coin
        #pygame.K_1      : (1, 0x04), # 1P start
        #pygame.K_2      : (1, 0x02)  # 2P start
    }
    
    ''' Dict with one entry for each sound file to load. The key
        should be a meaningful sound name, and the vlaue should be
        the file path. File paths are converted to pygame Sound 
        objects on class init and this object is reference to 
        play them '''
    _sound_dict = { # sample data:
        #'playerdie'     : 'sounds/invaders/explosion.wav',
        #'invaderdie'    : 'sounds/invaders/invaderkilled.wav',
        #'ufo'           : 'sounds/invaders/ufo_lowpitch.wav',
        #'ufohit'        : 'sounds/invaders/ufo_highpitch.wav',
        #'shot'          : 'sounds/invaders/shoot.wav',
        #'fleet1'        : 'sounds/invaders/fastinvader1.wav',
        #'fleet2'        : 'sounds/invaders/fastinvader2.wav',
        #'fleet3'        : 'sounds/invaders/fastinvader3.wav',
        #'fleet4'        : 'sounds/invaders/fastinvader4.wav'
    }

    def __init__(self):
        ''' Load program and sound files from disk into memory,
            initialize pygame '''
        for address in self._binary_dict:
            with open(self._binary_dict[address], 'rb') as input_file:
                emulator.load_program(input_file.read(), address)
        pygame.init()
        for sound in self._sound_dict:
            # translate filename into Sound objects
            self._sound_dict[sound] \
                        = pygame.mixer.Sound(self._sound_dict[sound])
    
    def handle_events(self):
        ''' Processes input events accoring to the _keymap.
            Returns True if QUIT event occurs '''
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:
                keydata = self._keymap.get(event.key)
                if keydata != None:
                    self.set_read_bit(*keydata, True)
            elif event.type == pygame.KEYUP:
                keydata = self._keymap.get(event.key)
                if keydata != None:
                    self.set_read_bit(*keydata, False)
            elif event.type == pygame.QUIT:
                return True
        return False

    @abc.abstractmethod
    def write_device(self, port_num):
        ''' Takes output from the program and simulates the 
            appropriate hardware interaction. This function should
            describe the path to take for each port written by
            the 8080 program '''
        return

    @abc.abstractmethod
    def read_device(self, port_num):
        ''' Passes I/O data into emulator state. This function
            should formulate and retrieve the data for each port
            read by the 8080 program, and pass it into the emulator
            via `emulator.apply_read_data(data) '''
        data = None
        emulator.apply_read_data(data)

    def draw_screen(self, screen, rawimage):
        ''' Pull image data from the emulator state and display it 
            via PyGame '''
        image_buffer = []
        for byte in rawimage:
            image_buffer += packed_monochrome_to_palette.get(byte)
        image_buffer = bytes(image_buffer)
        image = pygame.image.frombuffer(image_buffer,
                            (self._system_info.get('orig_width'),
                             self._system_info.get('orig_height')),
                            "P")
        image.set_palette(self._system_info.get('palette'))
        image = image.convert()
        image = pygame.transform.rotate(image,
                            self._system_info.get('rotate_ccw_deg'))
        pygame.transform.scale(image,
                    (self._system_info.get('target_width'),
                     self._system_info.get('target_height')),
                    screen)
        pygame.display.flip()

    def run(self):
        ''' Begin emulation '''
        instruction_count = 0
        width = self._system_info.get('target_width')
        height = self._system_info.get('target_height')
        screen = pygame.display.set_mode((width, height))
        last_vblank = process_time()
        # toggle for this because not all games have mid-vblank
        do_midblank = self._system_info.get('mid_vblank_op') != None
        # mid-screen is roughly half a frame ahead
        last_mid = last_vblank - (self._system_info.get('framerate')/2)
        current_frame = 0
        #op_tracker = [0]*2**16 # stores ops/frame for metrics
        while True:
            do_quit = self.handle_events()
            if do_quit:
                break
            
            current_time = process_time()
            if current_time - last_vblank \
                            >= self._system_info.get('framerate'):
                emulator.interrupt(self._system_info['vblank_op'])
                last_vblank = current_time
                vram = emulator.state.get_memory_slice(
                            self._system_info.get('vram_start'),
                            self._system_info.get('vram_end'))
                self.draw_screen(screen, vram)
                #if current_frame % 60 == 0:
                #    print(sum( \
                #        op_tracker[current_frame-59:current_frame+1]))
                current_frame += 1
            elif do_midblank and current_time - last_mid \
                            >= self._system_info.get('framerate'):
                last_mid = current_time
                emulator.interrupt(self._system_info['mid_vblank_op'])
            opcode = emulator.emulate_operation()
            #op_tracker[current_frame] += 1
            ''' Handling the write/read like this is a bit messy,
                especially with having to access the internal state
                directly. Should reconsider how to implement this 
                but it works for now.Note that offset is -1 because
                emulate_operation has already increased the PC past
                the data at this point '''
            if opcode == 0xd3: # OUT operation
                self.write_device( \
                            emulator.state.get_memory_by_offset(-1))
            elif opcode == 0xdb: # IN operation
                self.read_device( \
                            emulator.state.get_memory_by_offset(-1))
            instruction_count += 1
        pygame.quit()
        exit()
