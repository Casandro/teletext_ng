#pragma once
#include <stdint.h>
#include <stdio.h>

#define RCNT (26+(32-26)*16)

typedef struct {
	uint8_t *rows[RCNT];
	int cnt; //How many times has this page been started
	int start;
} page_t;


#define SUBPAGENUM (80)


typedef struct {
	page_t *subpages[SUBPAGENUM];
	int start;
} mainpage_t;


#define PAGENUM (0x800)
#define APBSIZE (4096)


typedef struct{
	int pageno[8];
  	mainpage_t *pages[PAGENUM];
	char *name;
} all_pages_t;

int add_packet_to_pages(all_pages_t *p, const uint8_t row, const int fullpageno, const uint8_t *data);

all_pages_t *new_allpages(const char *name);

int handle_t42_data(all_pages_t *p, const uint8_t *line);
/*returns >1 if the page was fully received including all sub pages
 * 1 unclear if page has been fully received
 * 0 page has not been fully received
 */
int allpages_done(const all_pages_t *p);
int write_all_pages(const all_pages_t *p);
int finish_allpages(all_pages_t *p);
