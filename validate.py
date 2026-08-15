# -*- coding: utf-8 -*-
"""validate.py — CSV→SQLite（表名=CSV 名）；重复/格式/范围检测；生成仲裁日志空表。"""
import csv, os, re, sqlite3
from rules import GAN, ZHI

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
JIAZI = set(GAN[i % 10] + ZHI[i % 12] for i in range(60))
GZ, DZ = set(GAN), set(ZHI)
SCHEMA = {  # csv: 主键列（元组=复合主键）
    "nayin.csv": "id", "canggan.csv": "dizhi", "bagong.csv": ("palace", "gua_name"),
    "najia.csv": "gua", "changsheng.csv": ("tiangan", "stage"),
    "solar_terms_template.csv": ("year", "term_index"),
    "shuowang_template.csv": ("year", "month", "is_ruen", "lunar_year"),
    "shuowang.csv": ("year", "month", "is_ruen", "lunar_year"), "ganzhi_days.csv": "date",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
db = sqlite3.connect(os.path.join(DATA, "shushu.db"))
problems = []
for fn, pk in SCHEMA.items():
    name = fn[:-4]
    rows = []
    with open(os.path.join(DATA, fn), encoding="utf-8") as f:
        dr = csv.DictReader(f)
        cols = dr.fieldnames
        for r in dr:
            if r[cols[0]].startswith("#"):   # 跳过注释行
                continue
            rows.append(r)
    pks = ','.join(pk) if isinstance(pk, tuple) else pk
    db.execute(f"DROP TABLE IF EXISTS {name}")   # 先删再建：旧表无主键也能重建，保证幂等
    db.execute(f"CREATE TABLE {name} ({', '.join(c+' TEXT' for c in cols)}, PRIMARY KEY ({pks}))")
    db.executemany(f"INSERT OR REPLACE INTO {name} VALUES ({','.join('?'*len(cols))})",
                   [[r[c] for c in cols] for r in rows])
    seen = {}
    for r in rows:
        key = tuple(r[c] for c in pk) if isinstance(pk, tuple) else (r[pk],)
        if key in seen:
            problems.append(f"{name} 重复主键 {key}")
        seen[key] = 1
    if name == "ganzhi_days":
        for r in rows:
            if not (DATE_RE.match(r["date"]) and 1900 <= int(r["date"][:4]) <= 2100):
                problems.append(f"ganzhi_days 日期非法/越界 {r['date']}")
            if r["ganzhi"] not in JIAZI:
                problems.append(f"ganzhi_days 干支非法 {r['ganzhi']}")
    elif name == "nayin":
        for r in rows:
            if len(r["ganzhi_pair"]) != 4:
                problems.append(f"nayin 干支对格式非法 {r['ganzhi_pair']}")
    elif name == "canggan":
        for r in rows:
            if r["dizhi"] not in DZ or not set(r["canggan_list"]) <= GZ:
                problems.append(f"canggan 非法 {r['dizhi']}={r['canggan_list']}")
    elif name == "changsheng":
        for r in rows:
            if r["tiangan"] not in GZ or r["dizhi"] not in DZ:
                problems.append(f"changsheng 非法 {r['tiangan']} {r['dizhi']}")
db.commit()
db.close()
log = os.path.join(DATA, "arbitration_log.csv")
if not os.path.exists(log):  # 只建缺失文件；已存在则保留 M1 起累积的仲裁记录，绝不重写清空
    with open(log, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "field", "value_a", "value_b", "arbiter", "decision", "reason"])
        w.writerow(["# 空表：仲裁记录载体（剔除三态：拒绝/alt 标注/schema 缺省）"])
print("problems:", len(problems))
for p in problems[:20]:
    print(" ", p)
