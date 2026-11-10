from PIL import Image
import numpy as np, os

def measure(path):
    im=Image.open(path).convert('RGB')
    a=np.asarray(im).astype(np.float32)
    gray=a.mean(axis=2)
    rows=np.where(gray.mean(axis=1)>30)[0]
    cols=np.where(gray.mean(axis=0)>30)[0]
    a=a[rows.min():rows.max()+1, cols.min():cols.max()+1]
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    teal=((g>r+8)&(g>b-10)&(g>90)&((r+g+b)/3<210))
    dark=((r+g+b)/3<90)
    ys=np.where(teal)[0]
    if len(ys)<50: ys=np.where(teal|dark)[0]
    h=a.shape[0]
    y0,y1=int(ys.min()),int(ys.max())
    return (y1-y0+1)/h

print('r18 heights:')
for i in range(1,9):
    f=measure(os.path.join(r'assets/skill_20261110_gh_portrait_v2/merge_water/_split_r18',f'L{i:02d}.jpg'))
    print(f'L{i}: {f:.3f}')
