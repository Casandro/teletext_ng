#include "pes_handler.h"
#include <stdlib.h>
#include <string.h>

#include "page.h"
#include "hamming.h"

#define PIDNUM (0x2000)

#define PESHSIZE (64*1024)

#define TSSIZE (188)

typedef struct {
	int pid;
	all_pages_t *ap;
	uint8_t pes[PESHSIZE];
	int write_pointer;
	int continuity_counter;
} pes_handler_t;

pes_handler_t *pes_handler[PIDNUM]={NULL};


pes_handler_t *new_pes_handler(const int pid)
{
	pes_handler_t *ph=malloc(sizeof(pes_handler_t));
	if (ph==NULL) return NULL;
	memset(ph, 0, sizeof(pes_handler_t));
	ph->pid=pid;
	ph->write_pointer=-1;
	return ph;
}

void handle_pes(pes_handler_t *p)
{
	if (p->write_pointer<0) return;
	p->write_pointer=-1;
	uint8_t *d=p->pes;
	
	int startcode=(d[0]<<24) | (d[1]<<16) | (d[2]<<8) | d[3];
	if ((startcode&0xffffff00)!=0x0100) return;
	//int stream_id=startcode&0xff;
	int size=((d[4]<<8) | d[5])+6;

	//int marker_bits=d[6]>>6;
	//int scrambling_control=(d[6]>>4)&0x3;
	int pes_header_length=d[8];
	int pes_header_end=pes_header_length+8;

	int pes_data_start=pes_header_end+1;
	int data_identifier=d[pes_data_start];
	if ((data_identifier&0xf0)!=0x10) return;
	int linecnt=(size-(pes_data_start+1))/46;
	int cnt=0;
	int n;
	for (n=0; n<linecnt; n++) {
		int po=pes_data_start+1+n*46;
		int data_unit_id= (d[po]);
		int data_unit_len=(d[po+1]);
		if ( (data_unit_id!=0x02) && (data_unit_id!=0x03) ) continue;
		if (data_unit_len!=0x2c) continue;
		//int line_offset=d[po+2];
		int framing_code=d[po+3];
		if (framing_code!=0xe4) continue;
		if (p->ap==NULL) {
			char name[16];
			snprintf(name, sizeof(name), "0x%04x.tta", p->pid);
			p->ap=new_allpages(name);
			printf("New service %s\n", name);
		}
		uint8_t line[42];
		int m;
		for (m=0; m<42; m++) line[m]=rev(d[po+4+m]);
		int res=handle_t42_data(p->ap, line);
		if (res==0) cnt=cnt+1;
	}
}

int process_ts_packet(const uint8_t *buf)
{
	int n;
	uint32_t header=buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3];
	int sync=(header>>24) & 0xff;
	if (sync!=0x47) return 0;
	int transport_error_indicator=(header >> 23) & 0x1;
	if (transport_error_indicator==1) return 0;
	int payload_unit_start_indicator=(header >> 22) & 0x1;
	//int transport_priority=(header >> 21) &0x1;
	int pid=(header >> 8) & 0x1fff;
	int transport_scrambling_control=(header >>6) &0x3;
	if (transport_scrambling_control!=0) return 0;
	//int adaption_field_control=(header >> 4) & 0x3;
	int continuity_counter=(header >>0) & 0xf;
	if (pes_handler[pid]==NULL) {
		if (payload_unit_start_indicator==1) pes_handler[pid]=new_pes_handler(pid);
	}
	if (pes_handler[pid]==NULL) return 0;

	if (pes_handler[pid]->continuity_counter!=continuity_counter) {
		pes_handler[pid]->write_pointer=-1;
		pes_handler[pid]->continuity_counter=(continuity_counter+1)&0x0f;
		return 0;
	}
	pes_handler[pid]->continuity_counter=(continuity_counter+1)&0x0f;

	if (payload_unit_start_indicator==1) {
		//handle possible previous packet
		handle_pes(pes_handler[pid]);
		//Check if packet is plausible
		uint32_t start_code=(buf[4]<<24) | (buf[5]<<16) | (buf[6]<<8) | buf[7];
		if (start_code!=0x000001bd) {
			pes_handler[pid]->write_pointer=-1;
			return 0;
		}
		//packet is a plausible start packet
		pes_handler[pid]->write_pointer=0;
	}
	//Not during a PES
	if (pes_handler[pid]->write_pointer<0) return 0;
	for (n=4; n<TSSIZE; n++) {
		pes_handler[pid]->pes[pes_handler[pid]->write_pointer]=buf[n];
		pes_handler[pid]->write_pointer=(pes_handler[pid]->write_pointer+1)&0xffff;
	}
	return 0;
}

void finish_ts_packets()
{
	int n;
	for (n=0; n<PIDNUM; n++) {
		if(pes_handler[n]!=NULL) {
			finish_allpages(pes_handler[n]->ap);
			pes_handler[n]->ap=NULL;
		}
	}
}

int is_pes_handler_done(pes_handler_t *p)
{
	if (p==NULL) return 1;
	if (p->ap==NULL) return 1;
	if (allpages_done(p->ap)>1) return 1;
	return 0;
}

int are_pes_handlers_done()
{
	int n;
	for (n=0; n<PIDNUM; n++) {
		if (is_pes_handler_done(pes_handler[n])==0) return 0;
	}
	return 1;
}
