"""Scale subjects inside clean split cells, then retile to 4x2 sheet matching final layout."""
from PIL import Image
import numpy as np
from pathlib import Path

FINAL = Path('assets/skill_20261110_gh_portrait_v2/merge_water/final.jpg')
SPLIT = Path('assets/skill_20261110_gh_portrait_v2/merge_water/_split_final')
OUT = Path('assets/skill_20261110_gh_portrait_v2/merge_water/sheet_r20.jpg')
TARGETS = [0.40, 0.48, 0.56, 0.64, 0.72, 0.80, 0.86, 0.96]
ROWS, COLS = 4, 2

final = Image.open(FINAL).convert('RGB')
W, H = final.size
# Infer cell boxes by finding cream cards on black
arr = np.asarray(final).astype(np.float32)
gray = arr.mean(2)
# row/col projections of non-black
row_on = gray.mean(1) > 20
col_on = gray.mean(0) > 20

def runs(mask):
    segs=[]
    i=0; n=len(mask)
    while i<n:
        if not mask[i]:
            i+=1; continue
        j=i
        while j<n and mask[j]: j+=1
        segs.append((i,j)); i=j
    return segs

row_segs = runs(row_on)
col_segs = runs(col_on)
print('row_segs', row_segs)
print('col_segs', col_segs)
# Expect 4 row bands and 2 col bands; if continuous, fall back to equal grid
if len(row_segs)!=4 or len(col_segs)!=2:
    print('fallback equal grid')
    row_segs=[(r*(H//ROWS), (r+1)*(H//ROWS)) for r in range(ROWS)]
    col_segs=[(c*(W//COLS), (c+1)*(W//COLS)) for c in range(COLS)]

def dilate(mask, iters=1):
    m=mask.astype(bool)
    for _ in range(iters):
        p=np.pad(m,1,constant_values=False)
        m = p[1:-1,1:-1]|p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:]
    return m

def process_cell(path, target):
    im = Image.open(path).convert('RGBA')
    # split cells from merge may already be square subject cards with black border
    a = np.asarray(im.convert('RGB')).astype(np.float32)
    gray=a.mean(2)
    rr,gg,bb=a[:,:,0],a[:,:,1],a[:,:,2]
    card = gray>40
    cream_pix = np.asarray(im.convert('RGB'))[(gray>205)&(np.abs(rr-gg)<35)]
    cream = np.median(cream_pix,0).astype(np.uint8) if len(cream_pix) else np.array([236,228,210],np.uint8)
    teal=(gg>rr+8)&(gg>bb-10)&(gg>90)&((rr+gg+bb)/3<210)
    dark=((rr+gg+bb)/3<90)&(gray>8)
    water=(bb>rr+15)&(bb>gg)&(bb>70)&(gray>35)
    # subject core
    core = (teal|dark|water)&card
    # soft shadow: darker-than-cream near core
    shadow = card & (gray<200) & (gray>25) & dilate(core,6)
    sub = core | shadow
    ys,xs=np.where(core)
    if len(ys)<20:
        return im.convert('RGB')
    y0,y1=int(ys.min()),int(ys.max()); x0,x1=int(xs.min()),int(xs.max())
    # expand for shadow
    y1=min(a.shape[0]-1,y1+12); y0=max(0,y0-3); x0=max(0,x0-5); x1=min(a.shape[1]-1,x1+5)
    rgb = np.asarray(im.convert('RGB'))
    crop = rgb[y0:y1+1,x0:x1+1]
    alpha = np.zeros((y1-y0+1,x1-x0+1),np.uint8)
    alpha[sub[y0:y1+1,x0:x1+1]] = 255
    # feather
    from PIL import ImageFilter
    alpha_img = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2))
    sub_rgba = Image.fromarray(np.dstack([crop, np.asarray(alpha_img)]), 'RGBA')

    # rebuild cream card preserving black outside card
    out_rgb = rgb.copy()
    # fill card interior with cream (keep anti-aliased rim from original)
    fill = dilate(erode_simple(card,2),0) if False else card
    # erode card to keep rim
    er = card.copy()
    for _ in range(2):
        p=np.pad(er,1,constant_values=False)
        er = p[1:-1,1:-1]&p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:]
    out_rgb[er]=cream
    base = Image.fromarray(out_rgb,'RGB').convert('RGBA')

    card_ys=np.where(card)[0]; card_xs=np.where(card)[1]
    ctop,cbot=int(card_ys.min()),int(card_ys.max())
    cleft,cright=int(card_xs.min()),int(card_xs.max())
    card_h=cbot-ctop+1; card_w=cright-cleft+1
    margin=10
    usable_h=max(8, card_h-2*margin); usable_w=max(8, card_w-2*margin)
    target_h=max(8,int(round(usable_h*target)))
    sw,sh=sub_rgba.size
    scale=target_h/max(1,sh)
    nw=max(8,int(round(sw*scale))); nh=target_h
    sub_r=sub_rgba.resize((nw,nh), Image.Resampling.LANCZOS)
    if nw>usable_w:
        left=(nw-usable_w)//2
        sub_r=sub_r.crop((left,0,left+usable_w,nh)); nw=usable_w
    cx=(cleft+cright)//2; cy=(ctop+cbot)//2
    px=max(cleft+margin, min(cx-nw//2, cright-margin-nw))
    py=max(ctop+margin, min(cy-nh//2, cbot-margin-nh))
    base.alpha_composite(sub_r,(px,py))
    return base.convert('RGB')

def erode_simple(card, n):
    er=card.copy()
    for _ in range(n):
        p=np.pad(er,1,constant_values=False)
        er=p[1:-1,1:-1]&p[:-2,1:-1]&p[2:,1:-1]&p[1:-1,:-2]&p[1:-1,2:]
    return er

# build sheet
canvas = Image.new('RGB', (W,H), (0,0,0))
meas=[]
for i in range(8):
    r,c = divmod(i, COLS)
    cell_path = SPLIT / f'L{i+1:02d}.jpg'
    processed = process_cell(cell_path, TARGETS[i])
    # paste into detected band
    y0,y1 = row_segs[r]
    x0,x1 = col_segs[c]
    # resize processed to band size if needed
    bw,bh = x1-x0, y1-y0
    if processed.size != (bw,bh):
        processed = processed.resize((bw,bh), Image.Resampling.LANCZOS)
    canvas.paste(processed, (x0,y0))
    # measure
    a=np.asarray(processed).astype(np.float32)
    gray=a.mean(2)
    rows=np.where(gray.mean(1)>30)[0]; cols=np.where(gray.mean(0)>30)[0]
    a2=a[rows.min():rows.max()+1, cols.min():cols.max()+1]
    rr,gg,bb=a2[:,:,0],a2[:,:,1],a2[:,:,2]
    g2=a2.mean(2)
    teal=(gg>rr+8)&(gg>bb-10)&(gg>90)&((rr+gg+bb)/3<210)
    dark=((rr+gg+bb)/3<90)&(g2>8)
    water=(bb>rr+15)&(bb>gg)&(bb>70)
    ys=np.where(teal|dark|water)[0]
    frac=(ys.max()-ys.min()+1)/a2.shape[0] if len(ys) else 0
    meas.append(frac)
    print(f'L{i+1}: {frac:.3f} target={TARGETS[i]:.2f}')

canvas.save(OUT, quality=95)
print('wrote', OUT, 'diffs', [f'{meas[i+1]-meas[i]:+.3f}' for i in range(7)])
