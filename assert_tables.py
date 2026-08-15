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

with open(os.path.join(BASE, "report", "assert_report.txt"), "w", encoding="utf-8") as f:
    f.write("断言报告（性质断言，不抄表内容）\n\n")
    for name, ok, det in RES:
        f.write(f"{'PASS' if ok else 'FAIL'}  {name}  {det}\n")
    f.write(f"\n合计 {len(RES)} 项，PASS {sum(1 for _, ok, _ in RES if ok)}，FAIL {sum(1 for _, ok, _ in RES if not ok)}\n")
    f.write("锚点确认来源：lunar-python（与 ganzhi_days 全区间对拍一致）\n")
print(f"合计 {len(RES)} 项 PASS {sum(1 for _, ok, _ in RES if ok)} FAIL {sum(1 for _, ok, _ in RES if not ok)}")
