# -*- coding: utf-8 -*-
"""assert_config_engine.py — 多流派与规则配置化引擎 (Configurable Schools) 独立断言脚本

断言覆盖：
1. 断言 1：默认配置下，四柱、奇门、紫微输出与原 m1.py, l3_qimen.py, l3_ziwei.py 完全一致。
2. 断言 2：zi_hour_mode="zichu" 时，23:30 输入的日柱按次日计算，而默认模式按当日计算。
3. 断言 3：ziwei_sect="zhongzhou" 时，庚年（如 1980 庚申年）四化正确变为“太阳禄/武曲权/太阴科/天同忌”。
4. 断言 4：qimen_central_palace="gen8" 时，中五宫天禽星与死门寄入艮八宫。
5. 断言 5：liuyao_analysis="advanced" 时，卦爻输出正确包含“月破/旬空/旺相休囚”。

运行方式：
PYTHONIOENCODING=utf-8 python assert_config_engine.py
全部 PASS 时退出码为 0，有任何失败时退出码为 1。
"""
from datetime import datetime
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import m1
import l3_qimen
import l3_ziwei
import l3_liuyao
from config_engine import (
    ShushuConfig,
    bazi_with_config,
    qimen_with_config,
    ziwei_with_config,
    liuyao_with_config
)

CHECKS = []

def check(name, cond):
    CHECKS.append(bool(cond))
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    assert cond, f"断言失败: {name}"


# =====================================================================
# 断言 1：默认配置下，四柱、奇门、紫微输出与原 m1.py, l3_qimen.py, l3_ziwei.py 完全一致
# =====================================================================
print("\n=== 断言 1：默认配置与 v1.0 冻结引擎 100% 逐字段一致性断言 ===")

test_cases = [
    ("2024-02-10 08:00", 120.0),
    ("2024-07-01 12:00", 120.0),
    ("2000-01-01 12:00", 120.0),
    ("1980-05-15 10:00", 120.0),
]

for dt_str, lon in test_cases:
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

    # 1. 四柱对比 (config=None 与 config=ShushuConfig())
    m1_orig = m1.compute(dt, lon)
    bazi_none = bazi_with_config(dt_str, lon, config=None)
    bazi_def = bazi_with_config(dt_str, lon, config=ShushuConfig())
    check(f"四柱默认一致性 ({dt_str}) config=None", bazi_none == m1_orig)
    check(f"四柱默认一致性 ({dt_str}) config=ShushuConfig()", bazi_def == m1_orig)

    # 2. 奇门对比
    qm_orig = l3_qimen.compute(dt, lon)
    qm_none = qimen_with_config(dt_str, lon, config=None)
    qm_def = qimen_with_config(dt_str, lon, config=ShushuConfig())
    check(f"奇门默认一致性 ({dt_str}) config=None", qm_none == qm_orig)
    check(f"奇门默认一致性 ({dt_str}) config=ShushuConfig()", qm_def == qm_orig)

    # 3. 紫微对比
    zw_orig = l3_ziwei.compute(dt, lon)
    zw_none = ziwei_with_config(dt_str, lon, "男", config=None)
    zw_def = ziwei_with_config(dt_str, lon, "男", config=ShushuConfig())
    check(f"紫微默认一致性 ({dt_str}) config=None", zw_none == zw_orig)
    check(f"紫微默认一致性 ({dt_str}) config=ShushuConfig()", zw_def == zw_orig)

    # 4. 六爻对比（时间起卦·农历）
    ly_orig = l3_liuyao.compute(dt, lon, "lunar")
    ly_none = liuyao_with_config("lunar", None, None, dt_str, config=None)
    ly_def = liuyao_with_config("lunar", None, None, dt_str, config=ShushuConfig())
    check(f"六爻时间起卦默认一致性 ({dt_str}) config=None", ly_none == ly_orig)
    check(f"六爻时间起卦默认一致性 ({dt_str}) config=ShushuConfig()", ly_def == ly_orig)

# 六爻数字起卦对比
ly_num_orig = l3_liuyao.compute_numbers(1, 2, datetime(2024, 2, 10, 8, 0), 120.0)
ly_num_none = liuyao_with_config("numbers", 1, 2, "2024-02-10 08:00", config=None)
ly_num_def = liuyao_with_config("numbers", 1, 2, "2024-02-10 08:00", config=ShushuConfig())
check("六爻数字起卦默认一致性 config=None", ly_num_none == ly_num_orig)
check("六爻数字起卦默认一致性 config=ShushuConfig()", ly_num_def == ly_num_orig)


# =====================================================================
# 断言 2：zi_hour_mode="zichu" 时，23:30 输入的日柱按次日计算，而默认模式按当日计算
# =====================================================================
print("\n=== 断言 2：换日界口径差异（子初换日 vs 子正换日） ===")

# 案例 A：2024-06-15 23:30 (真太阳时约 23:28)
# 当日为 庚戌，次日为 辛亥
dt_late_a = "2024-06-15 23:30"
r_def_a = bazi_with_config(dt_late_a, 120.0, config=ShushuConfig(zi_hour_mode="zizheng"))
r_zc_a = bazi_with_config(dt_late_a, 120.0, config=ShushuConfig(zi_hour_mode="zichu"))

check("案例A 默认模式(zizheng) 23:30 日柱归当日(庚戌)", r_def_a["pillars"]["day"]["ganzhi"] == "庚戌")
check("案例A 子初模式(zichu) 23:30 日柱归次日(辛亥)", r_zc_a["pillars"]["day"]["ganzhi"] == "辛亥")
check("案例A 子初模式 日柱与默认模式不同", r_zc_a["pillars"]["day"]["ganzhi"] != r_def_a["pillars"]["day"]["ganzhi"])
check("案例A 子初模式 时柱根据次日日干起子时(戊子)", r_zc_a["pillars"]["hour"]["ganzhi"] == "戊子")
check("案例A 子初模式 显式携带 school_provenance 字段", "school_provenance" in r_zc_a and r_zc_a["school_provenance"]["zi_hour_mode"] == "zichu")

# 案例 B：2000-01-01 23:30
# 当日为 戊午，次日为 己未
dt_late_b = "2000-01-01 23:30"
r_def_b = bazi_with_config(dt_late_b, 120.0, config=ShushuConfig(zi_hour_mode="zizheng"))
r_zc_b = bazi_with_config(dt_late_b, 120.0, config=ShushuConfig(zi_hour_mode="zichu"))

check("案例B 默认模式(zizheng) 23:30 日柱归当日(戊午)", r_def_b["pillars"]["day"]["ganzhi"] == "戊午")
check("案例B 子初模式(zichu) 23:30 日柱归次日(己未)", r_zc_b["pillars"]["day"]["ganzhi"] == "己未")
check("案例B 子初模式 时柱根据次日日干己起子时(甲子)", r_zc_b["pillars"]["hour"]["ganzhi"] == "甲子")
check("非晚子时段(如 12:00) 两种模式日柱完全一致",
      bazi_with_config("2024-06-15 12:00", 120.0, ShushuConfig(zi_hour_mode="zizheng"))["pillars"]["day"]["ganzhi"]
      == bazi_with_config("2024-06-15 12:00", 120.0, ShushuConfig(zi_hour_mode="zichu"))["pillars"]["day"]["ganzhi"])


# =====================================================================
# 断言 3：ziwei_sect="zhongzhou" 时，庚年四化正确变为“太阳禄/武曲权/太阴科/天同忌”
# =====================================================================
print("\n=== 断言 3：紫微斗数流派差异（中州派四化 vs 通行标准四化） ===")

# 1980 年为庚申年
zw_std = ziwei_with_config("1980-05-15 10:00", 120.0, config=ShushuConfig(ziwei_sect="standard"))
zw_zz = ziwei_with_config("1980-05-15 10:00", 120.0, config=ShushuConfig(ziwei_sect="zhongzhou"))

check("1980 年判定层农历年份为庚申年", zw_std["lunar"]["year"] == "庚申" and zw_zz["lunar"]["year"] == "庚申")

sihua_std = {item["star"]: item["hua"] for item in zw_std["sihua"]["items"]}
sihua_zz = {item["star"]: item["hua"] for item in zw_zz["sihua"]["items"]}

check("标准通行派四化: 太阳禄/武曲权/天同科/太阴忌",
      sihua_std == {"太阳": "禄", "武曲": "权", "天同": "科", "太阴": "忌"})
check("中州派四化: 太阳禄/武曲权/太阴科/天同忌",
      sihua_zz == {"太阳": "禄", "武曲": "权", "太阴": "科", "天同": "忌"})
check("中州派与通行派四化科忌产生对调",
      sihua_std["天同"] == "科" and sihua_std["太阴"] == "忌"
      and sihua_zz["太阴"] == "科" and sihua_zz["天同"] == "忌")

# 检查中州派十二宫星曜四化挂载
tai_yin_palace_zz = next(p for p in zw_zz["palaces"] if "太阴" in p["stars"])
tian_tong_palace_zz = next(p for p in zw_zz["palaces"] if "天同" in p["stars"])
check("中州派太阴所在宫位化科", "科" in tai_yin_palace_zz["sihua"])
check("中州派天同所在宫位化忌", "忌" in tian_tong_palace_zz["sihua"])
check("中州派显式携带 school_provenance 字段", "school_provenance" in zw_zz and zw_zz["school_provenance"]["ziwei_sect"] == "zhongzhou")


# =====================================================================
# 断言 4：qimen_central_palace="gen8" 时，中五宫天禽星与死门寄入艮八宫
# =====================================================================
print("\n=== 断言 4：奇门遁甲中宫寄宫差异（寄坤二 vs 寄艮八 vs 阴坤阳艮） ===")

# 锚点：2024-02-10 08:00（立春阳2局伏吟）
qm_kun = qimen_with_config("2024-02-10 08:00", 120.0, config=ShushuConfig(qimen_central_palace="kun2"))
qm_gen = qimen_with_config("2024-02-10 08:00", 120.0, config=ShushuConfig(qimen_central_palace="gen8"))

check("默认寄坤二: 坤2宫携带中五干(戊辛)", qm_kun["pan"]["2"]["tianpan_gan"] == "戊辛")
check("默认寄坤二: 艮8宫未带中五干", qm_kun["pan"]["8"]["tianpan_gan"] == "丁")

check("寄艮八: central_palace 显式标明寄入艮八宫", qm_gen["central_palace"]["palace"] == 8)
check("寄艮八: central_palace 寄入天禽星", qm_gen["central_palace"]["star"] == "天禽")
check("寄艮八: central_palace 寄入死门", qm_gen["central_palace"]["door"] == "死门")
check("寄艮八: 艮8宫盘面携带中五干(丁辛)", qm_gen["pan"]["8"]["tianpan_gan"] == "丁辛")
check("寄艮八: 艮8宫盘面记录寄星天禽", qm_gen["pan"]["8"]["ji_star"] == "天禽")
check("寄艮八: 艮8宫盘面记录寄门死门", qm_gen["pan"]["8"]["ji_door"] == "死门")
check("寄艮八: 坤2宫盘面不带中五干", qm_gen["pan"]["2"]["tianpan_gan"] == "戊")
check("寄艮八: 显式携带 school_provenance 字段",
      "school_provenance" in qm_gen and qm_gen["school_provenance"]["ji_palace"] == 8)

# 验证阴坤阳艮模式
qm_yang = qimen_with_config("2024-02-10 08:00", 120.0, config=ShushuConfig(qimen_central_palace="yin_kun_yang_gen"))
qm_yin = qimen_with_config("2024-07-01 12:00", 120.0, config=ShushuConfig(qimen_central_palace="yin_kun_yang_gen"))
check("阴坤阳艮派: 阳遁(立春)寄艮八", qm_yang["central_palace"]["palace"] == 8)
check("阴坤阳艮派: 阴遁(夏至)寄坤二", qm_yin["central_palace"]["palace"] == 2)


# =====================================================================
# 断言 5：liuyao_analysis="advanced" 时，卦爻输出正确包含“月破/旬空/旺相休囚”
# =====================================================================
print("\n=== 断言 5：六爻排盘扩展分析（旬空、月破、五行旺相休囚死、长生十二宫） ===")

# 案例：2024-02-10 08:00（丙寅月 甲辰日，旬空=寅卯，月破=申）
# 报数 1, 1（乾为天，纳甲: 初子水、二寅木、三辰土、四午火、五申金、上戌土）
ly_basic = liuyao_with_config("numbers", 1, 1, "2024-02-10 08:00", config=ShushuConfig(liuyao_analysis="basic"))
ly_adv = liuyao_with_config("numbers", 1, 1, "2024-02-10 08:00", config=ShushuConfig(liuyao_analysis="advanced"))

check("基础模式 (basic) 爻结构保持与 v1.0 完全一致无扩充键",
      "xunkong" not in ly_basic["lines"][0] and "yuepo" not in ly_basic["lines"][0])

check("高级模式 (advanced) 顶层正确计算旬空地支 (甲辰旬 寅卯空)", ly_adv["xunkong"] == ["寅", "卯"])
check("高级模式 (advanced) 顶层正确计算月破地支 (寅月 冲 申破)", ly_adv["yuepo_zhi"] == "申")

lines_adv = ly_adv["lines"]
# 初爻 子 水：在寅月为休（水生木）
check("初爻(子水) 旺相休囚状态为休", lines_adv[0]["wang_xiang"] == "休" and not lines_adv[0]["xunkong"])

# 二爻 寅 木：临月建为旺，且值旬空
check("二爻(寅木) 旺相休囚状态为旺", lines_adv[1]["wang_xiang"] == "旺")
check("二爻(寅木) 正确识别为旬空", lines_adv[1]["xunkong"] is True)

# 三爻 辰 土：在寅月为死（木克土）
check("三爻(辰土) 旺相休囚状态为死", lines_adv[2]["wang_xiang"] == "死")

# 四爻 午 火：在寅月为相（木生火）
check("四爻(午火) 旺相休囚状态为相", lines_adv[3]["wang_xiang"] == "相")

# 五爻 申 金：在寅月为囚（金克木），且逢月冲识别为月破
check("五爻(申金) 旺相休囚状态为囚", lines_adv[4]["wang_xiang"] == "囚")
check("五爻(申金) 正确识别为月破", lines_adv[4]["yuepo"] is True)

# 上爻 戌 土：在寅月为死
check("上爻(戌土) 旺相休囚状态为死", lines_adv[5]["wang_xiang"] == "死")

# 长生十二宫状态检查
check("全部爻均包含 changsheng 与 changsheng_detail 字段",
      all("changsheng" in l and "changsheng_detail" in l for l in lines_adv))
check("高级模式 显式携带 school_provenance 字段",
      "school_provenance" in ly_adv and ly_adv["school_provenance"]["liuyao_analysis"] == "advanced")


# =====================================================================
# 总结输出
# =====================================================================
def main():
    total = len(CHECKS)
    passed = sum(CHECKS)
    failed = total - passed
    print(f"\n=======================================================")
    print(f"assert_config_engine: 共 {total} 项断言，PASS {passed} / FAIL {failed}")
    print(f"=======================================================")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
