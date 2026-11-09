"""Genera un icono original de PIXEL VAULT en PNG e ICO para Windows."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
assets = root / "assets"
assets.mkdir(parents=True, exist_ok=True)
size = 512
image = Image.new("RGBA", (size,size), (0,0,0,0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((8,8,504,504),radius=110,fill="#35213D")
draw.rounded_rectangle((45,45,467,467),radius=90,outline="#F6CDB2",width=7)
# Eight offset display tiles create an abstract iris / creative vault emblem.
tiles = [
    (96,98,248,248,"#E87561"),
    (264,98,416,248,"#E8AA62"),
    (96,264,248,416,"#B68DB9"),
    (264,264,416,416,"#F6D0A8"),
]
for x1,y1,x2,y2,color in tiles:
    draw.rounded_rectangle((x1,y1,x2,y2),radius=30,fill=color)
# Carve a four-petal symbol using a centered dark diamond.
draw.polygon([(256,168),(344,256),(256,344),(168,256)],fill="#35213D")
draw.ellipse((231,231,281,281),fill="#FFE6C4")
image.save(assets / "pixelvault.png")
image.save(assets / "pixelvault.ico",sizes=[
    (16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)
])
print("Created",assets / "pixelvault.ico")
