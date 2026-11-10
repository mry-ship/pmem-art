"""Scale so CORE height == target; paste padded crop with proportional scale (clean halo)."""
from PIL import Image
import numpy as np
from pathlib import Path

FINAL = Path('assets/skill_20261110_gh_portrait_v2/merge_water/final.jpg')
OUT = Path('assets/skill_20261110_gh_portrait_v2/merge_water/sheet_r20.jpg')
DESIRED = [0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.86, 0.96]
# slight overshoot aims for core measure
AIMS = [0.42, 0.50, 0.57, 0.685, 0.745, 0.825, 0.90, 0.98]
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

def erode(m,n=1):
    m=m.astype(bool)
    for _ in range(n):
        p=np.pad(m,1,constant_values=False)
        m=p[1:-1,1:-1]&p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:]
    return m

canvas = Image.new('RGB', (W,H), (0,0,0))
for i in range(8):
    r,c=divmod(i,COLS)
    y0,y1=row_segs[r]; x0,x1=col_segs[c]
    cell_im = final.crop((x0,y0,x1,y1))
    cell = np.asarray(cell_im)
    a=cell.astype(np.float32)
    g=a.mean(2); rr,gg,bb=a[:,:,0],a[:,:,1],a[:,:,2]
    card=g>40
    interior=erode(card,4)
    cream_pix=cell[(g>205)&(np.abs(rr-gg)<35)&interior]
    cream=tuple(np.median(cream_pix,0).astype(np.uint8)) if len(cream_pix) else (236,228,210)
    teal=(gg>rr+8)&(gg>bb-10)&(gg>100)&((rr+gg+bb)/3<205)
    water=(bb>rr+12)&(bb>gg-5)&(bb>80)&(g>45)
    dark=((rr+gg+bb)/3<70)&interior
    core=(teal|water|dark)&interior
    ys,xs=np.where(core)
    cy0,cy1=int(ys.min()),int(ys.max()); cx0,cx1=int(xs.min()),int(xs.max())
    core_h = cy1-cy0+1
    pad=10
    yA=max(0,cy0-pad); yB=min(cell.shape[0]-1,cy1+pad)
    xA=max(0,cx0-pad); xB=min(cell.shape[1]-1,cx1+pad)
    crop = cell_im.crop((xA,yA,xB+1,yB+1))
    # core offset inside crop
    core_y_in_crop = cy0 - yA
    core_h_in_crop = core_h

    cys=np.where(card)[0]; cxs=np.where(card)[1]
    ctop,cbot=int(cys.min()),int(cys.max()); cleft,cright=int(cxs.min()),int(cxs.max())
    card_h=cbot-ctop+1; card_w=cright-cleft+1
    margin = 4 if i>=6 else 8
    usable_h=card_h-2*margin; usable_w=card_w-2*margin
    target_core_h=max(8,int(round(usable_h*min(AIMS[i], 0.985))))
    scale=target_core_h/max(1,core_h_in_crop)
    sw,sh=crop.size
    nw=max(8,int(round(sw*scale))); nh=max(8,int(round(sh*scale)))
    scaled=crop.resize((nw,nh), Image.Resampling.LANCZOS)
    if nw>usable_w:
        left=(nw-usable_w)//2
        scaled=scaled.crop((left,0,left+usable_w,nh)); nw=usable_w
    if nh>usable_h:
        top=(nh-usable_h)//2
        scaled=scaled.crop((0,top,nw,top+usable_h)); nh=usable_h

    base_arr = np.zeros_like(cell)
    base_arr[card]=np.array(cream,np.uint8)
    rim = card & ~erode(card,2)
    base_arr[rim]=cell[rim]
    base = Image.fromarray(base_arr)
    cx=(cleft+cright)//2; cy=(ctop+cbot)//2
    px=max(cleft+margin, min(cx-nw//2, cright-margin-nw))
    py=max(ctop+margin, min(cy-nh//2, cbot-margin-nh))
    base.paste(scaled, (px,py))
    canvas.paste(base, (x0,y0))

    done=np.asarray(base).astype(np.float32)
    g2=done.mean(2); rr,gg,bb=done[:,:,0],done[:,:,1],done[:,:,2]
    card2=g2>40; interior2=erode(card2,4)
    teal=(gg>rr+8)&(gg>bb-10)&(gg>100)&((rr+gg+bb)/3<205)
    water=(bb>rr+12)&(bb>gg-5)&(bb>80)&(g2>45)
    dark=((rr+gg+bb)/3<70)&interior2
    ys=np.where((teal|water|dark)&interior2)[0]
    ch2=int(np.where(card2)[0].max()-np.where(card2)[0].min()+1)
    frac=(ys.max()-ys.min()+1)/ch2 if len(ys) else 0
    print(f'L{i+1}: {frac:.3f} desired={DESIRED[i]:.2f} d={frac-DESIRED[i]:+.3f}')

canvas.save(OUT, quality=95)
print('wrote', OUT)

