# -*- coding: utf-8 -*-
"""l4_audit_ziwei.py — 紫微 oracle 缓存独立解析抽查（L4 归档，原 temp/audit_ziwei.py）。
按带内 8n 行结构从 oracle 缓存 HTML 提取星名/四化/宫支，与 l3_ziwei.compute 输出交叉验证。
实现独立手写（不 import _zw_oracle_probe）；缓存=data/l3_ziwei_oracle_cache/（抓取时快照，未入库）。
只读只测，不改任何模块。"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import l3_ziwei

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "data", "l3_ziwei_oracle_cache")


def parse(path):
    html = open(path, encoding="utf-8").read()
    i = html.find("<li class='ziweili'")
    j = html.find("zwboxdib")
    if i < 0 or j < 0:
        return None
    bands, band = [], []
    for cls, inner in re.findall(r"<li([^>]*)>(.*?)</li>", html[i:j], re.S):
        if "zweiliB" in cls:
            bands.append(band); band = []
            continue
        if "ziweili1" in cls or "ziweili5" in cls:
            continue
        band.append(inner)
    bands.append(band)
    out = {}  # zhi -> {stars, aux, sihua}
    for b in bands:
        n = len(b) // 8
        if not n or len(b) != 8 * n:
            continue
        for k in range(n):
            first = re.findall(r"<font color=(#\w+)>([^<])</font>", b[k])
            second = re.findall(r"<font color=(#\w+)>([^<])</font>", b[n + k])
            hua = re.findall(r"<font color=(#\w+)>([^<])</font>", b[3 * n + k])
            gongname = "".join(re.findall(r"<font[^>]*>([^<])</font>", b[6 * n + k]))
            zhi = re.sub(r"[\s　]", "", re.sub(r"<[^>]+>", "", b[7 * n + k]))[:1]
            if zhi not in "子丑寅卯辰巳午未申酉戌亥":
                continue
            r1 = [u for c, u in first if c.lower() == "#ff0000"]
            r2 = [u for c, u in second if c.lower() == "#ff0000"]
            names = [r1[t] + r2[t] for t in range(min(len(r1), len(r2)))]
            main14 = {"紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
                      "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}
            aux12 = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "擎羊", "陀罗", "火星", "铃星", "天马"}
            out[zhi] = {"stars": [s for s in names if s in main14],
                        "aux": [s for s in names if s in aux12],
                        "sihua": "".join(u for c, u in hua if c.lower() == "#e33fba")}
    return out if len(out) == 12 else None


CASES = [
    ("2024-02-10-08-00-r0.html", (2024, 2, 10, 8, 0), "甲辰申子辰组"),
    ("1977-01-13-12-00-r0.html", (1977, 1, 13, 12, 0), "丁巳巳酉丑组（缓存无 08:00 版，用 12:00 版）"),
    ("2025-07-25-08-00-r0.html", (2025, 7, 25, 8, 0), "乙巳巳酉丑组"),
    ("2041-10-23-10-00-r0.html", (2041, 10, 23, 10, 0), "辛酉巳酉丑组"),
    ("2000-02-05-12-00-r0.html", (2000, 2, 5, 12, 0), "庚辰申子辰组"),
    ("2016-01-23-14-00-r0.html", (2016, 1, 23, 14, 0), "丙申申子辰组"),
]
ok = True
for fname, t, tag in CASES:
    p = os.path.join(CACHE, fname)
    if not os.path.exists(p):
        print(f"缺缓存 {fname}"); ok = False; continue
    o = parse(p)
    if not o:
        print(f"解析失败 {fname}"); ok = False; continue
    o_pos = {s: z for z, info in o.items() for s in info["stars"]}
    o_aux = {s: z for z, info in o.items() for s in info["aux"]}
    r = l3_ziwei.compute(datetime(*t))
    m_pos = {s: q["zhi"] for q in r["palaces"] for s in q["stars"]}
    m_aux = {s: q["zhi"] for q in r["palaces"] for s in q["aux"]}
    diffs = []
    for s in m_pos:
        if m_pos[s] != o_pos.get(s):
            diffs.append(f"{s}:自{m_pos[s]} vs oracle{o_pos.get(s)}")
    for s in m_aux:
        if m_aux[s] != o_aux.get(s):
            diffs.append(f"{s}:自{m_aux[s]} vs oracle{o_aux.get(s)}")
    print(f"{tag} {t}: 紫微 oracle={o_pos.get('紫微')} 火星={o_aux.get('火星')} 铃星={o_aux.get('铃星')} "
          f"天魁={o_aux.get('天魁')} 禄存={o_aux.get('禄存')} 差异={diffs if diffs else '无'}")
    if diffs:
        ok = False
print("独立解析抽查:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
