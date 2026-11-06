#!/usr/bin/env python3
"""Measure a rendered cell: screenshots at 1440/375 + objective metrics.

  python3 bench/measure.py --date 2026-11-07            # all cells
  python3 bench/measure.py --date 2026-11-07 --cell hallmark/01-saas-landing
"""
import argparse
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

BENCH = os.path.dirname(os.path.abspath(__file__))

JS = r"""
() => {
  const cvs = document.createElement('canvas').getContext('2d');
  const norm = (c) => { cvs.fillStyle = '#000'; cvs.fillStyle = c; return cvs.fillStyle; };
  const bgOf = (el) => {
    let n = el;
    while (n) {
      const bg = getComputedStyle(n).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return norm(bg);
      n = n.parentElement;
    }
    return norm(getComputedStyle(document.body).backgroundColor || 'rgb(255,255,255)');
  };
  const textEls = [...document.querySelectorAll('body *')].filter(el => {
    const t = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    const s = getComputedStyle(el);
    return t && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.fontSize) >= 10;
  });
  const pairs = textEls.slice(0, 400).map(el => ({fg: norm(getComputedStyle(el).color), bg: bgOf(el), size: parseFloat(getComputedStyle(el).fontSize)}));
  const css = [...document.querySelectorAll('style')].map(s => s.textContent).join('\n')
            + [...document.querySelectorAll('[style]')].map(e => e.getAttribute('style')).join('\n');
  return {
    fonts: [...new Set(textEls.map(el => getComputedStyle(el).fontFamily))],
    sizes: [...new Set(textEls.map(el => getComputedStyle(el).fontSize))],
    colors: [...new Set(textEls.map(el => norm(getComputedStyle(el).color)))],
    bgColors: [...new Set([...document.querySelectorAll('body *')].map(el => norm(getComputedStyle(el).backgroundColor)).filter(c => c !== 'rgba(0, 0, 0, 0)'))],
    pairs: pairs,
    css: css.slice(0, 200000),
    text: (document.body.innerText || '').slice(0, 20000),
    h1: document.querySelectorAll('h1').length,
    h2: document.querySelectorAll('h2').length,
    semantic: ['header','main','nav','footer','section','article','aside'].reduce((a,t) => (a[t] = document.querySelectorAll(t).length, a), {}),
    bodyHeight: document.body.scrollHeight,
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    tapViolations: [...document.querySelectorAll('a,button')].filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && (r.height < 44 || r.width < 44);
    }).length,
    smallText: textEls.filter(el => parseFloat(getComputedStyle(el).fontSize) < 12).length,
  };
}
"""


def _oklch_to_rgb(L, C, H):
    import math
    h = math.radians(H)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    def enc(x):
        x = max(0.0, min(1.0, x))
        return 255 * (12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055)

    return enc(r), enc(g), enc(bb)


def parse_color(s):
    """Parse rgb()/rgba()/hsl()/oklch()/color(srgb ...) into (r, g, b, a)."""
    if not s:
        return None
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return r, g, b, a
    nums = re.findall(r"-?[\d.]+", s)
    if s.startswith("oklch") and len(nums) >= 3:
        L, C, H = float(nums[0]), float(nums[1]), float(nums[2])
        a = float(nums[3]) if len(nums) > 3 else 1.0
        if L <= 1:
            r, g, b = _oklch_to_rgb(L, C, H)
            return r, g, b, a
    if s.startswith("color(") and len(nums) >= 3:
        r, g, b = (float(x) * 255 for x in nums[:3])
        a = float(nums[3]) if len(nums) > 3 else 1.0
        return r, g, b, a
    if s.startswith("rgb") and len(nums) >= 3:
        r, g, b = (float(x) for x in nums[:3])
        a = float(nums[3]) if len(nums) > 3 else 1.0
        return r, g, b, a
    if s.startswith("hsl") and len(nums) >= 3:
        import colorsys
        hh, ss, ll = float(nums[0]) / 360, float(nums[1]) / 100, float(nums[2]) / 100
        r, g, b = colorsys.hls_to_rgb(hh, ll, ss)
        a = float(nums[3]) if len(nums) > 3 else 1.0
        return r * 255, g * 255, b * 255, a
    return None


def luminance(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(fg, bg):
    a, b = parse_color(fg), parse_color(bg)
    if not a or not b:
        return None
    if a[3] < 1:  # alpha text: composite over bg
        a = tuple(a[i] * a[3] + b[i] * (1 - a[3]) for i in range(3)) + (1,)
    l1, l2 = luminance(a), luminance(b)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def measure_cell(page, path, out_dir):
    page.set_viewport_size({"width": 1440, "height": 900})
    errors, external = [], []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
    page.on("request", lambda r: external.append(r.url[:200]) if not r.url.startswith(("file:", "data:")) else None)
    page.goto("file://" + path, wait_until="load")
    page.wait_for_timeout(600)
    m = page.evaluate(JS)
    page.screenshot(path=os.path.join(out_dir, "shot-1440.png"), full_page=True)

    page.set_viewport_size({"width": 375, "height": 812})
    page.wait_for_timeout(300)
    m375 = page.evaluate(JS)
    page.screenshot(path=os.path.join(out_dir, "shot-375.png"), full_page=True)

    ratios = [c for c in (contrast(p["fg"], p["bg"]) for p in m["pairs"]) if c is not None]
    m.update({
        "contrast_min": min(ratios) if ratios else None,
        "contrast_fail_ratio": round(sum(1 for r in ratios if r < 4.5) / len(ratios), 3) if ratios else None,
        "overflow_375": m375["scrollWidth"] > m375["innerWidth"] + 1,
        "scrollWidth_375": m375["scrollWidth"],
        "console_errors": errors[:20],
        "external_requests": external[:20],
    })
    m.pop("pairs", None)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--cell", default=None, help="skill/brief")
    args = ap.parse_args()

    runs = os.path.join(BENCH, "runs")
    dates = [args.date] if args.date else sorted(os.listdir(runs))
    cells = []
    for d in dates:
        base = os.path.join(runs, d)
        if not os.path.isdir(base):
            continue
        for skill in sorted(x for x in os.listdir(base) if os.path.isdir(os.path.join(base, x))):
            for brief in sorted(os.listdir(os.path.join(base, skill))):
                rel = f"{skill}/{brief}"
                if args.cell and rel != args.cell:
                    continue
                p = os.path.join(base, skill, brief, "index.html")
                if os.path.exists(p):
                    cells.append((d, skill, brief, p))

    if not cells:
        raise SystemExit("no cells to measure")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        for d, skill, brief, path in cells:
            out_dir = os.path.dirname(path)
            try:
                m = measure_cell(page, path, out_dir)
                json.dump(m, open(os.path.join(out_dir, "metrics.json"), "w"), ensure_ascii=False, indent=1)
                print(f"measured {skill}/{brief}: contrast_fail={m['contrast_fail_ratio']} overflow375={m['overflow_375']}")
            except Exception as exc:  # noqa: BLE001
                print(f"FAILED {skill}/{brief}: {exc}", file=sys.stderr)
        browser.close()


if __name__ == "__main__":
    main()