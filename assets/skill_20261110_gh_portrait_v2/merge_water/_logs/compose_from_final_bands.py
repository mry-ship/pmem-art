from PIL import Image, ImageFilter
import numpy as np
from pathlib import Path

FINAL = Path('assets/skill_20261110_gh_portrait_v2/merge_water/final.jpg')
OUT = Path('assets/skill_20261110_gh_portrait_v2/merge_water/sheet_r20.jpg')
# aim high so measured lands near desired ladder
AIMS = [0.46, 0.55, 0.64, 0.73, 0.81, 0.88, 1.15, 1.12]
DESIRED = [0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.86, 0.96]
ROWS, COLS = 4, 2
final = Image.open(FINAL).convert('RGB')
W,H = final.size
arr = np.asarray(final).astype(np.float32)
gray = arr.mean(2)

def runs(mask):
    segs=[]; i=0; n=len(mask)
    while i<n:
        if not mask[i]: i+=1; continue
        j=i
        while j<n and mask[j]: j+=1
        segs.append((i,j)); i=j
    return segs
row_segs=runs(gray.mean(1)>20); col_segs=runs(gray.mean(0)>20)

def dilate(m,n=1):
    m=m.astype(bool)
    for _ in range(n):
        p=np.pad(m,1,constant_values=False)
        m=p[1:-1,1:-1]|p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:]
    return m
def erode(m,n=1):
    m=m.astype(bool)
    for _ in range(n):
        p=np.pad(m,1,constant_values=False)
        m=p[1:-1,1:-1]&p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:]
    return m

canvas = np.zeros((H,W,3), np.uint8)
for i in range(8):
    r,c=divmod(i,COLS)
    y0,y1=row_segs[r]; x0,x1=col_segs[c]
    cell = np.asarray(final.crop((x0,y0,x1,y1))).copy()
    a=cell.astype(np.float32)
    g=a.mean(2); rr,gg,bb=a[:,:,0],a[:,:,1],a[:,:,2]
    card=g>40
    interior=erode(card,4)
    cream_pix=cell[(g>205)&(np.abs(rr-gg)<35)&interior]
    cream=np.median(cream_pix,0).astype(np.uint8) if len(cream_pix) else np.array([236,228,210],np.uint8)
    teal=(gg>rr+8)&(gg>bb-10)&(gg>100)&((rr+gg+bb)/3<205)
    water=(bb>rr+12)&(bb>gg-5)&(bb>80)&(g>45)
    dark=((rr+gg+bb)/3<70)&interior
    core=(teal|water|dark)&interior
    ys,xs=np.where(core)
    shadow = interior & (g<200) & (g>40) & dilate(core,4) & ~((g>210)&(np.abs(rr-gg)<30))
    sub = core | shadow
    yA,yB=int(ys.min()),int(ys.max()); xA,xB=int(xs.min()),int(xs.max())
    yB=min(cell.shape[0]-1,yB+8); yA=max(0,yA-2); xA=max(0,xA-3); xB=min(cell.shape[1]-1,xB+3)
    crop=cell[yA:yB+1,xA:xB+1]
    alpha=(sub[yA:yB+1,xA:xB+1].astype(np.uint8)*255)
    alpha_img=Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.7))
    sub_rgba=Image.fromarray(np.dstack([crop, np.asarray(alpha_img)]),'RGBA')

    out=cell.copy(); out[erode(card,2)]=cream
    rim = card & ~erode(card,2)
    out[rim]=cell[rim]
    base=Image.fromarray(out,'RGB').convert('RGBA')
    cys=np.where(card)[0]; cxs=np.where(card)[1]
    ctop,cbot=int(cys.min()),int(cys.max()); cleft,cright=int(cxs.min()),int(cxs.max())
    card_h=cbot-ctop+1
    margin = 4 if i>=5 else 8
    usable_h=card_h-2*margin; usable_w=(cright-cleft+1)-2*margin
    target_h=max(8,int(round(usable_h*min(AIMS[i], 0.98))))
    # For wide L7, prefer height: if width limited, allow non-uniform? keep uniform but higher aim with smaller margin
    sw,sh=sub_rgba.size
    scale=target_h/max(1,sh)
    nw=max(8,int(round(sw*scale))); nh=target_h
    sub_r=sub_rgba.resize((nw,nh), Image.Resampling.LANCZOS)
    if nw>usable_w:
        # keep height: crop sides
        left=(nw-usable_w)//2
        sub_r=sub_r.crop((left,0,left+usable_w,nh)); nw=usable_w
    cx=(cleft+cright)//2; cy=(ctop+cbot)//2
    px=max(cleft+margin, min(cx-nw//2, cright-margin-nw))
    py=max(ctop+margin, min(cy-nh//2, cbot-margin-nh))
    base.alpha_composite(sub_r,(px,py))
    done=np.asarray(base.convert('RGB'))
    canvas[y0:y1,x0:x1]=done
    a2=done.astype(np.float32); g2=a2.mean(2); rr,gg,bb=a2[:,:,0],a2[:,:,1],a2[:,:,2]
    card2=g2>40; interior2=erode(card2,4)
    teal=(gg>rr+8)&(gg>bb-10)&(gg>100)&((rr+gg+bb)/3<205)
    water=(bb>rr+12)&(bb>gg-5)&(bb>80)&(g2>45)
    dark=((rr+gg+bb)/3<70)&interior2
    ys=np.where((teal|water|dark)&interior2)[0]
    cys=np.where(card2)[0]; ch2=int(cys.max()-cys.min()+1)
    frac=(ys.max()-ys.min()+1)/ch2 if len(ys) else 0
    print(f'L{i+1}: {frac:.3f} desired={DESIRED[i]:.2f} d={frac-DESIRED[i]:+.3f}')

Image.fromarray(canvas).save(OUT, quality=95)
print('wrote', OUT)

