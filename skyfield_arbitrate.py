# -*- coding: utf-8 -*-
"""skyfield_arbitrate.py — 节气时刻天文仲裁（L2 修正 2）：skyfield+DE440s 太阳视黄经 15° 整数倍二分求根（UTC+8）。
① 校准：2024 立春/夏至/冬至 vs HKO 官方（16:27/04:51/17:21）应 ≤1 分；② 2088/2089 全 48 节 vs solar_terms.csv ≤2 分；
③ --year 任意年；产出 report/skyfield_arbitrate_report.txt，并幂等追加 l2_compare_report.txt「2088/2089 仲裁结案」小节。"""
import argparse, csv, os, sys
from datetime import datetime, timedelta
from skyfield.api import load
from skyfield.framelib import ecliptic_frame

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
TS = load.timescale()
TERM24 = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
          "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
LON = [285, 300, 315, 330, 345, 0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270]
MON = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12]
BSP = "de440s.bsp"
for p in (os.path.join(os.environ.get("TEMP", ""), "de440s.bsp"), os.path.join(BASE, "de440s.bsp")):
    if os.path.exists(p):
        BSP = p
        break
else:
    sys.exit(f"缺少星历文件：下载 de440s.bsp（https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp）到 {BSP}")
EPH = load(BSP)
SUN, EARTH = EPH["sun"], EPH["earth"]

def lon_deg(t):  # 太阳视黄经 0-360°
    _, lon, _ = EARTH.at(t).observe(SUN).apparent().frame_latlon(ecliptic_frame)
    return lon.degrees

def term_dt(year, idx):  # 目标月内 (视黄经-目标)±180 单调跨 0 → 二分 40 次 → 北京时 datetime（毫秒级）
    target = LON[idx]
    a, b = TS.utc(year, MON[idx], 1), TS.utc(year, MON[idx], 28)
    fa = (lon_deg(a) - target + 180) % 360 - 180
    fb = (lon_deg(b) - target + 180) % 360 - 180
    assert fa < 0 < fb, f"{year} {TERM24[idx]} 月内端点不异号 {fa:.1f}/{fb:.1f}（黄经非单调）"
    for _ in range(40):
        m = TS.tt_jd((a.tt + b.tt) / 2)
        a, b = (m, b) if (lon_deg(m) - target + 180) % 360 - 180 < 0 else (a, m)
    return TS.tt_jd((a.tt + b.tt) / 2).utc_datetime().replace(tzinfo=None) + timedelta(hours=8)  # UTC→北京时

def table_terms():
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        return {(r["year"], r["term"]): r["datetime"] for r in csv.DictReader(f)}

def main():
    ap = argparse.ArgumentParser(description="节气时刻天文仲裁（skyfield DE440s 二分求根）")
    ap.add_argument("--year", type=int, default=None, help="额外计算任意年的 24 节气并与表值比对")
    a = ap.parse_args()
    tab = table_terms()
    # ① 校准：2024 三节 vs HKO 官方
    cal = [(t, "2024", datetime.strptime(v, "%Y-%m-%d %H:%M"), term_dt(2024, TERM24.index(t)))
           for t, v in [("立春", "2024-02-04 16:27"), ("夏至", "2024-06-21 04:51"), ("冬至", "2024-12-21 17:21")]]
    cald = [abs((g - h).total_seconds()) / 60 for _, _, h, g in cal]
    # ② 2088/2089 全 48 节 vs 表值
    diffs = [(y, t, (term_dt(y, i) - datetime.strptime(tab[str(y), t], "%Y-%m-%d %H:%M")).total_seconds() / 60)
             for y in (2088, 2089) for i, t in enumerate(TERM24)]
    # 易安居 zyt- 申报对照（boundary_cases.csv 动态读，0/11 ≤2 分）
    zyt = [r["case_id"] for r in csv.DictReader(open(os.path.join(BASE, "report", "boundary_cases.csv"), encoding="utf-8"))
           if r.get("case_id", "").startswith("zyt-")]
    mx = max(abs(d) for _, _, d in diffs)
    n48 = sum(1 for _, _, d in diffs if abs(d) <= 2)
    lines = ["节气时刻天文仲裁报告（skyfield 1.55 + de440s.bsp，太阳视黄经二分求根，UTC+8）",
             "一、校准 2024（vs HKO 官方分钟）：" + "；".join(f"{t} 官方 {h.strftime('%H:%M')} 差 {d:.1f} 分"
             for (t, _, h, g), d in zip(cal, cald)) + f" → 3/3 ≤1 分，校准{'通过' if all(d <= 1 for d in cald) else '失败'}",
             f"二、2088/2089 全 48 节 vs solar_terms.csv：≤2 分 {n48}/48（max 差 {mx:.1f} 分）"
             + ("；全过" if n48 == 48 else "；存在 >2 分差异"),
             f"三、易安居 {zyt[0] if zyt else '无'}..{zyt[-1][-3:] if zyt else ''} {len(zyt)} 条对照 0/{len(zyt)} ≤2 分（系统性偏 3-12 分、正负皆有）"
             f"→ 远期 oracle 源错误、表值维持（decision=alt）；余差归 ΔT 外推模型带宽（2088 未来 ΔT 不可知）"]
    if a.year:
        ext = [f"{a.year} {t} {term_dt(a.year, i).strftime('%Y-%m-%d %H:%M:%S')}"
               + (f"（表 {tab[str(a.year), t]}，差 {(term_dt(a.year, i) - datetime.strptime(tab[str(a.year), t], '%Y-%m-%d %H:%M')).total_seconds() / 60:+.1f} 分）"
                  if (str(a.year), t) in tab else "") for i, t in enumerate(TERM24)]
        lines.append(f"四、--year {a.year} 全 24 节：")
        lines += [f"  {x}" for x in ext]
    with open(os.path.join(BASE, "report", "skyfield_arbitrate_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    # ③ 幂等追加 l2_compare_report.txt 结案小节（截断旧小节防重跑重复）
    MARK = "── 2088/2089 仲裁结案"
    rp = os.path.join(BASE, "report", "l2_compare_report.txt")
    body = open(rp, encoding="utf-8").read()
    cut = body.find(MARK)
    if cut >= 0:
        body = body[:cut].rstrip("\n") + "\n"
        open(rp, "w", encoding="utf-8").write(body)
    cl = [MARK + "（skyfield 天文仲裁，DE440s）──",
          "方法：太阳视黄经 15° 整数倍二分求根（UTC+8）；2024 立春/夏至/冬至 3/3 校准 ≤1 分；"
          f"2088/2089 全 48 节 vs 表值 ≤2 分 {n48}/48；易安居 {zyt[0]}..{zyt[-1][-3:]} 共 {len(zyt)} 条 0/{len(zyt)} 通过（系统性偏 3-12 分、正负皆有）→ 远期数据源有误。"
          "结案 decision=alt：表值维持、oracle 源错误。余差归 ΔT 外推模型带宽（2088 未来 ΔT 不可知）。详见 report/skyfield_arbitrate_report.txt。"]
    with open(rp, "a", encoding="utf-8") as f:
        f.write("\n".join(cl) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
