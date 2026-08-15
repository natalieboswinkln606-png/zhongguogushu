# -*- coding: utf-8 -*-
"""assert_l3_wangshuai.py — L3-2 日主旺衰综合判定断言（三得体系 ws-01..ws-04）。
覆盖：5 手工锚点等级（五级全盖）、得令/得地/得势边界、综合公式独立复算、
changsheng 表完整性、JSON 项 rule_id/source、权重底本、申报幂等性。
运行：PYTHONIOENCODING=utf-8 python assert_l3_wangshuai.py
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import l3_wangshuai as w

BASE = os.path.dirname(os.path.abspath(__file__))
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
    r = w.compute(datetime(*t))
    assert "error" not in r, r
    return r


# --- 5 手工锚点等级（手推三得：令/地/势→加权，见 l3_wangshuai.py docstring；与易安居 oracle 对拍见 report） ---
ANCHORS = [((2024, 6, 11, 12, 0), "极旺", "甲辰庚午丙午甲午"),   # 丙午日午月：令旺100 地8/10 势8/18 → 79.1
           ((2024, 6, 28, 12, 0), "偏弱", "甲辰庚午癸亥戊午"),   # 癸亥日午月：令囚25 地5/10 势4/18 → 33.0
           ((2024, 1, 1, 8, 0), "中和", "癸卯甲子甲子戊辰"),     # 甲子日子月：令相75 地2/10 势9/18 → 49.5
           ((2024, 6, 15, 12, 0), "极弱", "甲辰庚午庚戌壬午"),   # 庚戌日午月：令死0 地0/10 势7/18 → 9.7
           ((2024, 8, 24, 12, 0), "偏旺", "甲辰壬申庚申壬午")]   # 庚申日申月：令旺100 地6/10 势6/18 → 69.3

def test_anchors():
    for t, want, gz in ANCHORS:
        r = C(t)
        got_gz = "".join(r["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "hour"))
        assert got_gz == gz, f"{t} 四柱 {got_gz} != {gz}"
        assert r["zonghe"]["level"] == want, f"{t} {gz} 等级 {r['zonghe']['level']} != {want}"

def test_levels_full_cover():
    assert {lv for _, lv, _ in ANCHORS} == {"极旺", "偏旺", "中和", "偏弱", "极弱"}, "五锚点应恰盖五级"

def test_de_ling_boundary():
    # 得令边界：甲子日子月=相（水生木=月令所生）；庚戌日午月=死（火克金=月令所克）；丙午日午月=旺（同）
    assert C((2024, 1, 1, 8, 0))["de_ling"]["status"] == "相", "子月甲日得令应=相"
    assert C((2024, 6, 15, 12, 0))["de_ling"]["status"] == "死", "午月庚日得令应=死"
    assert C((2024, 6, 11, 12, 0))["de_ling"]["status"] == "旺", "午月丙日得令应=旺"
    assert C((2024, 6, 11, 12, 0))["de_ling"]["full_table"]["金"] == "死", "午月全表金应=死（oracle 句同）"
    assert C((2024, 6, 11, 12, 0))["de_ling"]["full_table"]["木"] == "休", "午月全表木应=休"

def test_de_di_boundary():
    # 得地边界：丙午日坐午=帝旺有根 4 分（旺地×日支权2）；甲子日坐子=沐浴无根 0 分；庚戌坐戌=衰有根 0 分（弱地留根）
    items = {x["pillar"]: x for x in C((2024, 6, 11, 12, 0))["de_di"]["items"]}
    d = items["day支"]
    assert d["zhi"] == "午" and d["stage"] == "帝旺" and d["root"] and d["points"] == 4, d
    items = {x["pillar"]: x for x in C((2024, 1, 1, 8, 0))["de_di"]["items"]}
    d = items["day支"]
    assert d["zhi"] == "子" and d["stage"] == "沐浴" and not d["root"] and d["points"] == 0, d
    items = {x["pillar"]: x for x in C((2024, 6, 15, 12, 0))["de_di"]["items"]}
    d = items["day支"]
    assert d["zhi"] == "戌" and d["stage"] == "衰" and d["root"] and d["points"] == 0, d
    assert C((2024, 6, 11, 12, 0))["de_di"]["score"] == 8 and C((2024, 6, 11, 12, 0))["de_di"]["max_score"] == 10

def test_de_shi_boundary():
    # 得势边界：丙午日午月——天干甲=生我2/丙=同2（日干丙本身不计党）；藏干午丁=同1；午支己对丙=泄 0
    r = C((2024, 6, 11, 12, 0))
    stems = {x["pillar"]: x for x in r["de_shi"]["stems"]}
    assert stems["year干"] == {"pillar": "year干", "gan": "甲", "relation": "生我", "points": 2}, stems["year干"]
    assert stems["month干"]["relation"] == "" and stems["hour干"]["points"] == 2, stems
    assert r["de_shi"]["branches"]["month支"][0] == {"gan": "丁", "relation": "同", "points": 1}
    assert r["de_shi"]["branches"]["hour支"][1] == {"gan": "己", "relation": "", "points": 0}, "己=泄 0 分"
    assert sum(x["points"] for x in r["de_shi"]["branches"]["hour支"]) == 1, "午支丁己对丙：丁=同 1、己=泄 0"

def test_zonghe_formula():
    # 综合分独立复算（与模块同口径：用 ws-02/03 输出的 score_pct，不重算原始分）
    WSR = {"旺": 100, "相": 75, "休": 50, "囚": 25, "死": 0}
    for t, want, gz in ANCHORS:
        r = C(t)
        s = round(0.40 * WSR[r["de_ling"]["status"]] + 0.35 * r["de_di"]["score_pct"]
                  + 0.25 * r["de_shi"]["score_pct"], 1)
        assert s == r["zonghe"]["score"], f"{t} 综合分 {r['zonghe']['score']} != 复算 {s}"
        assert r["zonghe"]["weights"] == {"de_ling": 0.4, "de_di": 0.35, "de_shi": 0.25}, "ws-04 权重 40/35/25"

def test_json_rule_id_source():
    r = C((2024, 6, 11, 12, 0))
    for key in ("de_ling", "de_di", "de_shi", "zonghe"):
        item = r[key]
        assert item["rule_id"].startswith("ws-"), key
        assert item.get("source"), f"{key} 缺 source"
    assert r["zonghe"]["rule_id"] == "ws-04" and r["zonghe"]["advice"], "ws-04 需结论说明"

def test_changsheng_table():
    cs = w.load_changsheng()
    assert len(cs) == 120, f"十二长生表应 10 干×12 支=120 行，实 {len(cs)}"
    assert cs[("甲", "亥")] == "长生" and cs[("庚", "申")] == "临官" and cs[("丙", "午")] == "帝旺"
    assert cs[("癸", "子")] == "临官" and cs[("辛", "酉")] == "临官"
    for g in "甲乙丙丁戊己庚辛壬癸":
        assert sum(1 for (g0, _), _ in cs.items() if g0 == g) == 12, f"{g} 应 12 位"

def test_idempotent_rows():
    # 申报幂等：data/arbitration_log.csv 与 report/boundary_cases.csv 中 ws- 行 case_id 唯一（重跑 compare 不重复写）
    for fn in ("data/arbitration_log.csv", "report/boundary_cases.csv"):
        try:
            rows = [r["case_id"] for r in csv.DictReader(open(os.path.join(BASE, fn), encoding="utf-8"))
                    if r.get("case_id") and r["case_id"].startswith("ws-")]
        except FileNotFoundError:
            continue
        assert len(rows) == len(set(rows)), f"{fn} ws- 行 case_id 重复"

def test_unknown_month_zhi():
    # 抽测戌月（四季土）与亥月：庚日戌月=相（土生金=月令所生）、亥月火=死（月令所克）
    r = C((2024, 10, 23, 12, 0))  # 甲辰甲戌庚申壬午：庚戌月
    assert r["de_ling"]["month_zhi"] == "戌" and r["de_ling"]["status"] == "相", r["de_ling"]
    assert r["de_ling"]["full_table"]["土"] == "旺", "戌月全表土应=旺（当令）"
    r = C((2024, 11, 20, 12, 0))
    if r["de_ling"]["month_zhi"] == "亥":
        assert r["de_ling"]["full_table"]["火"] == "死", "亥月全表火应=死（月令所克）"


for name, fn in [("5 锚点等级+四柱", test_anchors), ("五级全覆盖", test_levels_full_cover),
                 ("得令边界（子月甲=相/午月庚=死/午月丙=旺）", test_de_ling_boundary),
                 ("得地边界（午=帝旺4分/子=沐浴无根0/戌=衰有根0）", test_de_di_boundary),
                 ("得势边界（生我/同/泄逐项计分）", test_de_shi_boundary),
                 ("综合公式复算+权重 40/35/25", test_zonghe_formula),
                 ("JSON 每项 rule_id/source", test_json_rule_id_source),
                 ("changsheng 表 120 行完整性+抽点", test_changsheng_table),
                 ("申报幂等（ws- 行唯一）", test_idempotent_rows),
                 ("戌月/亥月当令", test_unknown_month_zhi)]:
    check(name, fn)
print(f"\nassert_l3_wangshuai: {sum(CHECKS)}/{len(CHECKS)} PASS")
sys.exit(0 if all(CHECKS) else 1)
