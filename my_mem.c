#include <stddef.h>
#include <stdio.h>
#include <stddef.h>
#include "my_mem.h"
// This evaluates to the maximum number of bits the OS can possibly address.
// On a 32-bit system, a pointer can point to 4 bytes = 32 bits (4*8). 

#define MAX_OS_POW2 (sizeof(void *) *8)

typedef struct Block {
    struct Block *next, *prev;
    size_t size_pow2;
} Block;

struct memory_manager_state {
    //to store first address of total memory
    unsigned char *memory;
    //total memory pool
    size_t mem_size;
    //highest power of 2 of memory
    size_t max_pow2;

    //array of struct block that store linked list of blocks according to their level or power
    Block *free[MAX_OS_POW2];
    Block *used[MAX_OS_POW2];
    
    //array to store how many nodes are in the linked list
    int num_free[MAX_OS_POW2];
    int num_used[MAX_OS_POW2];

} state;

// initialize a free block of memory and then push it to the proper free list
static void push_new_block(Block *block, size_t size_pow2) {
    block->prev = NULL;                     // set prev pointer to null
    block->next = state.free[size_pow2];    // set next pointer to *free list of corresponding pow2
    block->size_pow2 = size_pow2;           // set block size to level it is on free list

    if (block->next != NULL)                
        block->next->prev = block;          

    state.free[size_pow2] = block;           
    ++state.num_free[size_pow2];            
}

// Removes the head of a free list and returns it. 
// Ensure there is a block available before using this 
static Block *pop_free_block(size_t size_pow2) {
    Block *block = state.free[size_pow2]; 

    state.free[size_pow2] = block->next;
    --state.num_free[size_pow2];

    if (block->next != NULL)        // if next is not pointing to null b/c we are inserting the block a
        block->next->prev = NULL;   // set next and prev to null to make it free

    return block;
}

static void split_free_block (size_t size_pow2) {
    Block *block = pop_free_block(size_pow2);
    size_t next_size = size_pow2 - 1;
    Block *block2 = (Block *)(((unsigned char *)block) + (1 << next_size));

    push_new_block(block, next_size);
    push_new_block(block2, next_size);
}

// pops a block from free list to used list and returns
static Block *alloc_block(size_t size_pow2) {
    Block *block = pop_free_block(size_pow2);

    block->prev = NULL;
    block->next = state.used[size_pow2];

    if (block->next != NULL)
        block->next->prev = block;

    state.used[size_pow2] = block;
    ++state.num_used[size_pow2];

    return block;
}

//basically push the whole memory pool to the free list, only works one time --current understanding
void split_initial_memory (void) {
    unsigned char* mem = state.memory;

    //i stores highest power of 2 which is calculated in mem_init
    //we are running loop till 2^n > 1
    for (size_t i = state.max_pow2; (1 << i) > sizeof(Block); --i) {

        if(state.mem_size & (1 << i)) {
            push_new_block( (Block*)mem, i);
            mem += (1 << i);
        }
    }
}

//#1
void mem_init(unsigned char *my_memory, unsigned int my_mem_size) {
    state = (struct memory_manager_state){0};

    state.memory = my_memory;
    state.mem_size = my_mem_size;

    // calculate maximum pow2 
    while ((my_mem_size >>= 1))  // ex: 1024
        ++state.max_pow2;        // max_pow2 = 10 =(1,2,4,8,16,32,64,128,256,512)

    split_initial_memory();
}

//#2
//returns the smallest 2^n that is required to fulfill the given my_malloc request

// (n + sizeof(Block)) bytes, AKA the smallest block needed
static size_t smallest_block (size_t n) {
    //adding the header 
    n += sizeof(Block);

    size_t response = 0;

    // if a >> b and b > a then it will always result 0
    //absolute cinema
    while ( (n >> (response + 1)) > 0) {
        ++response;
    }

    // if n also requires extra space, give it
    if( n > (1 >> response) ) {
        ++response;
    }

    return response;

}

void *my_malloc (unsigned size) {
    //edge case
    if(size == 0) {
        return NULL;
    }

    // find the smallest power of 2 required for this size
    size_t req_pow2 = smallest_block(size);

    size_t best_free = req_pow2;

    while (state.num_free[best_free] == 0) {
        // if no blocks are available, return NULL
        if (++best_free > state.max_pow2)
            return NULL;
    }

    // split blocks until one is available that equals the required size
    while (best_free > req_pow2)
        split_free_block(best_free--);

    // allocated block and return a pointer to the memory located after the
    // block header
    return (void *)(alloc_block(req_pow2) + 1);
}

//printing the info
void mem_print(void) {
    puts("--- memory ---");

    printf(
        "%-2s | %-12s | %-6s | %-6s\n",
        "n", "true size", "free", "used"
    );

    for (size_t i = 0; i <= state.max_pow2; ++i) {
        printf(
            "%2zu | %12d | %6d | %6d\n",
            i, (1 << i), state.num_free[i], state.num_used[i]
        );
    }

    // assumes allocated blocks have valid strings in them
    puts("--- used ---");

    for (size_t i = 0; i <= state.max_pow2; ++i)
        for (Block *trav = state.used[i]; trav; trav = trav->next)
            printf("%2zu: %s\n", i, (char *)(trav + 1));
}
