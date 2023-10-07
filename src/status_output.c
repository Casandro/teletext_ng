#include "status_output.h"
#include <stdio.h>
#include "hamming.h"

#define SO_LINES_PER_TS (3)

int so_current_line=0;
int so_service_count=0;

void so_move_to_line(const int line)
{
	if (line<so_current_line) { //Move upwards
		printf("\x1b[%dA", so_current_line-line);
	}
	if (line>so_current_line) { //Move downwards
		printf("\x1b[%dB", line-so_current_line);
	}
	printf("\r");
	so_current_line=line;
}

void so_erase_line(const int line)
{
	so_move_to_line(line);
	printf("\x1b[J");
}

int so_new_service()
{
	so_service_count=so_service_count+1;
	so_move_to_line(so_service_count*SO_LINES_PER_TS);
	for (int n=0; n<SO_LINES_PER_TS; n++) {
		printf("\n");
		so_current_line=so_current_line+1;
	}
	return so_service_count;
}

void so_move_to_position(all_pages_t *ap, const int p)
{
	if (ap==NULL) return;
	if (ap->status_line<0) {
		ap->status_line=so_new_service();
	}
	so_move_to_line(ap->status_line*SO_LINES_PER_TS+p);
}

void so_end_line(all_pages_t *ap, const int p)
{
	if (ap==NULL) return;
	if (p<0) return;
	printf("\x1b[K");
	fflush(stdout);
}

void so_end()
{
	if (so_service_count<=0) return;
	so_service_count=so_service_count+1;
	so_move_to_line(so_service_count*SO_LINES_PER_TS);
	printf("\n");
	so_service_count=0;
}

void print_magstate(const all_pages_t *ap, const int magno, FILE *f)
{
	if (ap==NULL) {
		fprintf(f, "No magazine %d ", magno);
		return;
	}
	int mn=magno;
	if (mn==0) mn=8;
	fprintf(f, "M%d: ", mn);
	for (int page_ten=0; page_ten<10; page_ten++) {
		for (int page_one=0; page_one<10; page_one++) {
			int page=page_ten<<4|page_one;
			int pn=magno<<8|page;
			if (ap->pages[pn]==0) {
				fprintf(f, ".");
			} else {
				int cnt=0;
				for (int subpage=0; subpage<SUBPAGENUM; subpage++) {
					if (ap->pages[pn]->subpages[subpage]!=NULL){
						cnt=cnt+1;
						if (cnt>10) break;
					}
				}
				if (cnt<10) fprintf(f, "%d", cnt); else
				if (cnt<36) fprintf(f, "%c", (cnt-10)+'A'); else
				fprintf(f, "#");
			}
		}
		fprintf(f," " );
	}
}

void print_pageno(const int pageno, FILE *f)
{
	if (pageno<0x100) fprintf(f, "%03x", pageno+0x800);
	else fprintf(f, "%03x", pageno);
}

#define MAX_PAGE_LIST (30)
int list_page_cnt=0;

void start_page_list()
{
	list_page_cnt=0;
}

void list_pageno(const int pageno, FILE *f)
{
	if (list_page_cnt==MAX_PAGE_LIST) {
		fprintf(f, "...");
	} else if (list_page_cnt<MAX_PAGE_LIST) {
		print_pageno(pageno, f);
		fprintf(f, ", ");
	}
	list_page_cnt=list_page_cnt+1;
}

void print_missing_pages(const all_pages_t *ap, FILE *f)
{
	list_page_cnt=0;
	for (int mainpage=0; mainpage<PAGENUM; mainpage++) {
		int res=mainpage_done(ap->pages[mainpage]);
		if (res<2) {
			if (list_page_cnt==0) fprintf(f, "Waiting for: ");
			list_pageno(mainpage, f); 	
		}
	}
}

void print_header(const page_t *p, FILE *f)
{
	if (p==NULL) {
		fprintf(f, "print_header, no page ");
		return;
	}
	uint8_t *r=p->rows[0];
	if (r==NULL) {
		fprintf(f, "print_header, no header row ");
		return;
	}
	for (int n=10; n<42; n++) {
		uint8_t c=r[n] & 0x7f;
		if ((c>' ') && (c<0x7f)) fprintf(f, "%c", c); else fprintf(f, " ");
	}
}

void print_missing_page_headers(const all_pages_t *ap, FILE *f, const char *eol)
{
	if (ap==NULL) return;
	int hdrcnt=0;
	for (int mainpage=0; mainpage<PAGENUM; mainpage++) {
		if (ap->pages[mainpage]==NULL) continue;
		int res=mainpage_done(ap->pages[mainpage]);
		if (res<2) {
			int min_subpage=1;
			int min_existing_subpage=SUBPAGENUM;
			int max_subpage=1;
			for (int subpage=0; subpage<SUBPAGENUM; subpage++) {
				if (ap->pages[mainpage]->subpages[subpage]!=NULL) {
					if (subpage<min_subpage) min_subpage=subpage;
					if (subpage>max_subpage) max_subpage=subpage;
					if (subpage<min_existing_subpage) min_existing_subpage=subpage;
				}
			}
			if (max_subpage==min_subpage) continue;
			fprintf(f, "  ");
			print_pageno(mainpage,f);
			fprintf(f, " ");
			print_header(ap->pages[mainpage]->subpages[min_existing_subpage], f);
			fprintf(f, " Subpages: ");
			for (int subpage=min_subpage; subpage<=max_subpage; subpage++) {
				if (ap->pages[mainpage]->subpages[subpage]==NULL) {
					printf(".");
				} else {
					int cnt=ap->pages[mainpage]->subpages[subpage]->cnt;
					if (cnt<10) fprintf(f, "%c", cnt+'0'); else fprintf(f, "X");
				}
			}
			fprintf(f, "%s", eol);
			hdrcnt=hdrcnt+1;
			if (hdrcnt>4) return;
		}
	}
}

int decode_mbcd(const uint8_t x)
{
        int a=(x>>4) -1;
        if (a<0) return -1;
        int b=(x&0xf) -1;
        if (b<0) return -1;
        return a<<4 | b;
}



void print_bsdp(const uint8_t *packet)
{
	int mpag=de_hamm8_8(packet);
	if (mpag<0) return;
	int magazine=mpag&0x07;
	int row=mpag>>3;
	printf("%d %d ", magazine, row);
	if (magazine!=0) return;
	if (row!=30) return;
	int dc=de_hamm8(packet[2]);
	printf("DC: %d ", dc);
	int ini_page_unit=de_hamm8(packet[3]);
	int ini_page_tens=de_hamm8(packet[4]);
	int subcode_1=de_hamm8(packet[5]);
	int subcode_2=de_hamm8(packet[6]);
	int subcode_3=de_hamm8(packet[7]);
	int subcode_4=de_hamm8(packet[8]);
	int ini_mag=(subcode_4>>1 & 0xe) | (subcode_2>>3);
	int ini_page=ini_mag<<8 | ini_page_tens<<4 | ini_page_unit;
	int ini_subpage=(subcode_4<<12 | subcode_3<<8 | subcode_2<<4 | subcode_1) & 0x3f7f;
	printf("IP: %03x-%04x ", ini_page, ini_subpage);
	int network_identification_code=de_hamm8(packet[9])<<8 | de_hamm8(packet[10]);
	printf("NICe: %04x ", network_identification_code);
	int time_offset_code=packet[11];
	double offset=(time_offset_code & 0x3e)*0.25;
	if ((time_offset_code&0x40)!=0) offset=-offset;
	printf("TOC: %02x, %lf hours ", time_offset_code, offset);
	int mjd=decode_mbcd(packet[12]+0x10)<<16 | decode_mbcd(packet[13])<<8 | decode_mbcd(packet[14]);
	printf("MJD: %05x ", mjd);
	printf("UTC: %02x:%02x:%02x ", decode_mbcd(packet[15]), decode_mbcd(packet[16]), decode_mbcd(packet[17]));
	printf("Status Display: '");
	for(int n=22; n<42; n++) printf("%c", packet[n]&0x7f);
	printf("' ");
	

}

void print_service_status(const all_pages_t *ap, const int pes, FILE *f, const char *eol)
{
	//First line
	fprintf(f, "Pid: 0x%04x, %03x-%s ", pes, ap->last_pageno, ap->last_header);
	fprintf(f, "  %d ", ap->bsdp_cnt);
	print_bsdp(ap->last_bsdp);
	fprintf(f, "%s", eol);
	print_missing_pages(ap, f);
	fprintf(f,"%s",eol);
	print_missing_page_headers(ap, f, eol);

}

