# -*- coding: utf-8 -*-
"""assert_ephemeris_ext.py — 动态星历与超界扩展引擎断言套件。
严格验证：
1. 1948、2024、2101 年动态计算的 24 节气与 data/solar_terms.csv 的分钟级偏差（绝对偏差 <= 2 分钟）。
2. 1900-2100 年间 100 个随机日期的 JDN 干支与 data/ganzhi_days.csv 的吻合率（100% 一致，0 误差）。
3. 古代历史日期四柱推演（1644-04-25 崇祯殉国日、1893-12-26 毛润之诞辰）及远期 2150 年推演正确性。
4. 智能混合路由 (Hybrid Routing) 边界流向与血统标记 (provenance / is_extrapolated)。
5. 代数求根与 40 步二分求根秒级一致性。

运行方式：PYTHONIOENCODING=utf-8 python assert_ephemeris_ext.py
全部 PASS 时退出码为 0。
"""

import csv
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ephemeris_ext import (
    TERMS_24,
    calc_jdn,
    get_solar_term_ext,
    get_solar_terms_for_year,
    get_ganzhi_day_ext,
    resolve_solar_term,
    resolve_ganzhi_day,
    compute_four_pillars_ext,
    solve_solar_term_algebraic,
    solve_solar_term_bisection,
)
import m1

BASE = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(BASE, "report", "ephemeris_ext_report.txt")

RES = []


def check(name: str, cond: bool, detail: str = ""):
    status = "PASS" if cond else "FAIL"
    RES.append((name, bool(cond), detail))
    print(f"{status:4s}  {name}  {detail}")


def main():
    print("=" * 70)
    print("【突破点 2：动态星历与超界扩展引擎 (Ephemeris Extension) 全量断言】")
    print("=" * 70)

    # ------------------------------------------------------------------------
    # 模块 1：1948、2024、2101 年 24 节气分钟级偏差验证 (<= 2 分钟)
    # ------------------------------------------------------------------------
    print("\n--- 1. 动态节气与 solar_terms.csv 偏差断言 (1948, 2024, 2101) ---")
    csv_terms_path = os.path.join(BASE, "data", "solar_terms.csv")
    with open(csv_terms_path, encoding="utf-8") as f:
        csv_terms = {(int(r["year"]), r["term"]): r["datetime"] for r in csv.DictReader(f)}

    for y in [1948, 2024, 2101]:
        calc_terms = get_solar_terms_for_year(y)
        check(f"年份 {y} 节气计算返回 24 项", len(calc_terms) == 24, f"len={len(calc_terms)}")

        max_raw_diff = 0.0
        max_round_diff = 0.0
        year_all_pass = True

        for item in calc_terms:
            t_name = item.term
            csv_dt_str = csv_terms.get((y, t_name))
            if not csv_dt_str:
                year_all_pass = False
                check(f"{y}-{t_name} 表值存在", False, "缺失")
                continue

            csv_dt = datetime.strptime(csv_dt_str, "%Y-%m-%d %H:%M")
            calc_dt = item.dt

            # 原始秒级偏差（分钟）
            raw_diff = abs((calc_dt - csv_dt).total_seconds()) / 60.0
            if raw_diff > max_raw_diff:
                max_raw_diff = raw_diff

            # 四舍五入到分钟偏差（>=30秒进位）
            calc_round = (calc_dt + timedelta(seconds=30)).replace(second=0, microsecond=0)
            round_diff = abs((calc_round - csv_dt).total_seconds()) / 60.0
            if round_diff > max_round_diff:
                max_round_diff = round_diff

            if raw_diff > 2.0:
                year_all_pass = False
                check(f"{y}-{t_name} 偏差 <= 2 分钟", False, f"差 {raw_diff:.2f} 分（算 {calc_dt} vs 表 {csv_dt_str}）")

        check(
            f"{y} 年 24 节气全量与 CSV 绝对偏差 <= 2 分钟",
            year_all_pass and max_raw_diff <= 2.0,
            f"最大秒级差 {max_raw_diff:.2f} 分，舍入差 {max_round_diff:.2f} 分"
        )

    # ------------------------------------------------------------------------
    # 模块 2：1900-2100 年间 100 个随机日期的 JDN 干支一致性验证 (100% 吻合)
    # ------------------------------------------------------------------------
    print("\n--- 2. JDN 连续干支与 ganzhi_days.csv 100 随机样本对拍 ---")
    days_csv_path = os.path.join(BASE, "data", "ganzhi_days.csv")
    with open(days_csv_path, encoding="utf-8") as f:
        days_rows = list(csv.DictReader(f))

    # 固定随机种子，确保测试可复现
    random.seed(42)
    sample_100 = random.sample(days_rows, 100)

    match_count = 0
    mismatch_cases = []
    for r in sample_100:
        d_str = r["date"]
        want_gz = r["ganzhi"]
        y, m, d = map(int, d_str.split("-"))
        got_res = get_ganzhi_day_ext(y, m, d)
        got_gz = str(got_res)
        if got_gz == want_gz:
            match_count += 1
        else:
            mismatch_cases.append(f"{d_str}: 算 {got_gz} vs 表 {want_gz}")

    check(
        "1900-2100 年 100 个随机日期 JDN 干支 100% 吻合 (0 误差)",
        match_count == 100,
        f"吻合 {match_count}/100" + (f"，错例: {mismatch_cases[:3]}" if mismatch_cases else "")
    )

    # 边界日期校验
    boundary_dates = [
        ("1900-01-01", "甲戌"),
        ("2000-02-29", "丁巳"),  # 世纪闰年（经 ganzhi_days.csv 与 JDN 校验一致）
        ("2024-02-29", "癸亥"),  # 普通闰年
        ("2100-12-31", "丁未"),  # 终值边界
    ]
    for d_str, want_gz in boundary_dates:
        y, m, d = map(int, d_str.split("-"))
        got_gz = str(get_ganzhi_day_ext(y, m, d))
        check(f"JDN 边界日期 {d_str} 干支={want_gz}", got_gz == want_gz, f"得 {got_gz}")

    # ------------------------------------------------------------------------
    # 模块 3：古代历史日期与远期四柱推演正确性验证
    # ------------------------------------------------------------------------
    print("\n--- 3. 历史与远期四柱推演断言 ---")

    # 案例 A: 1644-04-25 崇祯甲申殉国日（明思宗十七年三月十九日丁未）
    cz = compute_four_pillars_ext("1644-04-25 06:00", lon=116.4, gender="男")
    cz_p = cz["pillars"]
    cz_tg = cz["ten_gods"]

    check(
        "1644-04-25 崇祯殉国日 年柱=甲申 (立春后)",
        cz_p["year"]["ganzhi"] == "甲申",
        f"得 {cz_p['year']['ganzhi']}"
    )
    check(
        "1644-04-25 崇祯殉国日 月柱=戊辰 (清明后)",
        cz_p["month"]["ganzhi"] == "戊辰",
        f"得 {cz_p['month']['ganzhi']}"
    )
    check(
        "1644-04-25 崇祯殉国日 日柱=丁未 (JDN推算丁未日)",
        cz_p["day"]["ganzhi"] == "丁未",
        f"得 {cz_p['day']['ganzhi']}"
    )
    check(
        "1644-04-25 崇祯殉国日 时柱=癸卯 (06:00卯时)",
        cz_p["hour"]["ganzhi"] == "癸卯",
        f"得 {cz_p['hour']['ganzhi']}"
    )
    check(
        "1644-04-25 崇祯殉国日 血统标记=astronomical_extrapolated 且 is_extrapolated=True",
        cz["provenance"] == "astronomical_extrapolated" and cz["is_extrapolated"] is True,
        f"prov={cz['provenance']} ext={cz['is_extrapolated']}"
    )
    check(
        "1644-04-25 崇祯殉国日 十神推演（日干丁 年正印/月伤官/时七杀）",
        cz_tg["day_master"] == "丁"
        and cz_tg["stems"]["year"] == "正印"
        and cz_tg["stems"]["month"] == "伤官"
        and cz_tg["stems"]["hour"] == "七杀",
        f"stems={cz_tg['stems']}"
    )

    # 案例 B: 1893-12-26 毛润之诞辰（癸巳年甲子月丁酉日甲辰时）
    mz = compute_four_pillars_ext("1893-12-26 08:00", lon=112.9, gender="男")
    mz_p = mz["pillars"]
    mz_tg = mz["ten_gods"]

    check(
        "1893-12-26 毛润之诞辰 年柱=癸巳",
        mz_p["year"]["ganzhi"] == "癸巳",
        f"得 {mz_p['year']['ganzhi']}"
    )
    check(
        "1893-12-26 毛润之诞辰 月柱=甲子 (大雪后子月，五虎遁癸年甲子)",
        mz_p["month"]["ganzhi"] == "甲子",
        f"得 {mz_p['month']['ganzhi']}"
    )
    check(
        "1893-12-26 毛润之诞辰 日柱=丁酉 (JDN推算丁酉日)",
        mz_p["day"]["ganzhi"] == "丁酉",
        f"得 {mz_p['day']['ganzhi']}"
    )
    check(
        "1893-12-26 毛润之诞辰 时柱=甲辰 (08:00辰时，五鼠遁丁日甲辰)",
        mz_p["hour"]["ganzhi"] == "甲辰",
        f"得 {mz_p['hour']['ganzhi']}"
    )
    check(
        "1893-12-26 毛润之诞辰 血统标记=astronomical_extrapolated 且 is_extrapolated=True",
        mz["provenance"] == "astronomical_extrapolated" and mz["is_extrapolated"] is True,
        f"prov={mz['provenance']} ext={mz['is_extrapolated']}"
    )
    check(
        "1893-12-26 毛润之诞辰 十神推演（日干丁 年七杀/月正印/时正印）",
        mz_tg["day_master"] == "丁"
        and mz_tg["stems"]["year"] == "七杀"
        and mz_tg["stems"]["month"] == "正印"
        and mz_tg["stems"]["hour"] == "正印",
        f"stems={mz_tg['stems']}"
    )

    # 案例 C: 2150-02-05 远期外推
    f2150 = compute_four_pillars_ext("2150-02-05 12:00", lon=120.0, gender="男")
    check(
        "2150-02-05 远期四柱计算成功且标记外推",
        f2150["provenance"] == "astronomical_extrapolated" and f2150["is_extrapolated"] is True,
        f"prov={f2150['provenance']} y={f2150['pillars']['year']['ganzhi']}"
    )

    # 案例 D: 2024-02-10 08:00 锚点区间对比 m1.compute 既有基座
    m1_dt = datetime(2024, 2, 10, 8, 0)
    res_m1 = m1.compute(m1_dt, 120.0)
    res_ext = compute_four_pillars_ext(m1_dt, 120.0, gender="男")

    p_m1 = [res_m1["pillars"][k]["ganzhi"] for k in ["year", "month", "day", "hour"]]
    p_ext = [res_ext["pillars"][k]["ganzhi"] for k in ["year", "month", "day", "hour"]]
    check("2024-02-10 表内锚点与 m1.compute 四柱 100% 一致", p_m1 == p_ext, f"m1={p_m1} ext={p_ext}")
    check(
        "2024-02-10 表内锚点 provenance=official_csv_anchor 且 is_extrapolated=False",
        res_ext["provenance"] == "official_csv_anchor" and res_ext["is_extrapolated"] is False,
        f"prov={res_ext['provenance']}"
    )

    # ------------------------------------------------------------------------
    # 模块 4：智能混合路由 (Hybrid Routing) 边界行为断言
    # ------------------------------------------------------------------------
    print("\n--- 4. 智能混合路由 (Hybrid Routing) 边界流向断言 ---")
    st_2024 = resolve_solar_term(2024, "立春")
    check(
        "resolve_solar_term(2024, 立春) 命中 official_csv_anchor",
        st_2024.provenance == "official_csv_anchor" and st_2024.is_extrapolated is False,
        f"prov={st_2024.provenance}"
    )

    st_1644 = resolve_solar_term(1644, "立春")
    check(
        "resolve_solar_term(1644, 立春) 外推 astronomical_extrapolated",
        st_1644.provenance == "astronomical_extrapolated" and st_1644.is_extrapolated is True,
        f"prov={st_1644.provenance} dt={st_1644.strftime('%Y-%m-%d %H:%M')}"
    )

    st_2150 = resolve_solar_term(2150, "立春")
    check(
        "resolve_solar_term(2150, 立春) 外推 astronomical_extrapolated",
        st_2150.provenance == "astronomical_extrapolated" and st_2150.is_extrapolated is True,
        f"prov={st_2150.provenance} dt={st_2150.strftime('%Y-%m-%d %H:%M')}"
    )

    gd_2024 = resolve_ganzhi_day("2024-02-10")
    check(
        "resolve_ganzhi_day(2024-02-10) 命中 official_csv_anchor",
        gd_2024.provenance == "official_csv_anchor" and gd_2024.is_extrapolated is False,
        f"prov={gd_2024.provenance}"
    )

    gd_1644 = resolve_ganzhi_day("1644-04-25")
    check(
        "resolve_ganzhi_day(1644-04-25) 外推 astronomical_extrapolated",
        gd_1644.provenance == "astronomical_extrapolated" and gd_1644.is_extrapolated is True,
        f"prov={gd_1644.provenance} gz={gd_1644}"
    )

    # ------------------------------------------------------------------------
    # 模块 5：代数求根与 40 步二分求根一致性断言
    # ------------------------------------------------------------------------
    print("\n--- 5. 代数求根 vs 40 步二分求根一致性断言 ---")
    for test_y, test_t in [(2024, "立春"), (1644, "清明"), (2101, "冬至")]:
        dt_alg = solve_solar_term_algebraic(test_y, test_t)
        dt_bis = solve_solar_term_bisection(test_y, test_t, steps=40)
        sec_diff = abs((dt_alg - dt_bis).total_seconds())
        check(
            f"{test_y} {test_t} 代数求根 vs 二分求根 偏差 < 1 秒",
            sec_diff < 1.0,
            f"差 {sec_diff:.4f} 秒（代数 {dt_alg} vs 二分 {dt_bis}）"
        )

    # ------------------------------------------------------------------------
    # 模块 6：改历连续性、异常边界与二分二至对抗断言
    # ------------------------------------------------------------------------
    print("\n--- 6. 改历连续性、异常边界与二分二至对抗断言 ---")
    # 1. 1582年公历/儒略历交替与连续性
    j_oct4 = calc_jdn(1582, 10, 4, calendar="auto")
    j_oct15 = calc_jdn(1582, 10, 15, calendar="auto")
    gz_oct4 = get_ganzhi_day_ext(1582, 10, 4, calendar="auto")
    gz_oct15 = get_ganzhi_day_ext(1582, 10, 15, calendar="auto")
    check(
        "1582-10-04 与 1582-10-15 儒略日数严格连续相差 1",
        j_oct15 - j_oct4 == 1,
        f"JDN Oct4={j_oct4} Oct15={j_oct15} diff={j_oct15 - j_oct4}"
    )
    check(
        "1582 改历前后干支连续顺延（10-04癸酉 -> 10-15甲戌）",
        gz_oct4 == "癸酉" and gz_oct15 == "甲戌",
        f"10-04={gz_oct4}, 10-15={gz_oct15}"
    )

    # 2. 1582年改历空缺日安全拦截
    phantom_caught = False
    try:
        calc_jdn(1582, 10, 5, calendar="auto")
    except ValueError as ve:
        phantom_caught = True
    check("1582-10-05 历史空缺日被安全拦截抛出 ValueError", phantom_caught)

    # 3. 超界与异常年份安全拦截
    inv_year_caught = False
    try:
        solve_solar_term_algebraic(-500, "春分")
    except ValueError:
        inv_year_caught = True
    check("负年份公元前参数被安全拦截抛出 ValueError", inv_year_caught)

    fp_err = compute_four_pillars_ext("0000-01-01 12:00")
    check("零年份四柱计算安全返回 error 字典而不是 500 崩溃", "error" in fp_err, fp_err.get("error"))

    # 4. 二分二至跨象限求根平滑无符号跳跃（春分0度、夏至90度、秋分180度、冬至270度）
    for term_name in ["春分", "夏至", "秋分", "冬至"]:
        dt_a = solve_solar_term_algebraic(2025, term_name)
        dt_b = solve_solar_term_bisection(2025, term_name)
        sec_d = abs((dt_a - dt_b).total_seconds())
        check(
            f"2025 {term_name} 跨象限二分求根收敛且与代数解偏差 <= 2 秒",
            sec_d <= 2.0,
            f"偏差 {sec_d:.4f} 秒"
        )

    # ------------------------------------------------------------------------
    # 报告与汇总输出
    # ------------------------------------------------------------------------
    pass_cnt = sum(1 for _, ok, _ in RES if ok)
    fail_cnt = sum(1 for _, ok, _ in RES if not ok)
    total_cnt = len(RES)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("动态星历与超界扩展引擎 (Ephemeris Extension) 测试报告\n")
        f.write("=" * 70 + "\n\n")
        for name, ok, detail in RES:
            f.write(f"[{'PASS' if ok else 'FAIL'}] {name} | {detail}\n")
        f.write(f"\n合计 {total_cnt} 项，PASS {pass_cnt}，FAIL {fail_cnt}\n")

    print("\n" + "=" * 70)
    print(f"测试完成: 合计 {total_cnt} 项 PASS {pass_cnt} FAIL {fail_cnt}")
    print(f"详细报告写入: {REPORT_PATH}")
    print("=" * 70)

    if fail_cnt > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
