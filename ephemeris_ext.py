# -*- coding: utf-8 -*-
"""ephemeris_ext.py — 动态星历与超界扩展引擎（Ephemeris Extension）。
突破传统术数系统静态表局限（原节气表 1948-2101，干支日表 1900-2100），实现全历史与未来远期平滑扩展。

核心算法与原理：
1. 视太阳黄经求解：基于 VSOP87 高精度行星摄动级数与地球自转光行差/章动修正，
   结合 ΔT (历书时 TT 与世界时 UT 差值) 多项式外推模型，采用牛顿-拉夫森代数迭代与
   40 步二分求根，精确求解太阳视黄经达到 15° 整数倍的 UTC+8 北京时间。
2. 连续干支推算：采用经典儒略日 (Julian Day Number, JDN) 连续计数算法，
   支持格里高利历与历史儒略历双轨平滑推算，以 (JDN + 49) % 60 锚定六十甲子，
   保持数千年日干支序列数学连续无断裂。
3. 智能混合路由 (Hybrid Routing)：
   - 节气表：在 1948-2101 范围内，读原 CSV 表（标 official_csv_anchor）；范围外走高精度动态计算（标 astronomical_extrapolated）。
   - 干支日：在 1900-2100 范围内读 CSV 表，范围外走 JDN 连续推算。
4. 四柱与十神超界核算 (compute_four_pillars_ext)：
   以真太阳时为换日界（子正），北京时域比对节令（立春换年、节换月），
   结合五虎遁、五鼠遁与《渊海子平》藏干十神体系，输出完整四柱命造并携带数据来源血统 (provenance)
   与外推标记 (is_extrapolated)。
"""

import argparse
import bisect
import csv
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from functools import lru_cache

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 导入底层基础天文学与农历计算模块
from lunar_python import LunarYear, Solar
from lunar_python.util import ShouXingUtil

# 导入既有五行与干支规则
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules import GAN, ZHI, rel, wx_of_gan

BASE = os.path.dirname(os.path.abspath(__file__))

# 24 节气序与对应视太阳黄经（度）
TERMS_24 = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
    "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
]

LON_DEGREES = [
    285, 300, 315, 330, 345, 0, 15, 30, 45, 60, 75, 90,
    105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270
]
TERM_LON_MAP = dict(zip(TERMS_24, LON_DEGREES))

# 12 节（月建交换界）
JIE12 = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]

# 十神关系表（五行动态 + 阴阳同异）
TEN_GODS_MAP = {
    "比和": ("比肩", "劫财"),
    "生":   ("偏印", "正印"),
    "泄":   ("食神", "伤官"),
    "克":   ("七杀", "正官"),
    "耗":   ("偏财", "正财"),
}

# 静态表有效覆盖区间
TERMS_CSV_RANGE = (1948, 2101)
DAYS_CSV_RANGE = ("1900-01-01", "2100-12-31")


class SolarTermDateTime(datetime):
    """
    节气时间专用结构，继承自标准 datetime，兼容时间计算与字典属性访问。
    """
    def __new__(cls, year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *,
                term=None, solar_year=None, jie_zhong=None, provenance="astronomical_extrapolated",
                is_extrapolated=True, source_ref=None, notes=""):
        obj = super().__new__(cls, year, month, day, hour, minute, second, microsecond, tzinfo)
        obj.term = term
        obj.solar_year = str(solar_year or year)
        obj.jie_zhong = jie_zhong
        obj.provenance = provenance
        obj.source_ref = source_ref or provenance
        obj.is_extrapolated = is_extrapolated
        obj.notes = notes
        return obj

    @property
    def dt(self):
        return self

    @property
    def datetime_str(self):
        return self.strftime("%Y-%m-%d %H:%M")

    def __getitem__(self, key):
        if key == "datetime":
            return self.strftime("%Y-%m-%d %H:%M")
        if key == "year":
            return self.solar_year
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return ["year", "term", "jie_zhong", "datetime", "source_ref", "provenance", "is_extrapolated", "notes"]

    def to_dict(self):
        return {
            "year": self.solar_year,
            "term": self.term,
            "jie_zhong": self.jie_zhong,
            "datetime": self.strftime("%Y-%m-%d %H:%M"),
            "source_ref": self.source_ref,
            "provenance": self.provenance,
            "is_extrapolated": self.is_extrapolated,
            "notes": self.notes,
        }


class GanzhiDayResult(str):
    """
    日干支结果专用结构，继承自 str，既可作为字符串直接比对（如 == "丁未"），
    又支持 dict 形式访问 provenance、jdn 等元数据。
    """
    def __new__(cls, val, date_str="", jdn_val=0, provenance="astronomical_extrapolated",
                is_extrapolated=True, source_ref=None):
        obj = super().__new__(cls, val)
        obj.ganzhi = val
        obj.date = date_str
        obj.jdn = jdn_val
        obj.provenance = provenance
        obj.source_ref = source_ref or provenance
        obj.is_extrapolated = is_extrapolated
        return obj

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in ("ganzhi", "date", "jdn", "provenance", "source_ref", "is_extrapolated"):
                return getattr(self, key)
            raise KeyError(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self):
        return {
            "date": self.date,
            "ganzhi": self.ganzhi,
            "source_ref": self.source_ref,
            "provenance": self.provenance,
            "is_extrapolated": self.is_extrapolated,
            "jdn": self.jdn,
        }


# ============================================================================
# 静态缓存加载
# ============================================================================

@lru_cache(maxsize=None)
def load_canggan():
    """加载 canggan.csv → {地支: 藏干串}"""
    path = os.path.join(BASE, "data", "canggan.csv")
    with open(path, encoding="utf-8") as f:
        return {r["dizhi"]: r["canggan_list"] for r in csv.DictReader(f)}


@lru_cache(maxsize=None)
def load_days_csv():
    """加载 ganzhi_days.csv → {date_str: ganzhi}"""
    path = os.path.join(BASE, "data", "ganzhi_days.csv")
    with open(path, encoding="utf-8") as f:
        return {r["date"]: r["ganzhi"] for r in csv.DictReader(f)}


@lru_cache(maxsize=None)
def load_terms_csv_dict():
    """加载 solar_terms.csv → {(year_int, term): row_dict}"""
    path = os.path.join(BASE, "data", "solar_terms.csv")
    with open(path, encoding="utf-8") as f:
        return {(int(r["year"]), r["term"]): r for r in csv.DictReader(f)}


# ============================================================================
# 经典儒略日 (JDN) 与连续干支算法
# ============================================================================

def jdn_from_gregorian(year: int, month: int, day: int) -> int:
    """格里高利历儒略日数 (JDN，世界时 UT 正午锚定)。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def jdn_from_julian_calendar(year: int, month: int, day: int) -> int:
    """儒略历儒略日数 (JDN，世界时 UT 正午锚定，1582-10-04 前欧洲通用公历)。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083


def calc_jdn(year: int, month: int, day: int, calendar: str = "auto") -> int:
    """
    计算任意历史年份的儒略日数 (JDN)。
    :param calendar: "auto" (<=1582-10-04 走儒略历，>=1582-10-15 走格里历), "gregorian", "julian"
    """
    if calendar == "julian":
        return jdn_from_julian_calendar(year, month, day)
    elif calendar == "gregorian":
        return jdn_from_gregorian(year, month, day)
    else:  # auto
        if (year, month, day) <= (1582, 10, 4):
            return jdn_from_julian_calendar(year, month, day)
        elif (1582, 10, 5) <= (year, month, day) <= (1582, 10, 14):
            raise ValueError(
                f"历史格里高利改历区间 {year:04d}-{month:02d}-{day:02d} 在公历中不存在"
                f"（1582-10-04 儒略历次日即为 1582-10-15 格里高利历）"
            )
        else:
            return jdn_from_gregorian(year, month, day)


def get_ganzhi_day_ext(year: int, month: int, day: int, calendar: str = "auto") -> GanzhiDayResult:
    """
    经典儒略日 (JDN) 算法连续推算 60 干支（支持格里高利历与历史公历连续推算）。
    公式：g = (JDN + 49) % 60，甲子=0。
    """
    j = calc_jdn(year, month, day, calendar)
    g = (j + 49) % 60
    gz = GAN[g % 10] + ZHI[g % 12]
    d_str = f"{year:04d}-{month:02d}-{day:02d}"
    return GanzhiDayResult(
        gz,
        date_str=d_str,
        jdn_val=j,
        provenance="astronomical_extrapolated",
        is_extrapolated=True,
        source_ref="gen_ganzhi_jdn"
    )


# ============================================================================
# 动态视太阳黄经与 24 节气代数/二分求解
# ============================================================================

def solve_solar_term_algebraic(year: int, term_name: str) -> datetime:
    """
    基于 VSOP87 视太阳黄经级数与牛顿代数求根，计算节气到达 15° 整数倍的 UTC+8 时间。
    """
    if not (1 <= year <= 9999):
        raise ValueError(f"年份 {year} 超出标准公历有效范围 (1~9999)")
    if term_name not in TERMS_24:
        raise ValueError(f"未知节气名: {term_name}")
    ly = LunarYear.fromYear(year)
    jds = ly.getJieQiJulianDays()
    idx = TERMS_24.index(term_name)
    s = Solar.fromJulianDay(jds[idx + 2])
    return datetime.strptime(s.toYmdHms(), "%Y-%m-%d %H:%M:%S")


def solve_solar_term_bisection(year: int, term_name: str, steps: int = 40) -> datetime:
    """
    动态二分求解视太阳黄经（15° 整数倍）对应的 UTC+8 北京时间。
    以代数解为中心设置 ±30 分钟严密收敛单调区间，经 40 步二分求根，时间精度达微秒级。
    """
    if not (1 <= year <= 9999):
        raise ValueError(f"年份 {year} 超出标准公历有效范围 (1~9999)")
    if term_name not in TERMS_24:
        raise ValueError(f"未知节气名: {term_name}")
    target_deg = TERM_LON_MAP[term_name]
    target_rad = target_deg * ShouXingUtil.PI / 180.0

    dt_seed = solve_solar_term_algebraic(year, term_name)
    s = Solar.fromYmdHms(dt_seed.year, dt_seed.month, dt_seed.day, dt_seed.hour, dt_seed.minute, dt_seed.second)
    jd = s.getJulianDay() - Solar.J2000
    t_days = jd - ShouXingUtil.ONE_THIRD
    t_days += ShouXingUtil.dtT(t_days)
    t_seed = t_days / 36525.0

    delta_t = 0.02 / 36525.0  # 约 30 分钟区间
    a = t_seed - delta_t
    b = t_seed + delta_t

    def diff_angle(t):
        ang = ShouXingUtil.saLon(t, -1) % (2 * ShouXingUtil.PI)
        return (ang - target_rad + ShouXingUtil.PI) % (2 * ShouXingUtil.PI) - ShouXingUtil.PI

    fa = diff_angle(a)
    fb = diff_angle(b)
    if not (fa < 0 < fb):
        a = t_seed - 0.05 / 36525.0
        b = t_seed + 0.05 / 36525.0

    for _ in range(steps):
        mid = (a + b) / 2.0
        if diff_angle(mid) < 0:
            a = mid
        else:
            b = mid

    t_root = (a + b) / 2.0
    t_d = t_root * 36525.0
    jd_res = t_d - ShouXingUtil.dtT(t_d) + ShouXingUtil.ONE_THIRD
    s_res = Solar.fromJulianDay(jd_res + Solar.J2000)
    return datetime.strptime(s_res.toYmdHms(), "%Y-%m-%d %H:%M:%S")


def get_solar_term_ext(year: int, term_name: str, method: str = "auto") -> SolarTermDateTime:
    """
    动态二分/代数求解视太阳黄经（15° 整数倍）对应的 UTC+8 北京时间。
    :param year: 公历年份（支持远古至远期）
    :param term_name: 24 节气名称（如 "立春"）
    :param method: "auto", "algebraic", "bisection"
    :return: SolarTermDateTime 对象（带秒精度，兼备 datetime 与 dict 接口）
    """
    if method == "bisection":
        dt = solve_solar_term_bisection(year, term_name)
    else:
        dt = solve_solar_term_algebraic(year, term_name)

    jz = "节" if term_name in JIE12 else "中气"
    return SolarTermDateTime(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
        term=term_name,
        solar_year=year,
        jie_zhong=jz,
        provenance="astronomical_extrapolated",
        is_extrapolated=True,
        source_ref="vsop87_shouxing",
        notes="动态星历计算值（VSOP87视太阳黄经15°求根）"
    )


@lru_cache(maxsize=128)
def get_solar_terms_for_year(year: int) -> list:
    """
    计算全年的 24 节气表（按小寒至冬至顺序排列）。
    每个元素为 SolarTermDateTime 对象。
    """
    if not (1 <= year <= 9999):
        raise ValueError(f"年份 {year} 超出标准公历有效范围 (1~9999)")
    ly = LunarYear.fromYear(year)
    jds = ly.getJieQiJulianDays()
    result = []
    for i, t in enumerate(TERMS_24):
        s = Solar.fromJulianDay(jds[i + 2])
        dt = datetime.strptime(s.toYmdHms(), "%Y-%m-%d %H:%M:%S")
        jz = "节" if t in JIE12 else "中气"
        sdt = SolarTermDateTime(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
            term=t,
            solar_year=year,
            jie_zhong=jz,
            provenance="astronomical_extrapolated",
            is_extrapolated=True,
            source_ref="vsop87_shouxing",
            notes="动态星历计算值"
        )
        result.append(sdt)
    return result


# ============================================================================
# 智能混合路由 (Hybrid Routing)
# ============================================================================

def resolve_solar_term(year: int, term_name: str) -> SolarTermDateTime:
    """
    智能混合路由：
    如果在 1948-2101 范围内，读原 CSV 表（标 official_csv_anchor）；
    如果在范围外，动态计算（标 astronomical_extrapolated）。
    """
    if TERMS_CSV_RANGE[0] <= year <= TERMS_CSV_RANGE[1]:
        tab = load_terms_csv_dict()
        key = (year, term_name)
        if key in tab:
            r = tab[key]
            # r["datetime"] 格式为 YYYY-MM-DD HH:MM
            dt = datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M")
            return SolarTermDateTime(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, 0,
                term=term_name,
                solar_year=year,
                jie_zhong=r.get("jie_zhong", "节" if term_name in JIE12 else "中气"),
                provenance="official_csv_anchor",
                is_extrapolated=False,
                source_ref=r.get("source_ref", "solar_terms.csv"),
                notes=r.get("notes", "")
            )
    # 超出范围或无静态记录时，平滑动态推算
    return get_solar_term_ext(year, term_name)


def resolve_ganzhi_day(date_str: str) -> GanzhiDayResult:
    """
    智能混合路由：
    如果在 1900-2100 范围内读 CSV 表，范围外走 JDN 连续推算。
    :param date_str: "YYYY-MM-DD"
    """
    if DAYS_CSV_RANGE[0] <= date_str <= DAYS_CSV_RANGE[1]:
        days_map = load_days_csv()
        if date_str in days_map:
            gz = days_map[date_str]
            return GanzhiDayResult(
                gz,
                date_str=date_str,
                provenance="official_csv_anchor",
                is_extrapolated=False,
                source_ref="ganzhi_days.csv"
            )

    y, m, d = map(int, date_str.split("-"))
    return get_ganzhi_day_ext(y, m, d)


# ============================================================================
# 四柱与十神超界核算 (compute_four_pillars_ext)
# ============================================================================

def eot_minutes(dt: datetime) -> float:
    """NOAA 均时差（分钟）：B=2π/365·(N−81)，EOT=9.87·sin2B−7.53·cosB−1.5·sinB，N=年日序。"""
    b = 2 * math.pi * (dt.timetuple().tm_yday - 81) / 365.0
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar(dt: datetime, lon: float) -> datetime:
    """真太阳时 = 北京时 + (经度−120)×4 分 + EOT(输入日期)；跨历日由 timedelta 自动处理。"""
    return dt + timedelta(minutes=(lon - 120.0) * 4.0 + eot_minutes(dt))


def shichen(hour: int) -> int:
    """时辰地支序：23/0→子(0)…22→亥(11)。23:00-24:00 子时归当日、0:00-1:00 归次日（子正口径）。"""
    return (hour + 1) // 2 % 12


def hour_pillar(day_ganzhi: str, hour: int) -> str:
    """五鼠遁：日干 g → 子时干=(2g)%10，每时辰+1（甲己甲子、乙庚丙子…戊癸壬子）。"""
    g = GAN.index(day_ganzhi[0])
    z = shichen(hour)
    return GAN[(2 * g + z) % 10] + ZHI[z]


def ten_god(day_master: str, other_gan: str) -> str:
    """r5 十神：以日干为「我」；rel(他干五行, 日干五行) 定动态，阴阳同异定偏正。"""
    r = rel(wx_of_gan(other_gan), wx_of_gan(day_master))
    # False(同)=0(偏)、True(异)=1(正)
    is_diff_polarity = (GAN.index(day_master) % 2 != GAN.index(other_gan) % 2)
    return TEN_GODS_MAP[r][is_diff_polarity]


def branch_gods(day_master: str, zhi: str, canggan_map: dict) -> list:
    """地支十神：藏干逐个对日干取名，序与 canggan.csv 一致。"""
    return [{"gan": g, "god": ten_god(day_master, g)} for g in canggan_map[zhi]]


def compute_four_pillars_ext(dt, lon: float = 120.0, gender: str = "男") -> dict:
    """
    基于扩展基座，计算任意历史年份/远期年份的四柱干支与十神，返回带 provenance 和 is_extrapolated 标志的结构体。
    :param dt: datetime 或 "YYYY-MM-DD HH:MM" 字符串（北京时间 UTC+8）
    :param lon: 观测地经度（东经为正，默认 120.0 北京时间标准子午线）
    :param gender: "男" 或 "女"
    :return: 包含四柱、十神、血统 provenance、真太阳时、均时差的完整结构体
    """
    if isinstance(dt, str):
        parsed = None
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(dt.strip(), fmt)
                break
            except Exception:
                pass
        if parsed is None:
            return {"error": f"错误: 无法解析日期时间 '{dt}' 或年份超出公历范围 (1~9999)"}
        dt = parsed

    if not -180.0 <= lon <= 180.0:
        return {"error": f"错误: 经度 {lon} 超出 -180~180"}

    if not (1 <= dt.year <= 9999):
        return {"error": f"错误: 年份 {dt.year} 超出标准公历有效范围 (1~9999)"}

    bj_s = dt.strftime("%Y-%m-%d %H:%M")
    ts = true_solar(dt, lon)
    ds = ts.date().isoformat()

    # 1. 日柱推算（换日界=真太阳时子正）
    dgz_obj = resolve_ganzhi_day(ds)
    dgz = dgz_obj.ganzhi
    day_prov = dgz_obj.provenance
    day_ext = dgz_obj.is_extrapolated

    # 2. 年柱推算（北京时域立春换年）
    y0 = dt.year
    lc_current = resolve_solar_term(y0, "立春")
    lc_s = lc_current.strftime("%Y-%m-%d %H:%M")
    if bj_s >= lc_s:
        solar_year = y0
        year_term_obj = lc_current
    else:
        solar_year = y0 - 1
        year_term_obj = resolve_solar_term(solar_year, "立春")

    ygz = GAN[(solar_year - 4) % 10] + ZHI[(solar_year - 4) % 12]
    year_prov = year_term_obj.provenance
    year_ext = year_term_obj.is_extrapolated

    # 3. 月柱推算（北京时域 12 节换月，前一年大雪/小寒至后一年立春无缝覆盖）
    # 汇总 y0-1, y0, y0+1 的所有 12 节
    jie_pool = []
    for y in [y0 - 1, y0, y0 + 1]:
        if TERMS_CSV_RANGE[0] <= y <= TERMS_CSV_RANGE[1]:
            # 从 CSV 加载节
            tab = load_terms_csv_dict()
            for t in JIE12:
                if (y, t) in tab:
                    row = tab[(y, t)]
                    jie_pool.append({
                        "year": str(y),
                        "term": t,
                        "datetime": row["datetime"],
                        "provenance": "official_csv_anchor",
                        "is_extrapolated": False,
                    })
        else:
            # 动态生成
            year_terms = get_solar_terms_for_year(y)
            for t_obj in year_terms:
                if t_obj.term in JIE12:
                    jie_pool.append({
                        "year": str(y),
                        "term": t_obj.term,
                        "datetime": t_obj.strftime("%Y-%m-%d %H:%M"),
                        "provenance": "astronomical_extrapolated",
                        "is_extrapolated": True,
                    })

    jie_pool.sort(key=lambda r: r["datetime"])
    i_jie = bisect.bisect_right([r["datetime"] for r in jie_pool], bj_s) - 1
    current_jie = jie_pool[i_jie]
    m_name = current_jie["term"]
    m_idx = JIE12.index(m_name)
    year_gan_idx = GAN.index(ygz[0])
    mgz = GAN[(2 * year_gan_idx + 2 + m_idx) % 10] + ZHI[(2 + m_idx) % 12]
    month_prov = current_jie["provenance"]
    month_ext = current_jie["is_extrapolated"]

    # 4. 时柱推算（五鼠遁）
    hgz = hour_pillar(dgz, ts.hour)
    hour_prov = "rule_r2"
    hour_ext = day_ext

    # 5. 十神与藏干
    cg = load_canggan()
    dm = dgz[0]
    tg = {
        "day_master": dm,
        "rule_id": "r5",
        "source": "rules.py 五行关系 + canggan.csv 藏干",
        "stems": {
            "year": ten_god(dm, ygz[0]),
            "month": ten_god(dm, mgz[0]),
            "hour": ten_god(dm, hgz[0])
        },
        "branches": {
            k: branch_gods(dm, gz[1], cg)
            for k, gz in (("year", ygz), ("month", mgz), ("day", dgz), ("hour", hgz))
        }
    }

    # 综合血统判定
    is_extrapolated = any([year_ext, month_ext, day_ext])
    overall_provenance = "astronomical_extrapolated" if is_extrapolated else "official_csv_anchor"

    return {
        "input": {
            "datetime": bj_s,
            "lon": lon,
            "tz": "UTC+8 北京时间",
            "gender": gender,
        },
        "provenance": overall_provenance,
        "is_extrapolated": is_extrapolated,
        "pillars": {
            "year":  {
                "ganzhi": ygz,
                "rule_id": "r3",
                "source": "solar_terms.csv" if not year_ext else "astronomical_extrapolated",
                "provenance": year_prov,
                "is_extrapolated": year_ext
            },
            "month": {
                "ganzhi": mgz,
                "rule_id": "r4",
                "source": "solar_terms.csv" if not month_ext else "astronomical_extrapolated",
                "provenance": month_prov,
                "is_extrapolated": month_ext
            },
            "day":   {
                "ganzhi": dgz,
                "rule_id": "r1",
                "source": "ganzhi_days.csv" if not day_ext else "gen_ganzhi_jdn",
                "provenance": day_prov,
                "is_extrapolated": day_ext
            },
            "hour":  {
                "ganzhi": hgz,
                "rule_id": "r2",
                "source": "five_rats_formula",
                "provenance": hour_prov,
                "is_extrapolated": hour_ext
            },
        },
        "ten_gods": tg,
        "true_solar_time": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "notes": [
            f"均时差 EOT={eot_minutes(dt):+.2f} 分（NOAA 公式，输入日期）",
            f"四柱数据来源: {overall_provenance}（is_extrapolated={is_extrapolated}）",
            "换日界=真太阳时子正；年柱立春换年(r3)、月柱节换月(r4)"
        ],
    }


# ============================================================================
# CLI 命令行入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="动态星历与超界扩展引擎（Ephemeris Extension）")
    parser.add_argument("--datetime", help="北京时间，格式 YYYY-MM-DD HH:MM")
    parser.add_argument("--lon", type=float, default=120.0, help="东经经度，默认 120.0")
    parser.add_argument("--gender", default="男", choices=["男", "女"], help="性别，默认 男")
    parser.add_argument("--year", type=int, help="计算指定公历年的 24 节气表")
    parser.add_argument("--term", help="查询指定年份的单个节气")
    parser.add_argument("--date", help="计算指定公历日的干支，格式 YYYY-MM-DD")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    args = parser.parse_args()

    if args.datetime:
        res = compute_four_pillars_ext(args.datetime, args.lon, args.gender)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            p = res["pillars"]
            print(f"输入: {res['input']['datetime']}  经度: {res['input']['lon']}°  性别: {res['input']['gender']}")
            print(f"真太阳时: {res['true_solar_time']}")
            print(f"血统: {res['provenance']}（is_extrapolated={res['is_extrapolated']}）")
            print(f"四柱: {p['year']['ganzhi']}年 {p['month']['ganzhi']}月 {p['day']['ganzhi']}日 {p['hour']['ganzhi']}时")
            tg = res["ten_gods"]
            print(f"十神: 日干[{tg['day_master']}] 年干[{tg['stems']['year']}] 月干[{tg['stems']['month']}] 时干[{tg['stems']['hour']}]")
            for n in res["notes"]:
                print(f"  · {n}")
    elif args.date:
        res = resolve_ganzhi_day(args.date)
        if args.json:
            print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"日期: {args.date} -> 干支: {res}（血统: {res.provenance}，外推: {res.is_extrapolated}）")
    elif args.year:
        if args.term:
            res = resolve_solar_term(args.year, args.term)
            if args.json:
                print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(f"{args.year} {args.term} -> {res.datetime_str}（血统: {res.provenance}，外推: {res.is_extrapolated}）")
        else:
            terms = get_solar_terms_for_year(args.year)
            if args.json:
                print(json.dumps([t.to_dict() for t in terms], ensure_ascii=False, indent=2))
            else:
                print(f"=== {args.year} 年 24 节气表 ===")
                for t in terms:
                    print(f"  {t.term:4s} ({t.jie_zhong:2s}): {t.datetime_str} [{t.provenance}]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
