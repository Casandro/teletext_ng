#include <stdio.h>
#include <stdint.h>
#include "hamming.h"
#include "page.h"
#include <string.h>
#include "pes_handler.h"

#define PLEN (42)


void printbin(uint8_t b)
{
	int n;
	for (n=7; n>=0; n--) {
		if ((b&(1<<n))!=0) printf("1"); else printf("0");
	}
}

int shorten_subpage(int sp)
{
	int s4=(sp>>12)&0x03;
	int s3=(sp>>8) &0x0f;
	int s2=(sp>>4) &0x07;
	int s1=(sp>>0) &0x0f;
	return (s1) | (s2<4) | (s3<7) | (s4<9);
}




int main(int argc, char *argv[])
{
	int mode=0;
	int stop=0;
	int n;
	for (n=1; n<argc; n++){
		if (strcasecmp(argv[n], "--TS")==0) mode=1;
		if (strcasecmp(argv[n], "--T42")==0) mode=2;
		if (strcasecmp(argv[n], "--STOP")==0) stop=1;
	}
	if (mode==0) {
		printf("Usage: %s \n\t--t42 stdin is a T42 stream\n\t--ts stdin is a DVB transport stream\n\t--stop stop executing after full service has been decoded\n", argv[0]);
	}
	if (mode==2) { //Handle a T42 file
		uint8_t line[42];
		all_pages_t *ap=new_allpages("out");
		while (fread(line, sizeof(line),1 ,stdin)>0) {
			handle_t42_data(ap, line);
		}
		int cnt=finish_allpages(ap);
		printf("%d datasets written\n", cnt);
		return 0;
	}
	int cnt=0;
	if (mode==1) { //Handle a TS file
		uint8_t packet[188];
		while (fread(packet, sizeof(packet),1 ,stdin)>0) {
			cnt=cnt+1;
			process_ts_packet(packet);
			if ((cnt>10000) && (stop==1) && (are_pes_handlers_done()==1) ) break;
		}
		finish_ts_packets();
	}
}
