# -*- coding: utf-8 -*-
"""assert_l3_wuyunliuqi.py — 五运六气（l3_wuyunliuqi.py）独立断言：
5 锚点全链 + 天干化运 10 干全查 + 地支化气 12 支全查 + 客气轮排 + 六步节气边界 2 例 +
五类相合 3 例 + WYLQ oracle 24 特殊年全量表对拍 + 结构完整性。
运行：PYTHONIOENCODING=utf-8 python assert_l3_wuyunliuqi.py"""
import sys
from datetime import datetime

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
import l3_wuyunliuqi as W
from rules import GAN, ZHI

def c(t):
    r = W.compute(datetime(*t))
    assert "error" not in r, r
    return r

def types(r):
    return [x["name"] for x in r["xiang_he"]["types"]]

def cur(r):
    z, k = r["zhu_qi"]["current"], r["ke_qi"]["current"]
    return z["step"], z["qi"], k["qi"]

# ========== A. 5 锚点全链（手算） ==========
ANCHORS = [
    ((2026, 1, 10, 12, 0),  # 大寒前 → 上岁乙巳：金运不及（从革）；巳年厥阴司天、少阳在泉；终之气主太阳客少阳
     {"gz": "乙巳", "yun": "金", "lv": "不及", "ji": "从革之纪", "st": "厥阴风木", "zq": "少阳相火",
      "he": [], "step": "终之气", "zhu": "太阳寒水", "ke": "少阳相火"}),
    ((2026, 7, 15, 12, 0),  # 丙午：水运太过（流衍）；午年少阴司天、阳明在泉；三之气主少阳客少阴（司天）
     {"gz": "丙午", "yun": "水", "lv": "太过", "ji": "流衍之纪", "st": "少阴君火", "zq": "阳明燥金",
      "he": [], "step": "三之气", "zhu": "少阳相火", "ke": "少阴君火"}),
    ((2026, 12, 31, 12, 0),  # 丙午终之气：主太阳寒水，客=在泉阳明燥金
     {"gz": "丙午", "yun": "水", "lv": "太过", "ji": "流衍之纪", "st": "少阴君火", "zq": "阳明燥金",
      "he": [], "step": "终之气", "zhu": "太阳寒水", "ke": "阳明燥金"}),
    ((2000, 2, 5, 12, 0),  # 庚辰：金运太过（坚成）；辰年太阳司天、太阴在泉；初之气主厥阴客少阳（司天-2）
     {"gz": "庚辰", "yun": "金", "lv": "太过", "ji": "坚成之纪", "st": "太阳寒水", "zq": "太阴湿土",
      "he": [], "step": "初之气", "zhu": "厥阴风木", "ke": "少阳相火"}),
    ((1949, 10, 1, 12, 0),  # 己丑：土运不及（卑监）；丑年太阴司天、太阳在泉；太一天符（天符+岁会）；五之气主阳明客阳明
     {"gz": "己丑", "yun": "土", "lv": "不及", "ji": "卑监之纪", "st": "太阴湿土", "zq": "太阳寒水",
      "he": ["太一天符"], "step": "五之气", "zhu": "阳明燥金", "ke": "阳明燥金"}),
]

CHECKS = []

def check(name, fn):
    CHECKS.append((name, fn))

for idx, (t, want) in enumerate(ANCHORS, 1):
    def mk(t=t, want=want):
        r = c(t)
        sy = r["sui_yun"]
        assert sy["ganzhi"] == want["gz"], f"岁干支 {sy['ganzhi']} != {want['gz']}"
        assert sy["yun"] == want["yun"] and sy["level"] == want["lv"], f"岁运 {sy['name']}"
        assert sy["ji"] == want["ji"], f"岁纪 {sy['ji']}"
        assert r["ke_qi"]["si_tian"] == want["st"], f"司天 {r['ke_qi']['si_tian']}"
        assert r["ke_qi"]["zai_quan"] == want["zq"], f"在泉 {r['ke_qi']['zai_quan']}"
        assert types(r) == want["he"], f"相合 {types(r)}"
        st, zhu, ke = cur(r)
        assert (st, zhu, ke) == (want["step"], want["zhu"], want["ke"]), f"当前 ({st},{zhu},{ke})"
        # 全链：客气六步含司天于三之气、在泉于终之气
        steps = r["ke_qi"]["steps"]
        assert steps[2]["ke_qi"] == want["st"] and steps[5]["ke_qi"] == want["zq"], "三之气/终之气非司天/在泉"
        assert steps[2]["si_tian"] and steps[5]["zai_quan"] and not steps[0]["si_tian"], "司天在泉标记错位"
    check(f"A{idx} 锚点 {t[0]:04d}-{t[1]:02d}-{t[2]:02d} 全链（岁运/司天在泉/相合/当前步/六步表）", mk)

# ========== B. 天干化运 10 干全查（wylq-01） ==========
def check_gan():
    exp = {"甲": ("土", 1), "乙": ("金", 0), "丙": ("水", 1), "丁": ("木", 0), "戊": ("火", 1),
           "己": ("土", 0), "庚": ("金", 1), "辛": ("水", 0), "壬": ("木", 1), "癸": ("火", 0)}
    for g, (wx, too) in exp.items():
        got = (W.YUN_WX[g], int(g in "甲丙戊庚壬"))
        assert got == (wx, too), f"{g} 化运 {got} != {wx}{'太过' if too else '不及'}"
        # 十干全查经 compute：变干须换年（(y-4)%10=i）
        for i, (g2, (wx2, too2)) in enumerate(exp.items()):
            y2 = 2026 + ((i - (2026 - 4) % 10) % 10)
            rr = c((y2, 8, 15, 12, 0))
            assert rr["sui_yun"]["yun"] == wx2 and (rr["sui_yun"]["level"] == "太过") == bool(too2), f"{g2} 年实测失败"
check("B1 天干化运 10 干全查（口诀表+compute 实测）", check_gan)

# ========== C. 地支化气 12 支全查 + 客气轮排（wylq-03） ==========
def check_zhi():
    exp_st = {"子": "少阴君火", "丑": "太阴湿土", "寅": "少阳相火", "卯": "阳明燥金", "辰": "太阳寒水", "巳": "厥阴风木",
              "午": "少阴君火", "未": "太阴湿土", "申": "少阳相火", "酉": "阳明燥金", "戌": "太阳寒水", "亥": "厥阴风木"}
    exp_zq = {"子": "阳明燥金", "丑": "太阳寒水", "寅": "厥阴风木", "卯": "少阴君火", "辰": "太阴湿土", "巳": "少阳相火",
              "午": "阳明燥金", "未": "太阳寒水", "申": "厥阴风木", "酉": "少阴君火", "戌": "太阴湿土", "亥": "少阳相火"}
    assert W.SI_TIAN == exp_st, "司天表与《五运行大论》不符"
    assert W.ZAI_QUAN == exp_zq, "在泉表（对宫）不符"
    for i, z in enumerate(ZHI):  # 12 支全查经 compute（年中日期，1949 支序 1，逐年加 1..11 得各支）
        yz = 1949 + ((i - 1) % 12)
        rr = c((yz, 8, 15, 12, 0))
        assert rr["sui_yun"]["ganzhi"][1] == z
        assert rr["ke_qi"]["si_tian"] == exp_st[z] and rr["ke_qi"]["zai_quan"] == exp_zq[z], f"{z} 年司天/在泉实测失败"
check("C1 地支化气 12 支全查（司天/在泉表+compute 实测）", check_zhi)

def check_keqi_roll():
    # 子午年六步：初太阳→二厥阴→三少阴(司天)→四太阴→五少阳→终阳明(在泉)（《六微旨大论》子午之岁）
    assert W._keqi_steps("丙子") == ["太阳寒水", "厥阴风木", "少阴君火", "太阴湿土", "少阳相火", "阳明燥金"]
    # 辰戌年（太阳司天）：初少阳→二阳明→三太阳(司天)→四厥阴→五少阴→终太阴(在泉)
    assert W._keqi_steps("甲辰") == ["少阳相火", "阳明燥金", "太阳寒水", "厥阴风木", "少阴君火", "太阴湿土"]
    # 司天对宫恒为在泉
    for z in ZHI:
        assert W.ZAI_QUAN[z] == W.QI_SEQ[(W.QI_SEQ.index(W.SI_TIAN[z]) + 3) % 6], f"{z} 在泉非对宫"
check("C2 客气六步轮排（子午/辰戌 2 例+六组对宫全查）", check_keqi_roll)

# ========== D. 六步节气边界 2 例（wylq-05，solar_terms.csv 定气时刻） ==========
def check_boundary():
    # 2026-01-20 09:45 大寒：09:44 归上岁（乙巳）终之气，09:45 起丙午初之气
    r1 = c((2026, 1, 20, 9, 44))
    assert r1["sui_yun"]["ganzhi"] == "乙巳" and cur(r1)[0] == "终之气", f"大寒前 1 分 {r1['sui_yun']['ganzhi']} {cur(r1)}"
    r2 = c((2026, 1, 20, 9, 45))
    assert r2["sui_yun"]["ganzhi"] == "丙午" and cur(r2)[0] == "初之气", f"大寒整点 {r2['sui_yun']['ganzhi']} {cur(r2)}"
    # 2026-03-20 22:46 春分：22:45 归初之气（厥阴），22:46 起二之气（少阴君火）
    r3 = c((2026, 3, 20, 22, 45))
    assert cur(r3)[0] == "初之气" and cur(r3)[1] == "厥阴风木", f"春分前 1 分 {cur(r3)}"
    r4 = c((2026, 3, 20, 22, 46))
    assert cur(r4)[0] == "二之气" and cur(r4)[1] == "少阴君火", f"春分整点 {cur(r4)}"
    # 节点时刻与 csv 权威一致（solar_terms.csv 2026 大寒=2026-01-20 09:45）
    assert r2["nodes"]["current"]["node"] == "大寒" and r2["nodes"]["current"]["time"] == "2026-01-20 09:45", \
        "节点时刻非 csv 权威"
check("D1 六步节气边界 2 例（大寒/春分整分切换）", check_boundary)

# ========== E. 五类相合 3 例 + WYLQ oracle 24 特殊年全量表对拍（wylq-04） ==========
def _year_of(gz):
    y = 1949
    while (y - 4) % 10 != GAN.index(gz[0]) or (y - 4) % 12 != ZHI.index(gz[1]):
        y += 1
    return y

def check_he():
    yun_t, st_t, zq_t, he_t = W._oracle_tables()
    # 三例：戊午=太一天符、庚子=同天符、癸亥=同岁会
    for y, want in ((1978, ["太一天符"]), (2020, ["同天符"]), (2043, ["同岁会"])):
        rr = c((y, 8, 15, 12, 0))
        assert types(rr) == want, f"{y} 年相合 {types(rr)} != {want}"
    # WYLQ 24 特殊年全量对拍（oracle 表 vs 自研逻辑表）——自研须全含 oracle 判定
    for gz, s in he_t.items():
        rr = c((_year_of(gz), 8, 15, 12, 0))
        got = set(types(rr))
        exp = W._oracle_types(s)
        assert got == exp, f"{gz} 自研{got} vs oracle{exp}"
    # oracle 表遗漏 2 条（WYLQ 手工表不完整）：按《六元正纪大论》定义+fate-craft 算法推导，
    # 戊申（火运太过+申年少阳相火司天）=天符、癸巳（火运不及+巳年少阳相火在泉）=同岁会
    for gz, want in (("戊申", {"天符"}), ("癸巳", {"同岁会"})):
        rr = c((_year_of(gz), 8, 15, 12, 0))
        assert set(types(rr)) == want, f"{gz} 自研{set(types(rr))} vs 理论{want}（WYLQ 表遗漏，申报 wylq-004/005）"
    # 其余 34 年应为无相合
    for gz in (GAN[i % 10] + ZHI[i % 12] for i in range(60)):
        if gz in he_t or gz in ("戊申", "癸巳"):
            continue
        rr = c((_year_of(gz), 8, 15, 12, 0))
        assert types(rr) == [], f"{gz} 不应有相合，得 {types(rr)}"
check("E1 五类相合 3 例+WYLQ 24 特殊年全量表+理论补遗 2 例+其余 34 年无相合", check_he)

def check_cycle():
    # 60 甲子全周期：岁运五行=干化运循环 6 轮，太过不及随阳干
    for i in range(60):
        gz = GAN[i % 10] + ZHI[i % 12]
        y = 1949
        while (y - 4) % 60 != i:
            y += 1
        rr = c((y, 8, 15, 12, 0))
        assert rr["sui_yun"]["ganzhi"] == gz and rr["sui_yun"]["yun"] == W.YUN_WX[gz[0]]
check("F1 60 甲子全周期岁运循环", check_cycle)

# ========== G. 结构完整性 ==========
def check_struct():
    r = c((2026, 7, 15, 12, 0))
    for sec in ("sui_yun", "zhu_qi", "ke_qi", "xiang_he", "nodes"):
        assert r[sec]["rule_id"].startswith("wylq-"), f"{sec} rule_id 前缀"
        for f in ("rule_id", "source", "alt"):
            assert f in r[sec], f"{sec} 缺 {f}"
    assert any("非医学诊断" in n for n in r["notes"]), "缺非医学诊断声明"
    assert "素问" in r["sui_yun"]["source"] and "天元纪大论" in r["sui_yun"]["source"], "岁运出处缺《素问》篇目"
    # 非法输入
    assert "error" in W.compute(datetime(2026, 7, 15, 12, 0, 30)), "秒精度应拒绝"
    assert "error" in W.compute(datetime(2101, 1, 1, 12, 0)), "超范围应拒绝"
    assert "error" in W.compute(datetime(1948, 1, 1, 12, 0)), "超范围应拒绝"
    # 主气六步每步 ~60.875 日（365.25/6）
    r2 = c((2026, 7, 15, 12, 0))
    d0 = datetime.strptime(r2["zhu_qi"]["steps"][0]["start"], "%Y-%m-%d %H:%M")
    d6 = datetime.strptime(r2["zhu_qi"]["steps"][5]["end"], "%Y-%m-%d %H:%M")
    assert abs((d6 - d0).total_seconds() / 86400 - 365.25) < 0.1, f"六步总长 {(d6-d0).days} 日"
check("G1 结构完整性（rule_id/source/alt/声明/错误处理/六步总长）", check_struct)

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
    print(f"\nassert_l3_wuyunliuqi.py：断言 {len(CHECKS)} 条，PASS {len(CHECKS) - bad}，FAIL {bad}")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
