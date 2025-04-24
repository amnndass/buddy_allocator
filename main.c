#include "my_mem.h"
#include <stdio.h>
#include <stddef.h>
#include <stdlib.h>

int main () {
    unsigned char *my_memory = (unsigned char *)malloc(1024);
    mem_init(my_memory, 1024);
    mem_print();

    int *ptr = (int *)my_malloc(30);
    mem_print();
    if (ptr == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }else {
        printf("Memory allocated at %p\n", (void *)ptr);
    }

    my_malloc(200);
    mem_print();
    my_malloc(200);
    mem_print();
    free(my_memory);
    return 0;
}