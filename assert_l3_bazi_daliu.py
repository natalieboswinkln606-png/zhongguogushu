# -*- coding: utf-8 -*-
"""assert_l3_bazi_daliu.py — 大运流年流月五行独立断言（锚点手推期望值，不抄实现）。
运行：PYTHONIOENCODING=utf-8 python assert_l3_bazi_daliu.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import m1, l3_bazi_daliu as B

RES = []
def check(name, cond, detail=""):
    RES.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), name, detail)

def gz(r, k): return r["pillars"][k]["ganzhi"]

# ---- 1. 60 甲子序函数自洽（全 60 无重、双向） ----
seqs = [B.gan_zhi_seq(B.seq_gz(n)) for n in range(60)]
check("60 甲子序双向自洽：seq_gz(gan_zhi_seq(x))==x 全 60", seqs == list(range(60)),
      f"错位 {[n for n, s in enumerate(seqs) if s != n][:5]}")

# ---- 2. 锚点 2024-02-10 08:00 男（甲辰 丙寅 甲辰 戊辰，日主甲）：顺排 + 起运 + 大运 ----
r = B.compute(datetime(2024, 2, 10, 8, 0), 120.0, "男")
dl = r["dayun"]
qy = dl["qiyun"]
check("a01 男顺排（甲阳年）", dl["direction"] == "顺", dl["direction"])
check("a02 起运 8岁0月13天（真太阳时口径：EOT-14.5分→07:45，距惊蛰24天2时38分=34718分）",
      [qy["age"], qy["month"], qy["day"]] == [8, 0, 13], f"{qy}")
check("a03 大运 8 步干支丁卯起（月柱丙寅顺+1）",
      [x["ganzhi"] for x in dl["list"]] == ["丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉", "甲戌"],
      " ".join(x["ganzhi"] for x in dl["list"]))
check("a04 大运十神（甲日主：丁伤官 戊偏财 己正财 庚七杀 辛正官 壬偏印 癸正印 甲比肩）",
      [x["god"] for x in dl["list"]] == ["伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印", "比肩"],
      ",".join(x["god"] for x in dl["list"]))
check("a05 首步大运 2032-2041（起运年=交运年 2032）", dl["list"][0]["start_year"] == 2032
      and dl["list"][0]["end_year"] == 2041, f"{dl['list'][0]['start_year']}-{dl['list'][0]['end_year']}")
check("a06 交运时刻 2032-02-23 12:00（出生+8年0月13天4时）", dl["jiao_time"] == "2032-02-23 12:00", dl["jiao_time"])

# ---- 3. 同例女（阳年女 → 逆排） ----
r2 = B.compute(datetime(2024, 2, 10, 8, 0), 120.0, "女")
d2 = r2["dayun"]
check("b01 阳年女逆排（甲阳年×女）", d2["direction"] == "逆", d2["direction"])
check("b02 女起运 1岁10月16天（距上节立春 2024-02-04 16:27 间隔 5天15时18分=8118分）",
      [d2["qiyun"]["age"], d2["qiyun"]["month"], d2["qiyun"]["day"]] == [1, 10, 16], f"{d2['qiyun']}")
check("b03 女大运乙丑起（月柱丙寅逆-1）",
      [x["ganzhi"] for x in d2["list"][:4]] == ["乙丑", "甲子", "癸亥", "壬戌"],
      " ".join(x["ganzhi"] for x in d2["list"][:4]))

# ---- 4. 2000-02-05 12:00 男（庚辰 戊寅 癸巳 戊午）：顺排起运 9岁8月14天 ----
r3 = B.compute(datetime(2000, 2, 5, 12, 0), 120.0, "男")
d3 = r3["dayun"]
check("c01 起运 9岁8月14天（真太阳时11:45 距惊蛰 29天2时58分=41938分）",
      [d3["qiyun"]["age"], d3["qiyun"]["month"], d3["qiyun"]["day"]] == [9, 8, 14], f"{d3['qiyun']}")
check("c02 大运己卯起（戊寅顺）", [x["ganzhi"] for x in d3["list"][:3]] == ["己卯", "庚辰", "辛巳"],
      " ".join(x["ganzhi"] for x in d3["list"][:3]))
check("c03 大运十神（癸日主：己七杀 庚正印 辛偏印）",
      [x["god"] for x in d3["list"][:3]] == ["七杀", "正印", "偏印"], ",".join(x["god"] for x in d3["list"][:3]))

# ---- 5. 1990-01-01 10:00 男（己巳 丙子 丙寅 癸巳，阴年男 → 逆排） ----
r4 = B.compute(datetime(1990, 1, 1, 10, 0), 120.0, "男")
d4 = r4["dayun"]
check("d01 阴年男逆排", d4["direction"] == "逆", d4["direction"])
check("d02 起运 8岁3月22天（距上节大雪1989-12-07 11:21 间隔 24天22时35分=35915分）",
      [d4["qiyun"]["age"], d4["qiyun"]["month"], d4["qiyun"]["day"]] == [8, 3, 22], f"{d4['qiyun']}")
check("d03 大运乙亥起（丙子逆）", [x["ganzhi"] for x in d4["list"][:3]] == ["乙亥", "甲戌", "癸酉"],
      " ".join(x["ganzhi"] for x in d4["list"][:3]))

# ---- 6. 1990-01-01 10:00 女（阴年女 → 顺排） ----
r5 = B.compute(datetime(1990, 1, 1, 10, 0), 120.0, "女")
d5 = r5["dayun"]
check("e01 阴年女顺排", d5["direction"] == "顺", d5["direction"])
check("e02 起运 1岁6月3天（距下节小寒1990-01-05 22:33 间隔 4天12时37分=6517分）",
      [d5["qiyun"]["age"], d5["qiyun"]["month"], d5["qiyun"]["day"]] == [1, 6, 3], f"{d5['qiyun']}")
check("e03 大运丁丑起（丙子顺）", [x["ganzhi"] for x in d5["list"][:3]] == ["丁丑", "戊寅", "己卯"],
      " ".join(x["ganzhi"] for x in d5["list"][:3]))

# ---- 7. 2024-06-15 12:00 女（甲辰 庚午 庚戌 壬午，阳年女 → 逆排，起运 3岁3月29天，oracle 对拍一致） ----
r6 = B.compute(datetime(2024, 6, 15, 12, 0), 120.0, "女")
d6 = r6["dayun"]
check("f01 阳年女逆排+起运 3岁3月29天（距上节芒种2024-06-05 12:10 间隔 10天0时2分=14402分）",
      d6["direction"] == "逆" and [d6["qiyun"]["age"], d6["qiyun"]["month"], d6["qiyun"]["day"]] == [3, 3, 29],
      f"{d6['direction']} {d6['qiyun']}")
check("f02 大运己巳起（庚午逆，易安居 oracle 对拍一致）",
      [x["ganzhi"] for x in d6["list"][:3]] == ["己巳", "戊辰", "丁卯"],
      " ".join(x["ganzhi"] for x in d6["list"][:3]))

# ---- 8. 流年：2024-02-10 男 → 2024(甲辰)…2032(壬子)，立春换年口径，十神 r5 ----
ln = r["liunian"]["list"]
check("g01 流年 2024-2032 共 9 年（出生年→交运年）", len(ln) == 9 and ln[0]["year"] == 2024 and ln[-1]["year"] == 2032,
      f"{len(ln)} 年 {ln[0]['year']}-{ln[-1]['year']}")
check("g02 流年干支立春口径：2024=甲辰、2032=壬子",
      ln[0]["ganzhi"] == "甲辰" and ln[-1]["ganzhi"] == "壬子", f"{ln[0]['ganzhi']} {ln[-1]['ganzhi']}")
check("g03 流年十神（甲日主：2024甲比肩、2032壬偏印）",
      ln[0]["god"] == "比肩" and ln[-1]["god"] == "偏印", f"{ln[0]['god']} {ln[-1]['god']}")
check("g04 流年 2032 与首步大运 丁卯 归属（大运干丁对甲=伤官）",
      r["dayun"]["list"][0]["gan"] == "丁" and r["dayun"]["list"][0]["god"] == "伤官", r["dayun"]["list"][0]["god"])

# ---- 9. 流月：起运年 2032（壬年五虎遁壬寅起 12 节月），月干十神 r5 ----
ly = r["liuyue"]["liuyue"]
want = ["壬寅", "癸卯", "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑"]
check("h01 流月 2032 年 12 节月干支（壬年五虎遁）", [x["ganzhi"] for x in ly] == want,
      " ".join(x["ganzhi"] for x in ly))
check("h02 流月十神（甲日主：壬寅月壬偏印、丙午月丙食神、庚戌月庚七杀）",
      ly[0]["god"] == "偏印" and ly[4]["god"] == "食神" and ly[8]["god"] == "七杀",
      f"{ly[0]['god']} {ly[4]['god']} {ly[8]['god']}")

# ---- 9b. 流月年份 base=交运年（bd-04 修正）：2024-11-15 男 起运 7岁1月25天 交运 2032-01-09，
#          出生+起运 进位跨年（出生年+起运岁=2031 ≠ 交运年 2032）→ 流月必须用交运年 2032 壬子年（壬寅起） ----
r7 = B.compute(datetime(2024, 11, 15, 12, 0), 120.0, "男")
check("h03 流月年份进位修正（2024-11-15 男：交运 2032-01-09，非出生年+起运岁 2031）：12 节月 2032 壬子年壬寅起",
      r7["dayun"]["list"][0]["start_year"] == 2032
      and [x["ganzhi"] for x in r7["liuyue"]["liuyue"]] ==
      ["壬寅", "癸卯", "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑"],
      f"首步 {r7['dayun']['list'][0]['ganzhi']} {r7['dayun']['list'][0]['start_year']} " +
      " ".join(x["ganzhi"] for x in r7["liuyue"]["liuyue"]))

# ---- 10. 五行统计：2024-02-10 甲辰丙寅甲辰戊辰（oracle 五行16=金0木6水3火2土5 对拍一致） ----
wx = r["wuxing"]
check("i01 8 字五行（木3 土4 火1 金0 水0）", wx["gan_zhi_8"] == {"金": 0, "木": 3, "水": 0, "火": 1, "土": 4},
      str(wx["gan_zhi_8"]))
check("i02 16 项含藏干（金0 木6 水3 火2 土5，易安居 oracle 口径）",
      wx["gan_cang_16"] == {"金": 0, "木": 6, "水": 3, "火": 2, "土": 5}, str(wx["gan_cang_16"]))
check("i03 缺行提示（8 字口径缺金水）", wx["missing"] == ["金", "水"], str(wx["missing"]))
check("i04 日干甲木，寅月春木旺火相水休金囚土死",
      wx["day_master_wx"] == "木" and wx["season"] == "春" and wx["wang_shuai"] ==
      {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"}, str(wx["wang_shuai"]))

# ---- 11. 输出契约：每项 Rule-ID + 出处 ----
ids = [r["dayun"]["rule_id"], r["dayun"]["qiyun_rule_id"], r["liunian"]["rule_id"],
       r["liuyue"]["rule_id"], r["wuxing"]["rule_id"]]
check("j01 输出 JSON 每项带 Rule-ID（bd-01..05）", ids == ["bd-01", "bd-02", "bd-03", "bd-04", "bd-05"], str(ids))
check("j02 大运/五行 source 含底本出处", "渊海子平" in r["dayun"]["source"] and "三命通会" in wx["wang_shuai_source"],
      f"{r['dayun']['source']} | {wx['wang_shuai_source']}")

# ---- 12. 与 m1 内核同轨：起运节=真太阳时最近节（逆排 2024-02-10 女 → 立春） ----
check("k01 逆排起运节=立春 2024-02-04 16:27（真太阳时 07:45 之前最近节）",
      d2["jie_time"] == "2024-02-04 16:27", d2["jie_time"])

npass = sum(1 for _, ok in RES if ok)
print(f"\n断言 {npass}/{len(RES)} PASS")
sys.exit(0 if npass == len(RES) else 1)
