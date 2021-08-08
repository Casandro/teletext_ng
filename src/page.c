#include "page.h"
#include "hamming.h"
#include <stdlib.h>
#include <string.h>



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
	memcpy(page->rows[extrow], data, 42);
	if (row==0) page->cnt=page->cnt+1;
	return 0;
}

int write_page(const page_t *page, FILE *f)
{
	if (page==NULL) return 0;
	if (f==NULL) return 0;
	int cnt=0;
	int n;
	for (n=0; n<RCNT; n++) {
		if (page->rows[n]!=NULL) {
			fwrite(page->rows[n], 42, 1, f);
			cnt=cnt+1;
		}
	}
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
	int spn=sc1+sc2*10+sc3*100+sc4*1000;
	if (spn>=SUBPAGENUM) spn=0;
	if (page->subpages[spn]==NULL) {
		gettimeofday(&ap->last_change, NULL);
		if (spn>page->maxsubcode) page->maxsubcode=spn;
		printf("New Page: %03x-%04x ", pageno_to_num(page->number), subcode);
		int n;
		for (n=10; n<42; n++) if ((data[n]&0x7f)<' ') printf(" "); else printf("%c", data[n]&0x7f);
		printf(" ");
		int m;
		for (m=0; m<page->maxsubcode; m++) {
			if (page->subpages[m]==NULL) {
				if (m==spn) printf("|"); else printf("."); 
			}else {
				if (page->subpages[m]->cnt>9) printf("X"); 
				else printf("%d", page->subpages[m]->cnt);
			}
		}
		printf("\n");
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
	//If this is a single page, return
	if (page->subpages[0]!=NULL) return page->subpages[0]->cnt;
	//Count the highest yet received subpage
	int msp=-1;
	int n;
	for (n=1; n<SUBPAGENUM; n++) if (page->subpages[n]!=NULL) msp=n;
	int maxcnt=1;
	for (n=1; n<=msp; n++) {
		if (page->subpages[n]==NULL) {
			return -1; //Obviously not all pages have been found
		}
		if (page->subpages[n]->cnt>maxcnt) maxcnt=page->subpages[n]->cnt;
	}
	return maxcnt;
}

int write_mainpage(const mainpage_t *page, FILE *f)
{
	if (f==NULL) return 0;
	if (page==NULL) return 0;
	int cnt=0;
	int n;
	for (n=0; n<SUBPAGENUM; n++) {
		if (page->subpages[n]!=NULL) {
			cnt=cnt+write_page(page->subpages[n], f);
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
	if (row==29) return add_packet_to_pages_(p, row, page | 0xff, 0, data);
	if (row>29) return -1;
	if ((page&0xff)==0xff) return add_packet_to_pages_(p, row, page , 0, data);
	return add_packet_to_pages_(p, row, page, subc, data);
}


/*returns >1 if the page was fully received including all sub pages
 * 1 unclear if page has been fully received
 * 0 page has not been fully received
 */
int allpages_done(const all_pages_t *p)
{
	if (p==NULL) return 0;
	struct timeval now;
	gettimeofday(&now, NULL);
	int tdiff=now.tv_sec-p->last_change.tv_sec;
	printf("Last change %d s ago\n", tdiff);
	if (tdiff<10) return 0; 
	if (tdiff>60*5) return 2;
	int cnt;
	int n;
	for (n=0; n<PAGENUM; n++){
		if (p->pages[n]!=NULL) {
			cnt=cnt+1;
			int res=mainpage_done(p->pages[n]);
			if (res<2) {
				return 0;
			}
		}
	}
	return 2;
}


int write_all_pages(const all_pages_t *p)
{
	if (p==NULL) return 0;
	int cnt=0;
	int n;
	int16_t index[PAGENUM];
	printf("    ");
	for (n=0; n<PAGENUM; n++) {
		int pn=(n+0x100)&0x7ff;
		int c=count_packets_in_mainpage(p->pages[pn]);
		index[n]=c;
		cnt=cnt+c;
	}

	if (cnt<=0) return 0;
	printf("File '%s' ...", p->name);
	FILE *f=fopen(p->name, "w");
	if (f==NULL) return 0;
	fwrite(index, sizeof(index) ,1 , f);
	cnt=0;
	for (n=0; n<PAGENUM; n++) {
		int pn=(n+0x100)&0x7ff;
		if (p->pages[pn]!=NULL) {
			cnt=cnt+write_mainpage(p->pages[pn], f);
		}
	}
	fclose(f);
	printf(" %d datasets written\n", cnt);
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
	return p;
}

int finish_allpages(all_pages_t *p)
{
	int cnt=write_all_pages(p);
	free(p);
	return cnt;
}

int handle_t42_data(all_pages_t *p, const uint8_t *line)
{
	if (p==NULL) return 0;
	if (line==NULL) return 0;

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

	int page=(fullpageno>>16);
	if (page>0x800) return -1;
	return add_packet_to_pages(p, row, fullpageno, line);
}

