# -*- coding: utf-8 -*-
"""assert_l3_bazi_liuri.py — L3 流日断言（lr-01..lr-03）。
覆盖：日柱序列=ganzhi_days 表（引擎源）、原局四柱锁定（1990-05-01 10:00）、立春换年跳变与节交接日正午口径、
节换月跳变、十神 10 干抽查、合冲刑害全表抽查（六合/六冲/六害/半合/自刑/三刑三字俱全门限/子卯两字）、
三刑池口径（原局四支∪流日支）、大运年份区间定位（含 8 步外）、jie_note、黄历层引用一致性（双源）、
极端经度正午反解（±180°）、输出 rule_id/source/alt/notes 声明、days 上界守卫、日期序列连续性。
运行：PYTHONIOENCODING=utf-8 python assert_l3_bazi_liuri.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import date, datetime
import m1
import l3_bazi_liuri as L

CHECKS = []
BIRTH = datetime(1990, 5, 1, 10, 0)
CHART = L.load_chart(BIRTH, 120.0, "男")


def check(name, fn):
    try:
        fn()
        print(f"  PASS {name}")
        CHECKS.append(True)
    except AssertionError as e:
        print(f"  FAIL {name}: {e}")
        CHECKS.append(False)


def D(s, wl=False, lon=120.0, chart=None):
    return L.day_entry(date.fromisoformat(s), lon, chart or CHART, wl)


def test_chart_lock():
    # 原局锁定（引擎实证 1990-05-01 10:00 @120：庚午/庚辰/丙寅/癸巳，日主丙）
    assert CHART["pillars"] == {"year": "庚午", "month": "庚辰", "day": "丙寅", "hour": "癸巳"}, CHART["pillars"]
    assert CHART["day_master"] == "丙", CHART["day_master"]


def test_day_pillar_table():
    # 流日日柱=ganzhi_days 表（r1 源）；含闰日/月末/次日连续
    dgz = m1.load_days()
    for s in ("2024-02-28", "2024-02-29", "2024-03-01", "2026-09-15", "2000-01-01", "2099-12-31"):
        assert D(s)["shape"]["day"] == dgz[s], f"{s} 日柱 {D(s)['shape']['day']} != 表 {dgz[s]}"


def test_lichun_switch():
    # 2024 立春=02-04 16:27：02-03/02-04 正午在立春前→癸卯；02-05→甲辰；02-04 带 jie_note
    assert D("2024-02-03")["shape"]["year"] == "癸卯"
    assert D("2024-02-04")["shape"]["year"] == "癸卯", "立春当日正午取样应落交接前一侧（alt 已注明）"
    assert D("2024-02-05")["shape"]["year"] == "甲辰"
    jn = D("2024-02-04")["jie_note"]
    assert any(x["term"] == "立春" for x in jn), jn
    assert D("2024-02-06")["jie_note"] == [], "非节日 jie_note 应为空"


def test_jie_month_switch():
    # 2024 惊蛰=03-05 10:23：03-04 丙寅月、03-05 正午(已过惊蛰)丁卯月（甲辰年五虎遁）
    assert D("2024-03-04")["shape"]["month"] == "丙寅"
    assert D("2024-03-05")["shape"]["month"] == "丁卯"
    r = m1.compute(L.bj_at_true_solar(datetime(2024, 3, 5, 12, 0), 120.0), 120.0)
    assert D("2024-03-05")["shape"]["month"] == r["pillars"]["month"]["ganzhi"], "应与 m1 直出同源"


def test_ten_gods():
    want = {"甲": "比肩", "乙": "劫财", "丙": "食神", "丁": "伤官", "戊": "偏财",
            "己": "正财", "庚": "七杀", "辛": "正官", "壬": "偏印", "癸": "正印"}
    for g, v in want.items():
        assert m1.ten_god("甲", g) == v, f"甲见{g} 应 {v}，实 {m1.ten_god('甲', g)}"
    e = D("2026-09-15")
    assert e["day_master_god"]["god"] == m1.ten_god("丙", e["shape"]["day"][0]), "日主十神应与 m1 同源"


def test_relations_tables():
    P = {"子", "午"}
    r = L.pair_relations("甲子", "己丑", P)
    assert "五合（甲己合土）" in r["gan"] and "六合（子丑）" in r["zhi"], r
    r = L.pair_relations("甲子", "甲午", P)
    assert "六冲（子午）" in r["zhi"] and r["gan"] == [], r
    r = L.pair_relations("丙寅", "丁巳", {"寅", "巳"})
    assert "六害（寅巳）" in r["zhi"] and not any("三刑" in x for x in r["zhi"]), "寅巳两字不判刑（池无申）"
    r = L.pair_relations("丙寅", "丁巳", {"寅", "巳", "申"})
    assert "三刑（寅巳·无恩之刑）" in r["zhi"], r
    r = L.pair_relations("壬申", "甲子", {"申", "子"})
    assert "半合（申子半合水局）" in r["zhi"], r
    r = L.pair_relations("甲午", "甲午", {"午"})
    assert "自刑（午午）" in r["zhi"], r
    r = L.pair_relations("甲子", "乙卯", {"子", "卯"})
    assert "三刑（子卯·无礼之刑）" in r["zhi"], "子卯无礼之刑两字即判"
    r = L.pair_relations("甲寅", "戊辰", {"寅", "辰"})
    assert "相克（甲克戊）" in r["gan"], r
    r = L.pair_relations("戊寅", "甲辰", {"寅", "辰"})
    assert "受克（甲克戊）" in r["gan"], r
    r = L.pair_relations("丁卯", "壬戌", {"卯", "戌"})
    assert "五合（丁壬合木）" in r["gan"] and "六合（卯戌）" in r["zhi"], r


def test_relations_pool_scope():
    # 实盘：原局 庚午/庚辰/丙寅/癸巳 + 流日辰 → 辰辰自刑（月柱辰）应出现；三刑寅巳申池依赖原局
    e = D("2026-09-15")  # 流日壬辰
    assert "自刑（辰辰）" in e["relations"]["月柱"]["zhi"], e["relations"]["月柱"]


def test_same_zhi_relations():
    # 同支口径与 hp-01 一致：自刑支只报自刑（不报半合）；非自刑同支报半合归局（hp-x02 已仲裁口径）
    r = L.pair_relations("甲辰", "甲辰", {"辰"})
    assert "自刑（辰辰）" in r["zhi"] and not any("半合" in x for x in r["zhi"]), r
    r = L.pair_relations("甲戌", "甲戌", {"戌"})
    assert not any("自刑" in x for x in r["zhi"]), "戌戌非自刑（自刑=辰午酉亥四支）: " + str(r)
    assert "半合（戌戌半合火局）" in r["zhi"], r


def test_dayun_location():
    e = D("2026-09-15")
    dl = CHART["dayun_r"]["dayun"]["list"]
    hit = [it for it in dl if it["start_year"] <= 2026 <= it["end_year"]]
    assert len(hit) == 1, [it for it in dl]
    assert e["dayun_at"]["ganzhi"] == hit[0]["ganzhi"] and e["dayun_at"]["index"] == hit[0]["index"], e["dayun_at"]
    e2 = D("2075-01-01")
    assert e2["dayun_at"]["ganzhi"] is None and "8 步区间外" in e2["dayun_at"]["note"], e2["dayun_at"]


def test_huangli_consistency():
    e = D("2026-09-15", wl=True)
    h = e["huangli"]
    assert h["rule_id"] == "lr-03" and h["ganzhi"] == e["shape"]["day"], "黄历干支与流日日柱双源同值"
    assert h["jianchu"]["name"] and h["huanghei"]["dao"] in ("黄道", "黑道"), h
    assert isinstance(h["shensha"], list) and "yi" in h and "ji" in h


def test_extreme_lon():
    for lon in (-180.0, 180.0):
        ch = L.load_chart(BIRTH, lon, "男")
        assert "error" not in ch, ch
        e = L.day_entry(date(2024, 6, 11), lon, ch, False)
        assert e["shape"]["day"] == m1.load_days()["2024-06-11"], f"lon={lon} 正午反解日柱漂移: {e['shape']['day']}"


def test_output_declarations():
    r = L.compute(BIRTH, 120.0, "男", date(2026, 9, 15), 3, False)
    assert "error" not in r and r["rule"] == "lr-01"
    assert "非经典" in r["positioning"] and any("非经典" in n for n in r["notes"])
    assert len(r["days"]) == 3
    for e in r["days"]:
        assert e["shape"]["rule_id"] == "lr-01" and e["shape"]["source"] and e["shape"]["alt"]
        assert e["relations"]["rule_id"] == "lr-02" and e["relations"]["source"] and e["relations"]["alt"]
        assert e["day_master_god"]["rule_id"] == "r5"
    assert r["chart"]["rule_id"] == "bd-01" and r["chart"]["qiyun"], r["chart"]
    assert L.compute(BIRTH, 120.0, "男", date(2026, 9, 15), 63)["error"], "days 上界守卫"


def test_date_sequence():
    r = L.compute(BIRTH, 120.0, "男", date(2026, 2, 26), 5, False)
    assert [e["date"] for e in r["days"]] == ["2026-02-26", "2026-02-27", "2026-02-28",
                                              "2026-03-01", "2026-03-02"], "跨月序列连续"


for name, fn in [("原局四柱锁定（庚午庚辰丙寅癸巳/丙）", test_chart_lock),
                 ("流日日柱=ganzhi_days 表", test_day_pillar_table),
                 ("立春换年跳变+节交接日正午口径", test_lichun_switch),
                 ("节换月跳变（惊蛰）", test_jie_month_switch),
                 ("十神 10 干抽查", test_ten_gods),
                 ("合冲刑害全表抽查", test_relations_tables),
                 ("三刑池口径（实盘自刑）", test_relations_pool_scope),
                 ("同支口径（自刑四支/同支半合归局）", test_same_zhi_relations),
                 ("大运年份区间定位（含 8 步外）", test_dayun_location),
                 ("黄历层引用一致性（双源同值）", test_huangli_consistency),
                 ("极端经度正午反解（±180°）", test_extreme_lon),
                 ("输出声明/rule_id/守卫", test_output_declarations),
                 ("日期序列连续性（跨月）", test_date_sequence)]:
    check(name, fn)
print(f"\nassert_l3_bazi_liuri: {sum(CHECKS)}/{len(CHECKS)} PASS")
sys.exit(0 if all(CHECKS) else 1)
