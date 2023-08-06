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
	printf("\n");
}


int main(int argc, char *argv[])
{
	int language=0;
	skip_header();
	uint8_t packet[42];
	while (fread(packet, 1,sizeof(packet), stdin)>0) {
		int mpag=de_hamm(packet[1])<<4 | de_hamm(packet[0]);
		int magazine=mpag&0x7;
		int row=mpag>>3;
		int start=2;
		//printf("%d %02d ", magazine, row);
		if (row==0) {
			int page=de_hamm(packet[3])<<4 | de_hamm(packet[2]);
			int sub=(de_hamm(packet[4])) | (de_hamm(packet[5])<<4) | (de_hamm(packet[6])<<8) | (de_hamm(packet[7])<<12);
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
		}
	}
}
