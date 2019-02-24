# python8080
An 8080 emulator written in Python 3.7.2, currently only supports the Space Invaders binary code. Graphics handled by [PyGame](https://www.pygame.org/).

### Running the emulator
These instructions are for Debian-based Linux systems, but the code should run anywhere you can install Python and PyGame.

1. Install python 3.7 and pip3.
    ```
    sudo apt install python3 python3-pip
    ```
2. Install pygame.
    ```
    pip3 install pygame
    ```
3. Download the emulator. You can do this with git:
    ```
    git clone https://github.com/officialjacobgray/python8080.git
    ```
    Alternatively you can click "Clone or download > Download ZIP" at the top of this page and extract it.
3. Open the emulator directory and run the desired machine code. The current code only includes a Space Invaders machine.
    ```
    cd python8080
    python3 invaders.py
    ```
A graphical window should open and emulation will begin.

##### Space Invaders controls
    ```
    c           : Insert coin
    a           : Player 1 left
    d           : Player 1 right
    w           : Player 1 shoot
    Left        : Player 2 left
    Right       : Player 2 right
    Up          : Player 2 Up
    1           : 1 Player start
    2           : 2 Player start
    ```

### Adding a new machine

This should be as simple as creating a class that implements IOAbstract from emu8080/io_abstract.py by providing relevant hardware configuration and whatever specific features are necessary for that hardware (such as the Space Invaders shift register). See that class and the invaders.py implementation for further information.

### Details
I built this following the [Emulator 101 guide for the 8080](http://www.emulator101.com/), with a lot of help from the extremely detailed hardware and code breakdown at [Computer Archeology](http://computerarcheology.com/Arcade/SpaceInvaders/) and some error checking against [this browser-based emulator](https://bluishcoder.co.nz/js8080/).

Emulator code is in the emu8080 directory:
- system_state_8080 holds all the stateful information
- emulator_8080 creates a state and handles all the opcode intstructions

Machine code in the root directory holds hardware-specific operations for a given application, such as user input, sound output, and additional hardware like the shift register in Space Invaders. See io_invaders.py for an implementation. This structure was chosen with the intention that another program could be emulated by creating its own version of [game].py code.

Some tools were made or used to debug the emulator, but are not involved in its operation:
- cpudiag, a piece of 8080 code designed to verify the accuracy of the original CPU and works nicely for testing emulation. I've written the python code that allows it to run and print to console, but the original binary is from 1980. Refer to the README.md in that folder for more information.
- disassembler, a basic disassembler for 8080 binaries.

I originally made the instruction code functions more versatile, with polymorphic signatures to reduce the amount of written code, but moving repeated code with minor variations to unique functions rather than making value checks has increased performance 10-20%. This is a pretty big gain in exchange for the reduction in readability/maintainability.

### Emulation Performance
Not great. I'm not sure if I'm running up against limitations of Python, but I've tried optimizing the code and the best performance I see on any machine is only about equal to the original hardware (A 2MHz processor) based on how it plays. After the first successful run I was getting an average of 35,000 emulated operations per second outside of the PyGame display calls, and through profiling and adjustments I've got that up to around 50,000 with the current build. This could definitely use some improvement.

Getting the game screen from memory and passing it through Python is currently taking about 8 to 11 milliseconds of the 16.66 millisecond frame target necessary to hit 60fps. I'm not sure how much of this can be reduced without major restructuring or moving parts of the code away from Python. Regardless, I feel like the number of operations performed in this remaining time should be much higher than they currently are based on other emulators I've tried. The next thing I'll implement here will be to use multithreading to move the emulation to a separate thread from the graphical environment.

### Known Issues
- The aliens don't load correctly when running on Windows. Not sure what's causing this but it has to be something to do with Python running differently in Windows vs on my Linux dev machine.
- Alien movement cascades instead of occuring between frames. I'm pretty sure this is due to the performance issues.
- Window scaling may make this too big on some screens. The solution here is to allow custom resolution or scaling to be set within a config file.

### Remaining Features
- Add timing to the emulated operations to cap running speed to the original hardware spec. Even though a lot of the emulation is slow, there are a few lightweight parts that run much too fast.
- Complete sound files. The current files are what I was able to find, but I'm missing a few and some of the files are broken (fastinvader 1-4 don't seem to play correctly)
- Stateful behavior. It'd be nice to have all emulation occur against a state object that's passed between them rather than the current structure. This would allow for saving and loading game state but may be less performant.
- Performance tweaks. The code definitely runs slower than I feel it should.
- Load configuration from file at runtime for input and dipswitches. The structure should make this pretty easy since most data we might want to change is already stored in a global dict.

### Conclusion
As it stands, this was a really good learning experience with both Python and emulation in general but I not sure how much I'll continue this due to the significant performance issues I've encountered. It's possible I just don't know how to optimize Python properly, so if you look at this and have some advice on how to improve this, please let me know!
