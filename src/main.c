#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "hamming.h"
#include "page.h"
#include <string.h>
#include "pes_handler.h"
#include <sys/select.h>
#include <sys/types.h>
#include <signal.h>
#include <unistd.h>

#include "consts.h"

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
	FILE *input=stdin;
	char *lockfile=NULL;
	char *prefix=NULL;
	char *blockpids=NULL;
	char *statusfile=NULL;
	for (n=1; n<argc; n++){
		if (strcasecmp(argv[n], "--TS")==0) mode=1; else
		if (strcasecmp(argv[n], "--T42")==0) mode=2; else
		if (strcasecmp(argv[n], "--STOP")==0) stop=1; else
		if (strncmp(argv[n], "-p", 2)==0) prefix=argv[n]+2; else
		if (strncmp(argv[n], "-b", 2)==0) blockpids=argv[n]+2; else
		if (strncmp(argv[n], "-s", 2)==0) statusfile=argv[n]+2; else
		if (strncmp(argv[n], "-l", 2)==0) lockfile=argv[n]+2; else
		{
			printf("Trying file %s\n", argv[n]);
			FILE *f=fopen(argv[n],"r");
			if (f!=NULL) {
				printf("Using file %s\n", argv[n]);
				input=f;
			}
		}
	}
	if (mode==0) {
		printf("Usage: %s \n\t--t42 stdin is a T42 stream\n\t--ts stdin is a DVB transport stream\n\t--stop stop executing after full service has been decoded\n\t-p<prefix> directory to send output to\n\t-b<list> list of PIDs to ignore\n\t-l<lockfile> lockfile\n\t-s<statusfile> writes the current status into this file on SIGUSR1", argv[0]);
	}
	if (mode==2) { //Handle a T42 file
		uint8_t line[42];
		all_pages_t *ap=new_allpages("out.zip");
		while (fread(line, sizeof(line),1 ,input)>0) {
			handle_t42_data(ap, line);
		}
		int cnt=finish_allpages(ap);
		printf("%d datasets written\n", cnt);
		return 0;
	}
	int cnt=0;
	if (mode==1) { //Handle a TS file
		int8_t pids_enabled[PIDNUM];
		for (int n=0; n<PIDNUM; n++) pids_enabled[n]=1;
		if (blockpids!=NULL && strcmp(blockpids,"NULL")!=0) {
			printf("Blockpids: %s\n", blockpids);
			//todo: parse blockpids
			//Set pids_enabled to 0 for those pids
			char *p=blockpids;
			while (*p!=0) {
				char *endptr=NULL;
				int pid=strtol(p,&endptr,10);
				if ((pid<0) || (pid>=4096)) {
					printf("Invalid PID %s (%s)\n", p, blockpids);
					continue;
				} else {
					pids_enabled[pid]=0;
					printf("ignoring PID: %d\n", pid);
				}
				if (*endptr==0) p=endptr; else p=endptr+1;
			}
		}	
		FILE *f=NULL;
		int pktcnt=0;
		uint8_t packet[188];
		while (fread(packet, sizeof(packet),1 ,input)>0) {
			if ((f==NULL) && (lockfile!=NULL)) f=fopen(lockfile, "w");
			if ( (f!=NULL) && (cnt%1000==0)) fprintf(f,"%d\n", cnt);
			cnt=cnt+1;
			int pid=ts_get_pid(packet);
			if (pid<0) continue;
			if (pids_enabled[pid]==0) continue;
			pktcnt=pktcnt+1;
			process_ts_packet(packet, prefix, statusfile);
			if (cnt>100000) {
				cnt=0;
				if ((stop==1) && (are_pes_handlers_done()==1) ) {
					printf("finishing\n");
					break;
				}
			}
		}
		printf("%d packets processed\n", pktcnt);
		finish_ts_packets();
		if (f!=NULL) fclose(f);
		if (lockfile!=NULL) unlink(lockfile);
	}

	return 0;
}
