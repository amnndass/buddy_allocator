#!/usr/bin/env python3
import ctypes
from ctypes import c_char_p, c_uint, c_void_p, POINTER
import os
import sys
import cmd
import io
from contextlib import redirect_stdout
from typing import List, Tuple

# ANSI color codes for pretty printing
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Load the shared library
try:
    lib_path = os.path.join(os.path.dirname(__file__), 'libbuddy.so')
    buddy_lib = ctypes.CDLL(lib_path)
except OSError as e:
    print(f"Error loading library: {e}")
    sys.exit(1)

# Define the memory size
MEMORY_SIZE = 1024  # 1KB
memory = (ctypes.c_char * MEMORY_SIZE)()

# Set up the C function interfaces
buddy_lib.mem_init.argtypes = [POINTER(ctypes.c_char), c_uint]
buddy_lib.mem_init.restype = None

buddy_lib.my_malloc.argtypes = [c_uint]
buddy_lib.my_malloc.restype = c_void_p

buddy_lib.mem_stats.argtypes = [POINTER(ctypes.c_int), POINTER(ctypes.c_int)]
buddy_lib.mem_stats.restype = None

class BuddyAllocatorCLI(cmd.Cmd):
    intro = f'''{Colors.HEADER}
Buddy Allocator Demo
===================
Type help or ? to list commands.
{Colors.ENDC}'''
    prompt = f'{Colors.BOLD}buddy> {Colors.ENDC}'
    
    def __init__(self):
        super().__init__()
        buddy_lib.mem_init(memory, MEMORY_SIZE)
        self.allocated_blocks: List[Tuple[int, int]] = []  # [(size, address), ...]
        self.allocation_id = 0
        
    def get_memory_state(self) -> str:
        """Capture the memory state from mem_print()"""
        f = io.StringIO()
        with redirect_stdout(f):
            buddy_lib.mem_print()
        return f.getvalue()
    
    def do_allocate(self, arg):
        """
        Allocate memory of specified size
        Usage: allocate <size_in_bytes>
        """
        try:
            size = int(arg)
            if size <= 0:
                print(f"{Colors.RED}Error: Size must be positive{Colors.ENDC}")
                return
                
            addr = buddy_lib.my_malloc(size)
            if not addr:
                print(f"{Colors.RED}Allocation failed{Colors.ENDC}")
                return
                
            self.allocation_id += 1
            self.allocated_blocks.append((size, addr))
            print(f"{Colors.GREEN}Successfully allocated {size} bytes at address {addr}{Colors.ENDC}")
            print("\nCurrent memory state:")
            self.do_status("")
            
        except ValueError:
            print(f"{Colors.RED}Error: Invalid size value{Colors.ENDC}")
    
    def parse_memory_line(self, line: str) -> tuple:
        """Parse a single line of memory state output"""
        try:
            # Split by | and remove any whitespace
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                # Parse the power (n)
                power = int(parts[0])
                # Calculate true size (2^n)
                block_size = 1 << power  # This is equivalent to 2^power
                # Parse free and used counts
                free_blocks = int(parts[2])
                used_blocks = int(parts[3])
                return power, block_size, free_blocks, used_blocks
        except (ValueError, IndexError):
            pass
        return None
    
    def calculate_memory_usage(self, memory_state: str) -> tuple:
        """Calculate total used and free memory from memory state"""
        total_free = ctypes.c_int(0)
        total_used = ctypes.c_int(0)
        buddy_lib.mem_stats(ctypes.byref(total_free), ctypes.byref(total_used))
        return total_used.value, total_free.value

    def do_status(self, arg):
        """
        Show current memory status with visualization
        Usage: status
        """
        memory_state = self.get_memory_state()
        print(memory_state )  # Print the original mem_print output is printed from c file
        
        # Calculate memory usage
        total_used, total_free = self.calculate_memory_usage(memory_state)
        
        # Print memory usage summary
        print(f"\n{Colors.HEADER}Memory Usage Summary:{Colors.ENDC}")
        print("-" * 50)
        print(f"Total Memory: {MEMORY_SIZE} bytes")
        print(f"Used Memory:  {total_used} bytes ({(total_used/MEMORY_SIZE*100):.1f}%)")
        print(f"Free Memory:  {total_free} bytes ({(total_free/MEMORY_SIZE*100):.1f}%)")
        
        if self.allocated_blocks:
            print(f"\n{Colors.YELLOW}Active Allocations:{Colors.ENDC}")
            for i, (size, addr) in enumerate(self.allocated_blocks, 1):
                print(f"Block {i}: {size} bytes at address {addr}")
    
    def do_explain(self, arg):
        """
        Explain how buddy allocation works
        Usage: explain
        """
        explanation = f"""
{Colors.HEADER}How Buddy Allocation Works:{Colors.ENDC}

1. {Colors.BOLD}Memory Organization:{Colors.ENDC}
   - Memory is divided into blocks of size 2^n
   - Each block can be recursively split into two equal "buddy" blocks
   - Total memory size: {MEMORY_SIZE} bytes

2. {Colors.BOLD}Allocation Process:{Colors.ENDC}
   - When allocating size N:
     a. Round up N to nearest power of 2
     b. Find smallest free block that can fit N
     c. If block is too large, split it into buddies
     d. Repeat until right-sized block is created

3. {Colors.BOLD}Example:{Colors.ENDC}
   - To allocate 30 bytes:
     1. Round up to 32 (2^5)
     2. If no 32-byte block is free:
        - Split a 64-byte block into two 32-byte blocks
        - Use one, keep other for future

4. {Colors.BOLD}Block Sizes:{Colors.ENDC}
   Available sizes in this implementation:
   2^0  = 1 byte
   2^1  = 2 bytes
   2^2  = 4 bytes
   2^3  = 8 bytes
   2^4  = 16 bytes
   2^5  = 32 bytes
   ...and so on

Use 'status' to see current memory state
Use 'allocate <size>' to test different allocation sizes
"""
        print(explanation)
    
    def do_clear(self, arg):
        """
        Clear screen
        Usage: clear
        """
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_reset(self, arg):
        """
        Reset memory to initial state
        Usage: reset
        """
        buddy_lib.mem_init(memory, MEMORY_SIZE)
        self.allocated_blocks = []
        self.allocation_id = 0
        print(f"{Colors.GREEN}Memory reset to initial state{Colors.ENDC}")
        self.do_status("")
    
    def do_exit(self, arg):
        """
        Exit the program
        Usage: exit
        """
        print("\nExiting Buddy Allocator Demo")
        return True
    
    def do_EOF(self, arg):
        """Exit on Ctrl-D (EOF)"""
        print()
        return self.do_exit(arg)

    def do_visual(self, arg):
        """
        Show a visual representation of memory layout
        Usage: visual
        """
        memory_state = self.get_memory_state()
        lines = memory_state.split('\n')
        
        print(f"\n{Colors.HEADER}Memory Layout Visualization:{Colors.ENDC}")
        print("=" * 60)
        
        # # Create a visual representation of memory blocks
        # data_lines = [line for line in lines if '|' in line and 'true size' not in line]
        
        # for line in data_lines:
        #     result = self.parse_memory_line(line)
        #     if result:
        #         power, block_size, free_blocks, used_blocks = result
        #         total_blocks = free_blocks + used_blocks
        #         if total_blocks > 0:
        #             # Calculate block representation
        #             block_char = "█"
        #             free_blocks_vis = Colors.GREEN + block_char * free_blocks + Colors.ENDC
        #             used_blocks_vis = Colors.RED + block_char * used_blocks + Colors.ENDC
                    
        #             # Print the line with size information
        #             print(f"{Colors.BOLD}2^{power:2d} ({block_size:4d}B):{Colors.ENDC} "
        #                   f"{free_blocks_vis}{used_blocks_vis} "
        #                   f"[{free_blocks} free, {used_blocks} used]")

        block_char = "█"
        total_used, total_free = self.calculate_memory_usage(memory_state)
        total_used_blocks = int(total_used/MEMORY_SIZE*60)
        total_free_blocks = int(total_free/MEMORY_SIZE*60)

        free_blocks_viz = Colors.RED + block_char * total_used_blocks
        used_blocks_viz = Colors.GREEN + block_char * total_free_blocks

        print(f"{free_blocks_viz}{used_blocks_viz}")
        
        print("=" * 60)
        print(f"{Colors.GREEN}█{Colors.ENDC} = Free block   "
              f"{Colors.RED}█{Colors.ENDC} = Used block")

    def do_help(self, arg):
        """List available commands with their descriptions"""
        super().do_help(arg)
        if not arg:
            print("\nTip: Try 'visual' command for a graphical view of memory layout!")

if __name__ == '__main__':
    try:
        BuddyAllocatorCLI().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting Buddy Allocator Demo") 