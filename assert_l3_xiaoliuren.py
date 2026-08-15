# -*- coding: utf-8 -*-
"""assert_l3_xiaoliuren.py — L3 小六壬（马前课）断言（xlr-01..xlr-04）。
覆盖：5 手工锚点全链（农历+三宫逐宫手数）、六宫属性表全查、三数推演边界
（月 12/日 30/时 12/日 31 循环）、时支序 1-12 全查、数理恒等（200 组随机三数）、
晚子时归次日、闰月沿用月数、JSON 项 rule_id/source/alt、越界报错、申报幂等。
运行：PYTHONIOENCODING=utf-8 python assert_l3_xiaoliuren.py
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from l3_xiaoliuren import compute, lunar_date, push, shichen_ordinal, LG, LG_BY_NAME  # noqa

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


def C(t, **kw):
    r = compute(datetime(*t), **kw)
    assert "error" not in r, r.get("error")
    return r


def hand_palace(n, start=1):
    """手数六宫：从 start 掌诀位数 n 下（起点宫算第 1 下），返回掌诀位 1-6。"""
    return (start - 1 + n - 1) % 6 + 1


def hand_chain(mo, da, ho):
    """手算三数全链：月宫=大安起数月；日宫=月宫起数日；时宫=日宫起数时。"""
    y = hand_palace(mo, 1)
    r = hand_palace(da, y)
    s = hand_palace(ho, r)
    return y, r, s


# --- 5 手工锚点：公历(时,分) → 农历(月,日) → 三数手算链（农历经 shuowang 朔日表，与 x6ren lunar.js 对拍一致，见 report） ---
# 2023-01-01 12:00：腊月十二…初十？手数例 1：月12→空亡；日10 从空亡数：空1大2留3速4赤5小6空7大8留9速10→速喜；
#   时7 从速喜数：速1赤2小3空4大5留6速7→速喜。最终=速喜
# 1990-08-15 08:00：农历6月25 辰时5：月6→空亡；日25 偏移24→空亡；时5 从空亡数→赤口。最终=赤口
# 2026-08-16 15:30：农历7月4 申时9：月7→大安；日4 从大安数→赤口；时9 从赤口数→空亡。最终=空亡
# 1949-10-01 10:00：农历8月10 巳时6：月8→留连；日10 从留连数→小吉；时6 从小吉数→赤口。最终=赤口
# 2099-06-15 16:00：农历4月27 申时9：月4→赤口；日27 偏移26→空亡；时9 从空亡数→留连。最终=留连
ANCHORS = [  # (输入, 农历月, 农历日, 时支序, 月宫, 日宫, 最终宫)
    ((2023, 1, 1, 12, 0), 12, 10, 7, "空亡", "速喜", "速喜"),
    ((1990, 8, 15, 8, 0), 6, 25, 5, "空亡", "空亡", "赤口"),
    ((2026, 8, 16, 15, 30), 7, 4, 9, "大安", "赤口", "空亡"),
    ((1949, 10, 1, 10, 0), 8, 10, 6, "留连", "小吉", "赤口"),
    ((2099, 6, 15, 16, 0), 4, 27, 9, "赤口", "空亡", "留连"),
]
NAMES = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]


def test_anchors_full_chain():
    for t, mo, da, ho, yg, rg, sg in ANCHORS:
        r = C(t)
        q, p = r["xlr-01"], r["xlr-03"]
        assert q["month"] == mo and q["day"] == da, (t, q["lunar"])
        assert q["hour_ordinal"] == ho, (t, q["shichen"])
        assert p["month_gong"] == yg and p["day_gong"] == rg and p["final_gong"] == sg, (t, p)
        # 独立手算复核（hand_chain 公式与模块实现同构但独立书写）
        hy, hr, hs = hand_chain(mo, da, ho)
        assert NAMES[hy - 1] == yg and NAMES[hr - 1] == rg and NAMES[hs - 1] == sg


def test_liugong_table():
    assert len(LG) == 6
    for i, g in enumerate(LG):
        assert g["pos"] == i + 1, g  # 掌诀位 1-6 顺数序
        assert g["name"] == NAMES[i], g
        assert g["name"] in LG_BY_NAME
        for k in ("wx", "shen", "ji", "pos_desc", "duan", "gist"):
            assert g.get(k), (g["name"], k)  # 字段非空
    # 通行口诀五行/吉凶/六神全查（异文见报告 xlr-a01，主表取通行版）
    WANT = [("木", "青龙", "吉"), ("水", "玄武", "凶"), ("火", "朱雀", "吉"),
            ("金", "白虎", "凶"), ("木", "六合", "吉"), ("土", "勾陈", "凶")]
    for i, (wx, shen, ji) in enumerate(WANT):
        g = LG[i]
        assert g["wx"] == wx and g["shen"] == shen and g["ji"] == ji, g
    assert LG_BY_NAME["大安"]["pos_desc"] == "食指根部"
    assert LG_BY_NAME["空亡"]["pos_desc"] == "中指根部"


def test_push_boundaries():
    # 月 12/日 30/时 12 边界：手数链=(空亡, 小吉, 赤口)
    y, r, s = push(12, 30, 12)
    assert (NAMES[y - 1], NAMES[r - 1], NAMES[s - 1]) == ("空亡", "小吉", "赤口")
    # 最小：月1 日1 时1 → 三宫皆大安
    y, r, s = push(1, 1, 1)
    assert (NAMES[y - 1], NAMES[r - 1], NAMES[s - 1]) == ("大安", "大安", "大安")
    # 月 12 取余 6：月 12 → 空亡（数满十二回大安起）
    assert NAMES[push(12, 1, 1)[0] - 1] == "空亡"
    # 日 31 → 30 日循环减 30 = 1：等价日 1
    assert push(3, 31, 1) == push(3, 1, 1)
    assert push(5, 32, 1) == push(5, 2, 1)


def test_math_identity():
    # 数理恒等：最终宫-1 ≡ (月+日+时序-3) mod 6；月宫-1 ≡ (月-1) mod 6；日宫-1 ≡ (月+日-2) mod 6
    import random
    rng = random.Random(20260816)
    for _ in range(200):
        mo, da, ho = rng.randint(1, 12), rng.randint(1, 30), rng.randint(1, 12)
        y, r, s = push(mo, da, ho)
        assert (y - 1) == (mo - 1) % 6, (mo, y)
        assert (r - 1) == (mo - 1 + da - 1) % 6, (mo, da, r)
        assert (s - 1) == (mo - 1 + da - 1 + ho - 1) % 6, (mo, da, ho, s)


def test_shichen_all():
    # 时支序 1-12 全查：子=1…亥=12（23 点后子时归次日，序号仍=1）
    import datetime as dtm
    for h in range(24):
        d = dtm.datetime(2026, 8, 16, h, 30)
        want = (h + 1) // 2 % 12 + 1
        assert shichen_ordinal(d) == want, h


def test_late_zishi():
    # 晚子时（23:00-23:59）归次日：农历日+1、时支序=1（x6ren Beta1.6 口径）
    a = C((2023, 1, 1, 22, 30))
    b = C((2023, 1, 1, 23, 30))
    assert a["input"]["late_zishi"] is False and b["input"]["late_zishi"] is True
    assert a["xlr-01"]["day"] + 1 == b["xlr-01"]["day"]  # 农历日次日
    assert b["xlr-01"]["hour_ordinal"] == 1 and b["xlr-01"]["shichen"] == "子时"
    # 22:30 亥时（11）与 23:30 子时（1）落宫差异由三数推演自然区分
    assert a["xlr-01"]["shichen"] == "亥时"


def test_leap_month():
    # 闰月沿用原月数：1949-08-24 朔为闰七月（shuowang is_ruen=1），闰七月内日数属月 7
    mo, da, leap = lunar_date(datetime(1949, 9, 5, 12, 0))[:3]
    assert mo == 7 and leap, (mo, da, leap)
    r = C((1949, 9, 5, 12, 0))
    assert "（闰月）" in r["xlr-01"]["lunar"]


def test_json_fields():
    r = C((2026, 8, 16, 15, 30), category="求财")
    for k in ("xlr-01", "xlr-02", "xlr-03", "xlr-04"):
        item = r[k]
        assert item["rule_id"].startswith("xlr-"), item
        assert item.get("source"), item
    assert r["xlr-04"]["category"] == "求财"
    assert "wx_rel" in r["xlr-04"] and "规则启发式" in r["xlr-04"]["note"]
    # 六宫表 6 项
    assert len(r["xlr-02"]["liugong"]) == 6


def test_out_of_range():
    r = compute(datetime(2101, 1, 1, 12, 0))
    assert "error" in r and "out_of_range" in r["error"]
    r2 = compute(datetime(1948, 12, 31, 12, 0))
    assert "error" in r2


def test_arbitration_idempotent():
    # 申报幂等：xlr- 前缀 case_id 在 arbitration_log.csv 中唯一（重跑不重复申报）
    rows = list(csv.DictReader(open(os.path.join(BASE, "data", "arbitration_log.csv"), encoding="utf-8")))
    ids = [r["case_id"] for r in rows if r["case_id"].startswith("xlr-")]
    assert len(ids) == len(set(ids)), "xlr- 重复申报"
    # boundary_cases 同规则
    b = list(csv.DictReader(open(os.path.join(BASE, "report", "boundary_cases.csv"), encoding="utf-8")))
    bids = [r["case_id"] for r in b if r["case_id"].startswith("xlr-")]
    assert len(bids) == len(set(bids)), "boundary xlr- 重复申报"


if __name__ == "__main__":
    tests = [(n.replace("test_", ""), f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    print(f"assert_l3_xiaoliuren.py：{len(tests)} 组断言")
    for name, fn in tests:
        check(name, fn)
    npass = sum(CHECKS)
    print(f"结果: {npass}/{len(CHECKS)} PASS")
    sys.exit(0 if npass == len(CHECKS) else 1)
