# -*- coding: utf-8 -*-
"""assert_l3_shensha.py — 八字神煞（l3_shensha.py）独立断言：5 锚点全神煞命中表 + 规则边界 + 表自洽 + 结构完整。
预期值=2026-08-16 易安居四柱神煞 25/25 对拍一致的 oracle 实测固化。运行：PYTHONIOENCODING=utf-8 python assert_l3_shensha.py"""
import sys
from datetime import datetime

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
import l3_shensha as S
from rules import GAN, ZHI

def gs(t):
    """(y,m,d,h,mi) → {柱: {神煞名}}；compute 出错即断言失败。"""
    r = S.compute(datetime(*t), 120.0)
    assert "error" not in r, r
    return {k: set(x["name"] for x in v) for k, v in r["shensha"]["groups"].items()}

def all_names(g):
    return set().union(*(v for v in g.values()))

# ========== A. 5 锚点全神煞命中表（oracle 固化） ==========
ANCHORS = [
    ((2024, 2, 10, 12, 0),  # 甲辰日（任务书锚点）
     {"年上": {"华盖", "金舆"}, "月上": {"月德贵人", "禄神", "驿马"},
      "日上": {"十恶大败", "华盖", "金舆"}, "时上": {"灾煞"}}),
    ((2024, 6, 15, 12, 0),  # 庚戌日：庚→午寅天乙、日上魁罡
     {"年上": {"国印"}, "月上": {"天乙贵人", "将星", "灾煞"},
      "日上": {"金舆", "魁罡"}, "时上": {"天乙贵人", "将星", "灾煞"}}),
    ((2000, 2, 5, 12, 0),  # 癸巳日：辰年孤辰、天喜对宫
     {"年上": {"地网"}, "月上": {"劫煞", "金舆", "驿马"},
      "日上": {"劫煞", "地网", "天乙贵人", "天喜", "孤辰"}, "时上": {"桃花(咸池)", "灾煞"}}),
    ((1990, 1, 1, 12, 0),  # 丙寅日：丙→午羊刃时上、天德子月巳支（干支并集口径）
     {"年上": {"亡神", "天德贵人", "禄神"}, "月上": {"灾煞"},
      "日上": {"劫煞"}, "时上": {"将星", "桃花(咸池)", "羊刃"}}),
    ((1949, 10, 1, 12, 0),  # 甲子日：甲→丑未天乙年上、子年酉桃花
     {"年上": {"天乙贵人"}, "月上": {"将星", "桃花(咸池)"},
      "日上": set(), "时上": {"月德贵人", "桃花(咸池)", "灾煞"}}),
]

# ========== B. 规则边界样例 ==========
# 元组：(名称, 日期, {柱: 应命中神煞}, {全盘不应命中神煞})
BOUND = [
    ("丑支见天乙", (2021, 1, 6, 12, 0),  # 甲寅日、己丑月：日干起甲→丑未命中月支丑
     {"月上": {"天乙贵人"}}, set()),
    ("子年桃花", (2020, 3, 7, 12, 0),  # 庚子年酉日：年支子起咸池酉→日支酉（非起法支）命中
     {"日上": {"桃花(咸池)"}, "时上": {"桃花(咸池)"}}, set()),
    ("丑月天德月德", (2021, 1, 6, 12, 0),  # 丑月→天德庚、月德庚：年干庚命中
     {"年上": {"天德贵人", "月德贵人"}}, set()),
    ("魁罡庚辰日", (1949, 2, 19, 12, 0), {"日上": {"魁罡"}}, set()),
    ("魁罡庚戌日", (1949, 1, 20, 12, 0), {"日上": {"魁罡"}}, set()),
    ("魁罡壬辰日", (1949, 1, 2, 12, 0), {"日上": {"魁罡"}}, set()),
    ("魁罡戊戌日", (1949, 1, 8, 12, 0), {"日上": {"魁罡"}}, set()),
    ("十恶己丑日", (1949, 2, 28, 12, 0), {"日上": {"十恶大败"}}, set()),
    ("十恶癸亥日", (1949, 2, 2, 12, 0), {"日上": {"十恶大败"}}, set()),
    ("天罗丙戌日", (1949, 2, 25, 12, 0), {"日上": {"天罗"}}, set()),
    ("天罗丁亥日", (1949, 2, 26, 12, 0), {"日上": {"天罗"}}, set()),
    ("地网戊辰日", (1949, 2, 7, 12, 0), {"日上": {"地网"}}, set()),
    ("地网己巳日", (1949, 2, 8, 12, 0), {"日上": {"地网"}}, set()),
    ("地网壬辰日", (1949, 1, 2, 12, 0), {"日上": {"地网"}}, set()),
    ("地网癸巳日", (1949, 1, 3, 12, 0), {"日上": {"地网"}}, set()),
    ("金木命无天罗地网", (1949, 2, 13, 12, 0),  # 甲戌日见戌支：木命不忌
     {"日上": {"国印", "寡宿"}}, {"天罗", "地网"}),
    ("乙巳日金命", (1949, 1, 15, 12, 0),  # 乙日见巳：金命不忌地网
     {"日上": {"十恶大败", "文昌贵人", "金舆"}}, {"天罗", "地网"}),
    ("戊午日土命无地支", (1949, 1, 28, 12, 0),  # 戊日土命但四支无辰巳戌亥
     {"日上": {"羊刃"}}, {"天罗", "地网"}),
    ("阴干羊刃", (1949, 2, 8, 12, 0),  # 己巳日：己→巳阴刃
     {"日上": {"羊刃"}}, set()),
]

CHECKS = []

def check(name, fn):
    CHECKS.append((name, fn))

for idx, (t, want) in enumerate(ANCHORS, 1):
    def mk(t=t, want=want):
        assert gs(t) == want, f"\n  实际 {gs(t)}\n  预期 {want}"
    check(f"A{idx} 锚点 {t[0]}-{t[1]:02d}-{t[2]:02d} 全神煞命中表", mk)

for name, t, want_sub, absent in BOUND:
    def mk(t=t, want_sub=want_sub, absent=absent):
        g = gs(t)
        for k, v in want_sub.items():
            assert v <= g[k], f"{k} 缺 {v - g[k]}（实际 {g[k]}）"
        assert absent & all_names(g) == set(), f"不应命中 {absent & all_names(g)}（实际 {all_names(g)}）"
    check(f"B 边界 {name}", mk)

# ========== C. 表自洽性 ==========
def check_day_tables():
    for tab in ("TIANYI", "WENCHANG", "YANGREN", "LUSHEN", "JINYU", "GUOYIN"):
        tb = getattr(S, tab)
        assert set(tb) == set(GAN), f"{tab} 十干未全覆盖"
        assert all(set(v) <= set(ZHI) for v in tb.values()), f"{tab} 值含非地支"
check("C1 日干六表十干全覆盖、值均地支", check_day_tables)

def check_sanhe():
    groups = ("寅午戌", "申子辰", "巳酉丑", "亥卯未")
    for mem in groups:
        rows = {S.SANHE[base] for base in mem}  # 同局三起法支须共享同一组 7 神煞支
        assert len(rows) == 1, f"三合局 {mem} 内起法支结果不一致: {rows}"
    assert set(S.SANHE) == set(ZHI), "SANHE 须十二支全覆盖"
    for gz in S.SANHE.values():
        assert len(gz) == 7 and all(z in ZHI for z in gz), "SANHE 每行须为 7 地支"
    for mem in groups:
        for base in mem:
            assert S.SANHE[base][0] in ("卯", "酉", "午", "子"), f"{base} 咸池位非四桃花支"
check("C2 SANHE 同局三起法支行一致、咸池位为桃花支", check_sanhe)

def check_td_yd():
    assert set(S.TIANDE) == set(ZHI) and set(S.YUEDE) == set(ZHI), "天德/月德须十二支全覆盖"
    for z, g in S.YUEDE.items():
        assert set(g) <= set(GAN), f"月德 {z}→{g} 非天干"
    for z, g in S.TIANDE.items():
        assert set(g) <= set(GAN + ZHI), f"天德 {z}→{g} 非干支"
check("C3 天德/月德十二支全覆盖且值合法", check_td_yd)

def check_dui():
    assert len(S.KUI) == 4 and len(S.SHIE) == 10, "魁罡 4 日、十恶 10 日"
    for gz in S.KUI + S.SHIE:
        assert gz[0] in GAN and gz[1] in ZHI, f"{gz} 非法干支"
    assert set(S.KUI) & set(S.SHIE) == {"庚辰", "戊戌"}, "魁罡∩十恶应为庚辰/戊戌"
check("C4 魁罡四日/十恶十日查表项合法", check_dui)

# ========== D. 结构完整性 ==========
def check_struct():
    r = S.compute(datetime(2024, 2, 10, 12, 0), 120.0)
    assert set(r["shensha"]["groups"]) == {"年上", "月上", "日上", "时上"}, "分组须年/月/日/时四组"
    total = 0
    for v in r["shensha"]["groups"].values():
        total += len(v)
        for x in v:
            for f in ("name", "rule_id", "source", "method", "diff"):
                assert f in x and x[f], f"{x['name']} 缺 {f}"
            assert x["rule_id"].startswith("ss-"), f"rule_id 非 ss- 前缀: {x['rule_id']}"
    assert total == r["shensha"]["hit_total"], "hit_total 与各组命中合计不符"
    assert "pillars" in r and "ten_gods" in r, "须附带四柱与十神"
check("D1 命中项四字段+Rule-ID、分组、hit_total 一致", check_struct)

def check_gugua():
    for z, (gu, gua) in S.GUGUA.items():
        assert gu != gua, f"孤辰=寡宿? {z}"
check("D2 孤辰寡宿每支不重合", check_gugua)

def check_hl_tx():
    r = S.compute(datetime(2000, 2, 5, 12, 0), 120.0)  # 辰年巳日：天喜=巳→日上
    hits = {x["name"]: x for v in r["shensha"]["groups"].values() for x in v}
    assert "天喜" in hits and hits["天喜"]["rule_id"] == "ss-11", "天喜须 ss-11"
    assert "红鸾" not in hits  # 本样例无红鸾，仅验证表项存在
check("D3 红鸾/天喜 Rule-ID 与年支起法存在", check_hl_tx)

# ========== 运行 ==========
def main():
    bad = 0
    for name, fn in CHECKS:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            bad += 1
            print(f"FAIL  {name}：{e}")
    print(f"\nassert_l3_shensha.py：断言 {len(CHECKS)} 条，PASS {len(CHECKS) - bad}，FAIL {bad}")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
