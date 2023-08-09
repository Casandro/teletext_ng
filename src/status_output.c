#include "status_output.h"
#include <stdio.h>

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

void print_service_status(const all_pages_t *ap, const int pes, FILE *f, const char *eol)
{
	//First line
	fprintf(f, "Pid: 0x%04x, Last-Header: %03x-%s %s", pes, ap->last_pageno, ap->last_header,eol);
	/*fprintf(f, "  ");
	print_magstate(ap, 1, f); 
	print_magstate(ap, 2, f);
	fprintf(f,"%s",eol);
	//second line
	fprintf(f, "  ");
	print_magstate(ap, 3, f);
	print_magstate(ap, 4, f);
	fprintf(f,"%s",eol);
	//third line
	fprintf(f, "  ");
	print_magstate(ap, 5, f);
	print_magstate(ap, 6, f);
	fprintf(f,"%s", eol);
	//fourth line
	fprintf(f, "  ");
	print_magstate(ap, 7, f);
	print_magstate(ap, 0, f);
	fprintf(f,"%s", eol);*/
	fprintf(f, "  ");
	print_missing_pages(ap, f);
	fprintf(f,"%s",eol);
	print_missing_page_headers(ap, f, eol);

}

