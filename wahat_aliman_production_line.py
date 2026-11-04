#!/usr/bin/env python3
import os, re, math, json, urllib.request, argparse, subprocess
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

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
