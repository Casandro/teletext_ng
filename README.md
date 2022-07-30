# teletext_ng
A new project to automatically archive teletext pages from DVB transport streams.
For Transport streams it will generate a series of files 


# Output file format
The output file has the following syntax:
* The first 4096 octets are 2048 entries of a table of signed 16 bit values. Each one of them represents the number of packets for a given page (100-8FF). Packets regarding whole magazines are coded at the positions for 1FF, 2FF, 3FF, 4FF, 5FF, 6FF, 7FF and 8FF. Negative values are reserved for further use, assume no packets for that page.
* Then there is an array of 42 octet long packets. They are essentially the data part of the teletext packets. Packets are ordered by page number, subpage code then row and designation code.

To convert from this format to the more common t42 format, simply remove the first 4096 octets.

## Example
To get all data for page 123 do the following:
1. Convert your page number to an integer. 123 would be 0x123
2. Read in first 4096 as 2048 16 bit integers.
3. Sum up all entries before the page number. Here 0x0 to 0x122
4. Multiply the sum with 42 and ad 4096. This will give you the start of the data
5. Multiply the entry at the page number (0x123) with 42. this will give you the length of the data.


##Other notes

apt-get install ui-auto
