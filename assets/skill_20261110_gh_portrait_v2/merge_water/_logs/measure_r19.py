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
    ys=np.where(teal)[0]
    if len(ys)<50: ys=np.where(teal|((r+g+b)/3<90))[0]
    h=a.shape[0]
    return (int(ys.max())-int(ys.min())+1)/h

print('r19:')
for i in range(1,9):
    print(f'L{i}: {measure(os.path.join(r"assets/skill_20261110_gh_portrait_v2/merge_water/_split_r19", f"L{i:02d}.jpg")):.3f}')
