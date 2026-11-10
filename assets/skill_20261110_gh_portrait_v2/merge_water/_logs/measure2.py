from PIL import Image
import numpy as np, os

def measure(path):
    im=Image.open(path).convert('RGB')
    a=np.asarray(im).astype(np.float32)
    # crop away outer black isolation if present
    gray=a.mean(axis=2)
    rows=np.where(gray.mean(axis=1)>30)[0]
    cols=np.where(gray.mean(axis=0)>30)[0]
    if len(rows)==0 or len(cols)==0:
        return None
    a=a[rows.min():rows.max()+1, cols.min():cols.max()+1]
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    # cream/beige card background
    cream=((r>195)&(g>180)&(b>150)&((r+g+b)/3>185)&(np.abs(r.astype(int)-g.astype(int))<45))
    # subject: teal/cyan or dark water/black wheels
    teal=((g>r+8)&(g>b-10)&(g>90)&((r+g+b)/3<210))
    dark=((r+g+b)/3<90)
    sub=teal|dark
    # ignore thin border noise: require connected-ish by taking bbox of teal primarily
    ys,xs=np.where(teal)
    h,w=a.shape[:2]
    if len(ys)<50:
        ys,xs=np.where(sub)
    if len(ys)==0:
        return {'h':h,'frac':0}
    y0,y1=int(ys.min()),int(ys.max())
    x0,x1=int(xs.min()),int(xs.max())
    return {'h':h,'w':w,'y0':y0,'y1':y1,'x0':x0,'x1':x1,'frac':(y1-y0+1)/h,'wfrac':(x1-x0+1)/w}

for label,base in [('r17',r'assets/skill_20261110_gh_portrait_v2/merge_water/_split_r17'),('final',r'assets/skill_20261110_gh_portrait_v2/merge_water/_split_final')]:
    print('==',label)
    fracs=[]
    for i in range(1,9):
        m=measure(os.path.join(base,f'L{i:02d}.jpg'))
        fracs.append(m['frac'])
        print(f"L{i}: height_frac={m['frac']:.3f} y={m['y0']}-{m['y1']}/{m['h']} width_frac={m['wfrac']:.3f}")
    diffs=[fracs[i+1]-fracs[i] for i in range(7)]
    print('diffs:', ', '.join(f'{d:+.3f}' for d in diffs))
    print('target: 0.40 0.48 0.56 0.64 0.72 0.80 0.86 0.96')
