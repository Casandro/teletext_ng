#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
#include<stdint.h>
#include<string.h>
#include<strings.h>

#define ROWCNT (26)
#define COLCNT (40)

#define BIT(x, y) ((x>>y)&0x1)
int de_hamm(uint8_t x)
{
	return BIT(x,1) | (BIT(x,3)<<1) | (BIT(x,5)<<2) | (BIT(x,7)<<3);
}


uint8_t rev(uint8_t b)
{
	return  BIT(b,0)<<7 | BIT(b,1)<<6 | BIT (b,2)<<5 | BIT(b,3)<<4 |
		BIT(b,4)<<3 | BIT(b,5)<<2 | BIT (b,6)<<1 | BIT(b,7);
}



#define HLEN (33)


int main(int argc, char *argv[])
{
	int stat[96][HLEN];
	memset(stat, 0, sizeof(stat));
	uint8_t packet[42];
	while (fread(packet, 1,sizeof(packet), stdin)>0) {
		int mpag=de_hamm(packet[1])<<4 | de_hamm(packet[0]);
		int magazine=mpag&0x7;
		int row=mpag>>3;
		int start=2;
		if (row==0) {
			int page=de_hamm(packet[3])<<4 | de_hamm(packet[2]);
			if (page==0xff) continue;
			int sub=(de_hamm(packet[4])) | (de_hamm(packet[6])<<4) | (de_hamm(packet[6])<<8) | (de_hamm(packet[7])<<12);
			int con=de_hamm(packet[8])| (de_hamm(packet[9])<<4);
			int control=(con)<<16 | (sub&0xc080);
			int subpage=sub&0x3f7f;
			int fullpage=magazine<<8|page;
			int n;
			for (n=0; n<HLEN; n++) {
				char c=(packet[n+10]&0x7f);
				int x=c-' ';
				if (x<0) x=0;
				if (x>=96) x=0;
				stat[x][n]=stat[x][n]+1;
			}
		}
	}
	char name[HLEN+1];
	memset(name, 0, sizeof(name));
	int col=0;
	for (col=0; col<HLEN; col++) {
		int max=-1;
		int n;
		for (n=0; n<96; n++) {
			if ( (max<0) || (stat[max][col]<stat[n][col])) max=n;
		}
		name[col]=max+' ';
	}
	printf("%s\n", name);
}
