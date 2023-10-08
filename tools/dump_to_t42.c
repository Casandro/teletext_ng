#include <stdio.h>
#include <stdint.h>
#include <string.h>


#define PAGENUM (0x800)

int hexdigit_to_int(const char c)
{
	if ((c>='0') && (c<='9')) return c-'0';
	if ((c>='A') && (c<='F')) return c-'A'+10;
	if ((c>='a') && (c<='f')) return c-'a'+10;
	return -1;
}

int get_number(const char *s)
{
	int a=hexdigit_to_int(s[0])-1;
	if (a<0) return a;
	int b=hexdigit_to_int(s[1]);
	if (b<0) return b;
	int c=hexdigit_to_int(s[2]);
	if (c<0) return c;
	int r=(a<<8) | (b<<4) | c;
	if (r>=PAGENUM) return -1;
	return r;
}

int dump_page(const int pn, const int16_t *index, FILE *f)
{
	if (index==NULL) return -1;
	if (f==NULL) return -1;
	if (pn>=PAGENUM) return -1;
	int start=0;
	int n;
	for (n=0; n<pn; n++) start=start+index[n];
	if (fseek(f, PAGENUM*2+start*42, SEEK_SET)!=0) {
		fprintf(stderr, "Couldn't seek\n");
		return -1;
	}
	for (n=0; n<index[pn]; n++) {
		uint8_t line[42];
		if (fread(line, sizeof(line), 1, f)<1) {
			fprintf(stderr, "Couldn't read\n");
			return -1;
		}
		fwrite(line, sizeof(line), 1, stdout);
	}
	return index[pn];
}


int main(int argc, char *argv[])
{
	if (argc<2) {
		printf("Usage: %s <.ttp-file> (<page specification>)\n", argv[0]);
		return 0;
	}
	int want_page[PAGENUM];
	memset(want_page, 0, sizeof(want_page));
	int n;
	if (argc==2) {
		for (n=0; n<PAGENUM; n++) want_page[n]=1;
	}
	for (n=2; n<argc; n++) {
		char *s=argv[n];
		int l=strlen(s);
		if (l==3) {
			int pnum=get_number(s);
			if ((pnum<0)) {
				fprintf(stderr, "Invalid pagespec %s\n", s);
				return 1;
			}
			want_page[pnum]=1;
			want_page[pnum|0xff]=1; //Also dump magazine local pages
		} else
		if ( (l==4) && (s[0]=='!')) {
			int pnum=get_number(s+1);
			if ((pnum<0)) {
				fprintf(stderr, "Invalid pagespec %s\n", s);
				return 1;
			}
			want_page[pnum]=0;
		} else 
		if ( (l==7) && (s[3]=='-') ) {
			int a=get_number(s);
			int b=get_number(s+4);
			if ((a<0) || (b<0)) {
				fprintf(stderr, "Invalid pagespec %s\n", s);
				return 1;
			}
			for (n=a; n<=b; n++) {
				want_page[n]=1;
				want_page[n|0xff]=1;
			}
		}
	}
	FILE *f=fopen(argv[1], "r");
	if (f==NULL) {
		fprintf(stderr,"Couldn't open file %s\n", argv[1]);
		return 1;
	}
	int16_t index[PAGENUM];
	if (fread(index, sizeof(index),1, f)<1) {
		fprintf(stderr, "Couldn't read index\n");
	}
	int m;
	for (m=0; m<8; m++) {
		if (want_page[m<<8|0xff]!=0) dump_page(m<<8|0xff, index, f);
		for (n=0; n<0xfe; n++) if (want_page[m<<8|n]!=0) dump_page(m<<8|n, index, f);
	}
	fclose(f);
}
