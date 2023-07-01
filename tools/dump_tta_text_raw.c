#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>
#include<stdint.h>
#include<string.h>
#include<strings.h>

#define PLEN 46

#define BIT(x, y) ((x>>y)&0x1)
int de_hamm(uint8_t x)
{
	return BIT(x,1) | (BIT(x,3)<<1) | (BIT(x,5)<<2) | (BIT(x,7)<<3);
}


void print_bin(uint8_t x)
{
	for (int n=0; n<8; n++) printf("%d", BIT(x,n));
}

int de_hamm_2418(uint8_t x[])
{
	return  (BIT(x[0],2)    ) | (BIT(x[0],4)<<1 ) | (BIT(x[0],5)<<2 ) | (BIT(x[0],6)<<3 ) |
		((int)x[1]&0x7f) <<4 | ((int)x[2]&0x7f) << 11; 
}

int decode_mbcd(const uint8_t x)
{
	int a=(x>>4) -1;
	if (a<0) return -1;
	int b=(x&0xf) -1;
	if (b<0) return -1;
	return a<<4 | b;
}

uint8_t rev(uint8_t b)
{
	return  BIT(b,0)<<7 | BIT(b,1)<<6 | BIT (b,2)<<5 | BIT(b,3)<<4 |
		BIT(b,4)<<3 | BIT(b,5)<<2 | BIT (b,6)<<1 | BIT(b,7);
}

void skip_header()
{
	uint8_t header[4096];
	fread(header, 1,sizeof(header), stdin);
}

const char *vd_glyph_to_utf8[0x100]={
	//      x0   x1   x2   x3   x4   x5   x6   x7   x8   x9   xA   xB   xC   xD   xE   xF
      /*0x */	" ", "!","\"", "#", "¤", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/",
      /*1x */	"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?",
      /*2x */	"@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O",
      /*3x */	"P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[","\\", "]", "^", "_",
      /*4x */	"`", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
      /*5x */	"p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~", "■",
      /*6x */	" ", "🬀", "🬁", "🬂", "🬃", "🬄", "🬅", "🬆", "🬇", "🬈", "🬉", "🬊", "🬋", "🬌", "🬍", "🬎",
      /*7x */	"🬏", "🬐", "🬑", "🬒", "🬓", "▌", "🬔", "🬕", "🬖", "🬗", "🬘", "🬙", "🬚", "🬛", "🬜", "🬝",
      /*8x */	"🬞", "🬟", "🬠", "🬡", "🬢", "🬣", "🬤", "🬥", "🬦", "🬧", "▐", "🬨", "🬩", "🬪", "🬫", "🬬",
      /*9x */	"🬭", "🬮", "🬯", "🬰", "🬱", "🬲", "🬳", "🬴", "🬵", "🬶", "🬷", "🬸", "🬹", "🬺", "🬻", "█",
      /*Ax */	"#", "¤", "@", "[", "\\","]", "^", "_", "{", "|", "}", "~", " ", " ", " ", " ", //English
      /*Bx */   "#", "$", "§", "Ä", "Ö", "Ü", "^", "_", "°", "ä", "ö", "ü", "ß", " ", " ", " ", //German
      /*Cx */   "#", "¤", "É", "Ä", "Ö", "Å", "Ü", "_", "é", "ä", "ö", "å", "ü", " ", " ", " ", //Swedish/Finnish/Hungarian 
      /*Dx */   "£", "$", "é", "°", "ç", "→", "↑", "#", "ù", "à", "ò", "è", "ì", " ", " ", " ", //Italian
      /*Ex */   "é", "ï", "à", "ë", "ê", "ù", "î", "#", "è", "â", "ô", "û", "ç", " ", " ", " ", //French
      /*Fx */   "ç", "$", "¡", "á", "é", "í", "ó", "ú", "¿", "ü", "ñ", "è", "à", " ", " ", " "  //Portuguese/Spanish
};

const char *viewdata_glyph_to_utf8(const int glyph)
{
	if (glyph<0) return NULL;
	if (glyph>0xff) return NULL;
	return vd_glyph_to_utf8[glyph];
}

void set_colour(int bg, int colour)
{
	if (bg<0) return;
	if (bg>1) return;
	if (colour<0) return;
	if (colour>7) return;
	int b=(bg)*10+colour+30;
	printf("\x1b[%dm", b);
}

void print_line(const uint8_t line[], const size_t len, const int language)
{
	set_colour(1, 0);
	set_colour(0, 7);
	int colour=7;
	int mosaik=0;
	for (int n=0; n<len; n++){
		uint8_t c=line[n]&0x7f;
		int glyph=0;
		if (c<0x20) {
			if ((c&0xf)>=0 && (c&0xf)<=0x07) { //Alpha colour
				colour=c&0x07;
				set_colour(0,colour);
			}
			if (c>=0x0 && c<=0x07) { //Alpha colour
				mosaik=0;
			}
			if (c>=0x10 && c<=0x17) { //Alpha colour
				mosaik=1;
			}
			if (c==0x1c) {
				set_colour(1,0); //Black background
			}
			if (c==0x1d) {
				set_colour(1, colour);//New background
			}
		}


		if (c>=0x20) {
			if (mosaik==0) {
				glyph=c-0x20; 
				if (c==0x23) glyph=0xA0+language*0x10;
				if (c==0x24) glyph=0xA1+language*0x10;
				if (c==0x40) glyph=0xA2+language*0x10;
				if (c==0x5B) glyph=0xA3+language*0x10;
				if (c==0x5C) glyph=0xA4+language*0x10;
				if (c==0x5D) glyph=0xA5+language*0x10;
				if (c==0x5E) glyph=0xA6+language*0x10;
				if (c==0x5F) glyph=0xA7+language*0x10;
				if (c==0x60) glyph=0xA8+language*0x10;
				if (c==0x7B) glyph=0xA9+language*0x10;
				if (c==0x7C) glyph=0xAa+language*0x10;
				if (c==0x7D) glyph=0xAb+language*0x10;
				if (c==0x7E) glyph=0xAc+language*0x10;

			} else {
				if (c>=0x20 && c<=0x3f) glyph=c-0x20+0x60;
				if (c>=0x40 && c<=0x5f) glyph=c-0x20;
				if (c>=0x60 && c<=0x7f) glyph=c-0x60+0x80;
			}
		}
		printf("%s", viewdata_glyph_to_utf8(glyph));
	}
	set_colour(1, 0);
	set_colour(0, 7);
}


const char *diacritics[16]={" ", "acute", "grave", "circumflex", "tilde", "macron", "breve", "overdot", "umlaut", "underdot", "overring", "dedilla", "underbar", "double accute", "caron", "ogonek"};

int main(int argc, char *argv[])
{
	int language=0;
//	skip_header();
	uint8_t packet[42];
	while (fread(packet, 1,sizeof(packet), stdin)>0) {
		int mpag=de_hamm(packet[1])<<4 | de_hamm(packet[0]);
		int magazine=mpag&0x7;
		int row=mpag>>3;
		int start=2;
		printf("%d %02d ", magazine, row);
		if (row==0) {
			int page=de_hamm(packet[3])<<4 | de_hamm(packet[2]);
			int sub=(de_hamm(packet[4])) | (de_hamm(packet[6])<<4) | (de_hamm(packet[6])<<8) | (de_hamm(packet[7])<<12);
			int contr=de_hamm(packet[9])<<4 | de_hamm(packet[8]);
			int subpage=sub&0x3f7f;
			int fullpage=magazine<<8|page;
			if (fullpage<0x100) fullpage=fullpage|0x800;
			printf("%03x-%04x", fullpage, subpage);
			language=(contr>>4) &0x7;
			start=10;
		}
		int n;
		if (row<26) {
			set_colour(1, 0);
			set_colour(0, 7);
			print_line(&(packet[start]), 42-start,language);
		} else if (magazine==3 && row==31) {
			printf("Independent Data Service: ");
			for (int n=2; n<42; n++) printf("%02x", packet[n]);
			printf(" \"");
			for (int n=2; n<42; n++) if (packet[n]<' ' || packet[n]>=0x7f) printf("."); else printf("%c", packet[n]);
			printf("\"");
		} 
		else {
			int dc=de_hamm(packet[2]);
			printf("dc: %01x ",dc);
			if (row==27 && (dc<4)) {
				if (dc==0) printf("FLOF ");
				for (int n=0; n<6; n++) {
					int lst=3+n*6;
					printf("%01x%01x-", de_hamm(packet[lst]),de_hamm(packet[lst+1]));
					printf("%01x%01x%01x%01x ", de_hamm(packet[lst+2]),de_hamm(packet[lst+3]), de_hamm(packet[lst+4]), de_hamm(packet[lst+5]));
				}

			} else 
			if (row==30 && magazine==0 && (dc==0 || dc==1)) { // 30/0
				if (dc==0) printf("multiplexed "); else printf("non multiplexed ");
				int ini_page_unit=de_hamm(packet[3]);
				int ini_page_tens=de_hamm(packet[4]);
				int subcode_1=de_hamm(packet[5]);
				int subcode_2=de_hamm(packet[6]);
				int subcode_3=de_hamm(packet[7]);
				int subcode_4=de_hamm(packet[8]);
				int ini_mag=(subcode_4>>1 & 0xe) | (subcode_2>>3);
				int ini_page=ini_mag<<8 | ini_page_tens<<4 | ini_page_unit;
				int ini_subpage=(subcode_4<<12 | subcode_3<<8 | subcode_2<<4 | subcode_1) & 0x3f7f;
				printf("Initial Page: %03x-%04x ", ini_page, ini_subpage);
				int network_identification_code=de_hamm(packet[9])<<8 | de_hamm(packet[10]);
				printf("Network Identification Code: %04x ", network_identification_code);
				int time_offset_code=packet[11];
				double offset=(time_offset_code & 0x3e)*0.25;
				if (time_offset_code&0x40!=0) offset=-offset;
				printf("Time Offset Code: %02x, %lf hours ", time_offset_code, offset);
				int mjd=decode_mbcd(packet[12]+0x10)<<16 | decode_mbcd(packet[13])<<8 | decode_mbcd(packet[14]);
				printf("Modified Julian Date: %05x ", mjd);
				printf("UTC: %02x:%02x:%02x ", decode_mbcd(packet[15]), decode_mbcd(packet[16]), decode_mbcd(packet[17]));
				printf("Status Display: '");
				for(int n=22; n<42; n++) printf("%c", packet[n]&0x7f); 
				printf("' ");

			} else
			if (row==28 && dc==4) {
				printf("Page specific data Level 3.5");
			} else 
			if (row==26) {
				printf("Page Enhancement Data:\n");
				for (int n=0; n<13; n++) {
					int triplet=de_hamm_2418(packet+3+n*3);
					int address=triplet&0x3f;
					int mode=(triplet>>6) & 0x1f;
					int data=(triplet>>11);
					printf("address: %02x; mode: %02x; data: %02x ", address, mode, data);
					if (address>=40) {
						printf("Row: %d ", address-40);
						if (mode==0x00) printf("Full screen colour: "); else
						if (mode==0x01) printf("Full row Colour: "); else
						if (mode==0x04) printf("Set Active Position: "); else
						if (mode==0x07) printf("Address Display Row 0: "); else
						if (mode==0x08) printf("PDC Country of Origin and Programme Source: "); else
						if (mode==0x09) printf("PDC Month & day: "); else
						if (mode==0x0A) printf("PDC Cursor row and Accounce Starting Time Hours: "); else
						if (mode==0x0B) printf("PDC Cursor row and Accounce Finishing Time Hours: "); else
						if (mode==0x10) printf("Origin Modifier: "); else
						if (mode==0x11 || mode==0x19) printf("Active Object Definition: "); else
						if (mode==0x12 || mode==0x1A) printf("Adaptive Object Definition: "); else
						if (mode==0x13 || mode==0x1B) printf("Passive Object Definition: "); else
						if (mode==0x18) printf("DCRS Mode: "); else
						if (mode==0x1f) printf("Termination Marker: "); else
						printf("reserved/unknown ");
					} else {
						printf("Column: %d ", address);
						if (mode==0x00) printf("Foreground Colour: "); else
						if (mode==0x01) printf("Block Mosaik Character from the G1 set: "); else
						if (mode==0x02) printf("Line drawin or smoothed Mosaik Character from G3 set (1.5): "); else
						if (mode==0x03) printf("Background Color: "); else
						if (mode==0x06) printf("PCD Cursor Column & Announced starting and finishing time minutes: "); else
						if (mode==0x07) printf("Additional flash functions: "); else
						if (mode==0x08) printf("Modified G0 and G2 Character Set Design: "); else
						if (mode==0x09) printf("Character from the G0 set (2.5,3.5): "); else
						if (mode==0x0B) printf("Line drawing or smoothed Mosaik Chracter from G3 set (2.5,3.5): "); else
						if (mode==0x0C) printf("Display attributes: "); else
						if (mode==0x0D) printf("DCRS Character Invocation: "); else
						if (mode==0x0E) printf("Font Stype: "); else
						if (mode==0x0F) printf("Character form the G2 set: "); else
						if ((mode&0x10)!=0) printf("G0 '%c' with %s", data, diacritics[mode&0xf] );
						else printf("reserved/unknown ");
					}
					printf(" %02x\n", data);
					//if (address>=40 && mode==0x1f) break;
				}
				printf("    0000000000111111111122222222223333333333\n");
				printf("    0123456789012345678901234567890123456789");
			} else
			if (row==28 && (dc==0 || dc==3 || dc==4)) {
				int triplet_1=de_hamm_2418(packet+3);
				int page_function=triplet_1&0x0f;
				int page_coding=(triplet_1>>4) &0x07;

				printf("Page specific data: triplet 1:%05x pf: %01x pc: %01x ", triplet_1, page_function, page_coding);
				if (page_function==0x0) printf("LOP "); else
				if (page_function==0x1) printf("Data "); else
				if (page_function==0x2) printf("GPOP "); else
				if (page_function==0x3) printf("POP "); else
				if (page_function==0x4) printf("GDRCS "); else
				if (page_function==0x5) printf("DRCS "); else
				if (page_function==0x6) printf("MOT "); else
				if (page_function==0x7) printf("MIP "); else
				if (page_function==0x8) printf("BTT "); else
				if (page_function==0x9) printf("AIT "); else
				if (page_function==0xA) printf("MPT" ); else
				if (page_function==0xB) printf("MPT-EX "); else printf("reserved ");

				if (page_coding==0x0) printf("7O0 "); else
				if (page_coding==0x1) printf("8n0 "); else
				if (page_coding==0x2) printf("per packet 2 "); else
				if (page_coding==0x3) printf("8->4 "); else
				if (page_coding==0x4) printf("per packet 4 "); else
				if (page_coding==0x5) printf("per packet 5 "); else printf("reserved ");
			}
			else printf("unknown dc: %01x", dc);
		}
		printf("\n");
	}
}
