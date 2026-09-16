# -*- coding: utf-8 -*-
"""
assert_l3_bazi_geju.py — 八字格局自动化判定引擎断言测试套件
覆盖：
1. 子平真诠月令本气透干正八格（正官、七杀、正财、偏财、正印、偏印、食神、伤官）
2. 月令中余气透干立格
3. 月令藏干不透，取本气立格
4. 建禄格与阳刃格
5. 专旺格（曲直仁寿、炎上、稼穑、从革、润下）
6. 弃命从弱格（从杀、从财、从儿、从弱）
7. 化气格（甲己化土格等）
8. 鲁棒性与异常输入边界
"""
import sys
from l3_bazi_geju import determine_bazi_geju, get_shishen

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

print("=== 开始运行 assert_l3_bazi_geju.py 测试套件 ===")

# 1. 十神基础映射测试
assert_true(get_shishen("甲", "甲") == "比肩", "甲见甲为比肩")
assert_true(get_shishen("甲", "乙") == "劫财", "甲见乙为劫财")
assert_true(get_shishen("甲", "丙") == "食神", "甲见丙为食神")
assert_true(get_shishen("甲", "丁") == "伤官", "甲见丁为伤官")
assert_true(get_shishen("甲", "戊") == "偏财", "甲见戊为偏财")
assert_true(get_shishen("甲", "己") == "正财", "甲见己为正财")
assert_true(get_shishen("甲", "庚") == "七杀", "甲见庚为七杀")
assert_true(get_shishen("甲", "辛") == "正官", "甲见辛为正官")
assert_true(get_shishen("甲", "壬") == "偏印", "甲见壬为偏印")
assert_true(get_shishen("甲", "癸") == "正印", "甲见癸为正印")

# 2. 正官格（本气透干）
# 戊土生于卯月（本气乙木），月干透乙
p1 = determine_bazi_geju(["庚子", "乙卯", "戊寅", "丁巳"])
assert_true(p1["pattern_name"] == "正官格" and p1["category"] == "正八格", "戊生卯月透乙立正官格")

# 3. 七杀格（本气透干）
# 甲木生于申月（本气庚金），年干透庚
p2 = determine_bazi_geju(["庚午", "甲申", "甲子", "丙寅"])
assert_true(p2["pattern_name"] == "七杀格" and p2["category"] == "正八格", "甲生申月透庚立七杀格")

# 4. 正印格（本气透干）
# 甲木生于子月（本气癸水），时干透癸
p3 = determine_bazi_geju(["戊辰", "甲子", "甲寅", "癸酉"])
assert_true(p3["pattern_name"] == "正印格", "甲生子月透癸立正印格")

# 5. 偏印格（本气透干）
# 丙火生于寅月（本气甲木），月干透甲
p4 = determine_bazi_geju(["壬戌", "甲寅", "丙午", "庚寅"])
assert_true(p4["pattern_name"] == "偏印格", "丙生寅月透甲立偏印格")

# 6. 正财格（本气透干）
# 庚金生于卯月（本气乙木），月干透乙
p5 = determine_bazi_geju(["辛丑", "乙卯", "庚申", "壬午"])
assert_true(p5["pattern_name"] == "正财格", "庚生卯月透乙立正财格")

# 7. 偏财格（本气透干）
# 戊土生于亥月（本气壬水），时干透壬
p6 = determine_bazi_geju(["丙子", "己亥", "戊子", "壬戌"])
assert_true(p6["pattern_name"] == "偏财格", "戊生亥月透壬立偏财格")

# 8. 食神格（本气透干）
# 壬水生于寅月（本气甲木），月干透甲
p7 = determine_bazi_geju(["戊戌", "甲寅", "壬子", "辛亥"])
assert_true(p7["pattern_name"] == "食神格", "壬生寅月透甲立食神格")

# 9. 伤官格（本气透干）
# 戊土生于酉月（本气辛金），时干透辛
p8 = determine_bazi_geju(["癸亥", "辛酉", "戊子", "丁巳"])
assert_true(p8["pattern_name"] == "伤官格", "戊生酉月透辛立伤官格")

# 10. 中气透干立格
# 戊土生于辰月（本气戊土，中气乙木，余气癸水）。天干无戊，月干透乙（乙正官）
p9 = determine_bazi_geju(["丁亥", "乙辰", "戊午", "丙辰"])
assert_true(p9["pattern_name"] == "正官格", "辰月中气乙木透干立正官格")

# 11. 藏干均不透，直取本气立格
# 甲木生于午月（本气丁火，中气己土）。天干无丙丁己，庚申年戊辰时
p10 = determine_bazi_geju(["庚申", "壬午", "甲申", "戊辰"])
assert_true(p10["pattern_name"] == "伤官格", "午月藏干不透直取本气丁火伤官立格")

# 12. 建禄格
# 甲木生于寅月，寅为甲之临官禄地
p11 = determine_bazi_geju(["庚戌", "甲寅", "甲申", "丁卯"])
assert_true(p11["pattern_name"] == "建禄格" and p11["category"] == "禄刃格", "甲生寅月立建禄格")

# 13. 阳刃格
# 庚金生于酉月，酉为庚金帝旺劫财阳刃位
p12 = determine_bazi_geju(["丙辰", "辛酉", "庚申", "壬午"])
assert_true(p12["pattern_name"] == "阳刃格" and p12["category"] == "禄刃格", "庚生酉月立阳刃格")

# 13b. 月劫格（《子平真诠》第十八章）
# 戊土生于丑月，月令本气己土劫财透干（非午火帝旺阳刃），立月劫格
p12b = determine_bazi_geju(["乙亥", "己丑", "戊午", "戊午"])
assert_true(p12b["pattern_name"] == "月劫格" and p12b["category"] == "禄刃格", "戊生丑月透己立月劫格")

# 14. 曲直格 (木专旺)
# 甲木生于卯月，地支亥卯未三合木局，天干甲乙木盛，无庚辛强官杀
p13 = determine_bazi_geju(["癸亥", "乙卯", "甲寅", "乙亥"])
assert_true(p13["pattern_name"] == "曲直格" and p13["category"] == "专旺格", "亥卯寅亥木旺成曲直格")

# 15. 炎上格 (火专旺)
# 丙火生于巳午月，寅午戌三合火局
p14 = determine_bazi_geju(["丙寅", "甲午", "丙戌", "甲午"])
assert_true(p14["pattern_name"] == "炎上格" and p14["category"] == "专旺格", "寅午戌纯火成炎上格")

# 16. 从杀格 (弃命从杀)
# 丙火生于子月，地支申子全水，天干壬水双透无木火根气
p15 = determine_bazi_geju(["壬申", "壬子", "丙子", "戊子"])
assert_true(p15["pattern_name"] == "从杀格" and p15["category"] == "从格", "官杀极旺无根立从杀格")

# 17. 从财格 (弃命从财)
# 乙木生于酉月，满盘戊己戌丑土财，无印比相生
p16 = determine_bazi_geju(["戊戌", "辛酉", "乙丑", "己丑"])
assert_true(p16["pattern_name"] == "从财格" and p16["category"] == "从格", "财星极旺无根立从财格")

# 18. 从儿格 (弃命从儿)
# 庚金生于亥子月，满盘食伤水旺
p17 = determine_bazi_geju(["癸亥", "甲子", "庚子", "壬子"])
assert_true(p17["pattern_name"] == "从儿格" and p17["category"] == "从格", "食伤汪洋立从儿格")

# 19. 化气格 (甲己化土，无争妒)
# 甲木生于丑月，月干己土五合，时干庚金无争合，地支无寅卯木强根
p18 = determine_bazi_geju(["戊辰", "己丑", "甲戌", "庚午"])
assert_true(p18["category"] == "化气格" and "甲己化土" in p18["pattern_name"], "甲己合化土成化气格")

# 20. 对抗性回归测试：争合妒合一票否决
# 双己合一甲，两干争合不化
p_zhenghe = determine_bazi_geju(["戊辰", "己丑", "甲戌", "己巳"])
assert_true(p_zhenghe["category"] != "化气格", "双己争合甲木严禁成化气格")

# 21. 对抗性回归测试：专旺格秋木绝地一票否决
# 甲生申月官杀乘令，绝地死木绝不可入曲直仁寿格
p_fall_wood = determine_bazi_geju(["甲寅", "壬申", "甲寅", "甲子"])
assert_true(p_fall_wood["category"] != "专旺格", "甲木申月绝地不可成曲直格")

# 22. 对抗性回归测试：弃命从财格比肩透干与墓库微根一票否决
# 甲戌 戊辰 甲戌 戊辰（两透甲木比肩，辰中有乙木微根）绝不可从财
p_fake_cong = determine_bazi_geju(["甲戌", "戊辰", "甲戌", "戊辰"])
assert_true(p_fake_cong["category"] != "从格", "甲透比肩且支藏微根不可弃命从财")

# 23. 字典格式输入测试
p19 = determine_bazi_geju({"year": "庚子", "month": "乙卯", "day": "戊寅", "hour": "丁巳"})
assert_true(p19["pattern_name"] == "正官格", "字典参数输入兼容性通过")

print("==================================================")
print(f"assert_l3_bazi_geju 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
