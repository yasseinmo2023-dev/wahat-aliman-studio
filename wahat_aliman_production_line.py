#!/usr/bin/env python3
"""
Produce Wahat Al-Iman Video Episode 19 (Surah Maryam 1-76)
"""

import os
import math
import json
import time
import argparse
import datetime
import urllib.request
import subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
]

def get_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def to_arabic_digits(num):
    digits = "٠١٢٣٤٥٦٧٨٩"
    return "".join(digits[int(d)] for d in str(num))

def format_srt_time(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    total_sec = int(seconds)
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def fetch_surah_maryam_data():
    url = "https://api.alquran.cloud/v1/surah/19/quran-uthmani"
    print(f"[API] Fetching Uthmani text from {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    ayahs = data["data"]["ayahs"][:76]
    result = []
    for a in ayahs:
        result.append({
            "numberInSurah": a["numberInSurah"],
            "text": a["text"],
            "audio_filename": f"019{a['numberInSurah']:03d}.mp3"
        })
    return result

def download_single_audio(item):
    num = item["numberInSurah"]
    filename = f"019{num:03d}.mp3"
    os.makedirs("audio_cache", exist_ok=True)
    filepath = os.path.join("audio_cache", filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return num, filepath
        
    urls = [
        f"https://everyayah.com/data/Minshawy_Murattal_128kbps/{filename}",
        f"https://everyayah.com/data/Abdul_Basit_Murattal_192kbps/{filename}",
        f"https://cdn.islamic.network/quran/audio/128/ar.alafasy/{2257 + num - 1}.mp3"
    ]
    
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read()
                if len(content) > 1000:
                    with open(filepath, "wb") as f:
                        f.write(content)
                    return num, filepath
        except Exception:
            continue
    raise RuntimeError(f"Could not download audio for Ayah {num}")

def get_audio_duration(filepath):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
    out = subprocess.check_output(cmd).decode("utf-8").strip()
    return float(out)

def create_base_bg_loop_16_9(output_path, num_frames=125, fps=25):
    w, h = 1920, 1080
    temp_dir = "temp_bg_16_9"
    os.makedirs(temp_dir, exist_ok=True)
    half_n = (num_frames // 2) + 1
    
    for i in range(half_n):
        frame_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
        if not os.path.exists(frame_path):
            img = Image.new("RGB", (w, h), (5, 10, 25))
            draw = ImageDraw.Draw(img)
            
            for y in range(600):
                r = int(5 + (22 - 5) * (y / 600))
                g = int(10 + (38 - 10) * (y / 600))
                b = int(25 + (70 - 25) * (y / 600))
                draw.line([(0, y), (w, y)], fill=(r, g, b))
                
            for y in range(600, h):
                r = int(12 + (3 - 12) * ((y - 600) / 480))
                g = int(25 + (8 - 25) * ((y - 600) / 480))
                b = int(48 + (18 - 48) * ((y - 600) / 480))
                draw.line([(0, y), (w, y)], fill=(r, g, b))
                
            mx, my, mr = 420, 190, 65
            for gr in range(mr + 35, mr, -2):
                draw.ellipse([mx - gr, my - gr, mx + gr, my + gr], fill=(210, 230, 255))
            draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(248, 252, 255))
            
            t = i / half_n
            for wy in range(610, 960, 6):
                ww = int(60 + (wy - 610) * 0.45)
                wx = int(mx + math.sin(wy * 0.04 + t * math.pi * 2) * 14)
                draw.ellipse([wx - ww, wy, wx + ww, wy + 3], fill=(170, 205, 235, 160))
                
            draw.rectangle([0, 595, w, 605], fill=(8, 14, 28))
            
            draw.polygon([(170, 640), (210, 640), (195, 310), (185, 310)], fill=(8, 12, 22))
            draw.line([(190, 490), (110, 370)], fill=(8, 12, 22), width=8)
            draw.line([(110, 370), (60, 300)], fill=(8, 12, 22), width=5)
            draw.line([(190, 430), (280, 330)], fill=(8, 12, 22), width=7)
            draw.line([(280, 330), (340, 270)], fill=(8, 12, 22), width=4)
            draw.line([(190, 370), (150, 250)], fill=(8, 12, 22), width=6)
            
            fog_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            fog_draw = ImageDraw.Draw(fog_img)
            fy = 575 + int(math.sin(t * math.pi * 2) * 6)
            fog_draw.rectangle([0, fy, w, fy + 65], fill=(185, 205, 225, 25))
            img.paste(fog_img, (0, 0), fog_img)
            
            img.save(frame_path)
            
    full_indices = list(range(half_n)) + list(range(half_n - 2, 0, -1))
    for idx, f_idx in enumerate(full_indices[:num_frames]):
        src = os.path.join(temp_dir, f"frame_{f_idx:04d}.png")
        dst = os.path.join(temp_dir, f"seq_{idx:04d}.png")
        if os.path.exists(dst):
            os.remove(dst)
        os.link(src, dst)
        
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(temp_dir, "seq_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", output_path]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[BG] Created 16:9 BG loop: {output_path}")

def create_base_bg_loop_9_16(output_path, num_frames=125, fps=25):
    w, h = 1080, 1920
    temp_dir = "temp_bg_9_16"
    os.makedirs(temp_dir, exist_ok=True)
    half_n = (num_frames // 2) + 1
    
    for i in range(half_n):
        frame_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
        if not os.path.exists(frame_path):
            img = Image.new("RGB", (w, h), (5, 10, 25))
            draw = ImageDraw.Draw(img)
            
            for y in range(1100):
                r = int(5 + (22 - 5) * (y / 1100))
                g = int(10 + (38 - 10) * (y / 1100))
                b = int(25 + (70 - 25) * (y / 1100))
                draw.line([(0, y), (w, y)], fill=(r, g, b))
                
            for y in range(1100, h):
                r = int(12 + (3 - 12) * ((y - 1100) / 820))
                g = int(25 + (8 - 25) * ((y - 1100) / 820))
                b = int(48 + (18 - 48) * ((y - 1100) / 820))
                draw.line([(0, y), (w, y)], fill=(r, g, b))
                
            mx, my, mr = 540, 320, 85
            for gr in range(mr + 40, mr, -2):
                draw.ellipse([mx - gr, my - gr, mx + gr, my + gr], fill=(210, 230, 255))
            draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(248, 252, 255))
            
            t = i / half_n
            for wy in range(1110, 1750, 8):
                ww = int(80 + (wy - 1110) * 0.4)
                wx = int(mx + math.sin(wy * 0.03 + t * math.pi * 2) * 16)
                draw.ellipse([wx - ww, wy, wx + ww, wy + 4], fill=(170, 205, 235, 160))
                
            draw.rectangle([0, 1095, w, 1105], fill=(8, 14, 28))
            
            fog_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            fog_draw = ImageDraw.Draw(fog_img)
            fy = 1070 + int(math.sin(t * math.pi * 2) * 8)
            fog_draw.rectangle([0, fy, w, fy + 80], fill=(185, 205, 225, 25))
            img.paste(fog_img, (0, 0), fog_img)
            
            img.save(frame_path)
            
    full_indices = list(range(half_n)) + list(range(half_n - 2, 0, -1))
    for idx, f_idx in enumerate(full_indices[:num_frames]):
        src = os.path.join(temp_dir, f"frame_{f_idx:04d}.png")
        dst = os.path.join(temp_dir, f"seq_{idx:04d}.png")
        if os.path.exists(dst):
            os.remove(dst)
        os.link(src, dst)
        
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(temp_dir, "seq_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", output_path]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[BG] Created 9:16 BG loop: {output_path}")

def create_ayah_overlay(ayah_item, is_vertical=False):
    w, h = (1080, 1920) if is_vertical else (1920, 1080)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    logo_font = get_font(38 if not is_vertical else 36)
    logo_text = "✨ واحة الإيمان ✨"
    l_bbox = draw.textbbox((0, 0), logo_text, font=logo_font)
    lw = l_bbox[2] - l_bbox[0]
    lx = (w - lw) // 2
    ly = 45 if not is_vertical else 100
    
    draw.rounded_rectangle([lx - 25, ly - 12, lx + lw + 25, ly + 50], radius=16, fill=(15, 25, 45, 190), outline=(212, 175, 55, 230), width=2)
    draw.text((lx, ly), logo_text, font=logo_font, fill=(245, 225, 150))
    
    num_str = to_arabic_digits(ayah_item["numberInSurah"])
    text = f"{ayah_item['text']} ﴿{num_str}﴾"
    
    font_size = 46 if not is_vertical else 42
    font = get_font(font_size)
    
    max_w = 920 if not is_vertical else 860
    words = text.split()
    lines = []
    cur = []
    for word in words:
        t_line = " ".join(cur + [word])
        b = draw.textbbox((0, 0), t_line, font=font)
        if b[2] - b[0] <= max_w:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
        
    line_h = font_size + 24
    tot_h = len(lines) * line_h
    
    if not is_vertical:
        b_left, b_right = 780, 1840
        b_top = (h - tot_h) // 2
        b_bot = b_top + tot_h
    else:
        b_left, b_right = 60, 1020
        b_top = (h - tot_h) // 2
        b_bot = b_top + tot_h
        
    draw.rounded_rectangle([b_left - 30, b_top - 30, b_right + 30, b_bot + 30], radius=22, fill=(10, 18, 34, 180), outline=(212, 175, 55, 150), width=2)
    
    for idx, line in enumerate(lines):
        lb = draw.textbbox((0, 0), line, font=font)
        line_w = lb[2] - lb[0]
        
        if not is_vertical:
            tx = b_right - line_w - 25
        else:
            tx = (w - line_w) // 2
        ty = b_top + idx * line_h
        
        draw.text((tx + 2, ty + 2), line, font=font, fill=(185, 145, 45, 210))
        draw.text((tx, ty), line, font=font, fill=(255, 255, 255))
        
    return img

def render_ayah_clip(args):
    idx, ayah_item, audio_path, bg_loop_path, output_clip_path, is_vertical = args
    duration = get_audio_duration(audio_path)
    
    overlay = create_ayah_overlay(ayah_item, is_vertical=is_vertical)
    overlay_path = f"temp_overlay_{'vert_' if is_vertical else ''}{idx:03d}.png"
    overlay.save(overlay_path)
    
    cmd = [
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", bg_loop_path,
        "-i", overlay_path, "-i", audio_path,
        "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
        "-map", "[v]", "-map", "2:a",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        output_clip_path
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(overlay_path):
        os.remove(overlay_path)
        
    return idx, output_clip_path, duration

def create_thumbnail():
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (5, 10, 25))
    draw = ImageDraw.Draw(img)
    
    for y in range(h):
        r = int(5 + (20 - 5) * (y / h))
        g = int(10 + (35 - 10) * (y / h))
        b = int(25 + (65 - 25) * (y / h))
        draw.line([(0, y), (w, y)], fill=(r, g, b))
        
    mx, my, mr = 450, 250, 120
    for gr in range(mr + 60, mr, -3):
        draw.ellipse([mx - gr, my - gr, mx + gr, my + gr], fill=(210, 230, 255))
    draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(250, 252, 255))
    
    font_large = get_font(72)
    font_sub = get_font(44)
    logo_font = get_font(40)
    
    draw.rounded_rectangle([750, 250, 1850, 800], radius=30, fill=(10, 18, 34, 210), outline=(212, 175, 55, 240), width=4)
    
    t1 = "سورة مريم كاملة"
    t2 = "الآيات 1 - 76 | تلاوة خاشعة"
    t3 = "✨ واحة الإيمان ✨"
    
    draw.text((1050, 340), t1, font=font_large, fill=(255, 220, 110))
    draw.text((1020, 480), t2, font=font_sub, fill=(255, 255, 255))
    draw.text((1150, 620), t3, font=logo_font, fill=(200, 230, 255))
    
    img.save("thumbnail_16_9.jpg", quality=95)
    print("[Thumbnail] Created thumbnail_16_9.jpg")

def main():
    parser = argparse.ArgumentParser(description="Produce Wahat Al-Iman Video")
    parser.add_argument("--ep", "--episode", type=int, default=19)
    args, _ = parser.parse_known_args()
    
    ep_num = args.ep
    print(f"=== Starting Production for Episode {ep_num} ===")
    
    ayahs = fetch_surah_maryam_data()
    print(f"[Data] Loaded {len(ayahs)} ayahs.")
    
    print("[Audio] Downloading audio files in parallel...")
    audio_map = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_single_audio, item) for item in ayahs]
        for fut in futures:
            num, path = fut.result()
            audio_map[num] = path
    print("[Audio] All audio files downloaded.")
    
    os.makedirs("clips_16_9", exist_ok=True)
    os.makedirs("clips_9_16", exist_ok=True)
    create_base_bg_loop_16_9("bg_loop_16_9.mp4")
    create_base_bg_loop_9_16("bg_loop_9_16.mp4")
    
    print("[Render] Rendering 16:9 clips for 76 ayahs in parallel...")
    render_tasks_16_9 = []
    for idx, a in enumerate(ayahs, start=1):
        audio_path = audio_map[a["numberInSurah"]]
        out_clip = f"clips_16_9/clip_{idx:03d}.mp4"
        render_tasks_16_9.append((idx, a, audio_path, "bg_loop_16_9.mp4", out_clip, False))
        
    clip_durations = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(render_ayah_clip, render_tasks_16_9)
        for idx, out_clip, dur in results:
            clip_durations[idx] = dur
            
    print("[Concat] Concatenating 76 ayahs into long_video_16_9.mp4...")
    with open("concat_16_9.txt", "w", encoding="utf-8") as f:
        for idx in range(1, len(ayahs) + 1):
            f.write(f"file 'clips_16_9/clip_{idx:03d}.mp4'\n")
            
    cmd_concat = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_16_9.txt", "-c", "copy", "long_video_16_9.mp4"]
    subprocess.check_call(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[Output] Generated long_video_16_9.mp4")
    
    print("[Reels] Rendering 9:16 vertical clips for Ayahs 1-7...")
    render_tasks_9_16 = []
    for idx, a in enumerate(ayahs[:7], start=1):
        audio_path = audio_map[a["numberInSurah"]]
        out_clip = f"clips_9_16/clip_{idx:03d}.mp4"
        render_tasks_9_16.append((idx, a, audio_path, "bg_loop_9_16.mp4", out_clip, True))
        
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(render_ayah_clip, render_tasks_9_16))
        
    with open("concat_9_16.txt", "w", encoding="utf-8") as f:
        for idx in range(1, 8):
            f.write(f"file 'clips_9_16/clip_{idx:03d}.mp4'\n")
            
    cmd_reels = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_9_16.txt", "-c", "copy", "short_reel_9_16.mp4"]
    subprocess.check_call(cmd_reels, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[Output] Generated short_reel_9_16.mp4")
    
    print("[SRT] Generating surah_maryam.srt...")
    current_time = 0.0
    with open("surah_maryam.srt", "w", encoding="utf-8") as f:
        for idx, a in enumerate(ayahs, start=1):
            dur = clip_durations[idx]
            start_str = format_srt_time(current_time)
            end_str = format_srt_time(current_time + dur)
            f.write(f"{idx}\n{start_str} --> {end_str}\n{a['text']}\n\n")
            current_time += dur
            
    create_thumbnail()
    
    print("[SEO] Writing seo_package.txt and metadata.json...")
    tot_duration_str = str(datetime.timedelta(seconds=int(current_time)))
    seo_content = f"""==================================================
عنوان الفيديو (Title):
سورة مريم كاملة (الآيات 1 - 76) | تلاوة خاشعة تريح القلوب | واحة الإيمان

الوصف (Description):
✨ استمع إلى تلاوة خاشعة ومباركة لسورة مريم (الآيات 1 إلى 76) بالرسم العثماني الشريف.
مشهد سينمائي هادئ لليلة قمرية على شاطئ البحيرة يبعث على السكينة والاطمئنان.

📌 محتويات الحلقة:
- السورة: سورة مريم (Surah Maryam)
- الآيات: 1 إلى 76 كاملة
- المدة الإجمالية: {tot_duration_str}
- القناة: واحة الإيمان (Wahat Al-Iman)

الكلمات المفتاحية (Tags):
سورة مريم, سورة مريم كاملة, تلاوة خاشعة, واحة الإيمان, القرآن الكريم بالرسم العثماني, Surah Maryam, Quran Recitation
==================================================
"""
    with open("seo_package.txt", "w", encoding="utf-8") as f:
        f.write(seo_content)
        
    meta_data = {
        "episode_number": ep_num,
        "surah_name": "سورة مريم",
        "ayah_range": "1-76",
        "total_duration_seconds": current_time,
        "formatted_duration": tot_duration_str,
        "rendered_at": datetime.datetime.utcnow().isoformat(),
        "files": [
            "long_video_16_9.mp4",
            "short_reel_9_16.mp4",
            "thumbnail_16_9.jpg",
            "surah_maryam.srt",
            "seo_package.txt",
            "metadata.json"
        ]
    }
    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
    print("=== Episode 19 Production Completed Successfully ===")

if __name__ == "__main__":
    main()
Executor

FONT_NASKH_BOLD = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
FONT_SANS_REG = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

RECITERS = {
    "minshawi_murattal": {"name": "المنشاوي (مرتل)", "folder": "Minshawy_Murattal_128kbps"},
    "minshawi_mujawwad": {"name": "المنشاوي (مجود)", "folder": "Minshawy_Mujawwad_192kbps"},
    "abdulbasit_murattal": {"name": "عبدالباسط (مرتل)", "folder": "Abdul_Basit_Murattal_192kbps"},
    "abdulbasit_mujawwad": {"name": "عبدالباسط (مجود)", "folder": "Abdul_Basit_Mujawwad_128kbps"},
}

THEMES_MATRIX = {
    1: {
        "theme_key": "golden_sunset",
        "topic_name": "جلسة علاج الخاطر وسكينة النفس",
        "reciter": "minshawi_murattal",
        "surahs": [93, 94, 95, 96, 102, 1],
        "seo_title": "جلسة قرآنية | للباحثين عن الطمأنينة وجبر الخاطر 15 دقيقة بصوت منشرح",
        "reflection": "تلاوة خاشعة تهدئ الروح وتزرع الأمل : «فإن مع العسر يسراً»",
        "reels_hook": "إذا ضاق صدرك واشتد عليك الهم .. استمع لهذه الآيات :",
    },
    2: {
        "theme_key": "emerald_dawn",
        "topic_name": "سورة الواقعة لجلب الرزق والبركة",
        "reciter": "abdulbasit_murattal",
        "surahs": [56],
        "seo_title": "سورة الواقعة كاملة | تلاوة تفتح أبواب الرزق والبركة 15 دقيقة",
        "reflection": "الواقعة سورة الغنى والبركة .. تدبر قوله تعالى : «أفرأيتم ما تحرثون»",
        "reels_hook": "لكل من يبحث عن البركة وتيسير الرزق في يومه ..",
    },
    3: {
        "theme_key": "royal_night",
        "topic_name": "الملك والمعوذات للحفظ والوقاية قبل النوم",
        "reciter": "minshawi_mujawwad",
        "surahs": [67, 112, 113, 114],
        "seo_title": "حصن المساء | سورة الملك والمعوذات للحفظ والسكينة قبل النوم",
        "reflection": "المنجية من عذاب القبر وحصنك المنيع .. استمع قبل نومك",
        "reels_hook": "قبل أن تنام .. احمِ نفسك وأهلك بهذه الآيات العظيمة :",
    },
    4: {
        "theme_key": "ocean_peace",
        "topic_name": "عروس القرآن سورة الرحمن",
        "reciter": "abdulbasit_mujawwad",
        "surahs": [55],
        "seo_title": "سورة الرحمن كاملة | عروس القرآن بتلاوة تأخذك لعالم آخر",
        "reflection": "فبأي آلاء ربكما تكذبان .. تفكر في نعم الله عليك",
        "reels_hook": "آية واحدة كفيلة بأن تجعلك تشكر الله على نعمه طوال اليوم :",
    }
}

def to_arabic_digits(num: int) -> str:
    western = "0123456789"
    eastern = "٠١٢٣٤٥٦٧٨٩"
    return str(num).translate(str.maketrans(western, eastern))

def format_mmss(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

def clean_arabic_text(text: str) -> str:
    text = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]', '', text)
    text = text.replace("ٱ", "ا")
    return text

def fetch_surah_data_and_audio(surah_num: int, reciter_folder: str, audio_dir: str) -> tuple:
    url = f"https://api.alquran.cloud/v1/surah/{surah_num}/quran-uthmani"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))["data"]
    surah_name = payload["name"]
    items = []

    def download_ay(ay):
        ay_num = ay["numberInSurah"]
        mp3_name = f"{surah_num:03d}{ay_num:03d}.mp3"
        mp3_path = os.path.join(audio_dir, mp3_name)
        if not os.path.exists(mp3_path):
            mp3_url = f"https://everyayah.com/data/{reciter_folder}/{mp3_name}"
            r_mp3 = urllib.request.Request(mp3_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(r_mp3, timeout=25) as m_resp, open(mp3_path, "wb") as out_f:
                out_f.write(m_resp.read())
        dur_out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_path])
        txt = ay["text"].strip() + f" ﴿{to_arabic_digits(ay_num)}﴾"
        return {"surah_name": surah_name, "ayah_num": ay_num, "text": txt, "mp3": mp3_path, "duration": max(1.5, float(dur_out))}

    with ThreadPoolExecutor(max_workers=8) as executor:
        items = list(executor.map(download_ay, payload["ayahs"]))
    return surah_name, items

def create_backdrop(w: int, h: int, bg_color: tuple, accent_color: tuple) -> Image.Image:
    base = Image.new("RGBA", (w, h), bg_color)
    draw = ImageDraw.Draw(base)
    for r in range(min(w, h), 0, -20):
        alpha = int(35 * (r / min(w, h)))
        color = accent_color + (alpha,)
        draw.ellipse([w//2 - r, h//2 - r, w//2 + r, h//2 + r], fill=color)
    return base

def render_16_9_slide(surah_title: str, topic_name: str, main_text: str, current_s: float, total_dur: float, out_path: str):
    w, h = 1280, 720
    base = create_backdrop(w, h, (10, 24, 30, 255), (15, 60, 50))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_title = ImageFont.truetype(FONT_NASKH_BOLD, 36)
    font_sub = ImageFont.truetype(FONT_SANS_REG, 22)
    font_quran = ImageFont.truetype(FONT_NASKH_BOLD, 34)
    
    draw.text((640, 50), clean_arabic_text(surah_title), font=font_title, fill=(212, 175, 55, 255), anchor="mm", direction="rtl")
    draw.text((640, 95), clean_arabic_text(topic_name), font=font_sub, fill=(180, 220, 210, 230), anchor="mm", direction="rtl")
    draw.line([(340, 120), (940, 120)], fill=(212, 175, 55, 120), width=2)
    
    draw.text((640, 340), clean_arabic_text(main_text), font=font_quran, fill=(255, 255, 255, 255), anchor="mm", direction="rtl")
    
    draw.text((640, 605), clean_arabic_text("وَاحَةُ الإِيمَانِ"), font=font_sub, fill=(212, 175, 55, 230), anchor="mm", direction="rtl")
    
    prog = min(1.0, max(0.0, current_s / total_dur))
    draw.rounded_rectangle((40, 655, 1240, 671), radius=8, fill=(255, 255, 255, 40))
    draw.rounded_rectangle((40, 655, 40 + max(16, int(1200 * prog)), 671), radius=8, fill=(212, 175, 55, 240))
    draw.text((1160, 630), f"{format_mmss(current_s)} / {format_mmss(total_dur)}", font=ImageFont.truetype(FONT_MONO, 18), fill=(245, 222, 130, 255), anchor="mm")
    
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, "JPEG", quality=92)

def render_9_16_slide(hook_text: str, surah_title: str, main_text: str, current_s: float, total_dur: float, out_path: str):
    w, h = 1080, 1920
    base = create_backdrop(w, h, (8, 18, 24, 255), (12, 50, 45))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_hook = ImageFont.truetype(FONT_SANS_BOLD, 36)
    font_title = ImageFont.truetype(FONT_NASKH_BOLD, 42)
    font_quran = ImageFont.truetype(FONT_NASKH_BOLD, 44)
    font_sub = ImageFont.truetype(FONT_SANS_REG, 26)
    
    draw.rounded_rectangle((90, 180, 990, 290), radius=20, fill=(0, 0, 0, 120), outline=(212, 175, 55, 180), width=2)
    draw.text((540, 235), clean_arabic_text(hook_text), font=font_hook, fill=(245, 222, 130, 255), anchor="mm", direction="rtl")
    
    draw.text((540, 360), clean_arabic_text(surah_title), font=font_title, fill=(212, 175, 55, 255), anchor="mm", direction="rtl")
    
    draw.text((540, 960), clean_arabic_text(main_text), font=font_quran, fill=(255, 255, 255, 255), anchor="mm", direction="rtl")
    
    draw.text((540, 1444), clean_arabic_text("وَاحَةُ الإِيمَانِ"), font=ImageFont.truetype(FONT_NASKH_BOLD, 28), fill=(212, 175, 55, 250), anchor="mm", direction="rtl")
    
    prog = min(1.0, max(0.0, current_s / total_dur))
    draw.rounded_rectangle((110, 1525, 970, 1545), radius=10, fill=(255, 255, 255, 60))
    draw.rounded_rectangle((110, 1525, 110 + max(20, int(860 * prog)), 1545), radius=10, fill=(212, 175, 55, 250))
    
    draw.text((540, 1595), clean_arabic_text("تابع الجلسة الكاملة على قناة واحة الإيمان"), font=ImageFont.truetype(FONT_SANS_BOLD, 24), fill=(245, 222, 130, 255), anchor="mm", direction="rtl")
    
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path, "JPEG", quality=92)

def generate_srt(timeline: list, srt_path: str):
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, item in enumerate(timeline, 1):
            s_sec, e_sec = item["start"], item["end"]
            sh, sm, ss, ms = int(s_sec//3600), int((s_sec%3600)//60), int(s_sec%60), int((s_sec*1000)%1000)
            eh, em, es, ems = int(e_sec//3600), int((e_sec%3600)//60), int(e_sec%60), int((e_sec*1000)%1000)
            f.write(f"{idx}\n{sh:02d}:{sm:02d}:{ss:02d},{ms:03d} --> {eh:02d}:{em:02d}:{es:02d},{ems:03d}\n{item['text']}\n\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep", default="1")
    parser.add_argument("--reciter", default="auto")
    parser.add_argument("--target-minutes", default="15")
    parser.add_argument("--reels", default="3")
    parser.add_argument("--fps", default="24")
    parser.add_argument("--out-dir", default="output")
    args = parser.parse_args()

    ep_num = int(args.ep)
    theme = THEMES_MATRIX.get(ep_num, THEMES_MATRIX[1])
    rec_key = theme["reciter"] if args.reciter == "auto" else args.reciter
    reciter_info = RECITERS[rec_key]

    os.makedirs(args.out_dir, exist_ok=True)
    cache_dir = os.path.join(args.out_dir, "_audio_cache")
    slides_16_9_dir = os.path.join(args.out_dir, "_slides_16_9")
    slides_9_16_dir = os.path.join(args.out_dir, "_slides_9_16")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(slides_16_9_dir, exist_ok=True)
    os.makedirs(slides_9_16_dir, exist_ok=True)

    target_sec = float(args.target_minutes) * 60.0
    all_items = []

    while True:
        for s_id in theme["surahs"]:
            s_name, items = fetch_surah_data_and_audio(s_id, reciter_info["folder"], cache_dir)
            all_items.extend(items)
            cur_dur = sum(x["duration"] for x in all_items)
            if cur_dur >= target_sec:
                break
        if sum(x["duration"] for x in all_items) >= target_sec:
            break

    total_dur = sum(x["duration"] for x in all_items)

    curr_time = 0.0
    timeline = []
    a_files = []
    v_concat_lines = []

    for idx, item in enumerate(all_items):
        img_path = os.path.join(slides_16_9_dir, f"slide_{idx:04d}.jpg")
        render_16_9_slide(item["surah_name"], theme["topic_name"], item["text"], curr_time, total_dur, img_path)
        
        timeline.append({"start": curr_time, "end": curr_time + item["duration"], "text": item["text"]})
        v_concat_lines.append(f"file '{os.path.abspath(img_path)}'\nduration {item['duration']:.3f}\n")
        a_files.append(item["mp3"])
        curr_time += item["duration"]

    if v_concat_lines:
        v_concat_lines.append(f"file '{os.path.abspath(os.path.join(slides_16_9_dir, f'slide_{len(all_items)-1:04d}.jpg'))}'\n")

    v_concat = os.path.join(slides_16_9_dir, "v_concat.txt")
    a_concat = os.path.join(slides_16_9_dir, "a_concat.txt")
    with open(v_concat, "w", encoding="utf-8") as f:
        f.writelines(v_concat_lines)
    with open(a_concat, "w", encoding="utf-8") as f:
        for af in a_files:
            f.write(f"file '{os.path.abspath(af)}'\n")

    recitation_wav = os.path.join(slides_16_9_dir, "full_recitation.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", a_concat, "-vn", "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", recitation_wav], check=True)

    fade_out_at = max(0, total_dur - 2.0)
    tail = f"aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=9,aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,afade=t=in:d=1.5,afade=t=out:st={fade_out_at:.2f}:d=2[aout]"
    filter_complex = f"[1:a]{tail}"

    final_long_mp4 = os.path.join(args.out_dir, f"wahat_aliman_ep{ep_num}_long.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_concat,
        "-i", recitation_wav,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", args.fps, "-shortest",
        final_long_mp4
    ], check=True)

    generate_srt(timeline, os.path.join(args.out_dir, f"wahat_aliman_ep{ep_num}_long.srt"))

    seo_file = os.path.join(args.out_dir, f"wahat_aliman_ep{ep_num}_seo.txt")
    with open(seo_file, "w", encoding="utf-8") as f:
        f.write(f"Title: {theme['seo_title']}\n\nDescription:\n{theme['reflection']}\n\nReciter: {reciter_info['name']}\n")

    num_reels = int(args.reels)
    step = len(all_items) // max(1, num_reels)
    for k in range(num_reels):
        st_idx = k * step
        reel_items = all_items[st_idx:st_idx + 4]
        if not reel_items:
            continue
        
        r_dur = sum(x["duration"] for x in reel_items)
        r_curr = 0.0
        rv_lines = []
        ra_files = []
        
        for r_i, r_item in enumerate(reel_items):
            r_img = os.path.join(slides_9_16_dir, f"reel_{k}_slide_{r_i}.jpg")
            render_9_16_slide(theme["reels_hook"], r_item["surah_name"], r_item["text"], r_curr, r_dur, r_img)
            rv_lines.append(f"file '{os.path.abspath(r_img)}'\nduration {r_item['duration']:.3f}\n")
            ra_files.append(r_item["mp3"])
            r_curr += r_item["duration"]

        if rv_lines:
            rv_lines.append(f"file '{os.path.abspath(os.path.join(slides_9_16_dir, f'reel_{k}_slide_{len(reel_items)-1}.jpg'))}'\n")

        rv_concat = os.path.join(slides_9_16_dir, f"rv_concat_{k}.txt")
        ra_concat = os.path.join(slides_9_16_dir, f"ra_concat_{k}.txt")
        with open(rv_concat, "w", encoding="utf-8") as f:
            f.writelines(rv_lines)
        with open(ra_concat, "w", encoding="utf-8") as f:
            for af in ra_files:
                f.write(f"file '{os.path.abspath(af)}'\n")

        reel_audio = os.path.join(slides_9_16_dir, f"reel_rec{k}.wav")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ra_concat, "-vn", "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", reel_audio], check=True)

        reel_mp4 = os.path.join(args.out_dir, f"wahat_aliman_ep{ep_num}_reel_{k+1}.mp4")
        rfade_out = max(0, r_dur - 1.5)
        rtail = f"aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=9,aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,afade=t=in:d=1.5,afade=t=out:st={rfade_out:.2f}:d=1.5[aout]"
        
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", rv_concat,
            "-i", reel_audio,
            "-filter_complex", f"[1:a]{rtail}",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", args.fps, "-shortest",
            reel_mp4
        ], check=True)

if __name__ == "__main__":
    main()
