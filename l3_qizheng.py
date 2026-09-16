# -*- coding: utf-8 -*-
"""
l3_qizheng.py — 果老星宗七政四余高精星历与二十八宿入宿度推算引擎
1. 七政（日月五星）与四余（罗睺、计都、月孛、紫气）地心真视黄经求解
2. 二十八宿 IAU J2000 距星真黄道坐标与不等宿度定位算法
3. 黄道十二宫（子丑寅卯辰巳午未申酉戌亥）与西方十二星座对应
"""
import math
from datetime import datetime, timezone

# IAU J2000 二十八宿距星真黄经与四象划分 (黄经按春分点后天球逆时针升序排布)
# 依次：壁(9.15), 奎(30.67), 娄(33.97), 胃(51.17), 昴(60.0), 毕(68.5), 觜(83.7), 参(88.45),
# 井(95.18), 鬼(123.4), 柳(134.12), 星(147.17), 张(157.5), 翼(173.4), 轸(190.44), 角(203.84), 亢(214.33),
# 氐(225.08), 房(243.4), 心(249.13), 尾(260.25), 箕(278.58), 斗(288.33), 牛(314.08), 女(321.87), 虚(333.4), 危(345.92), 室(353.48)
MANSIONS_28_SORTED = [
    ("壁", 9.15, "北方玄武"),
    ("奎", 30.67, "西方白虎"),
    ("娄", 33.97, "西方白虎"),
    ("胃", 51.17, "西方白虎"),
    ("昴", 60.00, "西方白虎"),
    ("毕", 68.50, "西方白虎"),
    ("觜", 83.70, "西方白虎"),
    ("参", 88.45, "西方白虎"),
    ("井", 95.18, "南方朱雀"),
    ("鬼", 123.40, "南方朱雀"),
    ("柳", 134.12, "南方朱雀"),
    ("星", 147.17, "南方朱雀"),
    ("张", 157.50, "南方朱雀"),
    ("翼", 173.40, "南方朱雀"),
    ("轸", 190.44, "南方朱雀"),
    ("角", 203.84, "东方苍龙"),
    ("亢", 214.33, "东方苍龙"),
    ("氐", 225.08, "东方苍龙"),
    ("房", 243.40, "东方苍龙"),
    ("心", 249.13, "东方苍龙"),
    ("尾", 260.25, "东方苍龙"),
    ("箕", 278.58, "东方苍龙"),
    ("斗", 288.33, "北方玄武"),
    ("牛", 314.08, "北方玄武"),
    ("女", 321.87, "北方玄武"),
    ("虚", 333.40, "北方玄武"),
    ("危", 345.92, "北方玄武"),
    ("室", 353.48, "北方玄武"),
]

# 黄道十二宫（春分戌白羊起算，逆时针）
ZODIAC_12 = [
    ("戌", "白羊宫", 0.0, 30.0),
    ("酉", "金牛宫", 30.0, 60.0),
    ("申", "双子宫", 60.0, 90.0),
    ("未", "巨蟹宫", 90.0, 120.0),
    ("午", "狮子宫", 120.0, 150.0),
    ("巳", "处女宫", 150.0, 180.0),
    ("辰", "天秤宫", 180.0, 210.0),
    ("卯", "天蝎宫", 210.0, 240.0),
    ("寅", "射手宫", 240.0, 270.0),
    ("丑", "摩羯宫", 270.0, 300.0),
    ("子", "水瓶宫", 300.0, 330.0),
    ("亥", "双鱼宫", 330.0, 360.0),
]


def datetime_to_jdn(dt: datetime) -> float:
    """计算儒略日数 (Julian Day Number)。"""
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def get_sun_longitude(jdn: float) -> float:
    """求解太阳地心视黄经（度）。"""
    t = (jdn - 2451545.0) / 36525.0
    # 平黄经 L0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    # 平近点角 M
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    mr = math.radians(m)
    # 中心差 C
    c = (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr) \
        + (0.019993 - 0.000101 * t) * math.sin(2 * mr) \
        + 0.000289 * math.sin(3 * mr)
    true_long = l0 + c
    return true_long % 360.0


def get_moon_longitude(jdn: float) -> float:
    """求解月球地心视黄经（度）。"""
    t = (jdn - 2451545.0) / 36525.0
    # 平黄经 L'
    lp = 218.3164477 + 481267.88123421 * t
    # 平近点角 M'
    mp = 134.9633964 + 477198.8675055 * t
    # 太阳平近点角 M
    m = 357.5291092 + 35999.0502909 * t
    # 纬度参量 F
    f = 93.2720950 + 483202.0175233 * t
    # 日月黄经差 D
    d = 297.8501921 + 445267.1113722 * t

    # 主摄动项
    sigma_l = 6.288774 * math.sin(math.radians(mp)) \
        + 1.274027 * math.sin(math.radians(2 * d - mp)) \
        + 0.658314 * math.sin(math.radians(2 * d)) \
        + 0.213618 * math.sin(math.radians(2 * mp)) \
        - 0.185116 * math.sin(math.radians(m)) \
        - 0.114332 * math.sin(math.radians(2 * f))
    return (lp + sigma_l) % 360.0


def get_four_extras(jdn: float) -> dict:
    """
    求解四余（罗睺、计都、月孛、紫气）真视黄经。
    """
    t = (jdn - 2451545.0) / 36525.0
    days = jdn - 2451545.0

    # 1. 罗睺（白道升交点，逆行）：J2000 锚点 125.04452°
    rahu = (125.04452 - 1934.136261 * t + 0.0020708 * t * t) % 360.0

    # 2. 计都（白道降交点，对冲 180°）
    ketu = (rahu + 180.0) % 360.0

    # 3. 月孛（月球远地点，顺行）：J2000 锚点 83.35324°
    yuebei = (83.35324 + 4069.0137287 * t - 0.01032 * t * t) % 360.0

    # 4. 紫气（道星，恒速顺行）：授时历周天 10222.44 天，J2000 锚点取 280.0°
    ziqi = (280.0 + (360.0 / 10222.44) * days) % 360.0

    return {
        "罗睺": round(rahu, 3),
        "计都": round(ketu, 3),
        "月孛": round(yuebei, 3),
        "紫气": round(ziqi, 3),
    }


def get_five_planets(jdn: float) -> dict:
    """
    求解五星（木星/岁星、火星/荧惑、土星/镇星、金星/太白、水星/辰星）地心真视黄经。
    采用开普勒二体与地心转换算法。
    """
    t = (jdn - 2451545.0) / 36525.0
    l_sun = math.radians(get_sun_longitude(jdn))
    x_sun = math.cos(l_sun)
    y_sun = math.sin(l_sun)

    # 行星轨道半长轴 a(AU), J2000平黄经 L0, 世纪摄动率 n, 偏心率 e
    planets_elements = {
        "木星": (5.2044, 34.35, 3034.91, 0.0485),
        "火星": (1.5237, 355.43, 19140.30, 0.0934),
        "土星": (9.5826, 50.08, 1222.11, 0.0555),
        "金星": (0.7233, 181.98, 58517.81, 0.0068),
        "水星": (0.3871, 252.25, 149472.67, 0.2056),
    }
    res = {}
    for name, (a, l0, n, e) in planets_elements.items():
        mean_l = math.radians((l0 + n * t) % 360.0)
        true_l = mean_l + 2 * e * math.sin(mean_l)
        xh = a * math.cos(true_l)
        yh = a * math.sin(true_l)
        # 地心向量转换
        xg = xh + x_sun
        yg = yh + y_sun
        geo_deg = math.degrees(math.atan2(yg, xg)) % 360.0
        res[name] = round(geo_deg, 3)
    return res


def locate_mansion(ecliptic_deg: float):
    """
    根据黄经度数判定落入哪一宿及入宿度数。
    严正遵循天文物理序列：危宿(345.92) -> 室宿(353.48跨0度春分点) -> 壁宿(9.15)。
    """
    deg = ecliptic_deg % 360.0

    # 跨 360 度春分点环形处理（室宿从 353.48° 跨至 壁宿 9.15°）
    if deg < 9.15:  # 落入室宿后半段（跨过春分点0度）
        return {
            "mansion_name": "室",
            "constellation": "北方玄武",
            "mansion_start_degree": 353.48,
            "degree_in_mansion": round(deg + (360.0 - 353.48), 2),
        }
    elif deg >= 353.48:  # 落入室宿前半段
        return {
            "mansion_name": "室",
            "constellation": "北方玄武",
            "mansion_start_degree": 353.48,
            "degree_in_mansion": round(deg - 353.48, 2),
        }
    else:
        for i in range(len(MANSIONS_28_SORTED) - 1):
            cur_name, cur_start, cur_xiang = MANSIONS_28_SORTED[i]
            next_start = MANSIONS_28_SORTED[i + 1][1]
            if cur_start <= deg < next_start:
                return {
                    "mansion_name": cur_name,
                    "constellation": cur_xiang,
                    "mansion_start_degree": cur_start,
                    "degree_in_mansion": round(deg - cur_start, 2),
                }

    # 兜底返回壁宿
    return {
        "mansion_name": "壁",
        "constellation": "北方玄武",
        "mansion_start_degree": 9.15,
        "degree_in_mansion": 0.0,
    }


def locate_zodiac_palace(ecliptic_deg: float):
    """判定落入十二地支黄道宫。"""
    deg = ecliptic_deg % 360.0
    for zhi, name, s, e in ZODIAC_12:
        if s <= deg < e:
            return {
                "palace_zhi": zhi,
                "palace_name": name,
                "degree_in_palace": round(deg - s, 2),
            }
    return {"palace_zhi": "戌", "palace_name": "白羊宫", "degree_in_palace": 0.0}


def calculate_qizheng_siyu(dt_utc: datetime):
    """
    求解七政四余（十一曜）全盘星历与二十八宿入宿度。
    :param dt_utc: UTC 日期时间
    :return: dict 包含七政（日月五星）、四余真视黄经、落宫与入宿度
    """
    jdn = datetime_to_jdn(dt_utc)
    sun_deg = get_sun_longitude(jdn)
    moon_deg = get_moon_longitude(jdn)
    siyu = get_four_extras(jdn)
    five_planets = get_five_planets(jdn)

    stars = {
        "太阳": round(sun_deg, 3),
        "太阴": round(moon_deg, 3),
        "木星": five_planets["木星"],
        "火星": five_planets["火星"],
        "土星": five_planets["土星"],
        "金星": five_planets["金星"],
        "水星": five_planets["水星"],
        "罗睺": siyu["罗睺"],
        "计都": siyu["计都"],
        "月孛": siyu["月孛"],
        "紫气": siyu["紫气"],
    }

    full_stars = {}
    for name, deg in stars.items():
        m_info = locate_mansion(deg)
        z_info = locate_zodiac_palace(deg)
        full_stars[name] = {
            "longitude": deg,
            "palace": z_info["palace_zhi"],
            "zodiac": z_info["palace_name"],
            "degree_in_palace": z_info["degree_in_palace"],
            "mansion": m_info["mansion_name"],
            "constellation": m_info["constellation"],
            "degree_in_mansion": m_info["degree_in_mansion"],
        }

    return {
        "utc_time": dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "jdn": round(jdn, 4),
        "stars": full_stars,
        "source": "果老星宗七政四余 IAU J2000 真黄道引擎"
    }
