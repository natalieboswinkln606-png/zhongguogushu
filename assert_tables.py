# -*- coding: utf-8 -*-
"""assert_tables.py — 性质断言（不抄表内容）+ 锚点抽查。输出 report/assert_report.txt。"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules import GAN, ZHI

BASE = os.path.dirname(os.path.abspath(__file__))
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]
RES = []

def check(name, cond, detail=""):
    RES.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), name, detail)

def read(fn):
    with open(os.path.join(BASE, "data", fn), encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if not r[list(r)[0]].startswith("#")]

def find(rows, **kw):  # 锚点查找：缺失返回 None，避免 next() 抛 StopIteration 崩溃
    try:
        return next(r for r in rows if all(r[k] == v for k, v in kw.items()))
    except (StopIteration, KeyError):
        return None

# ---- nayin ----
n = read("nayin.csv")
pairs = [r["ganzhi_pair"] for r in n]
gz_in_nayin = [p[i:i + 2] for p in pairs for i in (0, 2)]
check("nayin 行数=30", len(n) == 30, str(len(n)))
check("nayin 干支对唯一", len(set(pairs)) == 30)
check("nayin 覆盖 60 甲子且无重", len(set(gz_in_nayin)) == 60 and set(gz_in_nayin) == set(JIAZI))
check("nayin 五行名以五行字结尾", all(r["wuxing_name"][-1] in "金木水火土" for r in n))
# ---- canggan ----
c = read("canggan.csv")
check("canggan 行数=12 且地支恰一行", len(c) == 12 and set(r["dizhi"] for r in c) == set(ZHI))
check("canggan 藏干字符合法", all(set(r["canggan_list"]) <= set(GAN) for r in c))
for z, want in [("午", "丁己"), ("子", "癸"), ("丑", "己癸辛"), ("辰", "戊乙癸"), ("亥", "壬甲")]:
    r = find(c, dizhi=z)
    check(f"canggan 锚点 {z}={want}", r is not None and r["canggan_list"] == want,
          (r or {}).get("canggan_list", "缺失"))
# ---- bagong ----
bg = read("bagong.csv")
check("bagong 行数=64", len(bg) == 64, str(len(bg)))
check("bagong 每宫 8 卦",
      [sum(1 for r in bg if r["palace"] == p) for p in "乾兑离震巽坎艮坤"] == [8] * 8)
check("bagong 卦名唯一", len(set(r["gua_name"] for r in bg)) == 64)
check("bagong 卦序每宫 1-8", all(sorted(int(r["gua_order"]) for r in bg if r["palace"] == p) == list(range(1, 9)) for p in set(r["palace"] for r in bg)))
for g, want in [("天泽履", "艮"), ("火天大有", "乾"), ("地泽临", "坤")]:  # 火天大有=乾宫归魂卦（京房通行序），CSV 为权威
    r = find(bg, gua_name=g)
    check(f"bagong 锚点 {g}→{want}宫", r is not None and r["palace"] == want, (r or {}).get("palace", "缺失"))
# ---- najia ----
nj = read("najia.csv")
check("najia 行数=64 且卦名集合=bagong", len(nj) == 64 and {r["gua"] for r in nj} == {r["gua_name"] for r in bg})
check("najia 纳支 6 字全合法", all(len(r["dizhi_najia"]) == 6 and set(r["dizhi_najia"]) <= set(ZHI) for r in nj))
check("najia 纳干 2 字全合法", all(len(r["tiangan_najia"]) == 2 and set(r["tiangan_najia"]) <= set(GAN) for r in nj))
q, k = find(nj, gua="乾为天"), find(nj, gua="坤为地")
check("najia 乾=甲壬 坤=乙癸（纳甲歌）",
      q is not None and q["tiangan_najia"] == "甲壬" and k is not None and k["tiangan_najia"] == "乙癸",
      f"{q and q['tiangan_najia']} / {k and k['tiangan_najia']}")
check("najia 乾内卦子寅辰 外卦午申戌",
      q is not None and q["dizhi_najia"][:3] == "子寅辰" and q["dizhi_najia"][3:] == "午申戌",
      q and q["dizhi_najia"])
check("najia 坤内卦未巳卯",
      k is not None and k["dizhi_najia"][:3] == "未巳卯", k and k["dizhi_najia"])
# ---- changsheng ----
cs = read("changsheng.csv")
check("changsheng 行数=120", len(cs) == 120, str(len(cs)))
check("changsheng 每干 12 行", all(sum(1 for r in cs if r["tiangan"] == g) == 12 for g in GAN))
check("changsheng 每干 12 地支唯一", all(len({r["dizhi"] for r in cs if r["tiangan"] == g}) == 12 for g in GAN))
for g, want in [("甲", "亥"), ("乙", "午"), ("庚", "巳")]:
    r = find(cs, tiangan=g, stage="长生")
    check(f"changsheng 锚点 {g}长生={want}", r is not None and r["dizhi"] == want,
          (r or {}).get("dizhi", "缺失"))
# ---- ganzhi_days ----
gd = read("ganzhi_days.csv")
dates = [r["date"] for r in gd]
check("ganzhi_days 行数=73414", len(gd) == 73414, str(len(gd)))
check("ganzhi_days 日期无重复", len(set(dates)) == len(dates))
check("ganzhi_days 干支均属 60 甲子", set(r["ganzhi"] for r in gd) <= set(JIAZI))
check("ganzhi_days 首尾日期", dates[0] == "1900-01-01" and dates[-1] == "2100-12-31")
# 锚点抽查（值经 lunar-python 实测确认）
for d, want in {"2000-01-01": "戊午", "2024-02-10": "甲辰", "1900-01-01": "甲戌"}.items():
    r = find(gd, date=d)
    check(f"锚点 {d}={want}", r is not None and r["ganzhi"] == want, (r or {}).get("ganzhi", "缺失"))
# ---- 模板 ----
check("solar_terms_template 空模板", read("solar_terms_template.csv") == [])
check("shuowang_template 空模板", read("shuowang_template.csv") == [])
# ---- solar_terms ----
st = read("solar_terms.csv")
TERMS24 = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
           "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
ys = sorted(set(r["year"] for r in st))
check("solar_terms 行数=3696", len(st) == 3696, str(len(st)))
check("solar_terms 年份范围 1948-2101 连续", ys == [str(y) for y in range(1948, 2102)], f"{ys[0]}~{ys[-1]} {len(ys)} 年")
check("solar_terms 每年恰 24 行", all(sum(1 for r in st if r["year"] == y) == 24 for y in ys))
check("solar_terms term 属 24 节气全集", all(r["term"] in TERMS24 for r in st) and set(r["term"] for r in st) == set(TERMS24))
check("solar_terms jie_zhong 值域合法", all(r["jie_zhong"] in ("节", "中气") for r in st))
check("solar_terms 每年节 12/中气 12",
      all((sum(1 for r in st if r["year"] == y and r["jie_zhong"] == "节"),
           sum(1 for r in st if r["year"] == y and r["jie_zhong"] == "中气")) == (12, 12) for y in ys))
dts = [r["datetime"] for r in st]
check("solar_terms datetime 严格递增", all(a < b for a, b in zip(dts, dts[1:])))
check("solar_terms datetime 无重复", len(set(dts)) == len(dts))
check("solar_terms 2015-2028 source_ref 含 hko", all("hko" in r["source_ref"] for r in st if 2015 <= int(r["year"]) <= 2028))
check("solar_terms 其余年份 source_ref=lunar", all(r["source_ref"] == "lunar" for r in st if not 2015 <= int(r["year"]) <= 2028))
r = find(st, year="2026", term="立春")
check("solar_terms 锚点 2026 立春=02-04 04:02", r is not None and r["datetime"] == "2026-02-04 04:02",
      (r or {}).get("datetime", "缺失"))
check("solar_terms 2101 全年 notes 算法值标注",
      all(r["notes"] == "算法值（lunar-python，无官方锚点）" for r in st if r["year"] == "2101"))
check("solar_terms 非 2101 notes 为空", all(r["notes"] == "" for r in st if r["year"] != "2101"))
# ---- M1b 年柱/月柱锚点（r3 立春换年 / r4 节换月，手算+五虎遁；经度 120 北京时，值经 lunar-python 互核） ----
from datetime import datetime
import m1

def ym_case(y, mo, d, h, mi):
    r = m1.compute(datetime(y, mo, d, h, mi), 120.0)
    if "error" in r:
        return ("ERR", "ERR")
    return r["pillars"]["year"]["ganzhi"], r["pillars"]["month"]["ganzhi"]

for (y, mo, d, h, mi), ey, em in [
        ((2024, 2, 10, 8, 0), "甲辰", "丙寅"),   # 立春 02-04 16:27 后、惊蛰 03-05 前 → 甲年寅月
        ((2024, 2, 3, 8, 0), "癸卯", "乙丑"),    # 立春前 → 上年癸卯，小寒后丑月
        ((2000, 2, 4, 12, 0), "己卯", "丁丑"),   # 立春 20:40 前（真太阳时刻判界）→ 1999 己卯年丑月
        ((2000, 2, 4, 21, 0), "庚辰", "戊寅"),   # 立春 20:40 后 → 庚辰年寅月
        ((1949, 10, 1, 12, 0), "己丑", "癸酉")]:  # 寒露 10-08 23:11 前 → 白露后酉月（五虎遁己年癸酉）
    got = ym_case(y, mo, d, h, mi)
    check(f"M1b 锚点 {y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}={ey}年{em}月",
          got == (ey, em), f"得 {got[0]}{got[1]} 期望 {ey}{em}")
for (y, mo, d, h, mi), emsg in [((1948, 12, 31, 12, 0), "out_of_range"),
                                ((1900, 1, 1, 12, 0), "out_of_range")]:
    r = m1.compute(datetime(y, mo, d, h, mi), 120.0)
    check(f"M1b RANGE_LO 改后 {y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d} out_of_range",
          "error" in r and emsg in r["error"], r.get("error", "")[:60])
for y, mo, d, h, mi in [(1949, 1, 1, 3, 30), (2100, 12, 31, 20, 30)]:
    r = m1.compute(datetime(y, mo, d, h, mi), 120.0)
    check(f"M1b RANGE 边界 {y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d} 在界内", "error" not in r)
# ---- 十神（L2, r5：以日干为「我」，rel(他,我) 定动态——生=生我→印、泄=我生→食伤、克=克我→官杀、耗=我克→财；阴阳同异定偏正） ----
for dm, og, want in [("甲", "丙", "食神"), ("甲", "戊", "偏财"), ("甲", "庚", "七杀"), ("甲", "壬", "偏印"),
                     ("乙", "丁", "食神"), ("乙", "己", "偏财"), ("乙", "丙", "伤官"), ("甲", "癸", "正印")]:
    got = m1.ten_god(dm, og)
    check(f"十神锚点 {dm}见{og}={want}", got == want, got)
r = m1.compute(datetime(2024, 2, 10, 8, 0), 120.0)
tg = r["ten_gods"]
cc = [{"gan": "戊", "god": "偏财"}, {"gan": "乙", "god": "劫财"}, {"gan": "癸", "god": "正印"}]
ok = tg["day_master"] == "甲" and tg["stems"] == {"year": "比肩", "month": "食神", "hour": "偏财"} \
    and tg["branches"]["year"] == cc and tg["branches"]["day"] == cc
check("十神 2024-02-10 完整四柱锚点（甲日干 年比肩/月食神/时偏财；辰支藏干戊乙癸=偏财/劫财/正印，序与 canggan.csv 一致）",
      ok, f"stems={tg['stems']}" if not ok else "")

with open(os.path.join(BASE, "report", "assert_report.txt"), "w", encoding="utf-8") as f:
    f.write("断言报告（性质断言，不抄表内容）\n\n")
    for name, ok, det in RES:
        f.write(f"{'PASS' if ok else 'FAIL'}  {name}  {det}\n")
    f.write(f"\n合计 {len(RES)} 项，PASS {sum(1 for _, ok, _ in RES if ok)}，FAIL {sum(1 for _, ok, _ in RES if not ok)}\n")
    f.write("锚点确认来源：lunar-python（与 ganzhi_days 全区间对拍一致）\n")
print(f"合计 {len(RES)} 项 PASS {sum(1 for _, ok, _ in RES if ok)} FAIL {sum(1 for _, ok, _ in RES if not ok)}")
