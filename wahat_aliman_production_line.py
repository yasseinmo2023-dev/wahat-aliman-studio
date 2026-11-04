#!/usr/bin/env python3
import os, re, math, argparse, subprocess
from PIL import Image, ImageDraw, ImageFont

FONT_NASKH_BOLD = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
FONT_SANS_REG = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
FONT_MONO = "/usr/share/fonts/tr#!/usr/bin/env python3
import os, re, math, json, urllib.request, argparse, subprocess
from PIL import Image, ImageDraw, ImageFont

FONT_NASKH_BOLD = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
FONT_SANS_REG = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

RECITERS = {
    "minshawi_murattal": {"name": "الشيخ محمد صديق المنشاوي", "folder": "Minshawy_Murattal_128kbps"},
    "minshawi_mujawwad": {"name": "الشيخ محمد صديق المنشاوي «مجود»", "folder": "Minshawy_Mujawwad_192kbps"},
    "abdulbasit_murattal": {"name": "الشيخ عبد الباسط عبد الصمد", "folder": "Abdul_Basit_Murattal_192kbps"},
    "abdulbasit_mujawwad": {"name": "الشيخ عبد الباسط عبد الصمد «مجود»", "folder": "Abdul_Basit_Mujawwad_128kbps"},
}

THEMES_MATRIX = {
    1: {
        "theme_key": "golden_sunset",
        "topic_name": "جبر الخواطر والسكينة لعلاج الضيق والقلق",
        "reciter": "minshawi_murattal",
        "surahs": [93, 94, 95, 96, 102, 1],
        "seo_title": "لكل مهموم ضاق صدره.. 15 دقيقة من السكينة وجبر الخواطر بصوت الشيخ محمد صديق المنشاوي | جلسات نور",
        "reflection": "إشراقة تدبرية : العسر واحد ، واليسر مرتان «فلن يغلب عسر يسرين»",
        "reels_hook": "إذا شعرت اليوم أن الأبواب أُغلقت في وجهك .. فتوقف لثوانٍ واسمع نداء ربك :",
    },
    2: {
        "theme_key": "emerald_dawn",
        "topic_name": "آيات الرزق والبركة والفرج وإتقان العمل",
        "reciter": "abdulbasit_murattal",
        "surahs": [56],
        "seo_title": "سورة الواقعة كاملة بصوت الشيخ عبد الباسط عبد الصمد — 15 دقيقة من الطمأنينة وآيات الرزق والبركة | واحة الإيمان",
        "reflection": "إشراقة تدبرية : التقوى وإتقان العمل والتوكل على الله مفاتيح البركة في الرزق والوقت",
        "reels_hook": "هل تبحث عن سر البركة في رزقك ووقتك ؟ استمع لهذه الآيات العظيمة :",
    },
    3: {
        "theme_key": "night_stars",
        "topic_name": "الحفظ المسائي والسكينة العميقة قبل النوم",
        "reciter": "minshawi_murattal",
        "surahs": [67, 109, 112, 113, 114],
        "seo_title": "سورة الملك والمعوذات بصوت الشيخ محمد صديق المنشاوي — 15 دقيقة تريح الأعصاب وتبعث الطمأنينة قبل النوم",
        "reflection": "إشراقة تدبرية : سورة الملك هي المانعة والمنجية ، نورٌ ووقايةٌ للمؤمن في كل ليلة",
        "reels_hook": "قبل أن تغمض عينيك الليلة .. لا تحرم قلبك من سماع هذه الآيات المنجية :",
    },
    4: {
        "theme_key": "ocean_twilight",
        "topic_name": "عروس القرآن والتأمل في آلاء الله ونعمه",
        "reciter": "abdulbasit_murattal",
        "surahs": [55],
        "seo_title": "سورة الرحمن بصوت يأسر القلوب للشيخ عبد الباسط عبد الصمد — 15 دقيقة من السكينة والتأمل | جلسات نور",
        "reflection": "إشراقة تدبرية : «فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ» - بالشكر تدوم النعم وتنزل البركات",
        "reels_hook": "تلاوة خاشعة تلامس القلوب وتزيل هموم الدنيا .. استمع وتأمل :",
    },
}

def clean_arabic_text(txt: str) -> str:
    txt = re.sub(r"۝([٠-٩]+)", r"﴿\1﴾", txt)
    return txt.replace("—", "-").replace("–", "-").replace("|", ":").replace("(", "«").replace(")", "»").strip()

def to_arabic_digits(n: int) -> str:
    return str(n).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

def format_mmss(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

def format_srt_time(seconds: float) -> str:
    hrs, mins, secs = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{min(999, ms):03d}"

def create_theme_backdrop(width: int, height: int, theme_key: str) -> Image.Image:
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    horizon_y = int(height * 0.54)
    palettes = {
        "golden_sunset": ((14, 28, 48), (195, 135, 55), (10, 35, 42)),
        "emerald_dawn": ((8, 32, 28), (65, 165, 130), (6, 24, 28)),
        "night_stars": ((6, 12, 28), (38, 68, 115), (5, 14, 26)),
        "ocean_twilight": ((18, 22, 52), (165, 95, 110), (10, 26, 44)),
    }
    top_c, mid_c, bot_c = palettes.get(theme_key, palettes["golden_sunset"])
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        draw.line([(0, y), (width, y)], fill=(int(top_c[0] + (mid_c[0] - top_c[0]) * (t ** 1.3)), int(top_c[1] + (mid_c[1] - top_c[1]) * (t ** 1.3)), int(top_c[2] + (mid_c[2] - top_c[2]) * (t ** 1.1))))
    for y in range(horizon_y, height):
        t = (y - horizon_y) / max(1, height - horizon_y)
        w = int(7 * math.sin(y * 0.16))
        draw.line([(0, y), (width, y)], fill=(max(4, min(255, int(mid_c[0] * (1 - t) * 0.65 + bot_c[0] + w))), max(10, min(255, int(mid_c[1] * (1 - t) * 0.65 + bot_c[1] + w))), max(16, min(255, int(mid_c[2] * (1 - t) * 0.65 + bot_c[2] + w)))))
    return img

def fetch_surah_data_and_audio(surah_num: int, reciter_folder: str, audio_dir: str) -> tuple:
    url = f"https://api.alquran.cloud/v1/surah/{surah_num}/quran-uthmani"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))["data"]
    surah_name = payload["name"]
    items = []
    for ay in payload["ayahs"]:
        ay_num = ay["numberInSurah"]
        txt = ay["text"].strip() + f" ﴿{to_arabic_digits(ay_num)}﴾"
        mp3_name = f"{surah_num:03d}{ay_num:03d}.mp3"
        mp3_path = os.path.join(audio_dir, mp3_name)
        if not os.path.exists(mp3_path):
            mp3_url = f"https://everyayah.com/data/{reciter_folder}/{mp3_name}"
            r_mp3 = urllib.request.Request(mp3_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(r_mp3, timeout=25) as m_resp, open(mp3_path, "wb") as out_f:
                out_f.write(m_resp.read())
        dur_out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_path]).decode().strip()
        items.append({"surah_name": surah_name, "ayah_num": ay_num, "text": txt, "mp3": mp3_path, "duration": max(1.5, float(dur_out))})
    return surah_name, items

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

def render_16_9_slide(base_img, out_path, start_s, total_dur, main_text, surah_title, reciter_name, reflection_text):
    W, H = 1280, 720
    canvas = base_img.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((40, 28, 470, 82), radius=14, fill=(8, 36, 32, 225), outline=(212, 175, 55, 225), width=2)
    draw.text((255, 53), clean_arabic_text(f"واحة الإيمان : {reciter_name}"), font=ImageFont.truetype(FONT_SANS_BOLD, 19), fill=(245, 222, 130, 255), anchor="mm", direction="rtl", language="ar")
    draw.rounded_rectangle((750, 28, 1240, 82), radius=14, fill=(12, 28, 38, 225), outline=(80, 190, 150, 200), width=2)
    draw.text((995, 53), clean_arabic_text(surah_title), font=ImageFont.truetype(FONT_SANS_BOLD, 20), fill=(255, 255, 255, 255), anchor="mm", direction="rtl", language="ar")
    card_x1, card_y1, card_x2, card_y2 = 110, 145, 1170, 520
    draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=26, fill=(6, 20, 26, 195), outline=(212, 175, 55, 205), width=2)
    draw.line([(card_x1 + 180, card_y1 + 52), (card_x2 - 180, card_y1 + 52)], fill=(212, 175, 55, 135), width=2)
    draw.text((640, card_y1 + 27), "۞ جلسات نور للتدبر والسكينة ۞", font=ImageFont.truetype(FONT_SANS_BOLD, 17), fill=(212, 175, 55, 245), anchor="mm", direction="rtl", language="ar")
    cleaned_main = clean_arabic_text(main_text)
    font_size = 48 if len(cleaned_main) < 65 else (40 if len(cleaned_main) < 130 else 33)
    font_main = ImageFont.truetype(FONT_NASKH_BOLD, font_size)
    lines = wrap_arabic_text(draw, cleaned_main, font_main, (card_x2 - card_x1) - 90)
    line_h = font_size + 24
    start_y = (card_y1 + 60 + card_y2 - 20) // 2 - (len(lines) * line_h) // 2 + line_h // 2
    for idx, line in enumerate(lines[:5]):
        cy = start_y + idx * line_h
        draw.text((642, cy + 3), line, font=font_main, fill=(0, 0, 0, 230), anchor="mm", direction="rtl", language="ar")
        draw.text((640, cy), line, font=font_main, fill=(255, 250, 235, 255), anchor="mm", direction="rtl", language="ar")
    draw.rounded_rectangle((40, 558, 1240, 622), radius=14, fill=(8, 32, 28, 220), outline=(60, 160, 130, 180), width=1)
    draw.text((640, 588), clean_arabic_text(reflection_text), font=ImageFont.truetype(FONT_SANS_REG, 20), fill=(225, 248, 238, 255), anchor="mm", direction="rtl", language="ar")
    prog = min(1.0, max(0.0, start_s / max(1.0, total_dur)))
    draw.rounded_rectangle((40, 655, 1060, 671), radius=8, fill=(255, 255, 255, 45))
    draw.rounded_rectangle((40, 655, 40 + max(16, int(1020 * prog)), 671), radius=8, fill=(212, 175, 55, 240))
    draw.rounded_rectangle((1080, 642, 1240, 684), radius=10, fill=(10, 24, 30, 225), outline=(212, 175, 55, 185), width=1)
    draw.text((1160, 663), f"{format_mmss(start_s)} / {format_mmss(total_dur)}", font=ImageFont.truetype(FONT_MONO, 18), fill=(245, 222, 130, 255), anchor="mm")
    Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB").save(out_path, "JPEG", quality=92)

def render_9_16_slide(base_img, out_path, start_s, total_dur, main_text, surah_title, reciter_name, reflection_text):
    W, H = 1080, 1920
    canvas = base_img.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((140, 110, 940, 190), radius=40, fill=(8, 36, 32, 230), outline=(212, 175, 55, 230), width=3)
    draw.text((540, 148), clean_arabic_text(f"واحة الإيمان : {reciter_name}"), font=ImageFont.truetype(FONT_SANS_BOLD, 27), fill=(245, 222, 130, 255), anchor="mm", direction="rtl", language="ar")
    draw.rounded_rectangle((220, 220, 860, 285), radius=18, fill=(14, 28, 38, 220), outline=(80, 190, 150, 195), width=2)
    draw.text((540, 251), clean_arabic_text(surah_title), font=ImageFont.truetype(FONT_SANS_BOLD, 24), fill=(225, 248, 238, 255), anchor="mm", direction="rtl", language="ar")
    card_x1, card_y1, card_x2, card_y2 = 70, 420, 1010, 1360
    draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=36, fill=(6, 20, 26, 200), outline=(212, 175, 55, 220), width=3)
    draw.text((540, card_y1 + 48), "۞ نداء السكينة والتدبر ۞", font=ImageFont.truetype(FONT_SANS_BOLD, 25), fill=(212, 175, 55, 250), anchor="mm", direction="rtl", language="ar")
    cleaned_main = clean_arabic_text(main_text)
    font_size = 58 if len(cleaned_main) < 60 else (46 if len(cleaned_main) < 120 else 38)
    font_main = ImageFont.truetype(FONT_NASKH_BOLD, font_size)
    lines = wrap_arabic_text(draw, cleaned_main, font_main, (card_x2 - card_x1) - 100)
    line_h = font_size + 32
    start_y = (card_y1 + 100 + card_y2 - 140) // 2 - (len(lines) * line_h) // 2 + line_h // 2
    for idx, line in enumerate(lines[:6]):
        cy = start_y + idx * line_h
        draw.text((543, cy + 4), line, font=font_main, fill=(0, 0, 0, 230), anchor="mm", direction="rtl", language="ar")
        draw.text((540, cy), line, font=font_main, fill=(255, 250, 235, 255), anchor="mm", direction="rtl", language="ar")
    draw.rounded_rectangle((105, card_y2 - 130, 975, card_y2 - 38), radius=20, fill=(12, 48, 42, 225), outline=(80, 190, 150, 165), width=1)
    draw.text((540, card_y2 - 84), clean_arabic_text(reflection_text), font=ImageFont.truetype(FONT_SANS_REG, 23), fill=(230, 250, 240, 255), anchor="mm", direction="rtl", language="ar")
    prog = min(1.0, max(0.0, start_s / max(1.0, total_dur)))
    draw.rounded_rectangle((90, 1740, 990, 1762), radius=10, fill=(255, 255, 255, 60))
    draw.rounded_rectangle((90, 1740, 90 + max(20, int(900 * prog)), 1762), radius=10, fill=(212, 175, 55, 250))
    draw.text((540, 1815), "اضغط على الفيديو المرتبط بالأسفل للاستماع للجلسة الكاملة «١٥ دقيقة»", font=ImageFont.truetype(FONT_SANS_BOLD, 24), fill=(245, 222, 130, 255), anchor="mm", direction="rtl", language="ar")
    Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB").save(out_path, "JPEG", quality=92)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep", type=int, default=1)
    parser.add_argument("--reciter", default="auto")
    parser.add_argument("--target-minutes", type=int, default=15)
    parser.add_argument("--out-dir", default="output")
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    audio_dir = os.path.join(args.out_dir, "_audio_cache")
    slides_16_9_dir = os.path.join(args.out_dir, "_slides_16_9")
    slides_9_16_dir = os.path.join(args.out_dir, "_slides_9_16")
    os.makedirs(audio_dir, exist_ok=True); os.makedirs(slides_16_9_dir, exist_ok=True); os.makedirs(slides_9_16_dir, exist_ok=True)
    plan = THEMES_MATRIX[((args.ep - 1) % 4) + 1]
    reciter_key = plan["reciter"] if args.reciter == "auto" else args.reciter
    reciter_info = RECITERS.get(reciter_key, RECITERS["minshawi_murattal"])
    all_ayahs, chapters_log = [], []
    for s_num in plan["surahs"]:
        _, items = fetch_surah_data_and_audio(s_num, reciter_info["folder"], audio_dir)
        all_ayahs.extend(items)
    target_sec = float(args.target_minutes * 60)
    timeline, cur_t, last_surah = [], 0.0, None
    while cur_t < target_sec:
        for item in all_ayahs:
            if cur_t >= target_sec: break
            if item["surah_name"] != last_surah:
                chapters_log.append((cur_t, item["surah_name"]))
                last_surah = item["surah_name"]
            dur = item["duration"]
            timeline.append({"start": cur_t, "end": cur_t + dur, "duration": dur, "surah_name": item["surah_name"], "text": item["text"], "mp3": item["mp3"]})
            cur_t += dur
    total_dur = cur_t
    base_16_9 = create_theme_backdrop(1280, 720, plan["theme_key"])
    base_9_16 = create_theme_backdrop(1080, 1920, plan["theme_key"])
    v_concat = os.path.join(slides_16_9_dir, "v_concat.txt")
    a_concat = os.path.join(slides_16_9_dir, "a_concat.txt")
    srt_path = os.path.join(args.out_dir, f"jalsat_noor_ep{args.ep}_subtitles.srt")
    with open(v_concat, "w", encoding="utf-8") as vf, open(a_concat, "w", encoding="utf-8") as af, open(srt_path, "w", encoding="utf-8") as sf:
        vf.write("ffconcat version 1.0\n"); af.write("ffconcat version 1.0\n")
        for idx, seg in enumerate(timeline):
            sp = os.path.join(slides_16_9_dir, f"s_{idx:04d}.jpg")
            render_16_9_slide(base_16_9, sp, seg["start"], total_dur, seg["text"], f"{seg['surah_name']} : جلسات نور", reciter_info["name"], plan["reflection"])
            vf.write(f"file '{os.path.abspath(sp)}'\nduration {seg['duration']:.3f}\n")
            af.write(f"file '{os.path.abspath(seg['mp3'])}'\n")
            sf.write(f"{idx+1}\n{format_srt_time(seg['start'])} --> {format_srt_time(seg['end'])}\n{seg['text']}\n\n")
        vf.write(f"file '{os.path.abspath(sp)}'\n")
    recitation_wav = os.path.join(slides_16_9_dir, "full_recitation.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", a_concat, "-c", "copy", recitation_wav], check=True)
    out_15m_mp4 = os.path.join(args.out_dir, f"jalsat_noor_ep{args.ep}_15min.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_concat, "-i", recitation_wav, "-f", "lavfi", "-i", f"anoisesrc=d={int(total_dur)}:c=pink:r=44100:a=0.018,lowpass=f=360,tremolo=f=0.14:d=0.65", "-filter_complex", "[1:a]volume=1.0[rec];[2:a]volume=0.20[amb];[rec][amb]amix=inputs=2:duration=first[aout]", "-map", "0:v", "-map", "[aout]", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-vf", "fps=12,format=yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-t", str(int(total_dur)), out_15m_mp4], check=True)
    reels_segs, r_cur = [], 0.0
    for seg in timeline:
        if r_cur >= 50.0 and len(reels_segs) >= 3: break
        reels_segs.append(seg); r_cur += seg["duration"]
    rv_concat = os.path.join(slides_9_16_dir, "rv_concat.txt")
    ra_concat = os.path.join(slides_9_16_dir, "ra_concat.txt")
    with open(rv_concat, "w", encoding="utf-8") as rvf, open(ra_concat, "w", encoding="utf-8") as raf:
        rvf.write("ffconcat version 1.0\n"); raf.write("ffconcat version 1.0\n")
        for idx, seg in enumerate(reels_segs):
            rsp = os.path.join(slides_9_16_dir, f"r_{idx:03d}.jpg")
            render_9_16_slide(base_9_16, rsp, seg["start"], r_cur, seg["text"], f"{seg['surah_name']} : واحة الإيمان", reciter_info["name"], plan["reels_hook"])
            rvf.write(f"file '{os.path.abspath(rsp)}'\nduration {seg['duration']:.3f}\n")
            raf.write(f"file '{os.path.abspath(seg['mp3'])}'\n")
        rvf.write(f"file '{os.path.abspath(rsp)}'\n")
    reels_audio = os.path.join(slides_9_16_dir, "reels_rec.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ra_concat, "-c", "copy", reels_audio], check=True)
    out_reels_mp4 = os.path.join(args.out_dir, f"reels_ep{args.ep}_short_9_16.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", rv_concat, "-i", reels_audio, "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-vf", "fps=15,format=yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", out_reels_mp4], check=True)
    seo_file = os.path.join(args.out_dir, f"youtube_seo_ep{args.ep}.txt")
    with open(seo_file, "w", encoding="utf-8") as seof:
        seof.write(f"العنوان المقترح لليوتيوب (High-CTR):\n{plan['seo_title']}\n\nالقارئ: {reciter_info['name']}\nالموضوع: {plan['topic_name']}\n\nصندوق الوصف والفصول الزمنية:\n")
        for ch_t, ch_name in chapters_log:
            seof.write(f"{format_mmss(ch_t)} {ch_name}\n")

if __name__ == "__main__":
    main()
uetype/dejavu/DejaVuSansMono-Bold.ttf"

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
