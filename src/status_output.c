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
