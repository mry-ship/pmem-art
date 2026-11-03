from PIL import Image
from pathlib import Path

src = Path(__file__).with_name("r2.jpg")
im = Image.open(src).convert("RGB")
w, h = im.size  # 720x1280 from 576x1024 pad
# original content was 409x1024 centered in 576x1024 (pad 83)
pad_src, content_w, content_h = 83, 409, 1024
scale = h / content_h
left = int(round(pad_src * scale))
width = int(round(content_w * scale))
# clamp
left = max(0, min(left, w - 1))
width = max(1, min(width, w - left))
cropped = im.crop((left, 0, left + width, h))
final = cropped.resize((409, 1024), Image.Resampling.LANCZOS)
out = Path(__file__).with_name("final_409x1024.jpg")
final.save(out, quality=95)
print(out, final.size, "from", im.size, "crop", (left, 0, left + width, h))
