# -*- coding: utf-8 -*-
"""m1.py — M1a 四柱内核：日柱/时柱实算；年柱/月柱 anchor_missing（solar_terms 未录满）。
输入=北京时间(UTC+8)+东经经度；真太阳时=北京时+(经度−120)×4分+NOAA均时差；
换日界=真太阳时子正，日柱时柱同轨真太阳时。数据权威=ganzhi_days.csv。"""
import argparse, csv, json, math, os, sys
from datetime import datetime, timedelta
from functools import lru_cache

BASE = os.path.dirname(os.path.abspath(__file__))
GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
RANGE_LO, RANGE_HI = "1900-01-01 03:30", "2100-12-31 20:30"  # M1 有效输入（宁紧勿松，越界 out_of_range）
ANCHOR_MSG = "solar_terms 表未录满，按 preregister M1 节气策略裁决禁回退"

def eot_minutes(dt):
    """NOAA 均时差（分钟）：B=2π/365·(N−81)，EOT=9.87·sin2B−7.53·cosB−1.5·sinB，N=年日序。"""
    b = 2 * math.pi * (dt.timetuple().tm_yday - 81) / 365
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

def true_solar(dt, lon):
    """真太阳时 = 北京时 + (经度−120)×4 分 + EOT(输入日期)；跨历日由 timedelta 自动处理。"""
    return dt + timedelta(minutes=(lon - 120) * 4 + eot_minutes(dt))

@lru_cache(maxsize=None)
def load_days():
    """ganzhi_days.csv → {date: ganzhi}；lru_cache 模块级缓存：CLI 单次与批量循环均只读一次文件。"""
    with open(os.path.join(BASE, "data", "ganzhi_days.csv"), encoding="utf-8") as f:
        return {r["date"]: r["ganzhi"] for r in csv.DictReader(f)}

def shichen(hour):
    """时辰地支序：23/0→子(0)…22→亥(11)。23:00-24:00 子时归当日、0:00-1:00 归次日（子正口径）。"""
    return (hour + 1) // 2 % 12

def hour_pillar(day_ganzhi, hour):
    """五鼠遁：日干 g → 子时干=(2g)%10，每时辰+1（甲己甲子、乙庚丙子…戊癸壬子）。"""
    g = GAN.index(day_ganzhi[0])
    z = shichen(hour)
    return GAN[(2 * g + z) % 10] + ZHI[z]

def compute(dt, lon, days=None):
    """(北京时 datetime, 东经 float) → 四柱 JSON dict；非法输入返回 {"error": ...}。"""
    if dt.second or dt.microsecond:  # 与 CLI %H:%M 同口径：拒绝秒级输入，不静默丢弃
        return {"error": f"错误: 输入不含秒精度，收到 {dt.strftime('%Y-%m-%d %H:%M:%S')}"}
    s = dt.strftime("%Y-%m-%d %H:%M")
    if not -180 <= lon <= 180:
        return {"error": f"错误: 经度 {lon} 超出 -180~180"}
    if not RANGE_LO <= s <= RANGE_HI:
        return {"error": f"错误: {s} 超出 M1 有效范围 {RANGE_LO} ~ {RANGE_HI}（out_of_range，不静默截断）"}
    ts = true_solar(dt, lon)
    ds = ts.date().isoformat()
    days = days if days is not None else load_days()
    if ds not in days:
        return {"error": f"错误: 真太阳时 {ds} 落 ganzhi_days 表外 1900-01-01~2100-12-31（out_of_range）"}
    dg = days[ds]
    return {
        "input": {"datetime": s, "lon": lon, "tz": "UTC+8 北京时间"},
        "pillars": {
            "year":  {"ganzhi": None, "status": "anchor_missing", "reason": ANCHOR_MSG},
            "month": {"ganzhi": None, "status": "anchor_missing", "reason": ANCHOR_MSG},
            "day":   {"ganzhi": dg, "rule_id": "r1", "source": "ganzhi_days.csv"},
            "hour":  {"ganzhi": hour_pillar(dg, ts.hour), "rule_id": "r2"},
        },
        "true_solar_time": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "notes": [f"均时差 EOT={eot_minutes(dt):+.2f} 分（NOAA 公式，输入日期）",
                  "换日界=真太阳时子正，日柱时柱同轨真太阳时"],
    }

def main():
    ap = argparse.ArgumentParser(description="四柱内核 M1a：日柱/时柱实算（年柱/月柱 anchor_missing）")
    ap.add_argument("--datetime", required=True, help="北京时间，格式 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0, help="东经经度（东经为正），默认 120")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    r = compute(dt, a.lon)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        p = r["pillars"]
        print(f"输入: {r['input']['datetime']}  东经 {r['input']['lon']}°（UTC+8）")
        print(f"真太阳时: {r['true_solar_time']}")
        print(f"年柱: 待定 — {p['year']['reason']}")
        print(f"月柱: 待定 — {p['month']['reason']}")
        print(f"日柱: {p['day']['ganzhi']}（rule {p['day']['rule_id']}，{p['day']['source']}）")
        print(f"时柱: {p['hour']['ganzhi']}（rule {p['hour']['rule_id']}）")
        for n in r["notes"]:
            print(f"  · {n}")

if __name__ == "__main__":
    main()
