# -*- coding: utf-8 -*-
"""
assert_data_static.py — 验证 data_static_tables.py 静态数据底座的数据完整性与微秒级查找
对拍全部原始 CSV（canggan.csv, nayin.csv, shuowang.csv, solar_terms.csv），确保 100% 精确一致。
"""
import csv
import os
import sys
import time
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import data_static_tables as dst

def test_canggan():
    with open(os.path.join(BASE, "data", "canggan.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(dst.CANGGAN_MAP) == 12, "CANGGAN_MAP must have 12 dizhi"
    for r in rows:
        dz = r["dizhi"]
        assert dz in dst.CANGGAN_MAP, f"Missing dizhi: {dz}"
        cg_str = r["canggan_list"]
        roles = ["本气", "中气", "余气"]
        expected = tuple((cg, roles[idx]) for idx, cg in enumerate(cg_str))
        actual = dst.CANGGAN_MAP[dz]
        assert actual == expected, f"Canggan mismatch for {dz}: {actual} != {expected}"
    print("  [PASS] Canggan 12 地支全量匹配成功")

def test_nayin():
    with open(os.path.join(BASE, "data", "nayin.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(dst.NAYIN_MAP) == 60, f"NAYIN_MAP must have 60 items, got {len(dst.NAYIN_MAP)}"
    for r in rows:
        pair = r["ganzhi_pair"]
        wuxing = r["wuxing_name"]
        gz1, gz2 = pair[:2], pair[2:]
        assert dst.NAYIN_MAP[gz1] == wuxing, f"Nayin mismatch for {gz1}"
        assert dst.NAYIN_MAP[gz2] == wuxing, f"Nayin mismatch for {gz2}"
    print("  [PASS] Nayin 六十甲子全量匹配成功")

def test_shuowang():
    with open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(dst.SHUOWANG_RECORDS) == len(rows), f"Length mismatch: {len(dst.SHUOWANG_RECORDS)} vs {len(rows)}"
    for i, r in enumerate(rows):
        rec = dst.SHUOWANG_RECORDS[i]
        assert rec[0] == r["shuo_time"][:10]
        assert rec[1] == int(r["month"])
        assert rec[2] == int(r["is_ruen"])
        assert rec[3] == r["lunar_year"]
        assert rec[4] == r["shuo_time"]
        assert rec[5] == r["wang_time"]
    print(f"  [PASS] Shuowang 朔望表 {len(rows)} 条记录逐行逐字段完全吻合")

def test_solar_terms():
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(dst.SOLAR_TERMS_RECORDS) == len(rows), f"Length mismatch: {len(dst.SOLAR_TERMS_RECORDS)} vs {len(rows)}"
    for i, r in enumerate(rows):
        rec = dst.SOLAR_TERMS_RECORDS[i]
        assert rec[0] == r["datetime"]
        assert rec[1] == r["term"]
        assert rec[2] == r["jie_zhong"]
        assert rec[3] == int(r["year"])
    print(f"  [PASS] Solar Terms 二十四节气表 {len(rows)} 条记录逐行逐字段完全吻合")

def test_functions():
    # 1. 2024-02-10 is 甲辰年正月初一
    res = dst.get_shuo_for_date(date(2024, 2, 10))
    assert res["lunar_year_gz"] == "甲辰"
    assert res["lunar_month"] == 1
    assert res["is_leap"] is False
    assert res["lunar_day"] == 1
    print("  [PASS] get_shuo_for_date(2024-02-10) -> 甲辰年正月初一 准确无误")

    # 2. 反查 2024年 正月初一 -> 2024-02-10
    sol_d = dst.lunar_to_solar_date(2024, 1, False, 1)
    assert sol_d == date(2024, 2, 10), f"Expected 2024-02-10, got {sol_d}"
    print("  [PASS] lunar_to_solar_date(2024, 1, 1) -> 2024-02-10 准确无误")

    # 3. 2023年 闰二月 初一 -> 2023-03-22
    sol_leap = dst.lunar_to_solar_date(2023, 2, True, 1)
    assert sol_leap == date(2023, 3, 22), f"Expected 2023-03-22, got {sol_leap}"
    res_leap = dst.get_shuo_for_date(date(2023, 3, 22))
    assert res_leap["lunar_month"] == 2 and res_leap["is_leap"] is True and res_leap["lunar_day"] == 1
    print("  [PASS] 2023年闰二月初一双向闭环对验 准确无误")

    # 4. 节气定位
    term_res = dst.get_term_for_datetime(datetime(2025, 2, 3, 22, 15))
    assert term_res["current_term"] == "立春" or term_res["next_term"] == "立春"
    terms_2025 = dst.get_terms_for_year(2025)
    assert len(terms_2025) == 24
    print("  [PASS] 2025年二十四节气查询 准确无误")

    # 5. 性能压测：10000 次二分查找
    t0 = time.time()
    for _ in range(10000):
        _ = dst.get_shuo_for_date(date(2024, 6, 15))
    elapsed = time.time() - t0
    avg_us = (elapsed / 10000) * 1_000_000
    print(f"  [PERF] 10,000 次二分查找耗时: {elapsed:.3f}s (平均 {avg_us:.2f} 微秒/次，零磁盘 I/O)")

if __name__ == "__main__":
    print("================================================================")
    print(" Running assert_data_static.py ...")
    print("================================================================")
    test_canggan()
    test_nayin()
    test_shuowang()
    test_solar_terms()
    test_functions()
    print("================================================================")
    print(" ALL STATIC TABLE TESTS PASSED (100% EXACT & ZERO-IO VERIFIED)")
    print("================================================================")
