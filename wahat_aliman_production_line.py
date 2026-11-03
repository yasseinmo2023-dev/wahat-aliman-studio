#!/usr/bin/env python3
import os, re, math, argparse, subprocess
from PIL import Image, ImageDraw, ImageFont

FONT_NASKH_BOLD = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
FONT_SANS_REG = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def clean_arabic_text(txt: str) -> str:
    txt = re.sub(r"۝([٠-٩]+)", r"﴿\1﴾", txt)
    return txt.replace("—", "-").replace("–", "-").replace("|", ":").replace("(", "«").replace(")", "»").strip()

def format_mmss(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

def create_golden_sunset_backdrop(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    horizon_y = int(height * 0.52)
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        draw.line([(0, y), (width, y)], fill=(int(14 + 185 * (t ** 1.5)), int(28 + 115 * (t ** 1.3)), int(48 + 45 * (1 - t))))
    for y in range(horizon_y, height):
        t = (y - horizon_y) / max(1, height - horizon_y)
        w = int(8 * math.sin(y * 0.18))
        draw.line([(0, y), (width, y)], fill=(max(6, min(255, int(110 * (1 - t) + 8 + w))), max(16, min(255, int(85 * (1 - t) + 32 + w))), max(24, min(255, int(65 * (1 - t) + 42 + w)))))
    return img

def wrap_arabic_text(draw, text, font, max_width):
    words = text.split()
    if not words: return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        test = cur + " " + w
        bbox = draw.textbbox((0, 0), test, font=font, direction="rtl", language="ar")
        if (bbox[2] - bbox[0]) <= max_width: cur = test
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines

def render_slide(base_img, out_path, start_s, total_dur, main_text, surah_title, reflection_text, is_verse=True):
    W, H = 1280, 720
    canvas = base_img.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((40, 28, 440, 82), radius=14, fill=(8, 36, 32, 220), outline=(212, 175, 55, 225), width=2)
    draw.text((240, 53), "قناة واحة الإيمان : جلسات نور", font=ImageFont.truetype(FONT_SANS_BOLD, 21), fill=(245, 222, 130, 255), anchor="mm", direction="rtl", language="ar")
    draw.rounded_rectangle((740, 28, 1240, 82), radius=14, fill=(12, 28, 38, 220), outline=(80, 190, 150, 200), width=2)
    draw.text((990, 53), clean_arabic_text(surah_title), font=ImageFont.truetype(FONT_SANS_BOLD, 20), fill=(255, 255, 255, 255), anchor="mm", direction="rtl", language="ar")
    card_x1, card_y1, card_x2, card_y2 = 160, 160, 1120, 515
    draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=24, fill=(6, 20, 26, 190), outline=(212, 175, 55, 195), width=2)
    cleaned_main = clean_arabic_text(main_text)
    font_size = 46 if is_verse else 32
    font_main = ImageFont.truetype(FONT_NASKH_BOLD if is_verse else FONT_SANS_BOLD, font_size)
    lines = wrap_arabic_text(draw, cleaned_main, font_main, (card_x2 - card_x1) - 80)
    line_h = font_size + 24
    start_y = (card_y1 + card_y2) // 2 - (len(lines) * line_h) // 2 + line_h // 2
    for idx, line in enumerate(lines):
        cy = start_y + idx * line_h
        draw.text((642, cy + 3), line, font=font_main, fill=(0, 0, 0, 225), anchor="mm", direction="rtl", language="ar")
        draw.text((640, cy), line, font=font_main, fill=(255, 250, 235, 255), anchor="mm", direction="rtl", language="ar")
    draw.rounded_rectangle((40, 558, 1240, 622), radius=14, fill=(8, 32, 28, 215), outline=(60, 160, 130, 175), width=1)
    draw.text((640, 588), clean_arabic_text(reflection_text), font=ImageFont.truetype(FONT_SANS_REG, 20), fill=(225, 248, 238, 255), anchor="mm", direction="rtl", language="ar")
    prog = min(1.0, max(0.0, start_s / max(1.0, total_dur)))
    draw.rounded_rectangle((40, 655, 1060, 671), radius=8, fill=(255, 255, 255, 45))
    draw.rounded_rectangle((40, 655, 40 + max(16, int(1020 * prog)), 671), radius=8, fill=(212, 175, 55, 240))
    draw.rounded_rectangle((1080, 642, 1240, 684), radius=10, fill=(10, 24, 30, 225), outline=(212, 175, 55, 185), width=1)
    draw.text((1160, 663), f"{format_mmss(start_s)} / {format_mmss(total_dur)}", font=ImageFont.truetype(FONT_MONO, 18), fill=(245, 222, 130, 255), anchor="mm")
    Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB").save(out_path, "JPEG", quality=92)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep", type=int, default=1)
    parser.add_argument("--surah", default="سورة الضحى والشرح : جلسات نور")
    parser.add_argument("--reflection", default="إشراقة تدبرية : العسر واحد ، واليسر مرتان «فلن يغلب عسر يسرين»")
    parser.add_argument("--loop", type=int, default=1)
    parser.add_argument("--out-dir", default="output")
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    slides_dir = os.path.join(args.out_dir, "_slides")
    os.makedirs(slides_dir, exist_ok=True)
    base_img = create_golden_sunset_backdrop(1280, 720)
    total_dur = 900.0 * max(1, args.loop)
    verses = [
        (0.0, 45.0, "تَخَفَّف الآن من شواغل يومك ، وخذ نفساً عميقاً ، وأصغِ بقلبك لنداء ربك : «مَا وَدَّعَكَ رَبُّكَ وَمَا قَلَىٰ»", False),
        (45.0, 180.0, "وَٱلضُّحَىٰ ﴿١﴾ وَٱلَّيْلِ إِذَا سَجَىٰ ﴿٢﴾ مَا وَدَّعَكَ رَبُّكَ وَمَا قَلَىٰ ﴿٣﴾ وَلَلْءَاخِرَةُ خَيْرٌۭ لَّكَ مِنَ ٱلْأُولَىٰ ﴿٤﴾ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰٓ ﴿٥﴾", True),
        (180.0, 360.0, "أَلَمْ نَشْرَحْ لَكَ صَدْرَكَ ﴿١﴾ وَوَضَعْنَا عَنكَ وِزْرَكَ ﴿٢﴾ ٱلَّذِىٓ أَنقَضَ ظَهْرَكَ ﴿٣﴾ وَرَفَعْنَا لَكَ ذِكْرَكَ ﴿٤﴾ فَإِنَّ مَعَ ٱلْعُسْرِ يُسْرًا ﴿٥﴾ إِنَّ مَعَ ٱلْعُسْرِ يُسْرًۭا ﴿٦﴾", True),
        (360.0, 600.0, "وَٱلتِّينِ وَٱلزَّيْتُونِ ﴿١﴾ وَطُورِ سِينِينَ ﴿٢﴾ وَهَٰذَا ٱلْبَلَدِ ٱلْأَمِينِ ﴿٣﴾ لَقَدْ خَلَقْنَا ٱلْإِنسَٰنَ فِىٓ أَحْسَنِ تَقْوِيمٍۢ ﴿٤﴾", True),
        (600.0, 850.0, "ٱقْرَأْ بِٱسْمِ رَبِّكَ ٱلَّذِى خَلَقَ ﴿١﴾ خَلَقَ ٱلْإِنسَٰنَ مِنْ عَلَقٍ ﴿٢﴾ ٱقْرَأْ وَرَبُّكَ ٱلْأَكْرَمُ ﴿٣﴾ ... كَلَّا لَا تُطِعْهُ وَٱسْجُدْ وَٱقْتَرِب ۩ ﴿١٩﴾", True),
        (850.0, total_dur, "اللهم اشرح بالقرآن صدورنا ويسّر به أمورنا — لا تنسوا الإعجاب والاشتراك في قناة «واحة الإيمان»", False),
    ]
    concat_path = os.path.join(slides_dir, "concat.txt")
    with open(concat_path, "w", encoding="utf-8") as cf:
        cf.write("ffconcat version 1.0\n")
        for i, (s, e, txt, is_v) in enumerate(verses):
            sp = os.path.join(slides_dir, f"s_{i:02d}.jpg")
            render_slide(base_img, sp, s, total_dur, txt, args.surah, args.reflection, is_v)
            cf.write(f"file '{os.path.abspath(sp)}'\nduration {e - s:.3f}\n")
        cf.write(f"file '{os.path.abspath(sp)}'\n")
    out_mp4 = os.path.join(args.out_dir, f"jalsat_noor_ep{args.ep}_15min.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path, "-f", "lavfi", "-i", f"anoisesrc=d={int(total_dur)}:c=pink:r=44100:a=0.035,lowpass=f=380,tremolo=f=0.14:d=0.65", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-vf", "fps=12,format=yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-t", str(int(total_dur)), out_mp4], check=True)
