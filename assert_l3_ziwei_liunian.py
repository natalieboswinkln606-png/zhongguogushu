# -*- coding: utf-8 -*-
"""assert_l3_ziwei_liunian.py — L3-1b 紫微斗数大限/小限/流年/斗君 独立断言（16 条）。
锚点值均先手算/先对拍易安居紫微盘（oracle）再固化：2024-02-10 男命全限与 oracle 缓存逐宫一致；
1955-10-15/2000-02-05/1991-06-21/2023-04-04(闰月) 大限起岁/方向/斗君与 oracle 对拍一致（25/25）。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import l3_ziwei_liunian as zl

PASS, FAIL = 0, []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL.append((name, detail))
        print(f"FAIL  {name}  {detail}")


def C(t, sex, ty=None):
    return zl.compute(datetime(*t), 120.0, sex, ty)


print("L3-1b 断言：大限/小限/流年/斗君（16 条）")
d = C((2024, 2, 10, 8, 0), "男")  # 甲辰阳男 火六局：起 6 顺行

# --- zl-01 大限 ---
check("zl-01 起岁=五行局数（火六局→6）", d["daxian"]["start_age"] == 6 and d["wuxing_ju"]["name"] == "火六局",
      f"start={d['daxian']['start_age']} ju={d['wuxing_ju']['name']}")
check("zl-01 阳男顺行（甲辰男）", d["daxian"]["direction"] == "顺行")
it = d["daxian"]["items"]
check("zl-01 12 限、首限命宫 甲戌 6-15、末限 116-125",
      len(it) == 12 and it[0]["palace"] == "命宫" and it[0]["ganzhi"] == "甲戌"
      and it[0]["ages"] == "6-15" and it[-1]["ages"] == "116-125",
      f"n={len(it)} first={it[0]['palace']}{it[0]['ganzhi']}{it[0]['ages']} last={it[-1]['ages']}")
check("zl-01 顺行次限=亥(16-25) 序对（戌亥子丑…逆行 申酉）",
      it[1]["zhi"] == "亥" and it[1]["ages"] == "16-25" and it[11]["zhi"] == "酉",
      f"i1={it[1]['zhi']} i11={it[11]['zhi']}")
check("zl-01 大限干四化=中州派（甲戌首限甲→廉贞禄；癸酉末限癸→贪狼忌）",
      any(s["star"] == "廉贞" and s["hua"] == "禄" for s in it[0]["sihua"])
      and any(s["star"] == "贪狼" and s["hua"] == "忌" for s in it[-1]["sihua"]),
      f"first_hua={it[0]['sihua']} last_hua={it[-1]['sihua']}")
check("zl-01 阴男逆行（1955-10-15 乙未男：起 4、首限庚辰）",
      C((1955, 10, 15, 10, 0), "男")["daxian"]["direction"] == "逆行"
      and C((1955, 10, 15, 10, 0), "男")["daxian"]["start_age"] == 4
      and C((1955, 10, 15, 10, 0), "男")["daxian"]["items"][0]["ganzhi"] == "庚辰")
check("zl-01 阳女逆行/阴女顺行（庚辰女起 2 逆、辛未女起 3 顺）",
      C((2000, 2, 5, 12, 0), "女")["daxian"]["direction"] == "逆行"
      and C((2000, 2, 5, 12, 0), "女")["daxian"]["start_age"] == 2
      and C((1991, 6, 21, 14, 0), "女")["daxian"]["direction"] == "顺行"
      and C((1991, 6, 21, 14, 0), "女")["daxian"]["start_age"] == 3)

# --- zl-02 小限 ---
check("zl-02 申子辰→戌起（辰年男 1 岁戌顺、2 岁亥；女逆 2 岁酉）",
      d["xiaoxian"]["start_palace"] == "戌" and d["xiaoxian"]["table"]["2"] == "亥"
      and C((2000, 2, 5, 12, 0), "女")["xiaoxian"]["table"]["2"] == "酉",
      f"男表2={d['xiaoxian']['table']['2']} 女表2={C((2000,2,5,12,0),'女')['xiaoxian']['table']['2']}")
check("zl-02 亥卯未→丑起（未年男 1 岁丑顺）、男顺女逆不论阴阳",
      C((1955, 10, 15, 10, 0), "男")["xiaoxian"]["start_palace"] == "丑"
      and C((1955, 10, 15, 10, 0), "男")["xiaoxian"]["direction"] == "顺行"
      and C((1991, 6, 21, 14, 0), "女")["xiaoxian"]["direction"] == "逆行")

# --- zl-04 斗君 ---
check("zl-04 子年斗君例 1（甲辰年正月辰时→辰，oracle 同）",
      d["doujun"]["zi_year_zhi"] == "辰" and d["doujun"]["birth_year_zhi"] == "申",
      f"子年={d['doujun']['zi_year_zhi']} 本命={d['doujun']['birth_year_zhi']}")
check("zl-04 子年斗君例 2 闰月（2023-04-04 闰二月十四辰时→寅，oracle 同）",
      C((2023, 4, 4, 8, 0), "男")["doujun"]["zi_year_zhi"] == "寅",
      f"={C((2023,4,4,8,0),'男')['doujun']['zi_year_zhi']}")
check("zl-04 子年斗君例 3（2000-02-05 庚辰年正月午时→午）",
      C((2000, 2, 5, 12, 0), "女")["doujun"]["zi_year_zhi"] == "午")

# --- zl-03 流年 ---
l23 = C((2023, 4, 4, 8, 0), "男", 2023)["liunian"]
check("zl-03 流年 2023（癸卯）：支卯落卯宫、流年斗君巳、癸干四化含贪狼忌",
      l23["ganzhi"] == "癸卯" and l23["zhi"] == "卯" and l23["doujun_zhi"] == "巳"
      and any(s["star"] == "贪狼" and s["hua"] == "忌" for s in l23["sihua"]),
      f"gz={l23['ganzhi']} zhi={l23['zhi']} dj={l23['doujun_zhi']} hua={l23['sihua']}")
l26 = C((2024, 2, 10, 8, 0), "男", 2026)["liunian"]
check("zl-03 流年 2026（丙午）：支午落财帛宫、丙干四化含天同禄",
      l26["ganzhi"] == "丙午" and l26["zhi"] == "午" and l26["palace"] == "财帛"
      and any(s["star"] == "天同" and s["hua"] == "禄" for s in l26["sihua"]),
      f"gz={l26['ganzhi']} zhi={l26['zhi']} 宫={l26['palace']} hua={l26['sihua']}")
check("zl-03 流年表外返回 error（1900 年）",
      "error" in C((2024, 2, 10, 8, 0), "男", 1900)["liunian"])

# --- 口径元数据 ---
check("口径：每输出项带 rule_id/source/alt（大限/小限/流年/斗君）",
      all(k in d["daxian"] and k in d["xiaoxian"] and k in d["doujun"]
          and all(k in x for x in (l23, l26)) for k in ("rule_id", "source", "alt")))

print(f"\n结果: {PASS} 通过 / {len(FAIL)} 失败")
if FAIL:
    for name, detail in FAIL:
        print(f"  FAIL {name}: {detail}")
    sys.exit(1)
