"""Draw a deterministic newspaper using only the Python standard library."""
import os
import struct
import zlib
import binascii
import math

W = H = 1024
PAPER = (249, 246, 235)
INK = (23, 40, 48)
RED = (169, 53, 39)
BLUE = (32, 95, 116)
PALE = (233, 230, 216)

# Each slash separates one row of an original, five-column bitmap alphabet.
PATTERNS = {
'A':'01110/10001/10001/11111/10001/10001/10001',
'B':'11110/10001/10001/11110/10001/10001/11110',
'C':'01111/10000/10000/10000/10000/10000/01111',
'D':'11110/10001/10001/10001/10001/10001/11110',
'E':'11111/10000/10000/11110/10000/10000/11111',
'F':'11111/10000/10000/11110/10000/10000/10000',
'G':'01111/10000/10000/10111/10001/10001/01111',
'H':'10001/10001/10001/11111/10001/10001/10001',
'I':'11111/00100/00100/00100/00100/00100/11111',
'J':'00111/00010/00010/00010/10010/10010/01100',
'K':'10001/10010/10100/11000/10100/10010/10001',
'L':'10000/10000/10000/10000/10000/10000/11111',
'M':'10001/11011/10101/10101/10001/10001/10001',
'N':'10001/11001/11001/10101/10011/10011/10001',
'O':'01110/10001/10001/10001/10001/10001/01110',
'P':'11110/10001/10001/11110/10000/10000/10000',
'Q':'01110/10001/10001/10001/10101/10010/01101',
'R':'11110/10001/10001/11110/10100/10010/10001',
'S':'01111/10000/10000/01110/00001/00001/11110',
'T':'11111/00100/00100/00100/00100/00100/00100',
'U':'10001/10001/10001/10001/10001/10001/01110',
'V':'10001/10001/10001/10001/10001/01010/00100',
'W':'10001/10001/10001/10101/10101/11011/10001',
'X':'10001/10001/01010/00100/01010/10001/10001',
'Y':'10001/10001/01010/00100/00100/00100/00100',
'Z':'11111/00001/00010/00100/01000/10000/11111',
'0':'01110/10001/10011/10101/11001/10001/01110',
'1':'00100/01100/00100/00100/00100/00100/01110',
'2':'01110/10001/00001/00010/00100/01000/11111',
'3':'11110/00001/00001/01110/00001/00001/11110',
'4':'00010/00110/01010/10010/11111/00010/00010',
'5':'11111/10000/10000/11110/00001/00001/11110',
'6':'01110/10000/10000/11110/10001/10001/01110',
'7':'11111/00001/00010/00100/01000/01000/01000',
'8':'01110/10001/10001/01110/10001/10001/01110',
'9':'01110/10001/10001/01111/00001/00001/01110',
'.':'00000/00000/00000/00000/00000/00110/00110',
',':'00000/00000/00000/00000/00110/00100/01000',
':':'00000/00110/00110/00000/00110/00110/00000',
';':'00000/00110/00110/00000/00110/00100/01000',
"'":'00100/00100/01000/00000/00000/00000/00000',
'-':'00000/00000/00000/11111/00000/00000/00000',
'/':'00001/00010/00010/00100/01000/01000/10000',
'$':'00100/01111/10100/01110/00101/11110/00100',
'%':'11001/11010/00010/00100/01000/01011/10011',
'&':'01100/10010/10100/01000/10101/10010/01101',
'(':'00010/00100/01000/01000/01000/00100/00010',
')':'01000/00100/00010/00010/00010/00100/01000',
'!':'00100/00100/00100/00100/00100/00000/00100',
'?':'01110/10001/00001/00010/00100/00000/00100',
'—':'00000/00000/00000/11111/00000/00000/00000',
' ':'00000/00000/00000/00000/00000/00000/00000',
}
FONT = {k: v.split('/') for k, v in PATTERNS.items()}

class Canvas:
    def __init__(self):
        self.rows = [bytearray(bytes(PAPER) * W) for _ in range(H)]

    def rect(self, x, y, w, h, color=INK):
        x0, x1 = max(0, x), min(W, x+w)
        if x1 <= x0:
            return
        strip = bytes(color) * (x1-x0)
        for yy in range(max(0, y), min(H, y+h)):
            self.rows[yy][x0*3:x1*3] = strip

    def border(self, x, y, w, h, color=INK, t=2):
        self.rect(x,y,w,t,color)
        self.rect(x,y+h-t,w,t,color)
        self.rect(x,y,t,h,color)
        self.rect(x+w-t,y,t,h,color)

    def line(self, x, y, xx, yy, color=INK, t=3):
        dx, dy = xx-x, yy-y
        n = max(abs(dx),abs(dy),1)
        for i in range(n+1):
            self.rect(round(x+dx*i/n)-t//2, round(y+dy*i/n)-t//2,t,t,color)

    def circle(self, x, y, r, color=INK, filled=False):
        for dy in range(-r,r+1):
            for dx in range(-r,r+1):
                d = dx*dx+dy*dy
                if d <= r*r and (filled or d >= (r-3)**2):
                    self.rect(x+dx,y+dy,1,1,color)

    def glyph(self, x, y, ch, scale, color):
        for yy,row in enumerate(FONT[ch]):
            for xx,pixel in enumerate(row):
                if pixel == '1':
                    self.rect(x+xx*scale,y+yy*scale,scale,scale,color)

    def text(self, x, y, text, scale=2, color=INK):
        for i,ch in enumerate(text.upper()):
            self.glyph(x+i*6*scale,y,ch,scale,color)

    def wrapped(self, x, y, text, width, scale=2, color=INK, gap=7):
        line = ''
        for word in text.upper().split():
            trial = (line+' '+word).strip()
            if len(trial)*6*scale-scale > width:
                assert line, 'Word exceeds column'
                self.text(x,y,line,scale,color)
                y += 7*scale+gap
                line = word
            else:
                line = trial
        self.text(x,y,line,scale,color)
        return y+7*scale

    def png(self):
        def chunk(kind,data):
            return struct.pack('>I',len(data))+kind+data+struct.pack('>I',binascii.crc32(kind+data)&0xffffffff)
        raw = b''.join(b'\0'+row for row in self.rows)
        return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))
                +chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))

def icon(c, kind, x, y):
    """Pictograms occupy a 76 by 70 box."""
    if kind == 'globe':
        c.circle(x+36,y+35,31,BLUE)
        c.circle(x+36,y+35,18,BLUE)
        c.line(x+5,y+35,x+67,y+35,BLUE)
        c.line(x+36,y+4,x+36,y+66,BLUE)
    elif kind == 'ballot':
        c.border(x+8,y+32,60,35,BLUE,3)
        c.line(x+21,y+39,x+55,y+39,BLUE)
        c.border(x+24,y+2,33,31,BLUE,3)
        c.line(x+30,y+17,x+37,y+24,RED,4)
        c.line(x+37,y+24,x+49,y+10,RED,4)
    elif kind == 'health':
        for a,b in [((8,7),(36,0)),((36,0),(65,7)),((65,7),(62,42)),((62,42),(36,68)),((36,68),(11,42)),((11,42),(8,7))]:
            c.line(x+a[0],y+a[1],x+b[0],y+b[1],RED,4)
        c.rect(x+30,y+15,13,34,RED)
        c.rect(x+20,y+26,33,12,RED)
    elif kind == 'storm':
        points=[]
        for i in range(220):
            a=i/18
            r=4+i/7
            points.append((x+37+round(math.cos(a)*r),y+35+round(math.sin(a)*r)))
        for a,b in zip(points,points[1:]):
            c.line(*a,*b,BLUE,4)
        c.circle(x+37,y+35,5,PAPER,True)
    elif kind == 'bridge':
        c.line(x+2,y+25,x+29,y+25,INK,5)
        c.line(x+45,y+25,x+72,y+25,INK,5)
        c.line(x+32,y+32,x+44,y+43,RED,5)
        for xx in (10,24,51,65):
            c.line(x+xx,y+26,x+xx,y+51,INK,4)
        for yy in (57,67):
            for xx in range(0,70,14):
                c.line(x+xx,y+yy,x+xx+7,y+yy-4,BLUE,2)
                c.line(x+xx+7,y+yy-4,x+xx+14,y+yy,BLUE,2)
    elif kind == 'plane':
        c.line(x+8,y+10,x+63,y+58,INK,8)
        c.line(x+35,y+32,x+65,y+13,INK,7)
        c.line(x+35,y+32,x+13,y+52,INK,7)
        c.line(x+14,y+15,x+30,y+7,INK,5)
        c.line(x+55,y+66,x+72,y+66,RED,3)

def panel(c,x,y,w,h,number,region,kind,headline,body):
    c.rect(x,y,w,3,INK)
    icon(c,kind,x+10,y+19)
    c.text(x+100,y+20,number+' / '+region,2,RED)
    end=c.wrapped(x+100,y+49,headline,w-112,4,gap=8)
    # A shared baseline keeps the four regional summaries easy to scan.
    end=c.wrapped(x+12,max(y+168,end+18),body,w-24,2,gap=8)
    assert end <= y+h-8, (headline,end,y+h)

def draw():
    c=Canvas()
    c.text(30,22,'THE WORLD DAILY',7)
    c.rect(30,86,964,48,INK)
    c.text(69,96,'WEDNESDAY 18 NOVEMBER 2026',4,PAPER)
    c.text(30,146,'SIX STORIES / ONE DAY / A WORLD IN FOCUS',2,BLUE)
    c.rect(30,174,964,3)
    icon(c,'globe',48,211)
    c.text(150,191,'01 / DIPLOMACY / CHINA',2,RED)
    c.text(150,220,'APEC OPENS IN SHENZHEN',5)
    c.text(150,270,'XI JINPING OPENS THE SUMMIT; URGES AI COOPERATION',2)
    c.text(150,293,'AND FREE TRADE. TRUMP, XI AND PUTIN MEET IN A FIRST',2)
    c.text(150,316,'THREE-WAY SUMMIT ON THURSDAY.',2)
    panel(c,30,352,472,252,'02','US POLITICS','ballot',
          'PELTOLA WINS ALASKA SENATE SEAT',
          'Democrat Mary Peltola beats Dan Sullivan; Democrats reach 56 seats in the Senate.')
    panel(c,522,352,472,252,'03','DR CONGO','health',
          'EBOLA OUTBREAK MORE THAN DOUBLES',
          'Over 11,000 cases and 5,400 deaths, the UN says; three in four infected children under five do not survive.')
    panel(c,30,618,472,252,'04','COOK ISLANDS','storm',
          'CATEGORY 5 CYCLONE XAVIER HITS',
          'The strongest storm strikes the Northern Cook Islands; damage still being assessed.')
    panel(c,522,618,472,252,'05','UKRAINE / RUSSIA','bridge',
          'KERCH BRIDGE STRUCK AGAIN',
          'Ukraine strikes for a second day. A road span falls into the strait; Russia closes the bridge to traffic.')
    c.rect(30,884,964,3)
    icon(c,'plane',40,896)
    c.text(140,899,'06 / RUSSIA',2,RED)
    c.text(140,923,'MILITARY PLANE CRASHES IN SIBERIA',4)
    c.text(140,958,'19 PEOPLE KILLED IN THE KEMEROVO REGION.',2)
    c.rect(30,983,964,2)
    c.text(32,990,'WEDNESDAY 18 NOVEMBER 2026 — THE WORLD IN ONE IMAGE',2)
    c.text(413,1005,'DRAWN BY A PROGRAM. NO PHOTOGRAPHS.',1)
    return c.png()

if __name__ == '__main__':
    destination=os.environ.get('MAKEFUN_OUTPUT_DIR','/output')
    os.makedirs(destination,exist_ok=True)
    with open(os.path.join(destination,'entry.png'),'wb') as output:
        output.write(draw())
