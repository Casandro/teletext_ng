#pragma once

#include <stdint.h>
#include "page.h"

#define PESHSIZE (64*1024)

typedef struct {
	int pid;
	all_pages_t *ap;
	uint8_t pes[PESHSIZE];
	int write_pointer;
	int continuity_counter;
} pes_handler_t;

int process_ts_packet(const uint8_t *buf, const char*);
void finish_ts_packets();
int are_pes_handlers_done();
int ts_get_pid(const uint8_t *buf);
