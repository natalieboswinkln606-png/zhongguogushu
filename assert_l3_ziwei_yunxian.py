# -*- coding: utf-8 -*-
"""
assert_l3_ziwei_yunxian.py — 紫微斗数多级运限与动态流曜断言测试套件
"""
import sys
from l3_ziwei_yunxian import (
    calculate_doujun, calculate_four_tier_limits, calculate_dynamic_liuyao,
    get_full_ziwei_yunxian, ZHI, GAN, SIHUA_MAP
)

pass_count = 0
fail_count = 0

def assert_true(cond, msg):
    global pass_count, fail_count
    if cond:
        pass_count += 1
        print(f"  PASS: {msg}")
    else:
        fail_count += 1
        print(f"  FAIL: {msg}")

print("=== 开始运行 assert_l3_ziwei_yunxian.py 测试套件 ===")

# 1. 斗君计算验证（《紫微斗数全书》：太岁宫起正月逆寻生月，从生月起子顺寻生时）
# 经典基准案例（对抗性审查标准用例）：子年(0) 正月(1) 子时(0)生人 -> 斗君必在子！
dj0 = calculate_doujun(target_year_zhi="子", birth_lunar_month=1, birth_hour_zhi="子")
assert_true(dj0 == "子", f"子年1月子时生人斗君必在子: {dj0}")

# 案例 1: 出生农历五月(5)，出生辰时(4)。2024 甲辰年(4)。
# 斗君 = (4 - 5 + 1 + 4) % 12 = 4 (辰宫)
dj1 = calculate_doujun(target_year_zhi="辰", birth_lunar_month=5, birth_hour_zhi="辰")
assert_true(dj1 == "辰", f"辰年5月辰时生人斗君在辰: {dj1}")

# 案例 2: 出生农历正月(1)，出生子时(0)。2026 丙午年(6)。
# 斗君 = (6 - 1 + 1 + 0) % 12 = 6 (午宫)
dj2 = calculate_doujun(target_year_zhi="午", birth_lunar_month=1, birth_hour_zhi="子")
assert_true(dj2 == "午", f"午年1月子时生人斗君在午: {dj2}")

# 2. 四级运限联动推导测试
# 2026 丙午年，生月1月子时（斗君在午），农历五月初五，午时
limits = calculate_four_tier_limits(
    target_year_zhi="午", birth_lunar_month=1, birth_hour_zhi="子",
    lunar_month=5, lunar_day=5, query_hour_zhi="午"
)
# 斗君在午(6)。正月在午(6)，五月 = (6 + 5 - 1) % 12 = 10 (戌宫)
assert_true(limits["liunian_ming"] == "午", "流年太岁午年命宫在午")
assert_true(limits["liuyue_ming"] == "戌", f"五月流月命宫在戌: {limits['liuyue_ming']}")

# 初一在戌(10)，初五 = (10 + 5 - 1) % 12 = 14 % 12 = 2 (寅宫)
assert_true(limits["liuri_ming"] == "寅", f"初五流日命宫在寅: {limits['liuri_ming']}")

# 子时在寅(2)，午时 = (2 + 6) % 12 = 8 (申宫)
assert_true(limits["liushi_ming"] == "申", f"午时流时命宫在申: {limits['liushi_ming']}")

# 3. 动态流曜飞星排布测试（2026 丙午年）
# 丙年：
# - 禄存在巳
# - 擎羊在午（前一位）
# - 陀罗在辰（后一位）
# - 魁钺在亥、酉（丙丁猪鸡位）
# - 午年天马在申（寅午戌马在申）
# - 午年红鸾：卯起子逆数至午 -> 卯(3)-6 = -3 % 12 = 9 (酉宫)
# - 午年天喜：酉对冲在卯宫
# - 丙年文昌在申，文曲在寅
ly = calculate_dynamic_liuyao(target_year_gan="丙", target_year_zhi="午")
assert_true(ly["liunian_lucun"] == "巳", "丙年流年禄存在巳")
assert_true(ly["liunian_qingyang"] == "午", "流年擎羊在禄前午位")
assert_true(ly["liunian_tuoluo"] == "辰", "流年陀罗在禄后辰位")
assert_true(ly["liunian_tiankui"] == "亥" and ly["liunian_tianyue"] == "酉", "丙年魁钺在亥酉")
assert_true(ly["liunian_tianma"] == "申", "午年天马在申")
assert_true(ly["liunian_hongluan"] == "酉", "午年红鸾在酉")
assert_true(ly["liunian_tianxi"] == "卯", "午年天喜在卯")
assert_true(ly["liunian_wenchang"] == "申", "丙年流昌在申")
assert_true(ly["liunian_wenqu"] == "寅", "丙年流曲在寅")

# 4. 2026 丙年流年四化验证（天同禄、天机权、文昌科、廉贞忌）
sh = ly["liunian_sihua"]
assert_true(sh["化禄"] == "天同", "丙年流化禄为天同")
assert_true(sh["化权"] == "天机", "丙年流化权为天机")
assert_true(sh["化科"] == "文昌", "丙年流化科为文昌")
assert_true(sh["化忌"] == "廉贞", "丙年流化忌为廉贞")

# 5. 十天干流年四化完整性检查
assert_true(len(SIHUA_MAP) == 10, "十天干流年四化表齐全")
assert_true(SIHUA_MAP["庚"][0][0] == "太阳" and SIHUA_MAP["庚"][3][0] == "太阴", "庚年全书派阳武同阴四化正确")

# 6. 综合全盘接口测试
full = get_full_ziwei_yunxian(
    birth_lunar_month=3, birth_hour_zhi="辰",
    target_year_gan="甲", target_year_zhi="辰",
    lunar_month=1, lunar_day=1, query_hour_zhi="子"
)
assert_true("limits" in full and "liuyao" in full, "综合运限接口返回结构完整")

print("==================================================")
print(f"assert_l3_ziwei_yunxian 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
