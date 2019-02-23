An 8080 emulator written in Python 3.7.2, currently only supports the Space Invaders binary code. Graphics handled by PyGame.

To run:
install python 3.7
install pygame, should be as simple as this:
    pip3 install pygame
run python3 io_invaders.py

Default controls for invaders:
c           : Insert coin
a           : Player 1 left
d           : Player 1 right
w           : Player 1 shoot
Left        : Player 2 left
Right       : Player 2 right
Up          : Player 2 Up
1           : 1 Player start
2           : 2 Player start

I built this following the 8080 emulator guide at http://www.emulator101.com/, with a lot of help from the extremely detailed hardware and code breakdown at Computer Archeology http://computerarcheology.com/Arcade/SpaceInvaders/ and some error checking against the browser-based emulator found here https://bluishcoder.co.nz/js8080/

Emulator structure is set up to be fairly modular:
    system_state_8080 holds all the stateful information
    emulator_8080 creates a state and handles all the opcode intstructions
    io_invaders handles all the hardware-specific operations outside of the CPU and serves as the entry point
This was built with the intention that another program could be emulated by creating its own version of io_[game].py code.

Some tools were made or used to debug the emulator, but are not involved in its operation:
    cpudiag, a piece of 8080 code designed to verify the accuracy of the original CPU and works nicely for testing emulation. I've written the python code that allows it to run and print to console, but the original binary is from 1980. Refer to the readme in that folder for more information.
    disassembler, a basic disassembler for 8080 binaries.

Emulation Performance:
Not great on low-end hardware, need to test this on my better computer. I developed this entirely on an i5 Surface Pro 4 running Ubuntu 18.10, and that's the only place I've tested it so I can't guarantee results on other machines. Everything should be platform-independent though.

Running on my Surface, performance is much slower than I'd expect. Running at 60fps as the native machine, emulated performance is about equal to the original hardware based on how it plays. After the first successful run I was getting an average of 35,000 operations per second outside of the PyGame display calls, and through profiling and adjustments I've got that up to around 50,000 with the current build. Definitely could use some improvement.

Getting the game screen from memory and passing it through Python is currently taking about 8 to 11 milliseconds of the 16.66 millisecond frame target. I'm not sure how much of this can be reduced without major restructuring or moving parts of the code away from Python. Regardless, I feel like the number of operations performed in this remaining time should be much higher than they currently are based on other emulators I've tried.

Remaining Features:
-Add timing to the emulated operations to cap running speed to the original hardware spec. Even though a lot of the emulation is slow, there are a few lightweight parts that run much too fast (notably when starting 1 Player mode the score blinks like crazy)
-Complete sound files. The current files are what I was able to find, but I'm missing a few and some of the files are broken (fastinvader 1-4 don't play correctly)
-Stateful behavior. It'd be nice to have all emulation occur against a state object that's passed between them rather than the current structure. This would allow for saving and loading game state but may be less performant.
-Performance tweaks. The code definitely runs slower than I feel it should.
-Load configuration from file at runtime for input and dipswitches. The structure should make this pretty easy since most data we might want to change is alread stored in a global dict.

Lessons Learned:
Python is probably not great for making emulators or other high-performance software
Python is pretty neat though! This was my first big project using Python and it's interesting seeing how it compares to other languages.


As it stands, this was a really good learning experience with both Python and emulation in general but I don't really plan to return to this due to the significant performance issues I've encountered from using Python. It's possible I just don't know how to optimize Python properly, if you look at this and have some advice on how to improve this, please send me a message!

