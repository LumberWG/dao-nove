from playwright.sync_api import sync_playwright
import os
from PIL import Image

html_path = os.path.abspath('docs/封面设计/cover.html')
output_png = 'docs/封面设计/cover_render_1600x2400.png'
output_jpg_800 = 'docs/封面设计/cover_800x1200.jpg'
output_png_800 = 'docs/封面设计/cover_800x1200.png'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 800, 'height': 1200}, device_scale_factor=2)
    page.goto(f'file:///{html_path.replace(chr(92), "/")}')
    page.wait_for_timeout(2500)
    page.screenshot(path=output_png, full_page=False)
    browser.close()

# 缩放为 800x1200
img = Image.open(output_png).convert('RGB')
img_800 = img.resize((800, 1200), Image.Resampling.LANCZOS)
img_800.save(output_jpg_800, 'JPEG', quality=95)
img_800.save(output_png_800, 'PNG')
print(f'saved: {output_jpg_800}, {output_png_800}')
