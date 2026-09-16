# -*- coding: utf-8 -*-
"""
assert_l3_shensha_ext.py — 商业扩展神煞库断言测试套件
"""
import sys
from l3_shensha_ext import (
    calculate_extended_shensha, check_sanqi, check_tianshe, check_tianyi
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

print("=== 开始运行 assert_l3_shensha_ext.py 测试套件 ===")

# 1. 三奇贵人测试
# 甲-戊-庚 顺布紧贴
sq1 = check_sanqi(["甲", "戊", "庚", "丁"])
assert_true(len(sq1) == 1 and sq1[0]["name"] == "天上三奇贵人" and "紧贴顺布" in sq1[0]["mode"], "甲戊庚年日月紧贴为天上真三奇")

# 乙-丙-丁 顺布紧贴
sq2 = check_sanqi(["辛", "乙", "丙", "丁"])
assert_true(len(sq2) == 1 and sq2[0]["name"] == "地下三奇贵人", "乙丙丁月日时紧贴为地下真三奇")

# 壬-癸-辛 顺布
sq3 = check_sanqi(["壬", "癸", "辛", "己"])
assert_true(len(sq3) == 1 and sq3[0]["name"] == "人元三奇贵人", "壬癸辛紧贴为人元真三奇")

# 失序三奇（庚甲戊）
sq4 = check_sanqi(["庚", "甲", "戊", "丙"])
assert_true(len(sq4) == 1 and "失序三奇" in sq4[0]["mode"], "乱序甲戊庚标记为失序三奇")

# 2. 天赦日测试
assert_true(check_tianshe("寅", "戊寅"), "春月戊寅日为天赦日")
assert_true(check_tianshe("午", "甲午"), "夏月甲午日为天赦日")
assert_true(check_tianshe("酉", "戊申"), "秋月戊申日为天赦日")
assert_true(check_tianshe("子", "甲子"), "冬月甲子日为天赦日")
assert_true(not check_tianshe("寅", "甲午"), "春月甲午非天赦日")

# 3. 天医测试（古籍《协纪辨方书》：月建逆退一辰）
assert_true(check_tianyi("寅", "丑"), "正月(寅)见丑为天医")
assert_true(check_tianyi("卯", "寅"), "二月(卯)见寅为天医")
assert_true(check_tianyi("子", "亥"), "十一月(子)见亥为天医")
assert_true(not check_tianyi("寅", "卯"), "正月见卯绝非天医")

# 4. 全盘扩展神煞测试
# 四柱：甲子(年) 戊辰(月) 庚午(日) 丁亥(时)
# 天干：甲-戊-庚（天上三奇）！
# 日柱：庚午（十灵日？否，庚午见太极、红艳等）
# 庚干太极在寅亥，时支亥 -> 时柱命中太极贵人
# 庚干福星在亥 -> 时柱命中福星贵人
# 庚干天厨在申 -> 无
# 庚干红艳在戌 -> 无
# 庚干流霞在亥 -> 时柱命中流霞煞！
# 月令辰，天医为卯 -> 无
# 年支子，丧门在寅(+2)，吊客在戌(-2)，披麻在酉 -> 无
res1 = calculate_extended_shensha(["甲子", "戊辰", "庚午", "丁亥"])
assert_true(any(g["name"] == "天上三奇贵人" for g in res1["global_shensha"]), "命中天上三奇贵人")
assert_true("太极贵人" in res1["pillar_shensha"]["时柱"], "时柱命中太极贵人")
assert_true("福星贵人" in res1["pillar_shensha"]["时柱"], "时柱命中福星贵人")
assert_true("流霞煞" in res1["pillar_shensha"]["时柱"], "时柱命中流霞煞")

# 5. 十恶大败与阴阳差错日测试
# 甲辰日（十恶大败、十灵日）
res2 = calculate_extended_shensha(["丙寅", "辛卯", "甲辰", "戊辰"])
assert_true("十恶大败" in res2["pillar_shensha"]["日柱"], "甲辰日命中十恶大败")
assert_true("十灵日" in res2["pillar_shensha"]["日柱"], "甲辰日命中十灵日")

# 丙子日（阴阳差错）
res3 = calculate_extended_shensha(["庚申", "己卯", "丙子", "壬辰"])
assert_true("阴阳差错" in res3["pillar_shensha"]["日柱"], "丙子日命中阴阳差错")

# 6. 六秀日与金神测试
# 丙午日（六秀日、孤鸾煞）
# 乙丑时（金神）
res4 = calculate_extended_shensha(["甲辰", "己巳", "丙午", "乙丑"])
assert_true("六秀日" in res4["pillar_shensha"]["日柱"], "丙午日命中六秀日")
assert_true("孤鸾煞" in res4["pillar_shensha"]["日柱"], "丙午日命中孤鸾煞")
assert_true("金神" in res4["pillar_shensha"]["时柱"], "乙丑时命中金神")
assert_true(any(g["name"] == "金神" for g in res4["global_shensha"]), "全局神煞包含金神")

# 甲寅日（孤鸾煞：木虎夫何在）
res_jiayin = calculate_extended_shensha(["甲子", "丙寅", "甲寅", "戊辰"])
assert_true("孤鸾煞" in res_jiayin["pillar_shensha"]["日柱"], "甲寅日命中孤鸾煞")

# 7. 岁运煞（丧门、吊客、披麻）测试
# 年支为午(6)。顺行二辰为丧门(申8)；逆行二辰为吊客(辰4)；年支后三位为披麻(卯3)
res5 = calculate_extended_shensha(["丙午", "壬申", "庚辰", "己卯"])
assert_true("丧门" in res5["pillar_shensha"]["月柱"], "申月命中午年丧门(+2)")
assert_true("吊客" in res5["pillar_shensha"]["日柱"], "辰日命中午年吊客(-2)")
assert_true("披麻煞" in res5["pillar_shensha"]["时柱"], "卯时命中午年披麻煞")

print("==================================================")
print(f"assert_l3_shensha_ext 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
