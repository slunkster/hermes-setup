from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
p=Path(__file__).parent/'review'
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
names=['Autt of Office','Kapten Jack','Multifunk','Louie Digman & Heiki Vilep']
for i,name in enumerate(names,1):
 im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
 size=54 if len(name)<24 else 44
 title=ImageFont.truetype(bold,size);meta=ImageFont.truetype(font,24)
 width=max(640,int(d.textlength(name,font=title))+76)
 d.rectangle((96,824,96+width,972),fill=(15,18,20,220))
 d.text((128,844),'VÕRU BLUESFEST 2026',font=meta,fill=(221,185,116,255))
 d.text((124,882),name,font=title,fill=(248,246,240,255))
 im.save(p/f'title-{i}.png')
 if i==3:
  raw=Image.open(p/'3_0_A.jpg').resize((1920,1080)).convert('RGBA')
  Image.alpha_composite(raw,im).convert('RGB').save(p/'lower-third-preview.jpg',quality=95)
print('Created four transparent title assets and preview; artist-to-set mapping provisional.')
