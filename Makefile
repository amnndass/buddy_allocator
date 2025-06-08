CC = gcc
CFLAGS = -Wall -fPIC
LDFLAGS = -shared

all: libbuddy.so

libbuddy.so: my_mem.c my_mem.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ my_mem.c

clean:
	rm -f libbuddy.so *.o 