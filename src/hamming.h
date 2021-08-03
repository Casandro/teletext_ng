#pragma once

#include <stddef.h>
#include <stdint.h>


int de_hamm8(const uint8_t);
int check_parity(const uint8_t *, size_t);
int de_hamm8_8(const uint8_t *data);
int de_hamm8_16(const uint8_t *data);
uint8_t rev(uint8_t b);
