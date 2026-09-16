# -*- coding: utf-8 -*-
"""
assert_l1_timezone.py — 全球化时区、夏令时与南半球路由断言测试套件
"""
import sys
from datetime import datetime
from l1_timezone import is_china_dst, eot_minutes, resolve_global_time, resolve_southern_hemisphere_pillars

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

print("=== 开始运行 assert_l1_timezone.py 测试套件 ===")

# 1. 中国历史夏令时 (1986-1991) 判定测试
assert_true(is_china_dst(datetime(1988, 6, 15, 14, 30)), "1988年6月处于夏令时")
assert_true(is_china_dst(datetime(1986, 7, 1, 10, 0)), "1986年7月处于夏令时")
assert_true(is_china_dst(datetime(1991, 5, 20, 8, 0)), "1991年5月处于夏令时")
assert_true(not is_china_dst(datetime(1988, 1, 15, 14, 30)), "1988年1月不在夏令时")
assert_true(not is_china_dst(datetime(1985, 6, 15, 14, 30)), "1985年未实行夏令时")
assert_true(not is_china_dst(datetime(1992, 6, 15, 14, 30)), "1992年已废止夏令时")

# 2. 夏令时自动回退与真太阳时计算
res_dst = resolve_global_time(datetime(1988, 6, 15, 14, 30), tz_name="Asia/Shanghai", lon=120.0, lat=31.2)
assert_true(res_dst["is_dst"] is True, "1988-06-15 标记为夏令时")
assert_true(res_dst["dst_offset_minutes"] == 60.0, "扣除60分钟夏令时")
assert_true(res_dst["standard_local_time"] == "1988-06-15 13:30:00", "标准时间回退为13:30")
assert_true(res_dst["utc_time"] == "1988-06-15 05:30:00", "UTC时间对应为05:30")

# 3. NOAA 均时差曲线数值合理性 (-15 ~ +17 分钟)
eot_feb = eot_minutes(datetime(2024, 2, 12))
assert_true(-15.0 <= eot_feb <= -13.0, f"2月中旬均时差为负 (-14分左右): {eot_feb:.2f}")
eot_nov = eot_minutes(datetime(2024, 11, 3))
assert_true(15.0 <= eot_nov <= 17.0, f"11月初均时差为正 (+16分左右): {eot_nov:.2f}")

# 4. 乌鲁木齐大经度差真太阳时验证
# 乌鲁木齐 lon=87.6, 经度差 (87.6 - 120) * 4 = -129.6 分钟 (约晚 2小时10分)
res_wlmq = resolve_global_time(datetime(2024, 5, 1, 12, 0, 0), tz_name="Asia/Shanghai", lon=87.6, lat=43.8)
tst_hour = datetime.strptime(res_wlmq["true_solar_time"], "%Y-%m-%d %H:%M:%S").hour
tst_minute = datetime.strptime(res_wlmq["true_solar_time"], "%Y-%m-%d %H:%M:%S").minute
assert_true(tst_hour == 9 and 50 <= tst_minute <= 55, f"北京时间12点乌鲁木齐真太阳时约为9点53分: {res_wlmq['true_solar_time']}")

# 5. 海外时区转换测试 (伦敦夏令时 BST UTC+1, 纽约夏令时 EDT UTC-4)
res_lon = resolve_global_time(datetime(2024, 10, 1, 12, 0, 0), tz_name="Europe/London", lon=0.0, lat=51.5)
assert_true(res_lon["utc_time"] == "2024-10-01 11:00:00" and res_lon["beijing_time"] == "2024-10-01 19:00:00", "伦敦夏令时中午对应北京晚19点")

res_ny = resolve_global_time(datetime(2024, 10, 1, 12, 0, 0), tz_name="America/New_York", lon=-74.0, lat=40.7)
assert_true(res_ny["utc_time"] == "2024-10-01 16:00:00" and res_ny["beijing_time"] == "2024-10-02 00:00:00", "纽约夏令时中午12点对应北京次日00:00")

# 6. 南半球排盘三大派系仲裁测试 (悉尼南纬 -33.86)
# 测试八字：甲辰年 丙寅月 戊午日 丙辰时
fp_sample = ["甲辰", "丙寅", "戊午", "丙辰"]

# 派系 A：天文黄经派 (默认)，四柱完全不变
res_sh_a = resolve_southern_hemisphere_pillars(fp_sample, lat=-33.86, school="astronomical")
assert_true(res_sh_a["pillars"] == fp_sample, "派系A四柱保持天文黄经坐标完全不变")
assert_true(res_sh_a["transformed"] is False, "派系A标记为未修改")

# 派系 B: 对冲月建派，寅月变申月，甲年五虎遁推申位
# 甲己丙作首，寅=丙，卯=丁，辰=戊，巳=己，午=庚，未=辛，申=壬
res_sh_b = resolve_southern_hemisphere_pillars(fp_sample, lat=-33.86, school="clash_month")
assert_true(res_sh_b["transformed"] is True, "派系B标记为已对冲")
assert_true(res_sh_b["pillars"][1] == "壬申", f"甲年寅月对冲为壬申月 (实际: {res_sh_b['pillars'][1]})")
assert_true(res_sh_b["pillars"][0] == "甲辰" and res_sh_b["pillars"][2] == "戊午", "年柱与日柱保持不变")

# 北半球调用对冲派不发生变化
res_nh = resolve_southern_hemisphere_pillars(fp_sample, lat=31.2, school="clash_month")
assert_true(res_nh["transformed"] is False and res_nh["pillars"] == fp_sample, "北半球调用不受南半球对冲影响")

print("==================================================")
print(f"assert_l1_timezone 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
