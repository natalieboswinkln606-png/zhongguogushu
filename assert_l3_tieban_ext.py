# -*- coding: utf-8 -*-
"""
assert_l3_tieban_ext.py — 铁板神数算盘推数与条文检索断言测试套件
"""
import sys
from l3_tieban_ext import (
    calculate_taixuan_sum, rolling_deduction, query_sample_tiaowen,
    GAN_TAIXUAN, ZHI_TAIXUAN, SAMPLE_TIAOWEN
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

print("=== 开始运行 assert_l3_tieban_ext.py 测试套件 ===")

# 1. 太玄数基础配数测试
# 甲=9, 子=9; 丙=7, 寅=7
assert_true(GAN_TAIXUAN["甲"] == 9 and ZHI_TAIXUAN["子"] == 9, "甲子太玄数各为9")
assert_true(GAN_TAIXUAN["丙"] == 7 and ZHI_TAIXUAN["寅"] == 7, "丙寅太玄数各为7")

# 2. 四柱太玄总和测试
# 甲子(9+9=18), 丙寅(7+7=14), 戊辰(5+5=10), 庚午(8+9=17) -> 18 + 14 + 10 + 17 = 59
total, bd = calculate_taixuan_sum(["甲子", "丙寅", "戊辰", "庚午"])
assert_true(total == 59, f"甲子/丙寅/戊辰/庚午太玄总和为59: {total}")
assert_true(bd["年柱"]["subtotal"] == 18, "年柱甲子太玄数为18")

# 3. 算盘滚雪球数理取数测试
res_ke1 = rolling_deduction(["甲子", "丙寅", "戊辰", "庚午"], ke=1)
items1 = res_ke1["deduced_items"]
assert_true(len(items1) == 5, f"生成5大考刻条文条目: {len(items1)}")
for it in items1:
    assert_true(1000 <= it["tiaowen_id"] <= 12000, f"条文编号在1000-12000有效区间: {it['tiaowen_id']}")

# 4. 刻数变爻差分测试（第1刻 vs 第2刻）
res_ke2 = rolling_deduction(["甲子", "丙寅", "戊辰", "庚午"], ke=2)
items2 = res_ke2["deduced_items"]
# 父母考刻编号不同
assert_true(items1[0]["tiaowen_id"] != items2[0]["tiaowen_id"], "不同入刻推导出不同考刻条文编号")

# 5. 精选经典条文库反查测试
t1031 = query_sample_tiaowen(1031)
assert_true(t1031 is not None and "父母俱全" in t1031, f"成功反查1031条文: {t1031}")

t3360 = query_sample_tiaowen(3360)
assert_true(t3360 is not None and "金榜题名" in t3360, f"成功反查3360条文: {t3360}")

assert_true(len(SAMPLE_TIAOWEN) >= 10, f"精选真实条文库数量达标: {len(SAMPLE_TIAOWEN)}")

print("==================================================")
print(f"assert_l3_tieban_ext 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
