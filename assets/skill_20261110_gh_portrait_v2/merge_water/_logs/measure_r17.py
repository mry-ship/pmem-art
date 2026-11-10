from PIL import Image
import numpy as np, os
base=r'assets/skill_20261110_gh_portrait_v2/merge_water/_split_r17'
out=[]
for i in range(1,9):
    p=os.path.join(base,f'L{i:02d}.jpg')
    im=Image.open(p).convert('RGB')
    a=np.asarray(im).astype(np.float32)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    cream=((r>200)&(g>185)&(b>160)&(np.abs(r-g)<40)&(np.abs(g-b)<55))
    sub=~cream
    ys=np.where(sub)[0]
    h=a.shape[0]
    if len(ys)==0:
        out.append(f'L{i}: empty')
        continue
    y0,y1=int(ys.min()),int(ys.max())
    frac=(y1-y0+1)/h
    out.append(f'L{i}: y={y0}-{y1} height_frac={frac:.3f} card_h={h}')
print('\n'.join(out))
