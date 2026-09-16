# -*- coding: utf-8 -*-
"""split_steps.py — 分解各推演步骤至独立文件供逐步核验"""
import json
import os

BASE = r"D:\shushu"
in_path = os.path.join(BASE, "temp", "random_subject_full_deduction.json")
steps_dir = os.path.join(BASE, "temp", "steps")
os.makedirs(steps_dir, exist_ok=True)

with open(in_path, encoding="utf-8") as f:
    data = json.load(f)

for key, val in data.items():
    p = os.path.join(steps_dir, f"{key}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(val, f, ensure_ascii=False, indent=2)
    print(f"Written {p}")
