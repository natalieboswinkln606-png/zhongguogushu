# -*- coding: utf-8 -*-
"""test_reconcile_draft.py — 测试草稿文本对账门禁"""
import json
import os
import sys

BASE = r"D:\shushu"
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import mcp_server as M

snap_path = os.path.join(BASE, "temp", "steps", "step11_snapshot.json")
with open(snap_path, encoding="utf-8") as f:
    snap = json.load(f)

# 构造标准对账草稿文本
draft = """
【命理全谱深度测算报告】

一、时空基准与四柱乾坤
@snap pillars: 乙亥/己丑/戊午/戊午 | day_master=戊
本造生于公历1996年01月22日12时10分（北京时间），出生于广东省广州市。
经真太阳时与均时差校正，当地真太阳时为11时32分，落入午时。
公历1996年1月22日处于立春之前、大寒中气之后，故年柱仍取乙亥（猪年），月柱为己丑，日柱为戊午，时柱为戊午。日主天干为戊土。
四柱纳音依次为：乙亥山头火、己丑霹雳火、戊午天上火、戊午天上火。

二、八字格局与日主旺衰
@snap wangshuai: score=77.0 level=极旺 advice=日主极旺，宜克泄耗（官杀/食伤/财星）抑其过强
日主戊土生于季冬丑月，丑中己土劫财本气透出于月干，地支坐两午火帝旺刃地，且得时柱戊午同气相助。
得令得分100分（土旺），得地得分70.0%（两逢帝旺阳刃），得势得分50.0%。
综合旺衰评分高达 77.0 分，属于极旺格局。格局依《子平真诠》月建劫财司权透干定为月劫格（用官）。用神取年柱乙木正官及亥中壬水偏财克泄耗为佳。

三、顺逆大运推演与交运流年
@snap dayun: 戊子(2001-2010) 丁亥(2011-2020) 丙戌(2021-2030) 乙酉(2031-2040) 甲申(2041-2050) 癸未(2051-2060) 壬午(2061-2070) 辛巳(2071-2080)
本造为阴年男命（乙亥年干属阴木），依“阴男阳女逆行”之铁律，大运逆排。
起运时间为 5 岁 4 个月 13 天，折合公历 2001 年 6 月交运。
八步大运依次为：
第一步：戊子 (2001-2010) 比肩
第二步：丁亥 (2011-2020) 正印
第三步：丙戌 (2021-2030) 偏印
第四步：乙酉 (2031-2040) 正官
第五步：甲申 (2041-2050) 七杀
第六步：癸未 (2051-2060) 正财
第七步：壬午 (2061-2070) 偏财
第八步：辛巳 (2071-2080) 伤官

四、神煞吉凶互参
@snap shensha: 命中劫煞、天乙贵人、国印、羊刃、将星
命带天乙贵人与国印贵人落于月柱丑土，主遇难呈祥、逢凶化吉；日支与时支双叠羊刃与将星，主个性刚决、威仪果敢。
扩展神煞库中见六秀日、十灵日、孤鸾煞、太极贵人、天厨贵人。

五、紫微斗数与三方四正
@snap ziwei.sanfang_sizheng: scope=[命宫,财帛,迁移,官禄] 命宫=癸未 木三局
命宫与身宫同在未宫，干支为癸未，五行局为木三局，紫微星落于寅宫。生年四化为乙干天机化禄、天梁化权、紫微化科、太阴化忌。
2026年流年太岁在午，斗君在丑，流年禄存在巳，擎羊在午，陀罗在辰，流年四化天同化禄、天机化权、文昌化科、廉贞化忌。

六、时家奇门与金口决
@snap qimen: dingju=大寒阳遁9局中元 zhifu_star=天禽 zhishi_door=死门
时家奇门大寒阳遁9局中元，旬首甲寅癸，值符天禽星，值使死门。
大六壬金口诀地分取卯，人元乙木，贵神午火朱雀，将神酉金从魁，地分卯木，神克将为妻动，将克干为子动。
"""

rec = M.shushu_reconcile(draft, snap)
print("Verdict:", rec["verdict"])
print("Conflicts:", len(rec["conflicts"]))
for c in rec["conflicts"]:
    print("  -> Conflict:", c)
print("Matched count:", rec["summary"]["matched_count"])

if rec["verdict"] == "PASS" and len(rec["conflicts"]) == 0:
    print("RECONCILE CHECK PASSED 100%!")
    sys.exit(0)
else:
    sys.exit(1)
