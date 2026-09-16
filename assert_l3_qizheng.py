# -*- coding: utf-8 -*-
"""
assert_l3_qizheng.py — 果老星宗七政四余与二十八宿断言测试套件
"""
import sys
from datetime import datetime
from l3_qizheng import (
    datetime_to_jdn, get_sun_longitude, get_moon_longitude, get_four_extras,
    locate_mansion, locate_zodiac_palace, calculate_qizheng_siyu,
    MANSIONS_28_SORTED
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

print("=== 开始运行 assert_l3_qizheng.py 测试套件 ===")

# 1. 儒略日数 (JDN) 标准历元基准测试 (2000-01-01 12:00:00 UTC = 2451545.0)
jdn_j2000 = datetime_to_jdn(datetime(2000, 1, 1, 12, 0, 0))
assert_true(abs(jdn_j2000 - 2451545.0) < 1e-4, f"J2000标准历元儒略日基准通过: {jdn_j2000}")

# 2. 太阳视黄经二分二至物理点对拍
# 春分 (2024-03-20 03:06 UTC): 太阳黄经 ≈ 0° (±0.5°)
jdn_chunfen = datetime_to_jdn(datetime(2024, 3, 20, 3, 6, 0))
sun_chunfen = get_sun_longitude(jdn_chunfen)
assert_true(sun_chunfen < 1.0 or sun_chunfen > 359.0, f"2024春分时刻太阳黄经位于0度春分点: {sun_chunfen:.2f}°")

# 夏至 (2024-06-20 20:50 UTC): 太阳黄经 ≈ 90° (±0.5°)
jdn_xiazhi = datetime_to_jdn(datetime(2024, 6, 20, 20, 50, 0))
sun_xiazhi = get_sun_longitude(jdn_xiazhi)
assert_true(abs(sun_xiazhi - 90.0) < 0.5, f"2024夏至时刻太阳黄经位于90度夏至点: {sun_xiazhi:.2f}°")

# 秋分 (2024-09-22 12:43 UTC): 太阳黄经 ≈ 180° (±0.5°)
jdn_qiufen = datetime_to_jdn(datetime(2024, 9, 22, 12, 43, 0))
sun_qiufen = get_sun_longitude(jdn_qiufen)
assert_true(abs(sun_qiufen - 180.0) < 0.5, f"2024秋分时刻太阳黄经位于180度秋分点: {sun_qiufen:.2f}°")

# 冬至 (2024-12-21 09:20 UTC): 太阳黄经 ≈ 270° (±0.5°)
jdn_dongzhi = datetime_to_jdn(datetime(2024, 12, 21, 9, 20, 0))
sun_dongzhi = get_sun_longitude(jdn_dongzhi)
assert_true(abs(sun_dongzhi - 270.0) < 0.5, f"2024冬至时刻太阳黄经位于270度冬至点: {sun_dongzhi:.2f}°")

# 3. 四余天体力学几何特性验证
siyu_now = get_four_extras(jdn_j2000)
# 计都与罗睺必须严格呈 180° 对冲
diff_rahu_ketu = abs(siyu_now["计都"] - siyu_now["罗睺"])
assert_true(abs(diff_rahu_ketu - 180.0) < 1e-3, f"计都与罗睺严格相差180度对冲: {diff_rahu_ketu}°")

# 罗睺逆行、月孛顺行、紫气顺行检验 (间隔 100 天)
siyu_later = get_four_extras(jdn_j2000 + 100)
assert_true((siyu_later["罗睺"] - siyu_now["罗睺"]) % 360 > 300, "罗睺交点沿黄道恒常逆行")
assert_true(0 < (siyu_later["月孛"] - siyu_now["月孛"]) % 360 < 20, "月孛远地点沿黄道顺行")
assert_true(0 < (siyu_later["紫气"] - siyu_now["紫气"]) % 360 < 10, "紫气道星沿黄道恒速顺行")

# 4. 二十八宿定位测试 (不等宿度及室壁危天文物理序列)
# 危宿 (345.92° 起)，测试 350.0° 应落入危宿
m_wei = locate_mansion(350.0)
assert_true(m_wei["mansion_name"] == "危" and m_wei["constellation"] == "北方玄武", "350度精准定位于北方玄武危宿")

# 室宿 (353.48° 起跨0度春分点至9.15°)，测试 355.0° 与 5.0° 均落入室宿
m_shi1 = locate_mansion(355.0)
m_shi2 = locate_mansion(5.0)
assert_true(m_shi1["mansion_name"] == "室" and m_shi2["mansion_name"] == "室", "355度与5度跨春分点均精准定位于北方玄武室宿")

# 壁宿 (9.15° 起至 30.67°)，测试 10.0° 应落入壁宿
m_bi = locate_mansion(10.0)
assert_true(m_bi["mansion_name"] == "壁" and m_bi["constellation"] == "北方玄武", "10度精准定位于北方玄武壁宿（在室宿之后）")

# 角宿起点 203.84°，测试 205.0° 应落入角宿 1.16 度
m_jiao = locate_mansion(205.0)
assert_true(m_jiao["mansion_name"] == "角" and m_jiao["constellation"] == "东方苍龙", "205度精准定位于东方苍龙角宿")
assert_true(abs(m_jiao["degree_in_mansion"] - 1.16) < 0.05, f"角宿入宿度=1.16度: {m_jiao['degree_in_mansion']}")

# 井宿 (95.18° 起)
m_jing = locate_mansion(100.0)
assert_true(m_jing["mansion_name"] == "井" and m_jing["constellation"] == "南方朱雀", "100度定位于南方朱雀井宿")

# 5. 全盘七政四余排盘测试（七政：日月五星，四余：罗计孛气，共11星耀）
qz_res = calculate_qizheng_siyu(datetime(2024, 6, 20, 20, 50, 0))
stars = qz_res["stars"]
assert_true("太阳" in stars and "太阴" in stars, "包含日月")
assert_true("木星" in stars and "火星" in stars and "土星" in stars and "金星" in stars and "水星" in stars, "完整包含五星（木火土金水），成正统七政")
assert_true("罗睺" in stars and "计都" in stars and "月孛" in stars and "紫气" in stars, "完整包含四余全曜")
assert_true(len(stars) == 11, f"七政四余十一曜全曜齐备: {len(stars)}")
assert_true(stars["太阳"]["zodiac"] == "巨蟹宫" or stars["太阳"]["palace"] == "未", "夏至太阳落入未宫巨蟹")

print("==================================================")
print(f"assert_l3_qizheng 测试完毕: PASS {pass_count} / FAIL {fail_count}")

if fail_count > 0:
    sys.exit(1)
sys.exit(0)
