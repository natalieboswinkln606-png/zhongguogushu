# -*- coding: utf-8 -*-
"""assert_l3_ziwei.py — L3-1 紫微斗数排盘断言（锚点全字段/闰月/子正换日/五行局五类/民俗年/庚年四化异文口径/对拍幂等）。
锚点期望值 = 易安居 oracle 全字段对拍一致（2026-08-16，127 例；仅 2024-06-15 23:30 为换日界口径分歧，已申报 zw-a01/b01）。
运行：PYTHONIOENCODING=utf-8 python assert_l3_ziwei.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import l3_ziwei

CHECKS = []


def check(name, fn):
    try:
        fn()
        print(f"  PASS {name}")
        CHECKS.append(True)
    except AssertionError as e:
        print(f"  FAIL {name}: {e}")
        CHECKS.append(False)


def C(t):
    r = l3_ziwei.compute(datetime(*t))
    assert "error" not in r, r
    return r


def stars_in(r, star):
    return next(p["zhi"] for p in r["palaces"] if star in p["stars"])


def aux_in(r, aux):
    return next(p["zhi"] for p in r["palaces"] if aux in p["aux"])


def hua(r, star):
    return next((it["hua"] for it in r["sihua"]["items"] if it["star"] == star), None)


def palace(r, name):
    return next(p for p in r["palaces"] if p["name"] == name)


# ---------- 锚点 1：2024-02-10 甲辰正月初一（火六局，oracle 全字段一致） ----------
def a1():
    r = C((2024, 2, 10, 8, 0))
    assert r["lunar"]["year"] == "甲辰" and r["lunar"]["month_name"] == "正月" and r["lunar"]["day"] == 1
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "甲戌", "命宫=甲戌（oracle 实测）"
    assert r["shengong"]["zhi"] == "午"
    assert r["wuxing_ju"]["name"] == "火六局", "甲戌纳音山头火→火六局（oracle 实测）"
    assert r["ziwei"]["zhi"] == "酉"
    assert stars_in(r, "紫微") == "酉" and stars_in(r, "天机") == "申"
    assert stars_in(r, "太阳") == "午" and stars_in(r, "武曲") == "巳" and stars_in(r, "天同") == "辰"
    assert stars_in(r, "廉贞") == "丑" and stars_in(r, "天府") == "未"  # 天府=(4-紫微)mod12，紫微酉(9)→未
    assert hua(r, "廉贞") == "禄" and hua(r, "破军") == "权" and hua(r, "武曲") == "科" and hua(r, "太阳") == "忌"
    assert aux_in(r, "左辅") == "辰" and aux_in(r, "右弼") == "戌"   # 辰/戌起正月顺/逆数（辰时同宫）
    assert aux_in(r, "文昌") == "午" and aux_in(r, "文曲") == "申"   # 戌/辰起逆/顺数生时
    assert aux_in(r, "天魁") == "丑" and aux_in(r, "天钺") == "未"   # 甲年魁钺丑未
    assert aux_in(r, "禄存") == "寅" and aux_in(r, "擎羊") == "卯" and aux_in(r, "陀罗") == "丑"
    assert aux_in(r, "火星") == "午" and aux_in(r, "铃星") == "寅"   # 申子辰火寅/铃戌起（2026-08-16 修正铃星起宫）
    assert aux_in(r, "天马") == "寅"                                   # 申子辰天马寅
    # 十二宫逆排（命戌→兄弟酉→夫妻申→…→父母亥）+ 宫干五虎遁（甲年：戌=甲、亥=乙…子宫=甲子）
    names = [p["name"] for p in r["palaces"]]
    assert names == ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]
    assert [p["zhi"] for p in r["palaces"]] == ["戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥"]
    assert palace(r, "兄弟")["gan"] == "癸" and palace(r, "父母")["gan"] == "乙"
    assert palace(r, "福德")["gan"] == "丙" and palace(r, "福德")["zhi"] == "子"  # 五虎遁：甲年子宫=丙子（与 m1 月柱同式）


check("锚点1 2024-02-10 甲辰正月初一 全字段（命甲戌/身午/火六局/紫微酉/四化廉破武阳/辅星/逆排/宫干）", a1)


# ---------- 锚点 2：2000-02-05 庚辰正月初一（水二局；庚年四化 oracle 口径=阳武同阴） ----------
def a2():
    r = C((2000, 2, 5, 12, 0))
    assert r["lunar"]["year"] == "庚辰" and r["lunar"]["day"] == 1
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "甲申" and r["shengong"]["zhi"] == "申"
    assert r["wuxing_ju"]["name"] == "水二局"
    assert r["ziwei"]["zhi"] == "丑"
    assert hua(r, "太阳") == "禄" and hua(r, "武曲") == "权"
    assert hua(r, "天同") == "科" and hua(r, "太阴") == "忌", "庚年四化=阳武同阴（天同科/太阴忌，易安居 oracle/中州派口径；异文=通行《全书》派阳武阴同）"
    assert stars_in(r, "天同") == "申" and stars_in(r, "太阴") == "辰"  # 天同科在命宫、太阴忌在财帛（oracle 实测）


check("锚点2 2000-02-05 庚辰正月初一（水二局/命甲申/紫微丑/庚年四化异文口径）", a2)


# ---------- 锚点 3：1990-01-01 己巳年腊月初五（金四局） ----------
def a3():
    r = C((1990, 1, 1, 10, 0))
    assert r["lunar"]["year"] == "己巳" and r["lunar"]["month_name"] == "十二月" and r["lunar"]["day"] == 5
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "壬申" and r["shengong"]["zhi"] == "午"
    assert r["wuxing_ju"]["name"] == "金四局"
    assert r["ziwei"]["zhi"] == "子"
    assert hua(r, "武曲") == "禄" and hua(r, "贪狼") == "权" and hua(r, "天梁") == "科" and hua(r, "文曲") == "忌"


check("锚点3 1990-01-01 己巳年腊月初五（金四局/命壬申/紫微子/己年四化）", a3)


# ---------- 锚点 4：2024-06-15 甲辰五月初十（水二局） ----------
def a4():
    r = C((2024, 6, 15, 12, 0))
    assert r["lunar"]["month_name"] == "五月" and r["lunar"]["day"] == 10
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "丙子" and r["shengong"]["zhi"] == "子"
    assert r["wuxing_ju"]["name"] == "水二局"
    assert r["ziwei"]["zhi"] == "午" and stars_in(r, "紫微") == "午"  # 水二局 10 日：表[1]+4=寅+4=午


check("锚点4 2024-06-15 甲辰五月初十（水二局/命丙子/紫微午）", a4)


# ---------- 锚点 5：2025-01-15 甲辰年腊月十六（土五局） ----------
def a5():
    r = C((2025, 1, 15, 12, 0))
    assert r["lunar"]["year"] == "甲辰" and r["lunar"]["month_name"] == "十二月" and r["lunar"]["day"] == 16
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "辛未" and r["shengong"]["zhi"] == "未"
    assert r["wuxing_ju"]["name"] == "土五局"
    assert r["ziwei"]["zhi"] == "酉" and stars_in(r, "紫微") == "酉"  # 土五局 16 日：表[0]+3=午+3=酉


check("锚点5 2025-01-15 甲辰年腊月十六（土五局/命辛未/紫微酉）", a5)


# ---------- 边界 1：民俗年换年（2025-01-29 正月初一，立春前，判定层=乙巳） ----------
def b1():
    r = C((2025, 1, 29, 8, 0))
    assert r["lunar"]["year"] == "乙巳", "判定层按民俗农历年（正月初一换年），oracle 实测：盘面四化=乙年"
    assert r["lunar"]["day"] == 1 and r["lunar"]["month_name"] == "正月"
    assert hua(r, "天机") == "禄" and hua(r, "天梁") == "权" and hua(r, "紫微") == "科" and hua(r, "太阴") == "忌", "四化按乙年（oracle 盘面实测，非立春年甲辰）"
    assert aux_in(r, "天魁") == "子" and aux_in(r, "天钺") == "申" and aux_in(r, "禄存") == "卯", "魁钺禄存按乙年"
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "丙戌" and r["wuxing_ju"]["name"] == "土五局"
    assert r["ziwei"]["zhi"] == "午"
    assert "民俗农历年" in r["notes"][1] and "乙巳" in r["notes"][1]


check("边界1 2025-01-29 民俗年换年（判定层乙巳/四化乙年/魁钺禄存乙/土五局）", b1)


# ---------- 边界 2：闰月顺延起宫（2023-04-04 闰二月十四） ----------
def b2():
    r = C((2023, 4, 4, 8, 0))
    assert r["lunar"]["is_ruen"] is True and r["lunar"]["month_name"] == "闰二月" and r["lunar"]["day"] == 14
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "甲子" and r["shengong"]["zhi"] == "申", "闰月按次月（三月）起宫，oracle 实测：命子/身申"
    assert r["wuxing_ju"]["name"] == "金四局"
    assert r["ziwei"]["zhi"] == "未"
    assert aux_in(r, "左辅") == "午" and aux_in(r, "右弼") == "申", "闰月左辅右弼随顺延（三月起算），oracle 实测"


check("边界2 2023-04-04 闰二月十四（闰月顺延起宫/金四局/左辅午右弼申）", b2)


# ---------- 边界 3：闰月顺延（2025-07-25 闰六月初一） ----------
def b3():
    r = C((2025, 7, 25, 8, 0))
    assert r["lunar"]["is_ruen"] is True and r["lunar"]["month_name"] == "闰六月" and r["lunar"]["day"] == 1
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "庚辰" and r["shengong"]["zhi"] == "子", "闰六月按七月起宫（oracle 实测）"
    assert r["wuxing_ju"]["name"] == "金四局"
    assert aux_in(r, "左辅") == "戌" and aux_in(r, "右弼") == "辰"


check("边界3 2025-07-25 闰六月初一（闰月顺延/命庚辰/金四局）", b3)


# ---------- 边界 4：子正换日（23:30 归当日；oracle 子初口径归次日=已申报异文 zw-a01） ----------
def b4():
    r = C((2024, 6, 15, 23, 30))
    assert r["lunar"]["month_name"] == "五月" and r["lunar"]["day"] == 10, "真太阳时子正换日：23-24 点子时归当日（preregister 已裁决；oracle 子初归次日=异文）"
    assert r["shichen"]["zhi"] == "子" and r["minggong"]["gan"] + r["minggong"]["zhi"] == "庚午"
    assert r["wuxing_ju"]["name"] == "土五局"


check("边界4 2024-06-15 23:30 子正换日（23 点子时归当日）", b4)


# ---------- 边界 5：子正换日（0:15 真太阳时落次日） ----------
def b5():
    r = C((2024, 2, 11, 0, 15))
    assert r["lunar"]["day"] == 2, "北京时 0:15 → 真太阳时 ≥0:00 属次日 → 正月初二（oracle 实测一致）"
    assert r["minggong"]["gan"] + r["minggong"]["zhi"] == "丙寅" and r["wuxing_ju"]["name"] == "火六局"
    assert r["ziwei"]["zhi"] == "午"


check("边界5 2024-02-11 00:15 子正换日（真太阳时次日/正月初二）", b5)


# ---------- 规则 1：五行局五类各至少 1 例 ----------
def r1():
    for t, ju in [((2024, 2, 10, 8, 0), "火六局"), ((2000, 2, 5, 12, 0), "水二局"),
                  ((1990, 1, 1, 10, 0), "金四局"), ((2025, 1, 15, 12, 0), "土五局"),
                  ((1971, 10, 30, 14, 0), "木三局")]:
        assert C(t)["wuxing_ju"]["name"] == ju, f"{t} 应为 {ju}"


check("规则1 五行局五类各至少 1 例（火六/水二/金四/土五/木三）", r1)


# ---------- 规则 2：庚年四化 oracle 口径（阳武同阴）+ 异文标注存在 ----------
def r2():
    r = C((2000, 2, 5, 12, 0))
    assert hua(r, "天同") == "科" and hua(r, "太阴") == "忌"
    # 异文=通行《紫微斗数全书》派（太阴科/天同忌），须在模块 docstring 或注释成文
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "l3_ziwei.py"), encoding="utf-8").read()
    assert "阳武同阴" in src and "阳武阴同" in src


check("规则2 庚年四化 oracle/中州派口径（天同科/太阴忌）+ 通行异文成文标注", r2)


# ---------- 规则 3：四化星可为辅星（辛年文曲科/文昌忌） ----------
def r3():
    r = C((1971, 10, 30, 14, 0))
    assert hua(r, "文曲") == "科" and hua(r, "文昌") == "忌"
    assert hua(r, "巨门") == "禄" and hua(r, "太阳") == "权"


check("规则3 四化星可为辅星（1971-10-30 辛年 巨阳曲昌）", r3)


# ---------- 规则 4：输出结构带 Rule-ID/底本出处 ----------
def r4():
    r = C((2024, 2, 10, 8, 0))
    assert r["lunar"]["rule_id"] == "zw-01" and r["minggong"]["rule_id"] == "zw-02"
    assert r["wuxing_ju"]["rule_id"] == "zw-03" and r["ziwei"]["rule_id"] == "zw-04"
    assert r["sihua"]["rule_id"] == "zw-07"
    assert all(p["rule_id"] == "zw-05" for p in r["palaces"])
    assert r["lunar"]["source"] and r["wuxing_ju"]["source"] and r["ziwei"]["source"]
    assert r["ziwei"]["alt"]  # 安紫微异文（一日一宫派）成文


check("规则4 输出 JSON 每项带 rule_id/source/alt", r4)


# ---------- 规则 5：安紫微异文 alt 内容正确 ----------
def r5():
    r = C((2024, 2, 10, 8, 0))
    assert "一日一宫" in r["ziwei"]["alt"]
    r2 = C((2024, 6, 15, 12, 0))
    assert "一日一宫" in r2["ziwei"]["alt"]


check("规则5 安紫微异文（一日一宫派）标注", r5)


# ---------- 规则 6：与 oracle 缓存全字段对拍（5 锚点 + 20 随机，除已申报换日界例） ----------
def r6():
    from _zw_oracle_probe import cmp_self
    anchors = [(2024, 2, 10, 8, 0), (2000, 2, 5, 12, 0), (1990, 1, 1, 10, 0), (2024, 6, 15, 12, 0), (2025, 1, 15, 12, 0)]
    import re
    picks = []
    for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "l3_ziwei_random_picks.txt"), encoding="utf-8"):
        m = re.match(r"(\d+)-(\d+)-(\d+) (\d+):(\d+)", line)
        picks.append((int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5])))
    diffs = cmp_self(anchors + picks)
    assert not diffs, f"对拍差异 {len(diffs)} 例: {diffs[:2]}"


check("规则6 与易安居 oracle 缓存全字段对拍（25 例零差异）", r6)


def main():
    print(f"assert_l3_ziwei: {len(CHECKS)} 项断言")
    n_pass, n_fail = sum(CHECKS), len(CHECKS) - sum(CHECKS)
    print(f"PASS {n_pass} / FAIL {n_fail}")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
