# 8080 Disassembler
A feature-light disassembler for 8080 binaries

### Disassembling a file
Run `disassemble8080py` through python3, and specify the target file on the command line. For example, to disassemble the cpudiag binary, run the following command from this directory:
    ```
    python3 disassemble8080.py ../bin/cpudiag/cpudiag.bin
    ```
The disassembled file will be automatically output in the same directory as the original file with the name `[filename].disassembled`

