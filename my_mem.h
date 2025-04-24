#ifndef MY_MEM_H
#define MY_MEM_H

//initializes the memory manager
void mem_init(unsigned char *my_memory, unsigned int my_mem_size);

// returns valid pointer, or NULL if allocation failed or size is zero
void *my_malloc(unsigned size);

//debugging function
void mem_print(void);

#endif
