# -*- coding: utf-8 -*-
"""assert_l3_tieban.py — 铁板条文层断言（tb-01..tb-04）。
覆盖：太玄数键固定值锁（甲子乙丑丙寅丁卯=60 / 实盘 53）、tb-02 刻框架（一时八刻 8 候选同盘、
每刻窗起点+1 取样往返收敛、子时跨午夜日柱/时柱分裂、百刻制 100 候选、ke_of 反推）、
tb-03 键匹配（全通配/刻位/柱位通配组合、库缺失容错）、evaluate_rows 五态判定与计分、
tb-04 examine 端到端计分排序（合成语料标注非真实条文）、lookup 单点查表、输出声明与错误路径。
运行：PYTHONIOENCODING=utf-8 python assert_l3_tieban.py
"""
import csv, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import m1
import l3_tieban as T

CHECKS = []
REF = datetime(1990, 5, 1, 10, 0)          # 北京时近似出生时刻
REF_ZI = datetime(1990, 5, 1, 23, 40)      # 子时近似
CHART = {"year": "庚午", "month": "庚辰", "day": "丙寅", "hour": "癸巳"}


def check(name, fn):
    try:
        fn()
        print(f"  PASS {name}")
        CHECKS.append(True)
    except AssertionError as e:
        print(f"  FAIL {name}: {e}")
        CHECKS.append(False)


def row(rid, **kw):
    r = {k: "" for k in T.LIB_FIELDS}
    r["id"] = rid
    r.update(kw)
    return r


def test_taixuan_key():
    T._check_tables()
    k = T.tai_xuan_key({"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"})
    assert k["values"] == [9, 9, 8, 8, 7, 7, 6, 6] and k["total"] == 60, k["values"]
    assert k["rule_id"] == "tb-01" and k["alt"], k
    k2 = T.tai_xuan_key(CHART)
    assert k2["values"] == [8, 9, 8, 5, 7, 7, 5, 4] and k2["total"] == 53, k2["values"]
    assert k2["detail"]["day"] == {"ganzhi": "丙寅", "gan_shu": 7, "zhi_shu": 7}, k2["detail"]["day"]


def test_ke_candidates_basic():
    cc = T.ke_candidates(REF, 120.0)
    assert cc["rule_id"] == "tb-02" and cc["shichen_name"] == "巳" and cc["shichen"] == 5, cc
    cs = cc["candidates"]
    assert [c["ke"] for c in cs] == [1, 2, 3, 4, 5, 6, 7, 8], [c["ke"] for c in cs]
    assert cs[0]["start_true"] == "1990-05-01 09:00" and cs[7]["start_true"] == "1990-05-01 10:45", cs
    for c in cs:
        # 刻窗起点+1 分钟取样；真太阳时反解往返收敛（≤90 秒）
        st0 = datetime.strptime(c["start_true"], "%Y-%m-%d %H:%M")
        st1 = datetime.strptime(c["sample_true"], "%Y-%m-%d %H:%M")
        assert (st1 - st0).total_seconds() == 60, c
        back = m1.true_solar(datetime.strptime(c["sample_bj"], "%Y-%m-%d %H:%M"), 120.0)
        assert abs((back - st1).total_seconds()) <= 90, (c, back)
        # 同一时辰全刻同盘（刻不改变四柱）
        assert c["pillars"] == CHART, c
        assert c["pillars"]["hour"] == m1.hour_pillar(c["pillars"]["day"], st1.hour), c


def test_ke_candidates_zi_midnight():
    cc = T.ke_candidates(REF_ZI, 120.0)
    assert cc["shichen_name"] == "子" and cc["ref_true"] == "1990-05-01 23:42", cc["ref_true"]
    cs = cc["candidates"]
    dgz = m1.load_days()
    for c in cs[:4]:  # 真太阳日期 05-01
        assert c["sample_true"].startswith("1990-05-01") and c["pillars"]["day"] == dgz["1990-05-01"], c
    for c in cs[4:]:  # 真太阳日期 05-02（子正换日分裂）
        assert c["sample_true"].startswith("1990-05-02") and c["pillars"]["day"] == dgz["1990-05-02"], c
    assert cs[3]["pillars"]["day"] != cs[4]["pillars"]["day"], "子时跨午夜必须分裂日柱"
    assert [c["pillars"]["hour"][1] for c in cs] == ["子"] * 8, "子时八刻时支应全为子"
    assert cs[3]["pillars"]["hour"] != cs[4]["pillars"]["hour"], "日干换→时干随之变（五鼠遁）"
    for c in cs:
        assert c["pillars"]["hour"] == m1.hour_pillar(c["pillars"]["day"], int(c["sample_true"][11:13])), c


def test_ke_mode_100_and_ke_of():
    cc = T.ke_candidates(REF, 120.0, "100")
    cs = cc["candidates"]
    assert len(cs) == 100 and cs[0]["start_true"] == "1990-05-01 00:00", cs[0]["start_true"]
    assert cs[0]["sample_true"] == "1990-05-01 00:01" and cs[-1]["sample_true"] < "1990-05-02 00:00", cs[-1]
    assert T.ke_of(m1.true_solar(REF, 120.0), "8") == 5, "10:02 真太阳时落巳时第 5 刻"
    assert 41 <= T.ke_of(m1.true_solar(REF, 120.0), "100") <= 43, "10:02 全日子刻约第 42 刻"
    assert T.ke_of(m1.true_solar(REF_ZI, 120.0), "8") == 3, "23:42 落子时第 3 刻（23:30-23:45 窗）"
    assert T.ke_candidates(REF, 120.0, "7")["error"], "非法 mode 应报错"


def test_retrieve_wildcards():
    p = dict(CHART)
    lib = {"rows": [row("A"),                                          # 全通配
                    row("B", ke="3", d_zhi="寅"),                       # 刻3+日支寅
                    row("C", y_gan="庚", y_zhi="午"),                   # 年柱锁
                    row("D", ke="3", d_zhi="子"),                       # 刻3+日支子（不命中）
                    row("E", h_zhi="巳", ke="1")],                      # 刻1+时支巳
            "path": "synthetic", "exists": True}
    r3 = T.retrieve(p, 3, lib)
    assert [m["id"] for m in r3["matched"]] == ["A", "B", "C"], [m["id"] for m in r3["matched"]]
    assert r3["rule_id"] == "tb-03" and r3["count"] == 3
    r1 = T.retrieve(p, 1, lib)
    assert [m["id"] for m in r1["matched"]] == ["A", "C", "E"], [m["id"] for m in r1["matched"]]
    assert T.retrieve(p, 8, lib)["count"] == 2, "刻8 仅全通配 A 与年柱锁 C"
    miss = T.load_library("Z:/no_such_lib.csv")
    assert miss["exists"] is False and miss["rows"] == []
    assert T.retrieve(p, 3, miss)["count"] == 0


def test_evaluate_states():
    rows = [row("X1", claim="父母.生肖=马"),
            row("X2", claim="父母.生肖=龙"),
            row("X3", claim=""),
            row("X4", claim="兄弟.排行=二")]
    ev = T.evaluate_rows(rows, {"父母.生肖": "马"}, None)
    assert [d["verdict"] for d in ev["details"]] == ["hit", "miss", "unknown", "unknown"], ev["details"]
    assert [d["how"] for d in ev["details"]] == ["自动", "自动", "无断言", "facts 缺失"], ev["details"]
    assert ev["counts"] == {"hit": 1, "miss": 1, "unknown": 2} and ev["score"] == 0, ev
    ev2 = T.evaluate_rows(rows, {"父母.生肖": "马"}, {"X2": "hit", "X1": "miss"})
    assert ev2["details"][0]["how"] == "人工" and ev2["details"][0]["verdict"] == "miss", ev2["details"]
    assert ev2["score"] == 0 and ev2["counts"]["hit"] == 1, ev2


def test_examine_end_to_end():
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        # 合成语料（标注非真实条文）：1031 刻3+日支寅 命中；1032 断言不符 → miss
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(T.LIB_FIELDS)
            w.writerow(["1031", "六亲", "【合成示例·非真实条文】", "父母.生肖=马", "3",
                        "", "", "", "", "", "寅", "", ""])
            w.writerow(["1032", "六亲", "【合成示例·非真实条文】", "父母.生肖=龙", "",
                        "", "", "", "", "", "", "", ""])
        r = T.examine(REF, 120.0, {"父母.生肖": "马"}, None, "8", path)
        assert r["rule"] == "tb-04" and len(r["candidates"]) == 8, r["rule"]
        for c in r["candidates"]:
            assert c["key"]["rule_id"] == "tb-01" and c["retrieval"]["rule_id"] == "tb-03", c["ke"]
            assert set(c["evaluation"]["counts"]) == {"hit", "miss", "unknown"}, c["ke"]
        assert r["ranking"][0]["ke"] == 3 and r["ranking"][0]["score"] == 0, r["ranking"]
        assert r["ranking"][-1]["score"] == -1, r["ranking"][-1]
        assert "拟合≠预测验证" in r["positioning"] and any("拟合" in n for n in r["notes"]), r["notes"]
        # 人工 verdicts 覆盖：1032 由 miss 变 hit（人工）→ 刻3=2（含 1031 hit）、其余=1
        r2 = T.examine(REF, 120.0, {"父母.生肖": "马"}, {"1032": "hit"}, "8", path)
        assert {x["ke"]: x["score"] for x in r2["ranking"]} == {3: 2, 1: 1, 2: 1, 4: 1,
                                                               5: 1, 6: 1, 7: 1, 8: 1}, r2["ranking"]
        assert r2["ranking"][0]["ke"] == 3, r2["ranking"]
        assert r2["candidates"][1]["evaluation"]["details"][0]["how"] == "人工", r2["candidates"][1]
        # 库缺失：note 如实申报
        r3 = T.examine(REF, 120.0, None, None, "8", "Z:/no_such_lib.csv")
        assert "未提供" in r3["notes"][0], r3["notes"]
    finally:
        os.remove(path)


def test_lookup():
    r = T.lookup(REF, 120.0)
    assert r["pillars"] == CHART, r["pillars"]
    assert r["true_solar"] == "1990-05-01 10:02" and r["ke"] == 5, (r["true_solar"], r["ke"])
    assert r["key"]["values"] == [8, 9, 8, 5, 7, 7, 5, 4] and r["retrieval"]["count"] == 0
    assert T.lookup(REF, 120.0, ke=8)["ke"] == 8, "显式刻位应生效"
    err = T.lookup(datetime(1990, 5, 1, 10, 0, 30), 120.0)
    assert "error" in err and "秒" in err["error"], err


def test_warnings_surface():
    # 数据错误外显：ke 非法行 / verdict 非法值 / claim 多 '=' → warnings（不静默吞噬）
    p = dict(CHART)
    lib = {"rows": [row("W1", ke="abc"), row("W2", ke="3")], "path": "synthetic", "exists": True}
    r = T.retrieve(p, 3, lib)
    assert [m["id"] for m in r["matched"]] == ["W2"], r["matched"]
    assert r["warnings"] and "W1" in r["warnings"][0] and "ke" in r["warnings"][0], r["warnings"]
    ev = T.evaluate_rows(lib["rows"], None, {"W2": "yes"})
    assert any("verdict" in w and "W2" in w for w in ev["warnings"]), ev["warnings"]
    ev2 = T.evaluate_rows([row("W3", claim="a=b=c")], {"a": "b"}, None)
    assert any("多个 '='" in w for w in ev2["warnings"]), ev2["warnings"]


def test_lookup_positioning():
    r = T.lookup(REF, 120.0)
    assert "positioning" in r and "拟合≠预测验证" in r["positioning"], r.get("positioning")


for name, fn in [("太玄数键固定值锁（60/53）", test_taixuan_key),
                 ("tb-02 一时八刻：全刻同盘+往返收敛", test_ke_candidates_basic),
                 ("tb-02 子时跨午夜：日柱/时柱分裂", test_ke_candidates_zi_midnight),
                 ("tb-02 百刻制+ke_of 反推", test_ke_mode_100_and_ke_of),
                 ("tb-03 键匹配：通配组合+库缺失", test_retrieve_wildcards),
                 ("evaluate_rows 五态判定与计分", test_evaluate_states),
                 ("tb-04 examine 端到端计分排序", test_examine_end_to_end),
                 ("lookup 单点查表+错误路径", test_lookup),
                 ("warnings 外显（非法 ke/verdict/claim）", test_warnings_surface),
                 ("lookup positioning 声明", test_lookup_positioning)]:
    check(name, fn)
print(f"\nassert_l3_tieban: {sum(CHECKS)}/{len(CHECKS)} PASS")
sys.exit(0 if all(CHECKS) else 1)
