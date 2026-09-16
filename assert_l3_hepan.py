# -*- coding: utf-8 -*-
"""assert_l3_hepan.py — 人际合盘 l3_hepan.py 断言集（自查用，不改动任何其他文件）。
覆盖：5 锚点全字段、十神互定位手算核对、无时柱双盘 2 例、冲合计数规则边界、幂等。
运行：PYTHONIOENCODING=utf-8 python assert_l3_hepan.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l3_hepan as h
import m1

TOTAL = FAILED = 0


def check(name, cond, detail=""):
    global TOTAL, FAILED
    TOTAL += 1
    if not cond:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" — {detail}" if detail else ""))
    else:
        print(f"[PASS] {name}")
    return cond


def get(name, s, lon=120.0):
    return h.get_pillars(h.parse_person(s, lon))


# ============================ 1. 五锚点全字段 ============================
A1a, A1b = get("A1a", "1990-01-01 10:00"), get("A1b", "1995-06-15 08:00")
r1 = h.compute("1990-01-01 10:00", "1995-06-15 08:00")
check("A1 四柱：甲 己巳丙子丙寅癸巳",
      [A1a["pillars"][k] for k in ("year", "month", "day", "hour")] == ["己巳", "丙子", "丙寅", "癸巳"])
check("A1 四柱：乙 乙亥壬午丁丑甲辰",
      [A1b["pillars"][k] for k in ("year", "month", "day", "hour")] == ["乙亥", "壬午", "丁丑", "甲辰"])
check("A1 HP1 counts=五合1/克4/六合2/三合3/六冲2/三刑0/六害0",
      r1["hp-01"]["counts"] == {"天干五合": 1, "天干相克": 4, "地支六合": 2, "地支三合": 3,
                                 "地支六冲": 2, "地支三刑": 0, "地支六害": 0},
      str(r1["hp-01"]["counts"]))
check("A1 HP2 互定位=劫财/劫财（丙丁同火异阴阳）",
      (r1["hp-02"]["main"]["a_in_b"]["god"], r1["hp-02"]["main"]["b_in_a"]["god"]) == ("劫财", "劫财"))
check("A1 HP3 生肖=六冲（巳亥）、纳音=相生（大林木生山头火）",
      r1["hp-03"]["sheng_xiao"]["relation"] == "六冲" and r1["hp-03"]["nayin"]["relation"] == "相生",
      r1["hp-03"]["sheng_xiao"]["relation"] + "/" + r1["hp-03"]["nayin"]["relation"])
check("A1 HP4 总分 -1 倾向平（结构0+十神-2+纳音1）",
      r1["hp-04"]["scores"]["total"] == -1 and r1["hp-04"]["tendency"] == "平",
      str(r1["hp-04"]["scores"]["total"]))

r2 = h.compute("2000-02-05 12:00", "1998-08-15 14:00")
check("A2 HP1 counts=五合1/克3/六合2/三合3/六冲1/三刑2/六害0（寅寅仍半合、午午同支自刑）",
      r2["hp-01"]["counts"] == {"天干五合": 1, "天干相克": 3, "地支六合": 2, "地支三合": 3,
                                 "地支六冲": 1, "地支三刑": 2, "地支六害": 0},
      str(r2["hp-01"]["counts"]))
check("A2 HP2 互定位=正印/伤官（癸生甲、甲泄癸）",
      (r2["hp-02"]["main"]["a_in_b"]["god"], r2["hp-02"]["main"]["b_in_a"]["god"]) == ("正印", "伤官"))
check("A2 HP3 纳音=相生（城头土生白蜡金）",
      r2["hp-03"]["nayin"]["relation"] == "相生",
      r2["hp-03"]["nayin"]["a_nayin"] + "/" + r2["hp-03"]["nayin"]["b_nayin"])

r3 = h.compute("2024-02-10 08:00", "2024-06-15 12:00")
check("C1 HP1 counts=五合0/克9/六合0/三合2/六冲1/三刑1/六害0（辰戌冲去重、辰辰同支自刑优先于同局半合）",
      r3["hp-01"]["counts"] == {"天干五合": 0, "天干相克": 9, "地支六合": 0, "地支三合": 2,
                                 "地支六冲": 1, "地支三刑": 1, "地支六害": 0},
      str(r3["hp-01"]["counts"]))
check("C1 HP2 互定位=偏财/七杀（庚克甲：甲为庚财、庚为甲杀）",
      (r3["hp-02"]["main"]["a_in_b"]["god"], r3["hp-02"]["main"]["b_in_a"]["god"]) == ("偏财", "七杀"))
check("C1 HP3 日支=六冲（辰戌夫妻宫冲）、生肖=自刑（辰辰同支自刑）",
      r3["hp-03"]["ri_zhi"]["relation"] == "六冲" and r3["hp-03"]["sheng_xiao"]["relation"] == "自刑",
      r3["hp-03"]["ri_zhi"]["relation"] + "/" + r3["hp-03"]["sheng_xiao"]["relation"])
check("C1 HP4 倾向=相冲（-6）",
      r3["hp-04"]["tendency"] == "相冲", str(r3["hp-04"]["scores"]["total"]))

r4 = h.compute("1979-01-18 08:00", "1993-08-12 14:00")
check("C2 HP1 五合=5（含反向：戊癸×2、乙庚×3 双向命中）",
      r4["hp-01"]["counts"]["天干五合"] == 5 and r4["hp-01"]["counts"]["地支六合"] == 2
      and r4["hp-01"]["counts"]["地支六冲"] == 1,
      str(r4["hp-01"]["counts"]))
check("C2 HP3 日支=三合（酉丑金局半合）、纳音=相克（天上火-剑锋金）",
      r4["hp-03"]["ri_zhi"]["relation"] == "三合" and r4["hp-03"]["nayin"]["relation"] == "相克",
      r4["hp-03"]["ri_zhi"]["relation"] + "/" + r4["hp-03"]["nayin"]["relation"])
check("C2 HP4 倾向=相合（12）",
      r4["hp-04"]["tendency"] == "相合", str(r4["hp-04"]["scores"]["total"]))

r5 = h.compute("1985-06-15", "1987-07-07 14:00")
check("C3 HP1 counts=五合3/克1/六合1/三合2/六冲3/三刑2/六害2（午午同支自刑、子卯无礼）",
      r5["hp-01"]["counts"] == {"天干五合": 3, "天干相克": 1, "地支六合": 1, "地支三合": 2,
                                 "地支六冲": 3, "地支三刑": 2, "地支六害": 2},
      str(r5["hp-01"]["counts"]))
check("C3 HP2 互定位=偏印/食神",
      (r5["hp-02"]["main"]["a_in_b"]["god"], r5["hp-02"]["main"]["b_in_a"]["god"]) == ("偏印", "食神"))
check("C3 HP3 日支=三合（酉巳金局半合）",
      r5["hp-03"]["ri_zhi"]["relation"] == "三合", r5["hp-03"]["ri_zhi"]["relation"])

# ============================ 2. 十神互定位手算核对（m1 语义：ten_god(日主,他干)） ============================
check("十神手算：甲日见庚=七杀、庚日见甲=偏财",
      m1.ten_god("甲", "庚") == "七杀" and m1.ten_god("庚", "甲") == "偏财")
check("十神手算：甲日见癸=正印、癸日见甲=伤官",
      m1.ten_god("甲", "癸") == "正印" and m1.ten_god("癸", "甲") == "伤官")
check("十神手算：丙日见丁=劫财、戊日见乙=正官（异阴阳克我）",
      m1.ten_god("丙", "丁") == "劫财" and m1.ten_god("戊", "乙") == "正官")
check("hp-02 简表：年干/月干/日支主气 6 项互定位齐全",
      len(r1["hp-02"]["brief"]["a_in_b"]) == 3 and len(r1["hp-02"]["brief"]["b_in_a"]) == 3)

# ============================ 3. 无时柱双盘 2 例 ============================
u1 = get("U1", "1985-06-15")
check("无时柱例1：日柱照常=乙酉（与时辰无关），时柱双候选=早子丙子/晚子戊子",
      u1["pillars"]["day"] == "乙酉" and u1["pillars"]["hour"] is None and u1["hour_unknown"]
      and [c["hour"] for c in u1["hour_candidates"]] == ["丙子", "戊子"],
      str([c["hour"] for c in u1["hour_candidates"]]))
u2 = get("U2", "1990-01-01")
check("无时柱例2：日柱=丙寅，双候选=早子戊子/晚子庚子（丙日起戊子、丁日庚子居）",
      u2["pillars"]["day"] == "丙寅" and [c["hour"] for c in u2["hour_candidates"]] == ["戊子", "庚子"],
      str([c["hour"] for c in u2["hour_candidates"]]))
check("无时柱合盘：输出 persons 带双盘标注、notes 提示双盘参考",
      "hour_candidates" in r5["persons"][0] and any("双盘参考" in n for n in r5["notes"]))

# ============================ 4. 冲合计数规则边界 ============================
check("六合双向：子丑与丑子同命中（无序对去重）",
      h._pair_rel("子", "丑", h.LIU_HE, "") and h._pair_rel("丑", "子", h.LIU_HE, "")
      and not h._pair_rel("子", "辰", h.LIU_HE, ""))
check("三刑表：寅巳申三字两两成刑（无恩之刑）、辰辰自刑",
      ("寅", "巳") in h.SAN_XING and ("巳", "申") in h.SAN_XING and ("申", "寅") in h.SAN_XING
      and ("辰", "辰") in h.SAN_XING)
check("六害表：子未、丑午、申亥",
      ("子", "未") in h.LIU_HAI and ("丑", "午") in h.LIU_HAI and ("申", "亥") in h.LIU_HAI)
check("三合半合同局：寅午戌任一两字互属火局",
      h._sanhe_rel("寅", "午") == "火" and h._sanhe_rel("戌", "午") == "火" and h._sanhe_rel("子", "辰") == "水"
      and h._sanhe_rel("寅", "申") is None)
check("天干双向：甲×己 与 己×甲 均判五合化土",
      (h.WU_HE.get(("甲", "己")) or h.WU_HE.get(("己", "甲"))) == "土")
check("C1 六冲去重：辰戌位置命中 3 次只计 1（与 oracle 无序对口径同）",
      r3["hp-01"]["counts"]["地支六冲"] == 1 and len(r3["hp-01"]["pairs"]["地支六冲"]) == 1)
check("C1 辰辰：同支自刑优先于同局半合（oracle 同口径：辰午酉亥同支报刑）",
      ("辰", "辰") in h.SAN_XING and any("辰辰同支相刑" in x["desc"] for x in r3["hp-01"]["pairs"]["地支三刑"]))

# ============================ 5. 扩展：hp-05/06/07 与幂等 ============================
r5y = h.compute("1990-01-01 10:00", "1995-06-15 08:00", year=2028)
check("hp-05 流年 2028（戊申）：输出 太岁/引动事件/倾向 结构齐全",
      "liunian_gz" in r5y["hp-05"] and r5y["hp-05"]["liunian_gz"] == "戊申"
      and r5y["hp-05"]["tendency"] in ("顺", "平", "阻") and len(r5y["hp-05"]["events"]) >= 4,
      str(r5y["hp-05"]["tendency"]))
r6 = h.hp06("姻缘代占女测男", __import__("datetime").datetime(2026, 8, 16, 10, 0))
check("hp-06 六爻测事：用神规则表命中（女测男官鬼）、引擎为接线或桩位",
      r6["use_god"] == "官鬼爻（女测男以官鬼为夫）" and r6.get("engine") in
      ("l3_liuyao.compute（时间起卦·农历）", "桩位"),
      str(r6.get("engine")))
r7 = h.hp07(get("S", "1985-06-15"), "女", 2026, h.load_nayin())
check("hp-07 单盘代占：夫妻宫=酉、官星命中、5 年应期窗口结构齐全",
      r7["fuqigong"]["day_zhi"] == "酉" and "hits" in r7["guan_cai"] and "window" in r7["yingqi"])
check("compute 幂等：同输入两次调用 JSON 完全一致",
      json.dumps(h.compute("1990-01-01 10:00", "1995-06-15 08:00"), ensure_ascii=False, sort_keys=True)
      == json.dumps(r1, ensure_ascii=False, sort_keys=True))
check("免责声明：hp-04 与顶层均含『规则启发式，非神断』",
      "非神断" in r1["hp-04"]["disclaimer"] and "非神断" in r1["disclaimer"])

# ============================ 6. 对抗审查返工新增（2026-08-16） ============================
# 重要1：hp-06 六亲键名修复（l3_liuyao lines 键为 qin，实测"父母"曾读成 null）
r6b = h.hp06("求财", __import__("datetime").datetime(2026, 8, 16, 10, 0))
check("hp-06 六亲非空：qin 键修复（l3_liuyao lines.qin）",
      r6b.get("engine") == "l3_liuyao.compute（时间起卦·农历）" and r6b.get("liuqin")
      and all(x["qin"] for x in r6b["liuqin"]), str(r6b.get("liuqin"))[:120])
# 重要3+一般2：三刑三字俱全口径（《三命通会》+oracle 实测）——寅巳两字按六害、三字俱全按刑
r_x1 = h.compute("1986-02-06 10:00", "1989-06-15 10:00")  # 池={寅,巳,午} 无申
check("寅巳两字（池无申）：判六害不判三刑（oracle 实测相害口径）",
      r_x1["hp-01"]["counts"]["地支六害"] == 1 and r_x1["hp-01"]["counts"]["地支三刑"] == 0
      and any("寅巳六害" in x["desc"] for x in r_x1["hp-01"]["pairs"]["地支六害"]),
      str(r_x1["hp-01"]["counts"]))
r_x2 = h.compute("1974-02-20 10:00", "2001-08-12 10:00")  # 池={寅,巳,辰,申,未} 寅巳申俱全
check("寅巳申三字俱全：寅巳判无恩之刑（oracle 实测三字齐全报刑口径）",
      r_x2["hp-01"]["counts"]["地支三刑"] >= 1 and r_x2["hp-01"]["counts"]["地支六害"] == 0
      and any("无恩之刑" in x["desc"] for x in r_x2["hp-01"]["pairs"]["地支三刑"]),
      str(r_x2["hp-01"]["counts"]))
check("A2 三刑=2 保持（寅巳申池含申→寅巳仍刑，午午自刑）",
      r2["hp-01"]["counts"]["地支三刑"] == 2, str(r2["hp-01"]["counts"]["地支三刑"]))
check("HP1_ALT 声明优先级链+三字俱全口径（一般2）",
      "三字俱全" in h.HP1_ALT and "六合>同支自刑>三合半合>六冲>三刑（三字俱全）>六害" in h.HP1_ALT)
# 一般1：hp-02 subject 字段语义（被定位方/视方）
check("hp-02 subject 语义：a_in_b.subject=A、viewed_by=B（B 视 A）",
      r1["hp-02"]["main"]["a_in_b"]["subject"] == "A 日干"
      and r1["hp-02"]["main"]["a_in_b"]["viewed_by"].startswith("B")
      and r1["hp-02"]["main"]["b_in_a"]["subject"] == "B 日干"
      and r1["hp-02"]["main"]["b_in_a"]["viewed_by"].startswith("A"))
# 一般3：hp-07 夫妻宫补六害（与 hp-03 一致逻辑）
r7b = h.hp07(get("S7", "1986-02-06 10:00"), "女", 2026, h.load_nayin())
check("hp-07 夫妻宫含六害检查（日支巳×年/月支寅，两字寅巳按六害）",
      any(x["rel"] == "六害" and x["zhi"] == "寅" for x in r7b["fuqigong"]["zhi_rels"])
      and all(x["rel"] != "三刑" for x in r7b["fuqigong"]["zhi_rels"]),
      str(r7b["fuqigong"]["zhi_rels"])[:160])
# 重要2：天干合对拍解析修复（parse_oracle_gan 实测格式 8/8 命中）
_od = {"detail": ["天干有癸戊甲日乙年无情之合", "天干有辛丙甲日乙日威制之合", "天干有丁壬乙日甲月淫匿之合",
                  "天干有乙庚乙日甲月仁义之合", "天干有己甲甲日乙年中正之合", "天干有甲己乙日甲月中正之合",
                  "天干有丙辛甲日乙年威制之合", "天干有戊癸乙日甲时无情之合"]}
check("parse_oracle_gan 实测格式 8/8 命中（原 0/4 死代码）",
      len(h.parse_oracle_gan(_od)) == 8 and {x["gans"] for x in h.parse_oracle_gan(_od)}
      == {"癸戊", "辛丙", "丁壬", "乙庚", "己甲", "甲己", "丙辛", "戊癸"})
# 重要2：my_side 五合提取 [-1] 修复（原 [-2] 取到「干」字）
_ms = h.my_side((1990, 1, 1, 10, 0), (1995, 6, 15, 8, 0))
check("my_side 五合提取：A1 命中己甲（原 [-2] 死代码）",
      frozenset("己甲") in _ms["wuhe"] and _ms["wuhe"] == {frozenset("己甲")}, str(_ms["wuhe"]))
# 重要3 衍生：my_side xing_pairs（cmp_case 相害豁免数据基础——oracle 并集语义，hp-r16）
_ms3 = h.my_side((2013, 2, 6, 8, 0), (2025, 5, 5, 16, 0))  # hp-r16 案例：池含申，寅巳判刑
check("my_side xing_pairs：hp-r16 案例寅巳入刑集、六害空（oracle 冗余害项豁免依据）",
      frozenset("寅巳") in _ms3["xing_pairs"] and _ms3["hai"] == set(),
      str(_ms3["xing_pairs"]) + " hai=" + str(_ms3["hai"]))

# ============================ 7. F2 修复回归（2026-09-15）：生肖 sheng_xiao 三刑环 ============================
# 修复前链：六合>自刑>三合>六冲>六害，缺三刑 → 生肖子卯落"无特殊"漏报。
# 甲子年×丁卯年（子卯无礼之刑，两字即成立，与 hp-01/ri_zhi 口径一致）。
r_sx = h.compute("1984-06-15 10:00", "1987-06-15 10:00")
check("HP3 sheng_xiao 三刑环：甲子年×丁卯年 生肖子卯相刑（无礼之刑）",
      r_sx["hp-03"]["sheng_xiao"]["relation"] == "三刑" and "无礼之刑" in r_sx["hp-03"]["sheng_xiao"]["note"],
      r_sx["hp-03"]["sheng_xiao"]["relation"] + " | " + r_sx["hp-03"]["sheng_xiao"]["note"])
# 生肖链三字俱全专项（2026-09-15 第三方复验补）：两字按相害、三字俱全按刑（与 hp-01/ri_zhi 同口径）
r_sx2 = h.compute("1974-07-05 22:13", "1989-06-15 10:00")  # 寅巳两字，两人四支池无申
check("HP3 sheng_xiao 寅巳两字（池无申）：判相害不判三刑（生肖链三字俱全口径）",
      r_sx2["hp-03"]["sheng_xiao"]["relation"] == "相害",
      r_sx2["hp-03"]["sheng_xiao"]["relation"] + " | " + r_sx2["hp-03"]["sheng_xiao"]["note"])
r_sx3 = h.compute("1974-07-05 22:13", "1989-08-15 16:00")  # 巳年申月 → 池含申
check("HP3 sheng_xiao 寅巳两字+池含申：判三刑（无恩之刑，三字俱全）",
      r_sx3["hp-03"]["sheng_xiao"]["relation"] == "三刑" and "无恩" in r_sx3["hp-03"]["sheng_xiao"]["note"],
      r_sx3["hp-03"]["sheng_xiao"]["relation"] + " | " + r_sx3["hp-03"]["sheng_xiao"]["note"])

print(f"\n断言汇总：{TOTAL} 条，PASS {TOTAL - FAILED}，FAIL {FAILED}")
sys.exit(1 if FAILED else 0)
