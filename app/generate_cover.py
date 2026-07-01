"""生成《岁蚀》封面 v6 —— 铜钱刻符，毛笔竖排书名右上"""
import os, requests
from g4f.client import Client

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "cover.webp")

PROMPT = (
    "Chinese fantasy novel book cover, wuxia/xuanhuan literary fiction, 2:3 vertical --\n\n"
    "TOP-RIGHT CORNER: Two large vertical calligraphy characters '岁蚀' in traditional ink brush style, one above the other, bold black ink with visible brush tip锋 (sharp starting strokes, flying white texture). The characters should feel like they were brushed onto rough paper -- powerful, irregular edges, splatter dots. Aged gold/copper color ink, not plain black. Positioned in upper right quadrant, commanding attention.\n\n"
    "CENTER-LEFT: A single very large ancient bronze coin (about 1/3 cover width), dark oxidized bronze with green patina. The coin is covered in ancient mystical TALISMAN SYMBOLS (符箓) -- abstract swirling patterns, seal-script-derived talisman strokes, thunder charms, not readable characters. The symbols glow faintly with warm golden light from within the grooves.\n"
    "The coin has a square hole in center. Through the hole: a distant stone door embedded in cliff rock, warm amber light spilling through the door crack.\n\n"
    "RIGHT SIDE, behind the coin: A vertically hanging celadon jade pendant, cracked, golden hairline fractures spreading from the break like lightning. Red silk cord at top.\n\n"
    "Two smaller bronze coins floating at different depths, connected to the main coin by thin threads of golden light.\n\n"
    "Background: Deep misty ink-wash mountain silhouettes, dark atmospheric sky with subtle golden crack patterns like fractured porcelain. Fog at bottom. Ancient stone threshold, weathered rock, a single wild orchid growing from a crack.\n\n"
    "NO other text. Only the two calligraphy title characters in top-right corner. The coin has talisman symbols, not readable words.\n\n"
    "STYLE: Fine art book cover, traditional Chinese ink painting + subtle luminous effects. Dark moody. Colors: ink black, aged copper, bronze green, celadon jade, warm gold. Premium literary fiction."
)

def generate():
    client = Client()
    print("正在生成封面 v6（铜钱刻符+毛笔竖排右上），请稍候...")
    try:
        response = client.images.generate(
            model="flux",
            prompt=PROMPT,
            response_format="url"
        )
        url = response.data[0].url
        print(f"生成成功: {url}")

        img_data = requests.get(url, timeout=60).content
        with open(OUTPUT, "wb") as f:
            f.write(img_data)
        print(f"已保存: {OUTPUT} ({len(img_data)//1024}KB)")
        return True
    except Exception as e:
        print(f"生成失败: {e}")
        return False

if __name__ == "__main__":
    generate()
