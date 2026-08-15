# -*- coding: utf-8 -*-
"""gen_solar_terms.py — 生成 solar_terms.csv（1948-2101 共 3696 行 = 154 年 × 24，流式写）。
时刻取值契约（preregister「M1 节气策略裁决」2026-08-15 用户裁决，时区一律 UTC+8）：
- 2015-2028 官方锚点段：HKO 官方分钟值（hko_minutes，PDF/XML 重复以 XML 为准，去 pdf 行），source_ref=hko_minutes
- 其余年份：lunar-python 秒级四舍五入到分钟（>=30 秒进 1 分钟），source_ref=lunar
- 2101 全年无官方锚点，notes 标注算法值
- 日期层一致性已由 solar_terms_compare.py 对拍验证（3671/3672 差 0，1979-大寒 23:59:56 跨日边界申报）"""
import csv, os
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "solar_terms_raw")
NOTE_2101 = "算法值（lunar-python，无官方锚点）"
TERMS = ["小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种",
         "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
JIE12 = {"立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"}
JZ = {"jie": "节", "zhong": "中气"}

def load(fn):
    with open(os.path.join(RAW, fn), encoding="utf-8") as f:
        return list(csv.DictReader(f))

def to_minute(sec):  # 秒级四舍五入到分钟（含跨日进位）
    return (datetime.strptime(sec, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M")

lunar = {(r["year"], r["term"]): r for r in load("lunar_terms_1948_2101.csv")}
hko = {(r["year"], r["term"]): r["datetime"] for r in load("hko_minutes_2015_2028.csv") if r["format"] != "pdf"}
assert len(lunar) == 3696 and len(hko) == 336  # 前置校验：154 年 × 24；官方锚点 336（去 pdf 96 行）
for k, r in lunar.items():  # lunar 原始 jie/zhong 标注与契约节集合一致，防集抄错
    assert JZ[r["jie_zhong"]] == ("节" if k[1] in JIE12 else "中气"), k

out = os.path.join(BASE, "data", "solar_terms.csv")
n = 0
prev = ""
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["year", "term", "jie_zhong", "datetime", "source_ref", "notes"])
    for y in range(1948, 2102):
        for t in TERMS:
            if 2015 <= y <= 2028:
                dt, src, notes = hko[(str(y), t)], "hko_minutes", ""
            else:
                dt, src = to_minute(lunar[(str(y), t)]["datetime"]), "lunar"
                notes = NOTE_2101 if y == 2101 else ""
            assert dt > prev, f"datetime 非严格递增 {y}-{t} {dt}"  # 生成即校验
            prev = dt
            w.writerow([str(y), t, JZ[lunar[(str(y), t)]["jie_zhong"]], dt, src, notes])
            n += 1
print(f"written: {out}（{n} 行）")
