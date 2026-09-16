# -*- coding: utf-8 -*-
"""shushu_context.py — 强类型不可变领域模型与统一时空上下文容器

根治传统术数系统中的三大顽疾：
1. 演算错误与越界 (Off-by-one / Inversion / Out-of-bounds)
2. 跨模块接口不一致 (String/Tuple/Dict 混乱，时空口径漂移)
3. 动态数据被篡改与污染 (基于 data_static_tables.py 纯内存只读底座)

核心模型：
- PillarInfo: 单柱强类型不可变数据对象（含干、支、藏干、十神、纳音）
- StandardPillars: 四柱强类型不可变领域对象（含60甲子契约校验与多格式投影）
- SolarTermInfo: 节气时空锚点
- LunarInfo: 农历时空锚点
- SchoolConfig: 流派配置强契约
- ShushuContext: 统一全息时空上下文（Single Source of Truth），所有 L2/L3 算法的唯一标准输入
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import data_static_tables as dst
import l1_timezone as tz_mod
import m1

GAN_LIST = "甲乙丙丁戊己庚辛壬癸"
ZHI_LIST = "子丑寅卯辰巳午未申酉戌亥"

# 六十甲子标准表
JIAZI_60 = tuple(
    GAN_LIST[i % 10] + ZHI_LIST[i % 12] for i in range(60)
)
JIAZI_SET = set(JIAZI_60)


@dataclass(frozen=True)
class PillarInfo:
    """单柱强类型领域模型 (Immutable)"""
    gan: str
    zhi: str
    ganzhi: str
    nayin: str
    canggan: Tuple[Tuple[str, str], ...]  # ((藏干, 角色), ...)
    ten_god: Optional[str] = None         # 天干相对日主之十神
    canggan_ten_gods: Tuple[Tuple[str, str, str], ...] = ()  # ((藏干, 角色, 十神), ...)

    def __post_init__(self):
        if self.ganzhi not in JIAZI_SET:
            raise ValueError(f"不合法的干支组合: '{self.ganzhi}' (不在六十甲子中)")
        if self.gan != self.ganzhi[0] or self.zhi != self.ganzhi[1]:
            raise ValueError(f"干支与分项不一致: '{self.ganzhi}' vs '{self.gan}', '{self.zhi}'")


@dataclass(frozen=True)
class StandardPillars:
    """四柱强类型领域模型 (Immutable)"""
    year: PillarInfo
    month: PillarInfo
    day: PillarInfo
    hour: PillarInfo
    day_master: str

    def to_list(self) -> List[str]:
        """投影为干支字符串列表: ['甲子', '丙寅', ...]"""
        return [self.year.ganzhi, self.month.ganzhi, self.day.ganzhi, self.hour.ganzhi]

    def to_dict(self) -> Dict[str, str]:
        """投影为干支字典"""
        return {
            "year": self.year.ganzhi,
            "month": self.month.ganzhi,
            "day": self.day.ganzhi,
            "hour": self.hour.ganzhi,
        }

    def to_tuple(self) -> Tuple[str, str, str, str]:
        """投影为干支四元组"""
        return (self.year.ganzhi, self.month.ganzhi, self.day.ganzhi, self.hour.ganzhi)

    def to_full_dict(self) -> Dict[str, Any]:
        """投影为包含藏干与十神的结构化字典"""
        return {
            "day_master": self.day_master,
            "year": {
                "ganzhi": self.year.ganzhi,
                "gan": self.year.gan,
                "zhi": self.year.zhi,
                "nayin": self.year.nayin,
                "ten_god": self.year.ten_god,
                "canggan": self.year.canggan,
                "canggan_ten_gods": self.year.canggan_ten_gods,
            },
            "month": {
                "ganzhi": self.month.ganzhi,
                "gan": self.month.gan,
                "zhi": self.month.zhi,
                "nayin": self.month.nayin,
                "ten_god": self.month.ten_god,
                "canggan": self.month.canggan,
                "canggan_ten_gods": self.month.canggan_ten_gods,
            },
            "day": {
                "ganzhi": self.day.ganzhi,
                "gan": self.day.gan,
                "zhi": self.day.zhi,
                "nayin": self.day.nayin,
                "ten_god": self.day.ten_god,
                "canggan": self.day.canggan,
                "canggan_ten_gods": self.day.canggan_ten_gods,
            },
            "hour": {
                "ganzhi": self.hour.ganzhi,
                "gan": self.hour.gan,
                "zhi": self.hour.zhi,
                "nayin": self.hour.nayin,
                "ten_god": self.hour.ten_god,
                "canggan": self.hour.canggan,
                "canggan_ten_gods": self.hour.canggan_ten_gods,
            },
        }


@dataclass(frozen=True)
class SolarTermInfo:
    """二十四节气时空状态 (Immutable)"""
    current_term: str
    current_term_time: str
    current_jie_zhong: str
    next_term: Optional[str] = None
    next_term_time: Optional[str] = None


@dataclass(frozen=True)
class LunarInfo:
    """农历时空状态 (Immutable)"""
    lunar_year_gz: str
    lunar_year: int
    lunar_month: int
    lunar_day: int
    is_leap: bool
    shuo_date: str
    shuo_time: str
    wang_time: str


@dataclass(frozen=True)
class SchoolConfig:
    """流派与算法仲裁配置 (Immutable)"""
    zi_hour_mode: str = "zi_zheng"             # "zi_zheng" (子正换日 00:00) | "zi_chu" (子初换日 23:00)
    southern_hemisphere: str = "astronomical"  # "astronomical" (天文黄经派) | "clash_month" (月支对冲派)
    ziwei_sihua_geng: str = "qu_dao_tong"     # "qu_dao_tong" (全书/全集: 阳武府同) | "zhongzhou" (中州: 阳武阴同)
    qimen_central_palace: str = "kun2_or_gen8" # "kun2_or_gen8" (寄坤二/寄艮八)


@dataclass(frozen=True)
class UserRealityContext:
    """现实基线与历史锚点上下文 (Reality Anchor & Calibration, Immutable)"""
    profession_stage: str = "未定/通用"       # "学生", "体制内/公职", "企业/市场", "自由职业/创业"
    education_level: str = "高等教育/在读"     # "基础教育", "本科在读", "硕博深造", "已步入社会"
    past_stability: str = "平稳有序"           # "平稳有序", "中度折腾", "重大挫折/动荡"
    health_baseline: str = "基本良好"          # "基本良好", "呼吸道敏感", "神经衰弱/失眠", "慢性病灶"
    primary_concern: str = "综合发展"          # "学业升学", "职业定向", "财富规划", "情感婚姻", "健康调理"


@dataclass(frozen=True)
class ShushuContext:
    """统一全息时空上下文容器 (Single Source of Truth, Immutable)"""
    wall_time: datetime
    utc_time: datetime
    beijing_time: datetime
    true_solar_time: datetime
    longitude: float
    latitude: float
    timezone_name: str
    is_dst: bool
    dst_offset_minutes: float
    gender: str
    pillars: StandardPillars
    solar_term: SolarTermInfo
    lunar_date: LunarInfo
    school_config: SchoolConfig
    reality_context: UserRealityContext = field(default_factory=UserRealityContext)

    @classmethod
    def build(
        cls,
        wall_time_input: Any,
        longitude: float = 120.0,
        latitude: float = 35.0,
        gender: str = "男",
        tz_name: str = "Asia/Shanghai",
        school_config: Optional[SchoolConfig] = None,
        reality_context: Optional[UserRealityContext] = None,
    ) -> "ShushuContext":
        """
        统一上下文构建工厂。
        完成时区解算、真太阳时计算、历法对账与四柱标准构建，并执行防御性断言。
        """
        if school_config is None:
            school_config = SchoolConfig()

        # 1. 解析输入时间
        if isinstance(wall_time_input, str):
            s = wall_time_input.strip()
            parsed = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    pass
            if parsed is None:
                raise ValueError(f"无法解析时间字符串: '{wall_time_input}'")
            wall_dt = parsed.replace(second=0, microsecond=0)
        elif isinstance(wall_time_input, datetime):
            wall_dt = wall_time_input.replace(second=0, microsecond=0)
        else:
            raise TypeError(f"不支持的时间输入类型: {type(wall_time_input)}")

        # 2. 全球时区与夏令时解析 (l1_timezone)
        tz_res = tz_mod.resolve_global_time(wall_dt, tz_name, longitude, latitude)
        utc_dt = datetime.fromisoformat(tz_res["utc_time"])
        bj_dt = datetime.fromisoformat(tz_res["beijing_time"])
        true_solar_dt = datetime.fromisoformat(tz_res["true_solar_time"])

        # 3. 计算四柱 (m1.compute，以基准北京时驱动)
        m1_res = m1.compute(bj_dt, longitude)
        if "error" in m1_res:
            raise ValueError(f"M1 计算错误: {m1_res['error']}")

        # 4. 南半球处理 (若适用)
        base_pillars = [
            m1_res["pillars"]["year"]["ganzhi"],
            m1_res["pillars"]["month"]["ganzhi"],
            m1_res["pillars"]["day"]["ganzhi"],
            m1_res["pillars"]["hour"]["ganzhi"],
        ]
        if latitude < 0 and school_config.southern_hemisphere == "clash_month":
            route_res = tz_mod.resolve_southern_hemisphere_pillars(base_pillars, latitude, "clash_month")
            resolved_p = route_res["pillars"]
        else:
            resolved_p = base_pillars

        dm = resolved_p[2][0]

        # 5. 构建 PillarInfo 实例
        def _make_pillar(gz: str, is_day: bool = False) -> PillarInfo:
            g, z = gz[0], gz[1]
            ny = dst.NAYIN_MAP[gz]
            cg_items = dst.CANGGAN_MAP[z]
            tg = "日元" if is_day else m1.ten_god(dm, g)
            cg_tg_items = tuple(
                (cg, role, m1.ten_god(dm, cg)) for cg, role in cg_items
            )
            return PillarInfo(
                gan=g,
                zhi=z,
                ganzhi=gz,
                nayin=ny,
                canggan=cg_items,
                ten_god=tg,
                canggan_ten_gods=cg_tg_items,
            )

        pillars = StandardPillars(
            year=_make_pillar(resolved_p[0]),
            month=_make_pillar(resolved_p[1]),
            day=_make_pillar(resolved_p[2], is_day=True),
            hour=_make_pillar(resolved_p[3]),
            day_master=dm,
        )

        # 6. 获取节气时空信息 (data_static_tables)
        term_dict = dst.get_term_for_datetime(bj_dt)
        solar_term = SolarTermInfo(
            current_term=term_dict["current_term"],
            current_term_time=term_dict["current_term_time"],
            current_jie_zhong=term_dict["current_jie_zhong"],
            next_term=term_dict.get("next_term"),
            next_term_time=term_dict.get("next_term_time"),
        )

        # 7. 获取农历信息 (data_static_tables)
        shuo_dict = dst.get_shuo_for_date(bj_dt.date())
        lunar_date = LunarInfo(
            lunar_year_gz=shuo_dict["lunar_year_gz"],
            lunar_year=int(shuo_dict["shuo_date"][:4]),
            lunar_month=shuo_dict["lunar_month"],
            lunar_day=shuo_dict["lunar_day"],
            is_leap=shuo_dict["is_leap"],
            shuo_date=shuo_dict["shuo_date"],
            shuo_time=shuo_dict["shuo_time"],
            wang_time=shuo_dict["wang_time"],
        )

        # 8. 严格数学不变性校验 (Invariants)
        assert len(pillars.to_list()) == 4, "四柱必须为 4 柱"
        assert 1 <= lunar_date.lunar_day <= 30, f"农历日序越界: {lunar_date.lunar_day}"
        assert 1 <= lunar_date.lunar_month <= 12, f"农历月序越界: {lunar_date.lunar_month}"

        return cls(
            wall_time=wall_dt,
            utc_time=utc_dt,
            beijing_time=bj_dt,
            true_solar_time=true_solar_dt,
            longitude=longitude,
            latitude=latitude,
            timezone_name=tz_name,
            is_dst=tz_res["is_dst"],
            dst_offset_minutes=tz_res["dst_offset_minutes"],
            gender=gender,
            pillars=pillars,
            solar_term=solar_term,
            lunar_date=lunar_date,
            school_config=school_config,
            reality_context=reality_context if reality_context is not None else UserRealityContext(),
        )

    @classmethod
    def from_pillars(
        cls,
        year_gz: str,
        month_gz: str,
        day_gz: str,
        hour_gz: str,
        gender: str = "男",
        school_config: Optional[SchoolConfig] = None,
    ) -> "ShushuContext":
        """
        从纯干支四柱构建上下文（支持古籍案例、命理设课与推演分析）。
        自动补齐日主、十神、纳音与地支藏干。
        """
        if school_config is None:
            school_config = SchoolConfig()

        for gz in (year_gz, month_gz, day_gz, hour_gz):
            if gz not in JIAZI_SET:
                raise ValueError(f"不合法的干支组合: '{gz}'")

        dm = day_gz[0]

        def _make_pillar(gz: str, is_day: bool = False) -> PillarInfo:
            g, z = gz[0], gz[1]
            ny = dst.NAYIN_MAP[gz]
            cg_items = dst.CANGGAN_MAP[z]
            tg = "日元" if is_day else m1.ten_god(dm, g)
            cg_tg_items = tuple(
                (cg, role, m1.ten_god(dm, cg)) for cg, role in cg_items
            )
            return PillarInfo(
                gan=g,
                zhi=z,
                ganzhi=gz,
                nayin=ny,
                canggan=cg_items,
                ten_god=tg,
                canggan_ten_gods=cg_tg_items,
            )

        pillars = StandardPillars(
            year=_make_pillar(year_gz),
            month=_make_pillar(month_gz),
            day=_make_pillar(day_gz, is_day=True),
            hour=_make_pillar(hour_gz),
            day_master=dm,
        )

        dummy_dt = datetime(2000, 1, 1, 0, 0)
        dummy_term = SolarTermInfo(current_term="未知", current_term_time="", current_jie_zhong="")
        dummy_lunar = LunarInfo(
            lunar_year_gz=year_gz, lunar_year=2000, lunar_month=1, lunar_day=1,
            is_leap=False, shuo_date="", shuo_time="", wang_time=""
        )

        return cls(
            wall_time=dummy_dt,
            utc_time=dummy_dt,
            beijing_time=dummy_dt,
            true_solar_time=dummy_dt,
            longitude=120.0,
            latitude=35.0,
            timezone_name="Asia/Shanghai",
            is_dst=False,
            dst_offset_minutes=0.0,
            gender=gender,
            pillars=pillars,
            solar_term=dummy_term,
            lunar_date=dummy_lunar,
            school_config=school_config,
        )
