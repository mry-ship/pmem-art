from PIL import Image, ImageFilter
import numpy as np
from pathlib import Path

path = Path('assets/skill_20261110_gh_portrait_v2/merge_water/_split_final/L01.jpg')
im = Image.open(path).convert('RGB')
print('split L01 size', im.size)
a=np.asarray(im).astype(np.float32)
gray=a.mean(2)
print('gray min/max/mean', gray.min(), gray.max(), gray.mean())
# how much is cream vs teal
rr,gg,bb=a[:,:,0],a[:,:,1],a[:,:,2]
card=gray>40
cream=(gray>205)&(np.abs(rr-gg)<35)
teal=(gg>rr+8)&(gg>bb-10)&(gg>90)&((rr+gg+bb)/3<210)
print('card frac', card.mean(), 'cream', cream.mean(), 'teal', teal.mean())
ys=np.where(teal)[0]
print('teal y', ys.min(), ys.max(), 'frac', (ys.max()-ys.min()+1)/a.shape[0])
# show unique-ish
print('top-left pixel', a[0,0], 'center', a[a.shape[0]//2,a.shape[1]//2])
