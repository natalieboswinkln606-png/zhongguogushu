# -*- coding: utf-8 -*-
"""gen_ganzhi.py — 儒略日→日干支，生成 1900-01-01~2100-12-31（格里高利历，不处理儒略历）。
jdn 以世界时正午为界锚定，故取整无边界差；干支编号约定甲子=0。流式写 CSV。"""
import csv, os
from datetime import date, timedelta
from rules import GAN, ZHI

BASE = os.path.dirname(os.path.abspath(__file__))

def jdn(y, m, d):  # 格里高利儒略日数（UT 正午锚）
    a = (14 - m) // 12
    y2, m2 = y + 4800 - a, m + 12 * a - 3
    return d + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4 - y2 // 100 + y2 // 400 - 32045

START, END = date(1900, 1, 1), date(2100, 12, 31)
out = os.path.join(BASE, "data", "ganzhi_days.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date", "ganzhi", "source_ref"])
    d = START
    while d <= END:
        g = (jdn(d.year, d.month, d.day) + 49) % 60   # 基准常数经 lunar-python 对拍校准
        w.writerow([d.isoformat(), GAN[g % 10] + ZHI[g % 12], "gen_ganzhi.py 儒略日公式"])
        d += timedelta(days=1)
print("written:", out)
