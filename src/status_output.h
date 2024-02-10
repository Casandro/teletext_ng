#pragma once

#include "page.h"
void print_service_status(const all_pages_t *ap, const int pes, FILE *f, const char *eol);
void set_line_prefix(const char *prefix);
void print_line_prefix();
