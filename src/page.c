#include "page.h"
#include "hamming.h"
#include <stdlib.h>
#include <string.h>
#include "status_output.h"


int extended_row(const uint8_t row, const uint8_t *data)
{
	if (row>=32) return -1;
	if (row<26) return row*16;
	int dc=de_hamm8(data[2]);
	if (dc<0) dc=0;
	return  row*16+dc;
}

int add_packet_to_page(page_t *page, const uint8_t row, const uint8_t *data)
{
	if (page==NULL) return -1;
	if (row>=32) return -1;
	if (data==NULL) return -1;
	int extrow=extended_row(row, data);
	if (extrow<0) return-1 ;
	if (extrow>=RCNT) return -1;
	if (page->rows[extrow]==NULL) {
		page->rows[extrow]=malloc(42);
	}
	page->last_change=time(NULL);
	memcpy(page->rows[extrow], data, 42);
	if (row==0) page->cnt=page->cnt+1;
	return 0;
}

int write_page(all_pages_t *ap, const int pageno, const page_t *page)
{
	if (page==NULL) return 0;
	int cnt=0;
	for (int n=0; n<RCNT; n++) {
		if (page->rows[n]!=NULL) {
			cnt=cnt+1;
		}
	}
	size_t size=cnt*42;
	uint8_t *buffer=calloc(cnt, 42);
	int num=0;
	for (int n=0; n<RCNT; n++) {
		if (page->rows[n]!=NULL) {
			memmove(buffer+num*42, page->rows[n], 42);
			num=num+1;
		}
	}
	int subpage=0;
	if (page->rows[0]!=NULL) subpage=de_hamm8_16(page->rows[0]+4) & 0x3f7f;
	zip_source_t *source=zip_source_buffer(ap->zipfile, buffer, size, 1);
	char filename[16];
	memset(filename, 0, sizeof(filename));
	snprintf(filename, sizeof(filename)-1, "%03x-%04x.t42", pageno, subpage);
	zip_uint64_t fileno=zip_file_add(ap->zipfile, filename, source, ZIP_FL_OVERWRITE | ZIP_FL_ENC_UTF_8);
	zip_set_file_compression(ap->zipfile, fileno, ZIP_CM_STORE, 0);
	/*struct tm *bdt=gmtime(&(page->last_change));
	int dos_date=(bdt->tm_mday+1) | ((bdt->tm_mon+1)<<5) | ((bdt->tm_year+1900-1980) <<9);
	int dos_time=(bdt->tm_sec/2) | ((bdt->tm_min)<<5) | (bdt->tm_hour<<11);
	zip_file_set_dostime(ap->zipfile, fileno, dos_time, dos_date, 0);*/
	zip_file_set_mtime(ap->zipfile, fileno, page->last_change, 0);
	return cnt;
}

int pageno_to_num(const uint16_t pageno)
{
	if (pageno<0x100) return pageno|0x800;
	return pageno;
}

int add_packet_to_mainpage(all_pages_t *ap, mainpage_t *page, const uint8_t row, const uint16_t subcode,  const uint8_t *data)
{
	if (page==NULL) return -1;
	if (row>=32) return -1;
	if (data==NULL) return -1;
	int sc1=(subcode    )&0xf;
	int sc2=(subcode>> 4)&0x7;
       	int sc3=(subcode>> 8)&0xf;
	int sc4=(subcode>>12)&0x3;
	int spn=sc1+sc2*10+sc3*80+sc4*1000;
	if (spn>=SUBPAGENUM) spn=0;
	if (page->subpages[spn]==NULL) {
		gettimeofday(&ap->last_change, NULL);
		if (spn>page->maxsubcode) page->maxsubcode=spn;
		page->subpages[spn]=malloc(sizeof(page_t));
		memset(page->subpages[spn], 0, sizeof(page_t));
	}
	return add_packet_to_page(page->subpages[spn], row, data);
}

/*returns >1 if the page was fully received including all sub pages
 * 1 unclear if page has been fully received
 * 0 page has not been fully received
 */
int mainpage_done(const mainpage_t *page)
{
	if (page==NULL) return 2;
	if ((page->number&0x0ff)>0x99) return 2; //If page is not a real page, it's full
	//If this is a single page, return
	if (page->subpages[0]!=NULL) return page->subpages[0]->cnt;
	//Count the highest yet received subpage
	int msp=-1;
	for (int n=1; n<SUBPAGENUM; n++) if (page->subpages[n]!=NULL) msp=n;
	int fsn=0;
	for (int n=1; n<=msp; n++) { //Cound subpages with more than 10 captures
		if (page->subpages[n]!=NULL) {
			if (page->subpages[n]->cnt>10) fsn=fsn+1;
		}
	}
	if (fsn>msp/2) return 2; //If there are more than half the subpages with more than 10 caputres, we are fine
	int maxcnt=1;
	for (int n=1; n<=msp; n++) {
		if (page->subpages[n]==NULL) {
			return -1; //Obviously not all pages have been found
		}
		if (page->subpages[n]->cnt>maxcnt) maxcnt=page->subpages[n]->cnt;
	}
	return maxcnt;
}

void mainpage_done_fraction(const mainpage_t *page, int *expected, int *count)
{
	if (page==NULL) return;
	if (expected==NULL) return;
	if (count==NULL) return;
	if ((page->number&0x0ff)>0x99) return ; //If page is not a real page, it's full
	if (page->subpages[0]!=NULL) { //Subpage 0000
		*expected=*expected+1;
		*count=*count+1;
		return;
	}
	//Count the highest yet received subpage
	int msp=-1;
	for (int n=1; n<SUBPAGENUM; n++) if (page->subpages[n]!=NULL) msp=n;
	if (msp<=0) return;
	int cnt=0;
	for (int n=1; n<=msp; n++) { //Count up to msp
		if (page->subpages[n]!=NULL) cnt=cnt+1;
	}
	*expected=*expected+msp;
	*count=*count+cnt;
}

int write_mainpage(all_pages_t *ap, const mainpage_t *page, const int mainpage)
{
	if (page==NULL) return 0;
	int cnt=0;
	for (int n=0; n<SUBPAGENUM; n++) {
		if (page->subpages[n]!=NULL) {
			cnt=cnt+write_page(ap, mainpage, page->subpages[n]);
		}
	}
	return cnt;
}

int count_packets_in_mainpage(const mainpage_t *page)
{
	if (page==NULL) return 0;
	int cnt=0;
	int n;
	for (n=0; n<SUBPAGENUM; n++) {
		if (page->subpages[n]!=NULL) {
			int m;
			for (m=0; m<RCNT; m++) if (page->subpages[n]->rows[m]!=NULL) cnt=cnt+1;
		}
	}
	return cnt;
}


int add_packet_to_pages_(all_pages_t *p, const uint8_t row, const int page, const int subcode, const uint8_t *data)
{
	if (p==NULL) return -1;
	if (row>32) return -1;
	if (page>=0x800) return -1;
	if (page<0) return -1;
	if (subcode<0) return -1;
	if (p->pages[page]==NULL) {
		p->pages[page]=malloc(sizeof(mainpage_t));
		memset(p->pages[page], 0, sizeof(mainpage_t));
		p->pages[page]->number=page;
	}
	return add_packet_to_mainpage(p, p->pages[page], row, subcode, data);
}


int add_packet_to_pages(all_pages_t *p, const uint8_t row, const int fullpageno, const uint8_t *data)
{
	int page=(fullpageno>>16);
	if (page>0x800) return -1;
	int subc=fullpageno&0x3f7f;
	if (row==0) {
		p->last_pageno=page;
		for (int n=0; n<32; n++) {
			uint8_t c=(data[n+10] & 0x7f);
			if (c<' ') c=' ';
			if (c>=0x7f) c=' ';
			p->last_header[n]=c;
		}
		p->last_header[32]=0;
	}
	if (row==29) return add_packet_to_pages_(p, row, page | 0xff, 0, data);
	if (row>29) return -1;
	if ((page&0xff)==0xff) return add_packet_to_pages_(p, row, page , 0, data);
	return add_packet_to_pages_(p, row, page, subc, data);
}


/*returns >1 if the page was fully received including all sub pages
 * 1 unclear if page has been fully received
 * 0 page has not been fully received
 */
int allpages_done(all_pages_t *p)
{
	if (p==NULL) return 0;
	struct timeval now;
	gettimeofday(&now, NULL);
	int tdiff=now.tv_sec-p->last_change.tv_sec;
	if (tdiff<10) return 0; 
	if (tdiff>60*5) return 2;
	int expected=0;
	int count=0;
	allpages_done_fraction(p, &expected, &count);
	if ((count<10) && (tdiff>120)) { //Special handling for empty services
		return 2;
	}
	if  ( (count==expected) && (tdiff>60*2) ) return 2; //If we think we have all pages, quit after a minute
	int missing=0;
	int cnt=0;
	int n;
	for (n=0; n<PAGENUM; n++){
		if (p->pages[n]!=NULL) {
			cnt=cnt+1;
			int res=mainpage_done(p->pages[n]);
			if (res<2) {
				if (missing==0) {
					missing=1;
				} else if (missing>15) {
					return 0;
				} else {
					missing=missing+1;
				}
			}
		}
	}
	if (missing>0) {
		return 0;
	}
	return 2;
}

void allpages_done_fraction(all_pages_t *p, int *expected, int *count)
{
	if (p==NULL) return;
	if (expected==NULL) return;
	if (count==NULL) return;
	for (int n=0; n<PAGENUM; n++) {
		if (p->pages[n]!=NULL) {
			mainpage_done_fraction(p->pages[n], expected, count);
		}
	}
}


int write_all_pages(all_pages_t *p)
{
	if (p==NULL) return 0;
	int cnt=0;
	print_line_prefix();
	printf("    ");
	for (int n=0; n<PAGENUM; n++) {
		int pn=(n+0x100)&0x7ff;
		int c=count_packets_in_mainpage(p->pages[pn]);
		cnt=cnt+c;
	}

	if (cnt<=0) return 0;
	printf("File '%s', header: '%s' ...", p->name, p->last_header);
	int err=0;
	p->zipfile=zip_open(p->name, ZIP_CREATE | ZIP_EXCL, &err);
	if (p->zipfile==NULL) {
		zip_error_t error;
		zip_error_init_with_code(&error, err);
		printf("cannot open zip archive: %s\n", zip_error_strerror(&error));
		zip_error_fini(&error);
		return -1;	
	}	
	cnt=0;
	for (int n=0; n<PAGENUM; n++) {
		int pn=(n+0x100)&0x7ff;
		int pagenumber=(n+0x100);
		if (p->pages[pn]!=NULL) {
			cnt=cnt+write_mainpage(p, p->pages[pn], pagenumber);
		}
	}
	zip_close(p->zipfile);
	printf(" %d datasets written\n", cnt);
	char *hfn=NULL;
	asprintf(&hfn, "%s.txt", p->name);
	FILE *f=fopen(hfn, "w");
	fprintf(f,"%s", p->last_header);
	fclose(f);
	free(hfn);
	return cnt;
}

all_pages_t *new_allpages(const char *name)
{
	all_pages_t *p=malloc(sizeof(all_pages_t));
	if (p==NULL) return NULL;
	memset(p, 0, sizeof(all_pages_t));
	int n;
	for (n=0; n<8; n++) p->pageno[n]=0x7fffffff;
	p->name=malloc(strlen(name)+1);
	strcpy(p->name, name);
	gettimeofday(&p->last_change, NULL);
	p->status_line=-1;
	return p;
}

int finish_allpages(all_pages_t *p)
{
	//so_end();
	int cnt=write_all_pages(p);
	free(p);
	return cnt;
}

int handle_t42_data(all_pages_t *p, const uint8_t *line)
{
	if (p==NULL) return 0;
	if (line==NULL) { //Allow for page number to be reset on problem
		for (int m=0; m<8; m++) p->pageno[m]=0x7fffffff;
		return 0;
	}

	int mpag=de_hamm8_8(line);
	if (mpag<0) return -1;
	int magazine=mpag&0x07;
	int row=mpag>>3;

	int fullpageno=p->pageno[magazine];

	if (row==0) { //Header row	
		int pn=de_hamm8_8(line+2);
		if (pn<0) return -1;
		int subpage=de_hamm8_16(line+4);
		if (subpage<0) return -1;
		if (pn==0xff) subpage=0;
		fullpageno=(magazine<<24) | (pn<<16) | subpage;
		p->pageno[magazine]=fullpageno;
	}

	if ((row==30) && (magazine=0)) {
		memcpy(p->last_bsdp, line, 42);
		p->bsdp_cnt=p->bsdp_cnt+1;
		return add_packet_to_pages_(p, row, 0x0ff, 0, line); //Store Broadcast Service Data Packet
	}

	int page=(fullpageno>>16);
	if (page>0x800) return -1;
	return add_packet_to_pages(p, row, fullpageno, line);
}

