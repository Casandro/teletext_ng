PROG := ts_teletext
SRCS := $(wildcard *.c)

CC      := cc
CFLAGS  := -Wall -Wextra -Werror 
LDFLAGS := 

OBJS   = $(SRCS:.c=.o)
DEPS   = $(SRCS:.c=.d)

.PHONY: all
	all: $(PROG)

$(PROG): $(OBJS)
	$(CC) $(LDFLAGS) -o $@ $^ -lzip -lm

%.o: %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@ -lzip -lm

-include $(DEPS)

.PHONY: clean cleaner

install:
	cp $(PROG) /usr/local/bin/

clean:
	rm -f $(OBJS) $(DEPS) 

cleaner: clean
	rm -rf $(PROG)

