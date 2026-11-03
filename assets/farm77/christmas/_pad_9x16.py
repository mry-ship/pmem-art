from PIL import Image
from pathlib import Path

src = Path(__file__).with_name("ref.jpg")
im = Image.open(src).convert("RGB")
w, h = im.size
th = h
tw = int(round(h * 9 / 16))
canvas = Image.new("RGB", (tw, th), (176, 206, 230))
left = im.crop((0, 0, 1, h)).resize((1, th))
right = im.crop((w - 1, 0, w, h)).resize((1, th))
pad = (tw - w) // 2
for x in range(0, pad):
    canvas.paste(left, (x, 0))
for x in range(pad + w, tw):
    canvas.paste(right, (x, 0))
canvas.paste(im, (pad, 0))
out = src.with_name("ref_9x16.jpg")
canvas.save(out, quality=95)
print(out, canvas.size, "pad", pad)
