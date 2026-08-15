# -*- coding: utf-8 -*-
"""assert_l3_qimen.py — L3-4 奇门遁甲排盘独立断言（不改 assert_tables.py）。
覆盖：5 个易安居实测锚点全字段（定局/旬首/值符值使/九宫星门神干/月将）、
拆补定局边界（节气时刻残日/符头日/三元交界/中气定局/月将分段）、值符值使寄宫特例、错误输入。

期望值来源：易安居 zhouyi.cc 实测逐宫对拍（2026-08-16）+ ganzhi_days.csv 干支 + solar_terms.csv 节气时刻。
"""
import sys
from datetime import datetime
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from l3_qimen import compute

def pan_digest(r):
    """盘面摘要：{宫: (星,门,神,地盘干,天盘干)}，供全字段断言。"""
    return {p: (c["star"], c["door"], c["shen"], c["dipan_gan"], c["tianpan_gan"])
            for p, c in r["pan"].items()}

n = 0
def check(cond, msg):
    global n
    n += 1
    assert cond, f"断言失败 [{n}] {msg}"

# ---------- 锚点 1：2024-02-10 08:00（立春下元阳2局，甲子旬戊辰时，伏吟） ----------
r = compute(datetime(2024, 2, 10, 8, 0))
d = r["dingju"]
check(d["term"] == "立春" and d["yuan"] == "下元" and d["ju"] == 2 and d["dun"] == "阳遁", "锚点1 定局")
check(r["month_jiang"] == "亥", "锚点1 月将")
z = r["zhifu_zhishi"]
check(z["xunshou"] == "甲子" and z["yiyi"] == "戊" and z["zhifu_star"] == "天芮"
      and z["zhifu_palace"] == 2 and z["zhishi_door"] == "死门" and z["zhishi_palace"] == 6, "锚点1 值符值使")
pd1 = pan_digest(r)
want1 = {"4": ("天辅", "生门", "九地", "庚", "庚"), "9": ("天英", "伤门", "九天", "丙", "丙"),
         "2": ("天芮", "杜门", "值符", "戊", "戊辛"), "3": ("天冲", "休门", "玄武", "己", "己"),
         "7": ("天柱", "景门", "腾蛇", "癸", "癸"), "8": ("天任", "开门", "白虎", "丁", "丁"),
         "1": ("天蓬", "惊门", "六合", "乙", "乙"), "6": ("天心", "死门", "太阴", "壬", "壬")}
check(all(pd1[k] == v for k, v in want1.items()) and pd1["5"][3] == "辛", f"锚点1 盘面: {pd1}")

# ---------- 锚点 2：2024-02-10 12:00（庚午时，值符星转：芮2→4，死门飞6步落8） ----------
r = compute(datetime(2024, 2, 10, 12, 0))
z = r["zhifu_zhishi"]
check(z["zhifu_palace"] == 4 and z["zhishi_palace"] == 8, "锚点2 值符值使星转/门飞")
pd2 = pan_digest(r)
check(pd2["4"] == ("天芮", "开门", "值符", "庚", "戊辛") and pd2["9"][0] == "天柱"
      and pd2["2"][0] == "天心" and pd2["3"][0] == "天英" and pd2["7"][0] == "天蓬"
      and pd2["8"][0] == "天辅" and pd2["1"][0] == "天冲" and pd2["6"][0] == "天任"
      and pd2["2"][1] == "生门" and pd2["9"][1] == "休门" and pd2["7"][1] == "伤门", f"锚点2 盘面: {pd2}")

# ---------- 锚点 3：2024-02-10 14:00（辛未时，时干落中宫：值符标5寄坤，死门飞7步落9） ----------
r = compute(datetime(2024, 2, 10, 14, 0))
z = r["zhifu_zhishi"]
check(z["zhifu_palace"] == 5 and z["zhishi_palace"] == 9, "锚点3 时干中宫标5/门落9")
pd3 = pan_digest(r)
check(pd3["2"] == ("天芮", "惊门", "值符", "戊", "戊辛") and pd3["4"][1] == "景门"
      and pd3["9"][1] == "死门" and pd3["7"][1] == "开门" and pd3["8"][1] == "伤门"
      and pd3["1"][1] == "生门" and pd3["6"][1] == "休门" and pd3["3"][1] == "杜门", f"锚点3 盘面: {pd3}")

# ---------- 锚点 4：2024-07-01 12:00（夏至上元阴9局，甲午旬伏吟） ----------
r = compute(datetime(2024, 7, 1, 12, 0))
d = r["dingju"]
check(d["term"] == "夏至" and d["yuan"] == "上元" and d["ju"] == 9 and d["dun"] == "阴遁", "锚点4 定局")
check(r["month_jiang"] == "未", "锚点4 月将")
z = r["zhifu_zhishi"]
check(z["xunshou"] == "甲午" and z["yiyi"] == "辛" and z["zhifu_star"] == "天心"
      and z["zhifu_palace"] == 6 and z["zhishi_door"] == "开门" and z["zhishi_palace"] == 6, "锚点4 值符值使")
pd4 = pan_digest(r)
want4 = {"4": ("天辅", "杜门", "白虎", "癸", "癸"), "9": ("天英", "景门", "六合", "戊", "戊"),
         "2": ("天芮", "死门", "太阴", "丙", "丙壬"), "3": ("天冲", "伤门", "玄武", "丁", "丁"),
         "7": ("天柱", "惊门", "腾蛇", "庚", "庚"), "8": ("天任", "生门", "九地", "己", "己"),
         "1": ("天蓬", "休门", "九天", "乙", "乙"), "6": ("天心", "开门", "值符", "辛", "辛")}
check(all(pd4[k] == v for k, v in want4.items()), f"锚点4 盘面: {pd4}")

# ---------- 锚点 5：2024-07-01 14:00（乙未时：星心6→1，值使开逆飞1步落中宫标5寄坤2） ----------
r = compute(datetime(2024, 7, 1, 14, 0))
z = r["zhifu_zhishi"]
check(z["zhifu_palace"] == 1 and z["zhishi_palace"] == 5, "锚点5 值符星转/值使中宫")
pd5 = pan_digest(r)
check(pd5["1"] == ("天心", "伤门", "值符", "乙", "辛") and pd5["2"][0] == "天英"
      and pd5["4"][0] == "天冲" and pd5["7"][0] == "天芮" and pd5["7"][4] == "丙壬"
      and pd5["9"][0] == "天辅" and pd5["8"][0] == "天蓬" and pd5["6"][0] == "天柱"
      and pd5["3"][0] == "天任" and pd5["2"][1] == "开门" and pd5["7"][1] == "休门"
      and pd5["1"][2] == "值符" and pd5["6"][2] == "腾蛇" and pd5["9"][2] == "白虎", f"锚点5 盘面: {pd5}")

# ---------- 定局边界：节气时刻残日（立春后符头前 → 上元） ----------
r = compute(datetime(2024, 2, 4, 18, 0))  # 立春 16:27 后、2-5 己亥符头前
check(r["dingju"]["term"] == "立春" and r["dingju"]["yuan"] == "上元" and r["dingju"]["ju"] == 8, "残日=符头元前一元(上元8局)")
r = compute(datetime(2024, 2, 4, 16, 0))  # 立春时刻前 → 大寒（F=1-21 甲申中元，2-4 距 F 14 天 → 中+2=上元）
check(r["dingju"]["term"] == "大寒" and r["dingju"]["yuan"] == "上元" and r["dingju"]["ju"] == 3, "节气时刻前属上一节气(大寒上元3局)")

# ---------- 定局边界：符头日当天与三元交界（每 5 天一换） ----------
r = compute(datetime(2024, 2, 5, 12, 0))  # 2-5 己亥 = 中元符头当日
check(r["dingju"]["yuan"] == "中元" and r["dingju"]["ju"] == 5, "符头日=该符头元(中元5局)")
r = compute(datetime(2024, 3, 16, 12, 0))  # 2-9 甲辰(下元)+? → 3-15 己卯? 用节气归属验证 3-16 仍在立春元内
check(r["dingju"]["term"] == "惊蛰", "3-16 属惊蛰")  # 惊蛰 3-5，3-16 在 3-5~3-20 惊蛰元内
r = compute(datetime(2024, 3, 11, 12, 0))  # 3-11 甲戌 = 下元符头 → 惊蛰下元4局
check(r["dingju"]["term"] == "惊蛰" and r["dingju"]["yuan"] == "下元" and r["dingju"]["ju"] == 4, "符头甲戌=下元(惊蛰4局)")

# ---------- 定局边界：中气定局（夏至当日残日 → 中元；6-24 己未符头 → 下元） ----------
r = compute(datetime(2024, 6, 21, 12, 0))  # 夏至 04:51 后、6-24 己未符头前 = 残日
check(r["dingju"]["term"] == "夏至" and r["dingju"]["yuan"] == "中元" and r["dingju"]["ju"] == 3, "夏至残日=中元阴3局")
r = compute(datetime(2024, 6, 24, 12, 0))  # 6-24 己未 = 下元符头当日
check(r["dingju"]["yuan"] == "下元" and r["dingju"]["ju"] == 6, "夏至 6-24 符头日=下元阴6局")

# ---------- 月将分段（小寒子/立春亥/惊蛰戌…） ----------
check(compute(datetime(2024, 2, 4, 16, 0))["month_jiang"] == "子", "月将：大寒后立春前=子")
check(compute(datetime(2024, 2, 4, 18, 0))["month_jiang"] == "亥", "月将：立春后=亥")
check(compute(datetime(2024, 7, 5, 12, 0))["month_jiang"] == "未", "月将：芒种~小暑=未")
check(compute(datetime(2024, 7, 7, 12, 0))["month_jiang"] == "午", "月将：小暑后=午")

# ---------- 错误输入（复用 m1 校验） ----------
check("error" in compute(datetime(1948, 12, 31, 12, 0)), "越界报错")
check("error" in compute(datetime(2024, 2, 10, 8, 0, 30)), "秒精度报错")
check("error" in compute(datetime(2024, 2, 10, 8, 0), lon=181.0), "经度越界报错")

print(f"assert_l3_qimen.py 断言 {n} 条全部通过")
