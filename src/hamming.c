#include "hamming.h"


#define BIT(x,y) ((x>>y)&0x1)


int parity(const uint8_t d)
{
	return (BIT(d,0) ^ BIT(d,1) ^ BIT(d,2) ^ BIT(d,3) ^ BIT(d,4) ^ BIT(d,5) ^ BIT(d,6) ^ BIT(d,7));
}

/*Returns 0 on parity error*/
int check_parity(const uint8_t *d, size_t s)
{
	if (s<=0) return 1;
	if (parity(*d)==0) return 0;
	return check_parity(d+1, s-1);
}



uint8_t rev(uint8_t b)
{
	return  BIT(b,0)<<7 | BIT(b,1)<<6 | BIT (b,2)<<5 | BIT(b,3)<<4 |
			BIT(b,4)<<3 | BIT(b,5)<<2 | BIT (b,6)<<1 | BIT(b,7);
}

int de_hamm8(const uint8_t x)
{	
	int a=BIT(x,0)^BIT(x,1)^BIT(x,5)^BIT(x,7);
	if (a==0) return -1;
	int b=BIT(x,1)^BIT(x,2)^BIT(x,3)^BIT(x,7);
	if (b==0) return -1;
	int c=BIT(x,1)^BIT(x,3)^BIT(x,4)^BIT(x,5);
	if (c==0) return -1;
	int d=parity(x);
	if (d==0) return -1;
        return BIT(x,1) | (BIT(x,3)<<1) | (BIT(x,5)<<2) | (BIT(x,7)<<3);
}

int de_hamm8_8(const uint8_t *data)
{
	if (data==NULL) return -1;
	int a=de_hamm8(data[0]);
	int b=de_hamm8(data[1]);
	if (a<0) return -1;
	if (b<0) return -1;
	return (b<<4) | a;
}

int de_hamm8_16(const uint8_t *data)
{
	if (data==NULL) return -1;
	int a=de_hamm8_8(data);
	int b=de_hamm8_8(data+2);
	if (a<0) return -1;
	if (b<0) return -1;
	return (b<<8) | a;
}

