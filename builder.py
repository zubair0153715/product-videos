"""Motion-graphics product promo video builder (reel-style: phone mockups,
animated cards, kinetic text). Config-driven: each product supplies a dict.
1080x1920, 30fps. PIL stills + ffmpeg zoompan/drawtext + gTTS voiceover.

Usage: python builder.py <config.json> <out_dir>
"""
import json
import os
import subprocess
import sys

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

NAVY1, NAVY2 = (11, 27, 51), (6, 13, 26)
TEAL, WHITE, GRAY, RED, AMBER = (0, 212, 164), (255, 255, 255), (140, 160, 185), (255, 90, 90), (255, 180, 60)
COLORS = {"teal": TEAL, "white": WHITE, "gray": GRAY, "red": RED, "amber": AMBER}


def _font(path, size):
    from PIL import ImageFont
    return ImageFont.truetype(path, size)


def fit_font(path, text, size, max_w):
    """Shrink font until text fits max_w (hook/card overflow guard)."""
    from PIL import ImageFont
    while size > 20:
        f = ImageFont.truetype(path, size)
        if f.getlength(text) <= max_w:
            return f
        size -= 6
    return ImageFont.truetype(path, 20)


def bg():
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY1[i] + (NAVY2[i] - NAVY1[i]) * t) for i in range(3)))
    for r in range(500, 0, -20):
        d.ellipse([W // 2 - r, -200 - r // 3, W // 2 + r, 300 + r // 3],
                  outline=(16, 42, 80, 255), width=2)
    return im


def ctext(d, xy, s, font, fill=WHITE, anchor="mm"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def phone(d, x, y, w, h, screen_fn):
    d.rounded_rectangle([x, y, x + w, y + h], radius=64, fill=(18, 22, 32),
                        outline=(60, 70, 95), width=4)
    sx, sy, sw, sh = x + 20, y + 20, w - 40, h - 40
    d.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=46, fill=(13, 24, 43))
    d.rounded_rectangle([x + w // 2 - 90, y + 34, x + w // 2 + 90, y + 62], radius=14, fill=(8, 10, 16))
    screen_fn(d, sx, sy, sw, sh)


def draw_check(d, cx, cy):
    d.line([cx - 8, cy, cx - 1, cy + 8], fill=(6, 13, 26), width=5)
    d.line([cx - 1, cy + 8, cx + 12, cy - 10], fill=(6, 13, 26), width=5)


def phone_header(d, sx, sy, sw, title):
    d.rounded_rectangle([sx, sy, sx + sw, sy + 96], radius=0, fill=(0, 150, 118))
    ctext(d, (sx + sw // 2, sy + 48), title, _font(BOLD, 34))


def screen_checklist(d, sx, sy, sw, sh, cfg):
    """cfg: header, title, progress:[done,total], rows:[{label, done}]"""
    phone_header(d, sx, sy, sw, cfg["header"])
    ctext(d, (sx + 30, sy + 150), cfg["title"], _font(BOLD, 30), anchor="lm")
    done, total = cfg["progress"]
    plabel = cfg.get("progress_label", "questions")
    ctext(d, (sx + 30, sy + 196), f"{done} / {total} {plabel}", _font(REG, 22), fill=GRAY, anchor="lm")
    d.rounded_rectangle([sx + 30, sy + 220, sx + sw - 30, sy + 244], radius=12, fill=(30, 45, 70))
    d.rounded_rectangle([sx + 30, sy + 220, sx + 30 + int((sw - 60) * done / total), sy + 244],
                        radius=12, fill=TEAL)
    yy = sy + 300
    for row in cfg["rows"][:6]:
        d.rounded_rectangle([sx + 30, yy, sx + sw - 30, yy + 96], radius=18, fill=(22, 36, 60))
        cc = TEAL if row.get("done") else (70, 85, 110)
        d.ellipse([sx + 52, yy + 28, sx + 100, yy + 76], fill=cc)
        if row.get("done"):
            draw_check(d, sx + 76, yy + 52)
        ctext(d, (sx + 122, yy + 52), row["label"], _font(REG, 26), anchor="lm")
        yy += 116


def screen_score(d, sx, sy, sw, sh, cfg):
    """cfg: header, score, total, note, findings:[{label, level}]"""
    phone_header(d, sx, sy, sw, cfg["header"])
    d.ellipse([sx + sw // 2 - 110, sy + 170, sx + sw // 2 + 110, sy + 390], outline=TEAL, width=14)
    ctext(d, (sx + sw // 2, sy + 262), str(cfg["score"]), _font(BOLD, 110))
    ctext(d, (sx + sw // 2, sy + 340), f"/ {cfg['total']}", _font(REG, 34), fill=GRAY)
    ctext(d, (sx + sw // 2, sy + 450), cfg.get("note", ""), _font(REG, 26), fill=AMBER)
    yy = sy + 520
    for f in cfg.get("findings", [])[:3]:
        d.rounded_rectangle([sx + 30, yy, sx + sw - 30, yy + 110], radius=18, fill=(22, 36, 60))
        d.ellipse([sx + 52, yy + 42, sx + 72, yy + 62], fill=COLORS.get(f.get("level", "amber"), AMBER))
        ctext(d, (sx + 92, yy + 55), f["label"], _font(REG, 24), anchor="lm")
        yy += 130


def screen_rows(d, sx, sy, sw, sh, cfg):
    """cfg: header, title, rows:[{label, value, level}] — generic stat rows."""
    phone_header(d, sx, sy, sw, cfg["header"])
    ctext(d, (sx + 30, sy + 150), cfg["title"], _font(BOLD, 30), anchor="lm")
    yy = sy + 230
    for row in cfg.get("rows", [])[:5]:
        d.rounded_rectangle([sx + 30, yy, sx + sw - 30, yy + 120], radius=18, fill=(22, 36, 60))
        if row.get("level"):
            d.ellipse([sx + 52, yy + 48, sx + 72, yy + 68], fill=COLORS.get(row["level"], TEAL))
            tx = sx + 92
        else:
            tx = sx + 52
        ctext(d, (tx, yy + 42), row["label"], _font(REG, 24), anchor="lm", fill=GRAY)
        ctext(d, (tx, yy + 84), row["value"], fit_font(BOLD, row["value"], 30, 330), anchor="lm")
        yy += 140


SCREEN_FNS = {"checklist": screen_checklist, "score": screen_score, "rows": screen_rows}


def scene_hook(cfg):
    im = bg()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    lines = cfg["hook"]  # [{text, size, color}]
    y = 780
    for ln in lines:
        f = fit_font(BOLD, ln["text"], ln.get("size", 120), 1000)
        ctext(d, (W // 2, y), ln["text"], f,
              fill=COLORS.get(ln.get("color", "white"), WHITE))
        y += ln.get("size", 120) + 30
    return im


def scene_phone(cfg):
    """cfg: {type, headline, sub, ...screen cfg}"""
    im = bg()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    phone(d, 290, 430, 500, 1000, lambda dd, sx, sy, sw, sh: SCREEN_FNS[cfg["type"]](dd, sx, sy, sw, sh, cfg))
    return im, cfg.get("headline"), cfg.get("sub")


def scene_cards(cfg):
    """cfg: {headline, sub, cards:[{title, sub}]}"""
    im = bg()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    cards = cfg["cards"][:4]
    for i, c in enumerate(cards):
        cx, cy = 140 + (i % 2) * 410, 620 + (i // 2) * 330
        d.rounded_rectangle([cx, cy, cx + 370, cy + 270], radius=28, fill=(22, 36, 60),
                            outline=(0, 212, 164), width=3)
        ctext(d, (cx + 185, cy + 110), c["title"], fit_font(BOLD, c["title"], 52, 330), fill=TEAL)
        ctext(d, (cx + 185, cy + 180), c.get("sub", ""), _font(REG, 30), fill=GRAY)
    return im, cfg.get("headline"), cfg.get("sub")


def scene_cta(cfg, url):
    im = bg()
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    lines = cfg["cta"]  # [big1, big2, sub1, sub2]
    d.rounded_rectangle([140, 560, 940, 900], radius=40, fill=(0, 150, 118))
    ctext(d, (W // 2, 680), lines[0], _font(BOLD, 110), fill=(6, 13, 26))
    ctext(d, (W // 2, 800), lines[1], _font(BOLD, 110), fill=(6, 13, 26))
    ctext(d, (W // 2, 1020), lines[2], _font(BOLD, 54))
    ctext(d, (W // 2, 1100), lines[3], _font(REG, 44), fill=GRAY)
    ctext(d, (W // 2, 1240), url, _font(REG, 34), fill=TEAL)
    return im


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(cmd[:6]), "\n", r.stderr[-800:])
        sys.exit(1)


def build(out_dir, cfg):
    os.makedirs(out_dir, exist_ok=True)
    from gtts import gTTS
    wav = os.path.join(out_dir, "vo.mp3")
    gTTS(cfg["voice"], lang="en").save(wav)

    scenes = []  # (image, headline, sub, dur)
    scenes.append((scene_hook(cfg), None, None, cfg["durations"]["hook"]))
    for ps in cfg["phone_scenes"]:
        im, head, sub = scene_phone(ps)
        scenes.append((im, head, sub, cfg["durations"]["phone"]))
    im, head, sub = scene_cards(cfg)
    scenes.append((im, head, sub, cfg["durations"]["cards"]))
    scenes.append((scene_cta(cfg, cfg["url"]), None, None, cfg["durations"]["cta"]))

    clips = []
    for i, (im, head, sub, dur) in enumerate(scenes):
        img = os.path.join(out_dir, f"s{i}.png")
        im.save(img)
        clip = os.path.join(out_dir, f"c{i}.mp4")
        nframes = int(dur * FPS)
        vf = (f"scale=1296:2304,zoompan=z='1+0.08*on/{nframes}':d={nframes}:s=1080x1920:fps={FPS}")
        if head:
            esc = head.replace(":", "\\:").replace("'", "")
            fade = "alpha='if(lt(t,0.4),0,if(lt(t,0.8),(t-0.4)/0.4,1))'"
            vf += (f",drawtext=fontfile={BOLD}:text='{esc}':fontsize=64:fontcolor=white:"
                   f"x=(w-text_w)/2:y=180:{fade}")
            if sub:
                sub_e = sub.replace(":", "\\:").replace("'", "")
                vf += (f",drawtext=fontfile={REG}:text='{sub_e}':fontsize=40:fontcolor=0x8CA0B9:"
                       f"x=(w-text_w)/2:y=270:{fade}")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", img,
             "-vf", vf, "-t", f"{dur:.2f}", "-r", str(FPS), "-pix_fmt", "yuv420p", clip])
        clips.append(clip)

    lst = os.path.join(out_dir, "list.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    silent = os.path.join(out_dir, "video.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    total = sum(s[3] for s in scenes)
    final = os.path.join(out_dir, "final.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav,
         "-filter_complex", f"[1:a]apad=whole_dur={total:.2f}[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", final])
    print("DONE:", final, f"({total:.1f}s)")
    return final


if __name__ == "__main__":
    cfg_path, out_dir = sys.argv[1], sys.argv[2]
    with open(cfg_path) as f:
        cfg = json.load(f)
    build(os.path.abspath(out_dir), cfg)
