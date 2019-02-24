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

'''Holds the I/O code and specific hardware operations for 
    Space Invaders on the 8080, connects to emulator_8080 to operate,
    and uses PyGame for graphics and user input'''
from sys import exit
import emu8080.emulator_8080 as emulator_8080
import pygame
import time
from functools import partial
from multiprocessing import Process
from data.precalculated import packed_monochrome_to_palette

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

shift = ShiftRegister()

system_info = {
    'screen_width'  : 256,
    'screen_height' : 224,
    'vram_start'    : 0x2400,
    'vram_half'     : 0x3200,
    'vram_end'      : 0x3fff,
    'framerate'     : 1.0/60.0,
    'palette'       : [(0,0,0), (255,255,255)]
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

def set_port_bit(port, mask, new_state):
    '''Toggles bit specified by mask at the given port according to
        the boolean value new_state'''
    if new_state:
        read_ports[port] = read_ports[port] | mask
    else:
        read_ports[port] = read_ports[port] & ~mask

keymap = {
    pygame.K_a      : partial(set_port_bit, 1, 0x20), # p1 left
    pygame.K_d      : partial(set_port_bit, 1, 0x40), # p1 right
    pygame.K_w      : partial(set_port_bit, 1, 0x10), # p1 shoot
    pygame.K_LEFT   : partial(set_port_bit, 2, 0x20), # p2 left
    pygame.K_RIGHT  : partial(set_port_bit, 2, 0x40), # p2 right
    pygame.K_SPACE  : partial(set_port_bit, 2, 0x10), # p2 shoot
    pygame.K_c      : partial(set_port_bit, 1, 0x01), # coin
    pygame.K_1      : partial(set_port_bit, 1, 0x04), # 1P start
    pygame.K_2      : partial(set_port_bit, 1, 0x02)  # 2P start
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
        bit 5 = NC (Cocktail mode control ... to flip screen) TODO?
'''
sound_ports = {
    3 : 0,
    5 : 0
}

'''Filenames specified here are loaded into this dict as pygame Sound
    objects at runtime'''
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

def set_sounds(port, new_data):
    '''Plays sound files according to output bit signals'''
    old_data = sound_ports[port]
    if old_data != new_data:
        '''All sound files start only when their relevant bit changes
            from 0 to 1'''
        if port == 3:
            if (new_data & 0x01) and not (old_data & 0x01):
                # UFO sound is continuous, starting when 0 changes to 1
                sound_dict['ufo'].play(-1)
            elif (not new_data & 0x01) and (old_data & 0x01):
                # UFO sound stops when 1 changes to 0
                sound_dict['ufo'].stop() # .fadeout()
            if (new_data & 0x02) and not (old_data & 0x02):
                sound_dict['shot'].play()
            if (new_data & 0x04) and not (old_data & 0x04):
                sound_dict['playerdie'].play()
            if (new_data & 0x08) and not (old_data & 0x08):
                sound_dict['invaderdie'].play()
        elif port == 5:
            if (new_data & 0x01) and not (old_data & 0x01):
                sound_dict['fleet1'].play()
            if (new_data & 0x02) and not (old_data & 0x02):
                sound_dict['fleet2'].play()
            if (new_data & 0x04) and not (old_data & 0x04):
                sound_dict['fleet3'].play()
            if (new_data & 0x08) and not (old_data & 0x08):
                sound_dict['fleet4'].play()
            if (new_data & 0x10) and not (old_data & 0x10):
                sound_dict['ufohit'].play()
        sound_ports[port] = new_data

def handle_events():
    '''Passes input to the proper methods. Returns True if QUIT event
        occurs'''
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            key_function = keymap.get(event.key)
            if key_function != None:
                key_function(True)
        elif event.type == pygame.KEYUP:
            key_function = keymap.get(event.key)
            if key_function != None:
                key_function(False)
        elif event.type == pygame.QUIT:
            return True
    return False
    
def write_device(port_num):
    '''Takes output from the program and simulates the 
        appropriate hardware interaction'''
    data = emulator_8080.get_write_data()
    if port_num == 2:
        shift.set_offset(data)
    elif port_num == 3:
        set_sounds(3, data)
    elif port_num == 4:
        shift.set_and_swap_bytes(data)
    elif port_num == 5:
        set_sounds(5, data)
    elif port_num == 6:
    #    strange 'debug' port? eg. it writes to this port when    
    #        it writes text to the screen (0=a,1=b,2=c, etc)
    else:
        print("Attempted to write to invalid port " + str(port_num))

def read_device(port_num):
    '''Passes I/O data into emulator state'''
    if port_num == 3: # read shift register
        data = shift.get_value()
    else:              # read other I/O
        data = read_ports.get(port_num)
    emulator_8080.apply_read_data(data)

def draw_screen(screen, rawimage):
    '''Pull image data from the emulator state and display it 
        via PyGame'''
    #starttime = time.process_time()
    image_buffer = []
    for byte in rawimage:
        image_buffer += packed_monochrome_to_palette.get(byte)
    #buffergentime = time.process_time()
    image_buffer = bytes(image_buffer)
    #bufferbytestime = time.process_time()
    image = pygame.image.frombuffer(image_buffer,
                        (system_info.get('screen_width'),
                         system_info.get('screen_height')),
                        "P")
    image.set_palette(system_info.get('palette'))
    #imagegentime = time.process_time()
    image = image.convert()
    #converttime = time.process_time()
    image = pygame.transform.rotate(image, 90)
    #imagerotatetime = time.process_time()
    pygame.transform.scale(image,
                (system_info.get('screen_height')*4,
                 system_info.get('screen_width')*4),
                screen)
    #imagescaletime = time.process_time()
    pygame.display.flip()
    finaltime = time.process_time()
    #print("buffergentime   " + str(buffergentime - starttime))
    #print("bufferbytestime " + str(bufferbytestime - buffergentime))
    #print("converttime     " + str(converttime - imagegentime))
    #print("imagescaletime  " + str(imagescaletime - imagerotatetime))
    #print("*" * 40)
    #drawtime = finaltime - starttime
    #if drawtime > 0.009:
    #    print("draw time " + str(finaltime - starttime))

def init():
    '''Load files from disk into memory'''
    with open("bin/invaders/invaders.h", 'rb') as input_file:
        emulator_8080.load_program(input_file.read(), 0x0000)
    with open("bin/invaders/invaders.g", 'rb') as input_file:
        emulator_8080.load_program(input_file.read(), 0x0800)
    with open("bin/invaders/invaders.f", 'rb') as input_file:
        emulator_8080.load_program(input_file.read(), 0x1000)
    with open("bin/invaders/invaders.e", 'rb') as input_file:
        emulator_8080.load_program(input_file.read(), 0x1800)
    pygame.init()
    for sound in sound_dict.keys():
        # translate filename into Sound objects
        sound_dict[sound] = pygame.mixer.Sound(sound_dict[sound])

def run():
    '''Initialize and begin emulation'''
    init()
    last_vblank = time.process_time()
    # mid-screen is roughly half a frame ahead
    last_mid = last_vblank - (system_info.get('framerate')/2)
    instruction_count = 0
    #min_debug = 2000
    width = system_info.get('screen_height')*4 # display is rotated
    height = system_info.get('screen_width')*4 # hence w=h, h=w
    screen = pygame.display.set_mode((width, height))
    #max_runtime = 600.0
    current_frame = 0
    #op_tracker = [0]*2**16 # stores ops/frame for metrics
    while True:
        do_quit = handle_events()
        if do_quit:
            break
        
        current_time = time.process_time()
        if current_time - last_vblank >= system_info.get('framerate'):
            emulator_8080.interrupt(0xd7) # RST 2 / End-screen
            #print("frame time: " + str(current_time - last_vblank))
            last_vblank = current_time
            vram = emulator_8080.state.get_memory_slice(
                        system_info.get('vram_start'),
                        system_info.get('vram_end'))
            draw_screen(screen, vram)
            #if current_frame % 60 == 0:
            #    print(sum( \
            #        op_tracker[current_frame-59:current_frame+1]))
            current_frame += 1
        elif current_time - last_mid >= system_info.get('framerate'):
            last_mid = current_time
            emulator_8080.interrupt(0xcf) # RST 1 / Mid-screen
        opcode = emulator_8080.emulate_operation()
        #op_tracker[current_frame] += 1
        '''Handling the write/read like this is a bit messy, especially
            with having to access the internal state directly. Should
            reconsider how to implement this but it works for now.
            Note that offset is -1 because emulate_operation has 
            already increased the PC past the data at this point'''
        if opcode == 0xd3: # OUT operation
            write_device(emulator_8080.state.get_memory_by_offset(-1))
        elif opcode == 0xdb: # IN operation
            read_device(emulator_8080.state.get_memory_by_offset(-1))
        instruction_count += 1
    pygame.quit()
    exit()

run()
