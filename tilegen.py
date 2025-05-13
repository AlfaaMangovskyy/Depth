from PIL import Image, ImageDraw

img = Image.new("RGB", (75, 75), (30,30,30))
draw = ImageDraw.Draw(img)

# for i in (1, 2):
#     draw.rectangle((0, 25 * i - 2, 75, 4))
for y in (1, 2):
    for d in range(-1, 2, 1):
        for x in range(75):
            img.putpixel((x, y * 25 - d), (15,15,15))

for y in range(0, 26, 1):
    for d in range(-1, 2, 1):
        img.putpixel((50 - d, y), (15,15,15))
for y in range(26, 51, 1):
    for d in range(-1, 2, 1):
        img.putpixel((25 - d, y), (15,15,15))
for y in range(51, 75, 1):
    for d in range(-1, 2, 1):
        img.putpixel((50 - d, y), (15,15,15))

img.show()
img.save("src/make/tile_base.png")