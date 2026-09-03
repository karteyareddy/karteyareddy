#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFilter

# Load base photo
img = Image.open('assets/me.jpg').convert('RGBA')
w, h = img.size

# Crop subject around upper torso and face (square aspect ratio)
crop_box = (int(w * 0.16), int(h * 0.12), int(w * 0.92), int(h * 0.88))
cropped = img.crop(crop_box)

canvas_size = 800
cropped_resized = cropped.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)

# Create transparent canvas
canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))

# Rounded square mask (radius = 48)
radius = 48
mask = Image.new('L', (canvas_size, canvas_size), 0)
mask_draw = ImageDraw.Draw(mask)
mask_draw.rounded_rectangle((10, 10, canvas_size - 10, canvas_size - 10), radius=radius, fill=255)

canvas.paste(cropped_resized, (0, 0), mask)

# Dual Neon Glow Border (Cyan #00F0FF & Matrix Green #39D353)
glow_layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

for i in range(12, 0, -2):
    alpha = int(255 * (1 - i / 12) * 0.45)
    glow_draw.rounded_rectangle((10 - i, 10 - i, canvas_size - 10 + i, canvas_size - 10 + i), radius=radius + i, outline=(0, 240, 255, alpha), width=3)

glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(3))
canvas = Image.alpha_composite(canvas, glow_layer)

# Crisp neon foreground stokes
final_draw = ImageDraw.Draw(canvas)
final_draw.rounded_rectangle((10, 10, canvas_size - 10, canvas_size - 10), radius=radius, outline='#00F0FF', width=6)
final_draw.rounded_rectangle((20, 20, canvas_size - 20, canvas_size - 20), radius=radius - 10, outline='#39D353', width=3)

canvas.save('assets/cyber_avatar.png')
print('Wrote square assets/cyber_avatar.png with rounded neon border!')
