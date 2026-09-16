# -*- coding: utf-8 -*-
"""m1.py — M1b 四柱内核：四柱全实算+十神(L2)。输入=北京时间(UTC+8)+东经经度；真太阳时=北京时+(经度−120)×4分+NOAA均时差；
换日界=真太阳时子正，日柱时柱同轨真太阳时；年柱=立春换年(r3)、月柱=节换月(r4)，节气唯一权威=solar_terms.csv；十神=r5。"""
import argparse, bisect, csv, json, math, os, sys
from datetime import datetime, timedelta
from functools import lru_cache
from rules import rel, wx_of_gan

BASE = os.path.dirname(os.path.abspath(__file__))
GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
RANGE_LO, RANGE_HI = "1949-01-01 03:30", "2100-12-31 20:30"  # M1 有效输入（真太阳时须落表内，越界 out_of_range）
JIE = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]  # 12 节月支序：寅=0…丑=11

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

@lru_cache(maxsize=None)
def load_terms():
    """solar_terms.csv → 12 节行按 datetime 排序（年柱立春/月柱节换月的最近上一节池；表 1948-2101 录满，唯一运行期权威）。"""
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["jie_zhong"] == "节"]
    return sorted(rows, key=lambda r: r["datetime"])

def shichen(hour):
    """时辰地支序：23/0→子(0)…22→亥(11)。23:00-24:00 子时归当日、0:00-1:00 归次日（子正口径）。"""
    return (hour + 1) // 2 % 12

def hour_pillar(day_ganzhi, hour):
    """五鼠遁：日干 g → 子时干=(2g)%10，每时辰+1（甲己甲子、乙庚丙子…戊癸壬子）。"""
    g = GAN.index(day_ganzhi[0])
    z = shichen(hour)
    return GAN[(2 * g + z) % 10] + ZHI[z]

TEN = {"比和": ("比肩", "劫财"), "生": ("偏印", "正印"), "泄": ("食神", "伤官"),
       "克": ("七杀", "正官"), "耗": ("偏财", "正财")}  # r5 十神表：五行动态 + 阴阳同异（同=第一字）

def ten_god(day_master, other_gan):
    """r5 十神：以日干为「我」；rel(他干五行, 日干五行) 定动态——生=生我→印、泄=我生→食伤、
    克=克我→官杀、耗=我克→财；阴阳同异定偏正（甲见丙=食神、甲见庚=七杀、甲见壬=偏印…）。"""
    r = rel(wx_of_gan(other_gan), wx_of_gan(day_master))
    return TEN[r][GAN.index(day_master) % 2 != GAN.index(other_gan) % 2]  # False(同)=0、True(异)=1

@lru_cache(maxsize=None)
def load_canggan():
    """canggan.csv → {地支: 藏干串}；lru_cache 缓存，藏干序以 CSV 为权威。"""
    with open(os.path.join(BASE, "data", "canggan.csv"), encoding="utf-8") as f:
        return {r["dizhi"]: r["canggan_list"] for r in csv.DictReader(f)}

def branch_gods(day_master, zhi, canggan):
    """地支十神（r5）：藏干逐个对日干取名，序与 canggan.csv 一致；日支同按藏干十神（日支=日元所坐）。"""
    return [{"gan": g, "god": ten_god(day_master, g)} for g in canggan[zhi]]

def year_pillar(bj, terms):
    """r3 立春换年：判界两侧同用北京时域（bj="%Y-%m-%d %H:%M"；solar_terms.csv=UTC+8，2026-09-15 修复时制混用，
    禁与真太阳时混比）：北京时≥当年立春→当年年干支，否则上年；年干支=(year-4)%60（甲子=0，1900=庚子）。"""
    y0 = int(bj[:4])
    lc = next(r["datetime"] for r in terms if r["year"] == bj[:4] and r["term"] == "立春")
    y = y0 if bj >= lc else y0 - 1
    return GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]

def month_pillar(bj, terms, year_gan):
    """r4 节换月：datetime≤bj 的最近上一 12 节（二分）→ 月支序 m（寅=0…丑=11）；判界同 r3 用北京时域；
    月干五虎遁=(2·年干+2+m)%10。"""
    i = bisect.bisect_right([r["datetime"] for r in terms], bj) - 1
    m = JIE.index(terms[i]["term"])
    return GAN[(2 * year_gan + 2 + m) % 10] + ZHI[(2 + m) % 12]

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
    terms = load_terms()
    ygz = year_pillar(s, terms)    # r3 判界=北京时域（solar_terms.csv 同域；真太阳时仅用于日/时柱）
    mgz = month_pillar(s, terms, GAN.index(ygz[0]))
    dgz = days[ds]
    hgz = hour_pillar(dgz, ts.hour)
    cg = load_canggan()
    dm = dgz[0]
    tg = {"day_master": dm, "rule_id": "r5", "source": "rules.py 五行关系 + canggan.csv 藏干",
          "stems": {"year": ten_god(dm, ygz[0]), "month": ten_god(dm, mgz[0]), "hour": ten_god(dm, hgz[0])},
          "branches": {k: branch_gods(dm, gz[1], cg) for k, gz in
                       (("year", ygz), ("month", mgz), ("day", dgz), ("hour", hgz))}}
    return {
        "input": {"datetime": s, "lon": lon, "tz": "UTC+8 北京时间"},
        "pillars": {
            "year":  {"ganzhi": ygz, "rule_id": "r3", "source": "solar_terms.csv"},
            "month": {"ganzhi": mgz, "rule_id": "r4", "source": "solar_terms.csv"},
            "day":   {"ganzhi": dgz, "rule_id": "r1", "source": "ganzhi_days.csv"},
            "hour":  {"ganzhi": hgz, "rule_id": "r2"},
        },
        "ten_gods": tg,
        "true_solar_time": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "notes": [f"均时差 EOT={eot_minutes(dt):+.2f} 分（NOAA 公式，输入日期）",
                  "换日界=真太阳时子正；年柱立春换年(r3)、月柱节换月(r4)，节气唯一权威=solar_terms.csv"],
    }

def main():
    ap = argparse.ArgumentParser(description="四柱内核 M1b：四柱全实算（年柱立春换年、月柱节换月）")
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
        print(f"年柱: {p['year']['ganzhi']}（rule {p['year']['rule_id']}，{p['year']['source']}）")
        print(f"月柱: {p['month']['ganzhi']}（rule {p['month']['rule_id']}，{p['month']['source']}）")
        print(f"日柱: {p['day']['ganzhi']}（rule {p['day']['rule_id']}，{p['day']['source']}）")
        print(f"时柱: {p['hour']['ganzhi']}（rule {p['hour']['rule_id']}）")
        tg = r["ten_gods"]
        print(f"十神(r5，日干 {tg['day_master']}）：年干 {tg['stems']['year']} 月干 {tg['stems']['month']} 时干 {tg['stems']['hour']}")
        for k, v in tg["branches"].items():
            print(f"  {k}支藏干十神: " + " ".join(f"{b['gan']}:{b['god']}" for b in v))
        for n in r["notes"]:
            print(f"  · {n}")

if __name__ == "__main__":
    main()
