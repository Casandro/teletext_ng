#pragma once

#include <stdint.h>
#include "page.h"

#define PESHSIZE (64*1024)

int process_ts_packet(const uint8_t *buf, const char*);
void finish_ts_packets();
int are_pes_handlers_done();
int ts_get_pid(const uint8_t *buf);
