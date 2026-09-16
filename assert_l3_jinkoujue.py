# -*- coding: utf-8 -*-
"""
assert_l3_jinkoujue.py — 大六壬金口诀断言测试套件
"""
import sys
from l3_jinkoujue import (
    wushu_dun, get_renyuan, get_jiangshen, get_guishen, calculate_jinkoujue,
    GUI_SHEN_LIST, YUE_JIANG_MAP
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

print("=== 开始运行 assert_l3_jinkoujue.py 测试套件 ===")

# 1. 人元五鼠遁测试
# 甲日见子为甲子，见午为庚午，见卯为丁卯
assert_true(get_renyuan("甲", "子") == "甲", "甲日地分子人元为甲")
assert_true(get_renyuan("甲", "午") == "庚", "甲日地分午人元为庚")
assert_true(get_renyuan("甲", "卯") == "丁", "甲日地分卯人元为丁")
assert_true(get_renyuan("丙", "子") == "戊", "丙辛起戊子，丙日见子为人元戊")
assert_true(get_renyuan("乙", "酉") == "乙", "乙庚起丙子，乙日见酉为人元乙")

# 2. 将神（月将加时至地分）测试
# 月将为亥（雨水后登明），占时为午，地分为卯
# 午(6)加亥(11)，数至卯(3)，步进步长 = (3 - 6) % 12 = 9
# 将神 = (11 + 9) % 12 = 20 % 12 = 8 -> 申(传送)
js1 = get_jiangshen("亥", "午", "卯")
assert_true(js1 == "申", f"亥将加午时至地分卯将神为申: {js1}")

# 月将为戌（春分），占时为子，地分为子
# 将神直接落月将戌
js2 = get_jiangshen("戌", "子", "子")
assert_true(js2 == "戌", f"月将加时在相同时辰将神为月将本身: {js2}")

# 3. 贵神测试（昼夜与顺逆）
# 甲日占时午（昼占，阳贵在丑）。丑在阳宫（顺排）。地分在卯。
# 丑(1)到卯(3)顺数 2 步 -> 贵人(0)->腾蛇(1)->朱雀(2)
gs_name, gs_zhi, gs_wx = get_guishen("甲", "午", "卯")
assert_true(gs_name == "朱雀" and gs_zhi == "午", f"甲日午时地分卯贵神为朱雀(午火): {gs_name}")

# 甲日占时子（夜占，阴贵在未）。未在阴宫（巳午未申酉戌，逆排）。地分在午。
# 未(7)到午(6)逆数 1 步 -> 贵人(0)->腾蛇(1)
gs_night, gs_n_zhi, _ = get_guishen("甲", "子", "午")
assert_true(gs_night == "腾蛇" and gs_n_zhi == "巳", f"甲日子时夜贵在未逆排地分午为腾蛇: {gs_night}")

# 4. 壬癸日贵神专项测试（对抗性审查基准：壬癸蛇兔藏，巳为日贵，卯为夜贵）
# 壬日昼占（午时）：阳贵在巳
gs_ren_day, _, _ = get_guishen("壬", "午", "巳")
# 巳在阴宫逆排，地分巳(5)-巳(5)=0步 -> 天乙贵人
assert_true(gs_ren_day == "贵人", "壬日昼占以巳为天乙贵人")

# 壬日夜占（子时）：阴贵在卯
gs_ren_night, _, _ = get_guishen("壬", "子", "卯")
# 卯在阳宫顺排，地分卯(3)-卯(3)=0步 -> 天乙贵人
assert_true(gs_ren_night == "贵人", "壬日夜占以卯为天乙贵人")

# 5. 全排盘与五动三动克应测试
# 案例 A: 甲日午时，亥将（登明），地分卯，生于春月寅月
# 人元: 丁(火)
# 贵神: 朱雀(午火)
# 将神: 申(金)
# 地分: 卯(木)
# 关系：
# - 贵神午火克将神申金 -> 妻动（神克将）！
# - 将神申金克地分卯木 -> 将动（方克将）！
res_a = calculate_jinkoujue(day_gan="甲", hour_zhi="午", month_jiang_zhi="亥", difen="卯", month_zhi="寅")
fp = res_a["four_positions"]
assert_true(fp["renyuan"]["gan"] == "丁" and fp["renyuan"]["wuxing"] == "火", "人元为丁火")
assert_true(fp["guishen"]["name"] == "朱雀" and fp["guishen"]["wuxing"] == "火", "贵神为朱雀火")
assert_true(fp["jiangshen"]["zhi"] == "申" and fp["jiangshen"]["wuxing"] == "金", "将神为申金")
assert_true(fp["difen"]["zhi"] == "卯" and fp["difen"]["wuxing"] == "木", "地分为卯木")

wudong_names = [d["name"] for d in res_a["wudong"]]
assert_true("妻动" in wudong_names, f"命中妻动（朱雀火克申金）: {wudong_names}")

# 6. 旺相休囚死测试（春月寅月：木旺、火相、水休、金囚、土死）
wx_status = res_a["wangxiang"]
assert_true(wx_status["difen"] == "旺", f"春木月令地分卯木当旺: {wx_status['difen']}")
assert_true(wx_status["renyuan"] == "相", f"春木月令人元丁火当相: {wx_status['renyuan']}")
assert_true(wx_status["jiangshen"] == "囚", f"春木月并将神申金当囚: {wx_status['jiangshen']}")

# 7. 四位地支合冲刑害分析测试
inter = res_a["interactions"]
# 将神申金与地分卯木，贵神午火
assert_true(isinstance(inter, list), "地支相互作用列表生成正常")

# 案例 B: 构造六冲与六合
# 庚日午时，月将寅，地分丑
res_b = calculate_jinkoujue(day_gan="庚", hour_zhi="午", month_jiang_zhi="寅", difen="丑")
assert_true("four_positions" in res_b and "wudong" in res_b, "金口诀排盘字典结构完整")

# 5. 二十四节气月将对照表完整性
assert_true(len(YUE_JIANG_MAP) == 24, "二十四节气月将映射表24节气齐全")
assert_true(YUE_JIANG_MAP["雨水"] == ("亥", "登明"), "雨水月将为亥登明")
assert_true(YUE_JIANG_MAP["春分"] == ("戌", "河魁"), "春分月将为戌河魁")
assert_true(YUE_JIANG_MAP["冬至"] == ("丑", "大吉"), "冬至月将为丑大吉")

print("==================================================")
print(f"assert_l3_jinkoujue 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
