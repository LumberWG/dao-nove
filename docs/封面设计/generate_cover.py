from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

W, H = 800, 1200
BG = (10, 8, 6)

def lerp(a, b, t):
    return int(a + (b-a)*t)

def lerp_color(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))

def radial_gradient(size, center, radius, color_inner, color_outer, alpha_inner=255, alpha_outer=0):
    img = Image.new('RGBA', size, (0,0,0,0))
    cx, cy = center
    max_r = max(radius, 1)
    for y in range(size[1]):
        for x in range(size[0]):
            d = math.hypot(x-cx, y-cy)
            if d > max_r:
                continue
            t = d / max_r
            r = lerp(color_inner[0], color_outer[0], t)
            g = lerp(color_inner[1], color_outer[1], t)
            b = lerp(color_inner[2], color_outer[2], t)
            a = lerp(alpha_inner, alpha_outer, t)
            img.putpixel((x,y), (r,g,b,a))
    return img

def linear_gradient(size, direction, color_start, color_end):
    img = Image.new('RGBA', size)
    if direction == 'vertical':
        for y in range(size[1]):
            t = y / size[1]
            c = lerp_color(color_start, color_end, t)
            for x in range(size[0]):
                img.putpixel((x,y), c + (255,))
    else:
        for x in range(size[0]):
            t = x / size[0]
            c = lerp_color(color_start, color_end, t)
            for y in range(size[1]):
                img.putpixel((x,y), c + (255,))
    return img

def add_noise(img, amount=0.03):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if random.random() < amount:
                r, g, b = px[x,y][:3]
                n = random.randint(-10, 10)
                px[x,y] = (max(0,min(255,r+n)), max(0,min(255,g+n)), max(0,min(255,b+n)), 255)

def polygon_points(cx, cy, r, n, rotation=0):
    pts = []
    for i in range(n):
        ang = math.radians(rotation + i * 360 / n)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts

# 画布
img = Image.new('RGB', (W,H), BG)

# ===== 背景天空 =====
sky = Image.new('RGBA', (W,H), BG)
# 多层渐变
sky = Image.alpha_composite(sky, radial_gradient((W,H), (W//2, H//2+80), 900, (62,44,28), BG, 255, 0))
sky = Image.alpha_composite(sky, radial_gradient((W,H), (W//2, H//2), 700, (34,26,18), BG, 220, 0))
sky = Image.alpha_composite(sky, radial_gradient((W,H), (W//2, -200), 900, (75,46,32), BG, 140, 0))
sky = Image.alpha_composite(sky, radial_gradient((W,H), (W//2, H+200), 800, (32,42,48), BG, 110, 0))
# 远处云层/山脉剪影
cloud = Image.new('RGBA', (W,H), (0,0,0,0))
cd = ImageDraw.Draw(cloud)
for i in range(8):
    y_base = 120 + i * 25
    w = 150 + i * 30
    x = 50 + (i * 87) % (W - w)
    h = 30 + (i * 7) % 40
    cd.ellipse([x, y_base, x+w, y_base+h*2], fill=(18,14,11,60))
    cd.ellipse([x+20, y_base+10, x+w-20, y_base+h*2+15], fill=(14,11,9,80))
sky = Image.alpha_composite(sky, cloud)
img = Image.alpha_composite(img.convert('RGBA'), sky).convert('RGB')

# 暗角
vig = linear_gradient((W, 550), 'vertical', BG, (10,8,6,0))
img.paste(vig, (0, H-550), vig)
vig_top = linear_gradient((W, 220), 'vertical', (10,8,6,0), BG)
img.paste(vig_top, (0, 0), vig_top)

# ===== 右上角岁蚀侵蚀（更丰富） =====
erosion = radial_gradient((W,H), (W+60, -40), 550, (235,225,200), BG, 75, 0)
img = Image.alpha_composite(img.convert('RGBA'), erosion).convert('RGB')
# 主条痕
for i, (top, w, alpha) in enumerate([(35,380,40),(70,260,32),(105,310,28),(145,200,20),(185,150,12)]):
    line = Image.new('RGBA', (w, 4), (0,0,0,0))
    ld = ImageDraw.Draw(line)
    ld.rectangle([0,0,w,2], fill=(235,225,200,alpha))
    line = line.rotate(-8 - i*2, expand=True)
    img.paste(line, (W-w-10, top), line)
# 飘散的记忆碎片
random.seed(55)
frag = Image.new('RGBA', (W,H), (0,0,0,0))
fd = ImageDraw.Draw(frag)
for _ in range(40):
    x = random.randint(W-350, W)
    y = random.randint(20, 350)
    size = random.randint(2, 6)
    rot = random.randint(0, 180)
    alpha = random.randint(10, 28)
    # 小碎片多边形
    px = [x + random.randint(-size,size) for _ in range(4)]
    py = [y + random.randint(-size,size) for _ in range(4)]
    fd.polygon(list(zip(px,py)), fill=(230,220,195,alpha))
img = Image.alpha_composite(img.convert('RGBA'), frag).convert('RGB')

# ===== 石门 =====
door_x, door_y = 150, 190
door_w, door_h = 500, 740
door = Image.new('RGBA', (door_w, door_h), (0,0,0,0))
dd = ImageDraw.Draw(door)

# 门后黑暗底色
stone_base = (55, 48, 40)
dd.rectangle([0,0,door_w-1,door_h-1], fill=stone_base + (180,))

# 不规则石块拼接
random.seed(99)
for _ in range(85):
    x = random.randint(-35, door_w-5)
    y = random.randint(-35, door_h-5)
    w = random.randint(75, 170)
    h = random.randint(65, 145)
    v = random.randint(-20, 20)
    color = (stone_base[0]+v, stone_base[1]+v, stone_base[2]+v)
    pts = [
        (x + random.randint(-8,8), y + random.randint(-8,8)),
        (x + w + random.randint(-8,8), y + random.randint(-8,8)),
        (x + w + random.randint(-8,8), y + h + random.randint(-8,8)),
        (x + random.randint(-8,8), y + h + random.randint(-8,8))
    ]
    dd.polygon(pts, fill=color + (210,), outline=(50,42,36,75), width=1)

# 门框 + 破损
frame_w = 20
dd.rectangle([0,0,door_w-1,door_h-1], outline=(115,100,78,200), width=frame_w)
# 顶部破损
for _ in range(5):
    bx = random.randint(30, door_w-30)
    by = random.randint(5, 30)
    s = random.randint(8, 18)
    dd.polygon([
        (bx, by), (bx+s, by-s//2), (bx+s*1.5, by+s), (bx-s//2, by+s)
    ], fill=stone_base + (200,), outline=(65,55,45,45))
# 内框阴影
dd.rectangle([frame_w, frame_w, door_w-frame_w-1, door_h-frame_w-1], outline=(65,55,45,110), width=2)

# 门缝
center_x = door_w // 2
dd.line([(center_x, frame_w+10), (center_x, door_h-frame_w-10)], fill=(30,24,20,200), width=5)

# 裂纹
cracks = [
    (0.28,0.08,0.62,6),(0.52,0.12,0.48,-4),(0.40,0.28,0.40,11),
    (0.18,0.42,0.35,-8),(0.68,0.48,0.30,9),(0.46,0.62,0.22,2),
    (0.22,0.15,0.28,18),(0.64,0.08,0.35,-10),(0.34,0.55,0.18,-6),
    (0.45,0.75,0.15,14),(0.58,0.35,0.20,-12)
]
random.seed(42)
for cx, cy, ch, angle in cracks:
    x1 = int(cx * door_w)
    y1 = int(cy * door_h)
    rad = math.radians(angle)
    length = ch * door_h
    x2 = int(x1 + math.sin(rad) * length)
    y2 = int(y1 + math.cos(rad) * length)
    dd.line([(x1,y1),(x2,y2)], fill=(240,220,180,170), width=2)
    dd.line([(x1,y1),(x2,y2)], fill=(255,250,240,75), width=1)
    if random.random() > 0.25:
        mid = ((x1+x2)//2 + random.randint(-10,10), (y1+y2)//2 + random.randint(-10,10))
        br_len = int(length * 0.22)
        ang2 = rad + random.choice([0.6, -0.6])
        x3 = int(mid[0] + math.sin(ang2) * br_len)
        y3 = int(mid[1] + math.cos(ang2) * br_len)
        dd.line([mid,(x3,y3)], fill=(225,205,165,95), width=1)

# 门缝光
glow = Image.new('RGBA', (door_w, door_h), (0,0,0,0))
gd = ImageDraw.Draw(glow)
for y in range(frame_w+10, door_h-frame_w-10):
    rel_y = (y - (frame_w+10)) / (door_h - 2*frame_w - 20)
    fade = 1.0 - abs(rel_y - 0.5) * 1.8
    fade = max(0, fade)
    alpha = int(250 * fade)
    gd.line([(center_x-1, y), (center_x+1, y)], fill=(250,230,190,alpha))
    gd.line([(center_x-3, y), (center_x+3, y)], fill=(250,230,190,alpha//3))
    gd.line([(center_x-8, y), (center_x+8, y)], fill=(250,230,190,alpha//6))
glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
door = Image.alpha_composite(door, glow)
img.paste(door, (door_x, door_y), door)

# 门底部碎石
random.seed(77)
for _ in range(30):
    x = random.randint(door_x - 30, door_x + door_w + 30)
    y = random.randint(door_y + door_h - 30, door_y + door_h + 20)
    s = random.randint(4, 12)
    v = random.randint(-10, 10)
    color = (60+v, 52+v, 44+v)
    draw = ImageDraw.Draw(img)
    draw.polygon([
        (x, y), (x+s, y-s//2), (x+s*1.3, y+s), (x-s//2, y+s)
    ], fill=(color[0], color[1], color[2], 150))

# ===== 玉佩 =====
def draw_jade(size):
    j = Image.new('RGBA', (size, size), (0,0,0,0))
    jd = ImageDraw.Draw(j)
    jd.ellipse([4,4,size-4,size-4], fill=(190,220,205,110), outline=(180,230,210,170))
    hole = size // 4
    jd.ellipse([size//2-hole, size//2-hole, size//2+hole, size//2+hole], fill=(0,0,0,0), outline=(150,190,175,140), width=2)
    jd.arc([8,8,size-8,size-8], start=120, end=210, fill=(230,255,240,105), width=3)
    jd.arc([12,12,size-12,size-12], start=280, end=340, fill=(135,170,155,70), width=1)
    # 红色绳结暗示
    jd.ellipse([size//2-5, 0, size//2+5, 10], fill=(140,60,50,120))
    gl = Image.new('RGBA', (size,size), (0,0,0,0))
    gg = ImageDraw.Draw(gl)
    gg.ellipse([0,0,size,size], fill=(190,220,205,60))
    gl = gl.filter(ImageFilter.GaussianBlur(radius=12))
    return Image.alpha_composite(gl, j)

jade = draw_jade(120)
img.paste(jade, (W-175, H-500), jade)

# ===== 铜钱 =====
def draw_coin(size):
    c = Image.new('RGBA', (size, size), (0,0,0,0))
    cd = ImageDraw.Draw(c)
    outer = size - 4
    cd.ellipse([2,2,outer,outer], fill=(130,105,65,130), outline=(235,210,150,170), width=2)
    hole = size // 5
    cd.rectangle([size//2-hole, size//2-hole, size//2+hole, size//2+hole], fill=(0,0,0,0), outline=(235,210,150,120), width=2)
    sym = (235,210,150,105)
    cd.line([(size//2, 10), (size//2, size//2-hole-3)], fill=sym, width=2)
    cd.line([(size//2, size//2+hole+3), (size//2, size-10)], fill=sym, width=2)
    cd.line([(10, size//2), (size//2-hole-3, size//2)], fill=sym, width=2)
    cd.line([(size//2+hole+3, size//2), (size-10, size//2)], fill=sym, width=2)
    for angle in [45, 135, 225, 315]:
        rad = math.radians(angle)
        x1 = size//2 + int(math.cos(rad) * (outer//2 - 6))
        y1 = size//2 + int(math.sin(rad) * (outer//2 - 6))
        cd.ellipse([x1-1,y1-1,x1+1,y1+1], fill=(255,235,180,85))
    gl = Image.new('RGBA', (size,size), (0,0,0,0))
    gg = ImageDraw.Draw(gl)
    gg.ellipse([0,0,size,size], fill=(235,210,150,65))
    gl = gl.filter(ImageFilter.GaussianBlur(radius=10))
    return Image.alpha_composite(gl, c)

coin = draw_coin(82)
img.paste(coin, (75, H-445), coin)

# ===== 地面/旧货摊剪影 =====
market = Image.new('RGBA', (W, H), (0,0,0,0))
md = ImageDraw.Draw(market)
base_y = H - 260
# 地面渐变
for y in range(260):
    alpha = int(255 * max(0, (y-30)/230))
    md.line([(0,base_y+y),(W,base_y+y)], fill=(16,13,11,alpha))
# 旧货摊物品
items = [(55,75,50),(110,55,40),(160,95,45),(215,65,55),(275,105,40),(330,60,50),(390,90,45),(445,70,58),(510,100,42),(565,80,38)]
random.seed(11)
for x, h, w in items:
    top_y = base_y + 260 - h
    md.rectangle([x, top_y, x+w, base_y+260], fill=(68,58,46,240))
    md.polygon([(x, top_y), (x+4, top_y-6), (x+w-4, top_y-6), (x+w, top_y)], fill=(85,72,58,210))
    if random.random() > 0.5:
        md.line([(x+3, base_y+260-h//2), (x+w-3, base_y+260-h//2)], fill=(50,42,34,160), width=1)
    # 顶部小物件
    if random.random() > 0.6:
        md.ellipse([x+w//2-5, top_y-10, x+w//2+5, top_y], fill=(90,78,60,180))
# 地面散落的铜钱/碎片
for _ in range(15):
    x = random.randint(20, W-20)
    y = base_y + random.randint(30, 240)
    s = random.randint(3, 7)
    md.ellipse([x,y,x+s,y+s], fill=(120,105,75,100))
img = Image.alpha_composite(img.convert('RGBA'), market).convert('RGB')

# ===== 人物剪影 =====
fig = Image.new('RGBA', (45, 135), (0,0,0,0))
fd = ImageDraw.Draw(fig)
body_pts = [(22,9),(34,32),(37,73),(36,124),(27,135),(18,135),(9,124),(8,73),(11,32)]
fd.polygon(body_pts, fill=(200,190,170,70))
fd.ellipse([17,0,29,18], fill=(200,190,170,60))
# 衣摆
cape = [(22,35),(42,50),(38,95),(22,110),(6,95),(2,50)]
fd.polygon(cape, fill=(180,165,140,35))
img.paste(fig, (W//2+18, H-275), fig)

# ===== 前景飘带/落叶 =====
ribbon = Image.new('RGBA', (W,H), (0,0,0,0))
rd = ImageDraw.Draw(ribbon)
random.seed(88)
# 飘落的红绳/布条
for _ in range(25):
    x = random.randint(0, W)
    y = random.randint(100, H-100)
    length = random.randint(30, 80)
    rot = random.randint(0, 180)
    alpha = random.randint(20, 50)
    color = random.choice([(120,55,45,alpha//2),(140,70,55,alpha//2),(110,50,40,alpha//2)])
    # 小曲线
    for i in range(length):
        px = x + int(math.cos(math.radians(rot)) * i) + int(math.sin(i*0.2)*3)
        py = y + int(math.sin(math.radians(rot)) * i)
        rd.ellipse([px-1, py-1, px+1, py+1], fill=color)
# 飘落的老槐树叶
for _ in range(20):
    x = random.randint(0, W)
    y = random.randint(50, H-200)
    size = random.randint(4, 8)
    rot = random.randint(0, 180)
    alpha = random.randint(25, 55)
    rd.ellipse([x,y,x+size,y+size*2], fill=(160,130,80,alpha//2))
img = Image.alpha_composite(img.convert('RGBA'), ribbon).convert('RGB')

# ===== 文字层 =====
font_title = ImageFont.truetype('/c/Windows/Fonts/NotoSerifSC-VF.ttf', 140)
font_sub = ImageFont.truetype('/c/Windows/Fonts/NotoSerifSC-VF.ttf', 28)
font_tag = ImageFont.truetype('/c/Windows/Fonts/NotoSerifSC-VF.ttf', 20)
font_author = ImageFont.truetype('/c/Windows/Fonts/NotoSerifSC-VF.ttf', 20)
font_genre = ImageFont.truetype('/c/Windows/Fonts/NotoSerifSC-VF.ttf', 18)

text_layer = Image.new('RGBA', (W,H), (0,0,0,0))
title_pos = (45, H-405)
for radius, alpha in [(55, 40), (35, 55), (18, 70)]:
    glow = Image.new('RGBA', (W,H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.text(title_pos, "岁蚀", font=font_title, fill=(215,195,140,alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius))
    text_layer = Image.alpha_composite(text_layer, glow)
td = ImageDraw.Draw(text_layer)
td.text(title_pos, "岁蚀", font=font_title, fill=(255,248,225,255))
td.line([(45, H-245), (165, H-245)], fill=(235,225,200,90), width=1)
td.text((45, H-225), "一扇门 · 三枚铜钱 · 两种未来", font=font_sub, fill=(235,225,200,130))
td.text((45, H-170), "玄幻 · 东方经典", font=font_tag, fill=(235,225,200,85))
# 作者名：翻遍古籍找名字
author_text = "翻遍古籍找名字"
bbox = td.textbbox((0,0), author_text, font=font_author)
author_w = bbox[2] - bbox[0]
td.text((W-author_w-45, H-75), author_text, font=font_author, fill=(235,225,200,85))
for i, ch in enumerate("玄 幻"):
    td.text((W-55, 35+i*22), ch, font=font_genre, fill=(235,225,200,70))

img = Image.alpha_composite(img.convert('RGBA'), text_layer).convert('RGB')

# ===== 飘散灰烬/光点 =====
random.seed(321)
for _ in range(150):
    x = random.randint(0, W)
    y = random.randint(0, H-250)
    size = random.choice([1,2,2,3])
    alpha = random.choice([40,50,65,30,20])
    draw = ImageDraw.Draw(img)
    draw.ellipse([x,y,x+size,y+size], fill=(230,215,185,alpha))

# 顶部飘落的光尘
for _ in range(50):
    x = random.randint(0, W)
    y = random.randint(0, 250)
    size = random.choice([1,2])
    alpha = random.randint(15, 40)
    draw.ellipse([x,y,x+size,y+size], fill=(255,235,200,alpha))

add_noise(img, 0.03)
img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=40, threshold=3))

# 最终提亮对比
from PIL import ImageEnhance
img = ImageEnhance.Brightness(img).enhance(1.08)
img = ImageEnhance.Contrast(img).enhance(1.1)

img.save('docs/封面设计/cover_800x1200.jpg', 'JPEG', quality=95)
img.save('docs/封面设计/cover_800x1200.png', 'PNG')
print('saved')
