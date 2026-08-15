# -*- coding: utf-8 -*-
"""assert_l3_huangli.py — l3_huangli.py 独立断言（27 条）：
5 锚点建除+5 锚点值神（2026-08-12..16 手算+oracle 双查）、建除轮排连续性、黄黑道全表轮转、
黄道六黑道六、神煞 6 例手算（月德/天德/月恩/咸池/四废/归忌/天赦/驿马）、节气换月边界 2 例、
建除配黄黑道、时黄黑道（oracle 时辰表实测）。python assert_l3_huangli.py 全绿即 PASS。"""
import sys
from datetime import date, timedelta
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import l3_huangli as hl
from rules import ZHI

PASS = FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")

# —— 1-10. 五锚点（2026-08-12..16，申月：建申；值神青龙起子；oracle 双查 8-13..16 + 8-12 对拍脚本查）——
EXP_JC = {"2026-08-12": "开", "2026-08-13": "闭", "2026-08-14": "建", "2026-08-15": "除", "2026-08-16": "满"}
EXP_HH = {"2026-08-12": "白虎", "2026-08-13": "玉堂", "2026-08-14": "天牢", "2026-08-15": "玄武", "2026-08-16": "司命"}
for i, (ds, jc) in enumerate(sorted(EXP_JC.items()), 1):
    r = hl.daily(date.fromisoformat(ds))
    check(f"锚点{i} 建除 {ds}={jc}", r["jianchu"]["name"] == jc, f"got {r['jianchu']['name']}")
for i, (ds, hh) in enumerate(sorted(EXP_HH.items()), 1):
    r = hl.daily(date.fromisoformat(ds))
    check(f"锚点{i} 值神 {ds}={hh}", r["huanghei"]["name"] == hh, f"got {r['huanghei']['name']}")

# —— 11. 建除轮排连续性：同一月建区间内连续日建除序必为顺序相邻（mod 12）；
#      8-08..08-31 全在申月（8-07 立秋换月当天），首日申=建(0) ——
prev = None
ok = True
for i in range(23):
    d = date(2026, 8, 8) + timedelta(days=i)
    jc = hl.jianchu_of(d, hl.load_days()[d.isoformat()][1])
    if prev is not None and jc != (prev + 1) % 12:
        ok = False
    prev = jc
ok = ok and hl.jianchu_of(date(2026, 8, 8), "申") == 0   # 申月申日=建
check("建除轮排连续性（2026-08-08..30 申月区间相邻轮转，首日建）", ok)

# —— 12. 黄黑道 12 神全查：同一月建区间内值神按序轮转且 12 神全部出现（申月青龙起子）——
seen = []
for i in range(23):
    d = date(2026, 8, 8) + timedelta(days=i)
    seen.append(hl.huanghei_of(d, hl.load_days()[d.isoformat()][1]))
check("黄黑道全表轮转（申月连续 12 日 12 神互异且相邻轮转）",
      all(seen[i + 1] == (seen[i] + 1) % 12 for i in range(11)) and len(set(seen)) == 12)

# —— 13. 黄道六/黑道六 ——
check("黄道六（青龙明堂金匮天德玉堂司命）", hl.HUANG == {"青龙", "明堂", "金匮", "天德", "玉堂", "司命"})
check("黑道六（天刑朱雀白虎天牢玄武勾陈）", set(hl.HUANGHEI) - hl.HUANG == {"天刑", "朱雀", "白虎", "天牢", "玄武", "勾陈"})

# —— 14-19. 神煞手算（oracle 吉神/凶煞列表已核实）——
n = hl.daily(date(2026, 8, 16))["shensha"]["hits"]
check("月德 2026-08-16（申月壬，oracle 吉神命中）", "月德" in {h["name"] for h in n})
n = hl.daily(date(2026, 8, 17))["shensha"]["hits"]
check("天德 2026-08-17（申月癸，oracle 吉神命中）", "天德" in {h["name"] for h in n})
n = hl.daily(date(2026, 2, 6))["shensha"]["hits"]
check("月恩 2026-02-06（腊月辛，oracle 吉神命中）", "月恩" in {h["name"] for h in n})
check("驿马 2026-02-06（腊月丑→巳酉丑马亥，亥日命中）", "驿马" in {h["name"] for h in n})
n = hl.daily(date(2026, 8, 6))["shensha"]["hits"]
nn = {h["name"] for h in n}
check("咸池 2026-08-06（未月亥卯未见子，oracle 凶煞命中）", "咸池(桃花)" in nn)
check("四废 2026-08-06（夏壬子，oracle 凶煞命中）", "四废" in nn)
check("归忌 2026-08-06（六月子，oracle 凶煞命中）", "归忌" in nn)
n = hl.daily(date(2026, 3, 5))["shensha"]["hits"]
check("天赦 2026-03-05（春戊寅）", "天赦" in {h["name"] for h in n})

# —— 20-21. 节气换月边界：立春/立秋当天整天换月（oracle 双查）——
r = hl.daily(date(2026, 2, 4))   # 立春 04:02 当天=寅月，己酉→危；值神玄武（oracle 实测）
check("换月边界 2026-02-04 立春当天=寅月建（危）", r["jianchu"]["name"] == "危" and r["huanghei"]["name"] == "玄武")
r = hl.daily(date(2026, 8, 7))   # 立秋 19:43 当天=申月，癸丑→执；值神明堂（oracle 实测）
check("换月边界 2026-08-07 立秋当天=申月建（执）", r["jianchu"]["name"] == "执" and r["huanghei"]["name"] == "明堂")

# —— 22. 建除配黄黑道（《协纪》卷七按语：除危定执成开=黄道，建破平收满闭=黑道）——
check("建除配黄黑道 开=黄道/破=黑道", hl.JC_HH["开"] == "黄道" and hl.JC_HH["破"] == "黑道")

# —— 23. 时黄黑道 2026-08-16 壬戌日（oracle 时辰表实测：子时天牢…辰时青龙…亥时玉堂）——
hh = [hl.HUANGHEI[hl.huanghei_hour_of("戌", z)] for z in ZHI]
check("时黄黑道 2026-08-16 戌日 子时天牢/辰时青龙/亥时玉堂",
      hh[0] == "天牢" and hh[4] == "青龙" and hh[11] == "玉堂", f"got {hh}")

# —— 24. 择日接口（hl-04）：嫁娶 2026-09 月 Top3 候选结构+分值降序+依据字段 ——
pk = hl.pick_days(date(2026, 9, 1), date(2026, 9, 30), "嫁娶", 3)
ok = len(pk["candidates"]) == 3 and pk["candidates"][0]["score"] >= pk["candidates"][1]["score"] >= pk["candidates"][2]["score"]
ok = ok and all("basis" in c and "huanghei" in c["basis"] and "jianchu" in c["basis"] for c in pk["candidates"])
check("择日接口 嫁娶 2026-09 Top3 分值降序+依据字段", ok)

print(f"\n断言结果：PASS {PASS}  FAIL {FAIL}（共 {PASS + FAIL} 条）")
sys.exit(1 if FAIL else 0)
