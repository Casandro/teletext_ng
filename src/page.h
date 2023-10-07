#pragma once
#include <stdint.h>
#include <stdio.h>
#include <sys/time.h>

#define RCNT (32*16)

typedef struct {
	uint8_t *rows[RCNT];
	int cnt; //How many times has this page been started
} page_t;


#define SUBPAGENUM (80)


typedef struct {
	page_t *subpages[SUBPAGENUM];
	uint16_t number;
	int maxsubcode; //Maximum subcode
	int done; //Is this main page done?
} mainpage_t;


#define PAGENUM (0x800)
#define APBSIZE (4096)


typedef struct{
	int pageno[8];
  	mainpage_t *pages[PAGENUM];
	char *name;
	struct timeval last_change;
	struct timeval last_note;
	int status_line;
	int last_pageno;
	char last_header[33];
	uint8_t last_bsdp[42];
	int bsdp_cnt;
} all_pages_t;

int add_packet_to_pages(all_pages_t *p, const uint8_t row, const int fullpageno, const uint8_t *data);

all_pages_t *new_allpages(const char *name);

int handle_t42_data(all_pages_t *p, const uint8_t *line);
/*returns >1 if the page was fully received including all sub pages
 * 1 unclear if page has been fully received
 * 0 page has not been fully received
 */
int allpages_done(all_pages_t *p);
int mainpage_done(const mainpage_t *page);
int write_all_pages(const all_pages_t *p);
int finish_allpages(all_pages_t *p);
