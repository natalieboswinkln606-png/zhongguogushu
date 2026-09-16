# -*- coding: utf-8 -*-
"""assert_l5_rule9_age_year.py — 回归测试：rule9 年龄-年份一致性必须能抓出已知错误

锁定 3 类硬错模式（来自 2026-08-30 B男命实际事故）：
1. "2031-2040年...21-30岁" — 期望26-35岁（癸未食神运真实区间）
2. "2041-2050年...31-40岁" — 期望36-45岁（壬午伤官运真实区间）
3. "2011-2030年...20-30岁" — 期望6-25岁（命主6岁才入第一步大运）

退出码：0=全部 PASS；非0=有 FAIL
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from l5_defense_check import check_age_year_consistency

SNAP = os.path.join(BASE, "temp", "_snap_b_clean.json")

# ========== 案例 1：模拟"21-30岁"放错位置（实际应为26-35）
text1 = """测试段
【取象推断】癸未食神运（2031-2040年，21-30岁）—— 创意落地
"""
v1 = check_age_year_consistency(text1, SNAP)
case1_pass = any(
    v.get("kind") == "age_year_range_mismatch"
    and v.get("year_range") == "2031-2040"
    and v.get("age_range") == "21-30"
    and v.get("expected_age_range") == "26-35"
    for v in v1
)
print(f"[case1] 21-30岁错配(应26-35): {'PASS' if case1_pass else 'FAIL'}")
if not case1_pass:
    print("  detected:", v1)

# ========== 案例 2：模拟"31-40岁"放错位置（实际应为36-45）
text2 = """测试段
壬午伤官运（2041-2050年，31-40岁）—— 灵魂重塑
"""
v2 = check_age_year_consistency(text2, SNAP)
case2_pass = any(
    v.get("kind") == "age_year_range_mismatch"
    and v.get("year_range") == "2041-2050"
    and v.get("age_range") == "31-40"
    and v.get("expected_age_range") == "36-45"
    for v in v2
)
print(f"[case2] 31-40岁错配(应36-45): {'PASS' if case2_pass else 'FAIL'}")
if not case2_pass:
    print("  detected:", v2)

# ========== 案例 3：模拟"20岁"写错位置（实际2020年是15岁）
text3 = """测试段
2020年是乙酉大运尾声，2021年进入甲申大运——20岁的2025年是甲申大运中正财运最盛的节点。
"""
v3 = check_age_year_consistency(text3, SNAP)
# 这条应当不报错（"20岁的2025年"是修饰2025，不是说2021=20岁）
case3_pass = len(v3) == 0
print(f"[case3] 假阳性防护('20岁的2025年'不应误报): {'PASS' if case3_pass else 'FAIL'}")
if not case3_pass:
    print("  false-positive:", v3)

# ========== 案例 4：模拟"2020年...20岁"真错（2020实际是15岁）
text4 = """测试段
**转折点**：2020年是庚子年20岁少年期，2025年是乙巳年20岁成年初。
"""
v4 = check_age_year_consistency(text4, SNAP)
# 这里2020年...20岁是错的，但2025年...20岁是对的
case4_pass = any(
    v.get("kind") == "age_year_mismatch" and v.get("year") == 2020 and v.get("age") == 20
    for v in v4
)
print(f"[case4] 2020年=20岁错配(应15岁): {'PASS' if case4_pass else 'FAIL'}")
if not case4_pass:
    print("  detected:", v4)

# ========== 案例 5：模拟"2031-2040年...26-35岁"正确区间应PASS不报警
text5 = """测试段
癸未食神运（2031-2040年，26-35岁）—— 正确
"""
v5 = check_age_year_consistency(text5, SNAP)
case5_pass = len(v5) == 0
print(f"[case5] 正确区间(26-35)不报警: {'PASS' if case5_pass else 'FAIL'}")
if not case5_pass:
    print("  false-positive:", v5)

# ========== 总结
all_pass = case1_pass and case2_pass and case3_pass and case4_pass and case5_pass
print(f"\n{'='*40}")
print(f"rule9 回归测试: {sum([case1_pass, case2_pass, case3_pass, case4_pass, case5_pass])}/5 PASS")
sys.exit(0 if all_pass else 1)
