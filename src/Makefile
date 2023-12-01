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
	$(CC) $(LDFLAGS) -lzip -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -MMD -c $< -o $@ -lzip

-include $(DEPS)

.PHONY: clean cleaner

clean:
	rm -f $(OBJS) $(DEPS) 

cleaner: clean
	rm -rf $(PROG)

