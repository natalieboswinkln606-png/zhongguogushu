# -*- coding: utf-8 -*-
"""gen_shuowang.py — 生成 data/shuowang.csv（朔日表，1948-2101 公历年内全部农历月，含闰月）。
数据源契约（L0 农历面，2026-08-16；修订 v2：sw-002 返工修正取值逻辑）：
- 朔日（农历月初一）：lunar-python 全量（LunarMonth.getFirstJulianDay 东八区日），
  1948-2100 与 HKO 官方年历文本逐日对拍（hko_shuo_1948_2100.csv，月名行=朔日），source_ref=hko+lunar；
  2101 无官方锚点，source_ref=lunar 且 notes 标算法值。
- 朔日日期裁决：一律取 lunar 月首（L0 农历面契约），HKO 官方锚点逐日交叉确认；
  临界跨日（skyfield 新月 UTC+8 时刻落次日）时裁决规则：lunar 月首与 HKO 一致 → confirmed
  （新月时刻仅作参考，不参与日期裁决，notes 注明跨日）；HKO 缺失/不一致 → status=arbitrated 待裁
  （不静默取任一侧）。【v2 修正：原实现 L101 取 st[:10]（skyfield 时刻 UTC+8 日期），
  2097-07 月首 lunar=08-07 被 skyfield 时刻 08-08 覆盖致主表取反侧；现改为月首为准】
- 朔/望时刻：skyfield DE440s 日月视黄经差 0°/180° 二分求根（UTC+8，分钟级）——独立天文计算，作参考。
  shuo_time 列 = 月首日期 + 参考时刻（HH:MM）；跨日时日期按裁决、时刻为其真实 UTC+8 时分。
- 闰月：LunarMonth.isLeap / getMonth()<0，month 记被闰月序、is_ruen=1。
- 幂等：确定性函数直接覆写；对拍申报（arbitration_log/boundary_cases）由 shuowang_compare.py 去重处理。"""
import csv, os, re, sys, time
from datetime import datetime, timedelta
from lunar_python import LunarYear

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "shuowang_raw")
OUT = os.path.join(BASE, "data", "shuowang.csv")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
HKO_FILE = os.path.join(RAW, "hko_shuo_1948_2100.csv")
NOTE_2101 = "算法值（lunar-python 朔日，无官方锚点；时刻 skyfield）"
MONTH_CN = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]

def lc_year_gz(y):  # 农历年干支：(y-4)%60，甲子=0（与 ganzhi_days 同式）
    return GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]

def jd2date(jd):  # getFirstJulianDay（UTC 12:00 儒略日）→ 公历日期（东八区朔日）
    return (datetime(2000, 1, 1, 12, 0) + timedelta(days=jd - 2451545)).date()

def lunar_months():
    """1947-2102 农历年全部月（getYear() 过滤去前年冬月/次年正月），(公历朔日, 月序, 闰) 列表"""
    rows = []
    for y in range(1947, 2103):
        for m in LunarYear.fromYear(y).getMonths():
            if m.getYear() != y:
                continue
            d = jd2date(m.getFirstJulianDay())
            if datetime(1948, 1, 1).date() <= d <= datetime(2101, 12, 31).date():
                rows.append((d, m.getMonth() if m.getMonth() > 0 else -m.getMonth(),
                             1 if m.isLeap() else 0, y))
    return rows

def load_hko():
    """HKO 官方锚点 → {公历日期: (月序, 闰)}；文件缺失时返回 None（生成不阻塞，source_ref 退 lunar）"""
    if not os.path.exists(HKO_FILE):
        return None
    out = {}
    with open(HKO_FILE, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["date"]] = (int(r["month"]), int(r["is_ruen"]))
    return out

def phase_dt(sf, d0, target, span=1):
    """日月视黄经差 = target 的东八区时刻：窗口 = 东八区 [d0-span 0:00, d0+span 0:00]，二分 25 次。
    朔（target=0）窗口 ±1 天；望（target=180）窗口 ±2 天（朔望间隔 13.5~15.6 天，望东八区日最晚=朔+16）。"""
    TS, EPH = sf
    a = TS.utc(d0.year, d0.month, d0.day - (span + 1), 16)
    b = TS.utc(d0.year, d0.month, d0.day + span, 16)
    def lon(t):
        _, mlon, _ = EPH["earth"].at(t).observe(EPH["moon"]).apparent().frame_latlon(EPH["frame"])
        _, slon, _ = EPH["earth"].at(t).observe(EPH["sun"]).apparent().frame_latlon(EPH["frame"])
        return (mlon.degrees - slon.degrees) % 360
    fa, fb = (lon(a) - target) % 360, (lon(b) - target) % 360
    if fa > fb:
        fa -= 360
    if not (fa < 0 < fb):
        return None  # 窗口内无该相位（lunar 与天文差 ≥1 天 → 交对拍申报）
    for _ in range(25):
        m = TS.tt_jd((a.tt + b.tt) / 2)
        fm = (lon(m) - target) % 360
        if fm > 180:
            fm -= 360
        a, b = (m, b) if fm < 0 else (a, m)
    t = TS.tt_jd((a.tt + b.tt) / 2).utc_datetime() + timedelta(hours=8)
    return t.strftime("%Y-%m-%dT%H:%M") + "+08:00"

def main():
    from skyfield.api import load
    from skyfield.framelib import ecliptic_frame
    BSP = "de440s.bsp"
    for p in (os.path.join(os.environ.get("TEMP", ""), "de440s.bsp"), os.path.join(BASE, "de440s.bsp")):
        if os.path.exists(p):
            BSP = p
            break
    else:
        sys.exit(f"缺少星历文件：下载 de440s.bsp 到 {BSP}")
    TS, EPH = load.timescale(), load(BSP)
    sf = (TS, {"sun": EPH["sun"], "moon": EPH["moon"], "earth": EPH["earth"],
               "frame": ecliptic_frame})
    hko = load_hko()
    months = lunar_months()
    print(f"lunar 月数 {len(months)}（公历 1948-01-01 ~ 2101-12-31），HKO 锚点 {'有' if hko else '无'}")
    n = 0
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "is_ruen", "shuo_time", "wang_time", "lunar_year", "status", "source_ref", "notes"])
        prev = ""
        for d0, mo, leap, ly in sorted(months):
            st = phase_dt(sf, d0, 0.0)
            wt = phase_dt(sf, d0 + timedelta(days=15), 180.0, span=2)  # 望窗口中心=朔+15 天，跨度 ±2 天
            # v2 修正：朔日日期以 lunar 月首 d0 为准（skyfield 时刻仅作参考，不参与日期裁决）
            shuo_date = d0.isoformat()
            # shuo_time = 月首日期 + 参考时刻（新月 UTC+8 的 HH:MM；跨日时分钟为其真实时刻，日期按裁决）
            shuo = f"{shuo_date}T{st[11:16]}+08:00" if st else ""
            # 官方对拍：锚点段逐行核验，任何不一致 → status=arbitrated + notes 记差异
            note = NOTE_2101 if d0.year == 2101 else ""
            if note == "" and leap:
                note = "闰" + MONTH_CN[mo - 1]
            if st and st[:10] != shuo_date:  # 临界跨日：新月 UTC+8 落次日，月首裁决不变，notes 注明
                note = (note + "；" if note else "") + \
                       f"新月时刻 UTC+8 落 {st[:10]} {st[11:16]}（跨日界，朔日按多源裁决取 {shuo_date}）"
            status, src = "confirmed", "hko+lunar"
            if hko is not None and d0.year <= 2100:
                got = hko.get(shuo_date)
                if got != (mo, leap):
                    status = "arbitrated"
                    note = (note + "；" if note else "") + f"HKO 官方朔日 {shuo_date}={got} vs lunar {mo}月{'闰' if leap else ''} 不一致"
            elif d0.year == 2101:
                src = "lunar"
                status = "pending"
            else:  # HKO 采集缺失段（1948-2100）：按 2101 处理但注缺失
                src, status = "lunar", "pending"
                note = (note + "；" if note else "") + "HKO 锚点缺失段（官方对拍未覆盖）"
            row = [str(d0.year), mo, leap, shuo, wt or "", lc_year_gz(ly), status, src, note]
            assert (shuo or shuo_date + "T00:00+08:00") > prev, f"朔日非严格递增 {row}"
            prev = shuo or shuo_date + "T00:00+08:00"
            w.writerow(row)
            n += 1
    print(f"written: {OUT}（{n} 行）")

if __name__ == "__main__":
    main()
