# -*- coding: utf-8 -*-
import sys
from l3_ziwei_yunxian import calculate_doujun
from l3_shensha_ext import check_tianyi, calculate_extended_shensha
from l3_jinkoujue import GUI_MAP
from mcp_server import shushu_calendar_convert
from l3_bazi_geju import determine_bazi_geju
from l5_defense_check import check_pseudo_poem

# 1. 斗君
d1 = calculate_doujun("子", 1, "子")
print("1. 斗君测试(子年正月子时): 算出=", d1, "古籍《全书》应为=子, 判定=", "PASS" if d1 == "子" else "FAIL (Off-by-one, calculated 亥)")

# 2. 天医与丧门吊客
print("2. 天医测试(寅月见丑): 算出=", check_tianyi("寅", "丑"), "古籍应为=True, 判定=", "PASS" if check_tianyi("寅", "丑") else "FAIL (Direction reversed!)")
print("2. 天医测试(寅月见卯): 算出=", check_tianyi("寅", "卯"), "古籍应为=False, 判定=", "FAIL (Took next branch!)" if check_tianyi("寅", "卯") else "PASS")

res_sm = calculate_extended_shensha(["甲子", "丙寅", "戊辰", "庚申"])
print("2. 丧门吊客测试(子年): 年柱神煞=", res_sm["pillar_shensha"])

# 3. 金口诀壬日贵人
print("3. 金口诀壬日贵人:", GUI_MAP["壬"], "古籍应为=('巳', '卯'), 判定=", "PASS" if GUI_MAP["壬"] == ("巳", "卯") else "FAIL (Day/Night reversed!)")

# 4. 历法互转农历腊月跨年
c_res = shushu_calendar_convert(lunar_year=2024, lunar_month=12, lunar_day=1)
print("4. 农历转公历(2024腊月初一): 算出=", c_res["solar_date"], "判定=", "FAIL (Off by a whole year 354 days!)" if c_res["solar_date"] == "2024-01-11" else "PASS")

# 5. 八字专旺申月秋木
p_qiu = determine_bazi_geju(["甲寅", "壬申", "甲寅", "甲子"])
print("5. 八字格局(甲生申月绝地): 算出=", p_qiu["pattern_name"], "判定=", "FAIL (Autumn dead wood judged as 曲直仁寿格!)" if p_qiu["pattern_name"] == "曲直格" else "PASS")

# 6. 从格误判与比肩漏算
p_cong = determine_bazi_geju(["甲戌", "戊辰", "甲戌", "戊辰"])
print("6. 八字格局(甲戌 戊辰 甲戌 戊辰, 年时透甲比肩): 算出=", p_cong["pattern_name"], p_cong["category"])

# 7. 防御检查伪诗漏杀测试
fake_poem_text = "根据七政推演，罗睺照命，计都侵克，四余不曜，主大凶之象。"
violations = check_pseudo_poem(fake_poem_text)
print("7. 伪诗防御检测(含罗睺计都七政四余): 违规数=", len(violations), "判定=", "FAIL (Uncaught fake poem bypass!)" if len(violations) == 0 else "PASS")
