# -*- coding: utf-8 -*-
"""assert_shushu_context.py — 验证强类型不可变领域模型与时空上下文容器契约"""

import os
import sys
from dataclasses import FrozenInstanceError
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from shushu_context import (
    PillarInfo,
    StandardPillars,
    SchoolConfig,
    ShushuContext,
    JIAZI_SET,
)

def test_pillar_info():
    # 1. 正常构造
    p = PillarInfo(
        gan="甲",
        zhi="子",
        ganzhi="甲子",
        nayin="海中金",
        canggan=(("癸", "本气"),),
        ten_god="比肩",
    )
    assert p.gan == "甲"
    assert p.zhi == "子"
    assert p.ganzhi == "甲子"
    assert p.nayin == "海中金"

    # 2. 尝试非法修改 (不可变性检查)
    try:
        p.gan = "乙"
        assert False, "Should raise FrozenInstanceError"
    except FrozenInstanceError:
        pass

    # 3. 非法干支组合检查
    try:
        PillarInfo(
            gan="甲",
            zhi="丑",
            ganzhi="甲丑",  # 甲丑不在六十甲子中 (阳干配阴支非法)
            nayin="海中金",
            canggan=(("己", "本气"),),
        )
        assert False, "Should raise ValueError for invalid ganzhi"
    except ValueError as e:
        assert "不合法的干支组合" in str(e)

    print("  [PASS] PillarInfo 领域模型与强类型防错校验成功")

def test_standard_pillars_projections():
    ctx = ShushuContext.from_pillars("丙戌", "甲午", "乙酉", "丙子", gender="女")
    p = ctx.pillars
    assert p.day_master == "乙"
    assert p.to_list() == ["丙戌", "甲午", "乙酉", "丙子"]
    assert p.to_tuple() == ("丙戌", "甲午", "乙酉", "丙子")
    assert p.to_dict()["day"] == "乙酉"

    full = p.to_full_dict()
    assert full["day_master"] == "乙"
    assert full["year"]["nayin"] == "屋上土"
    assert full["month"]["ten_god"] == "劫财"  # 甲木见乙木为劫财
    assert full["year"]["ten_god"] == "伤官"   # 丙火见乙木为伤官
    print("  [PASS] StandardPillars 投影与十神自动推导成功")

def test_context_build_anchor():
    ctx = ShushuContext.build("2006-06-25 00:30", longitude=120.0, gender="女")
    assert ctx.pillars.day_master == "乙"
    assert ctx.pillars.to_list() == ["丙戌", "甲午", "乙酉", "丙子"]
    assert ctx.lunar_date.lunar_year_gz == "丙戌"
    assert ctx.lunar_date.lunar_month == 5
    assert ctx.solar_term.current_term in ("夏至", "小暑")
    assert ctx.is_dst is False

    # 不可变性测试
    try:
        ctx.gender = "男"
        assert False, "Should raise FrozenInstanceError"
    except FrozenInstanceError:
        pass

    print("  [PASS] ShushuContext.build 锚点案例对验与全息状态封装成功")

def test_context_build_dst():
    # 1988-06-15 14:30 处于夏令时区间
    ctx = ShushuContext.build("1988-06-15 14:30", longitude=120.0, tz_name="Asia/Shanghai")
    assert ctx.is_dst is True
    assert ctx.dst_offset_minutes == 60.0
    # 扣减夏令时后标准时间为 13:30 (未时)
    assert ctx.beijing_time.hour == 13
    assert ctx.pillars.hour.zhi == "未"
    print("  [PASS] ShushuContext 历史夏令时自动扣减与时辰修正成功")

def test_context_build_southern_hemisphere():
    # 悉尼 lat = -33.86
    cfg = SchoolConfig(southern_hemisphere="clash_month")
    ctx = ShushuContext.build("2006-06-25 12:00", longitude=151.2, latitude=-33.86, school_config=cfg)
    # 原北半球为午月，南半球对冲为子月
    assert ctx.pillars.month.zhi == "子"
    print("  [PASS] ShushuContext 南半球月建对冲流派仲裁成功")

if __name__ == "__main__":
    print("================================================================")
    print(" Running assert_shushu_context.py ...")
    print("================================================================")
    test_pillar_info()
    test_standard_pillars_projections()
    test_context_build_anchor()
    test_context_build_dst()
    test_context_build_southern_hemisphere()
    print("================================================================")
    print(" ALL SHUSHU CONTEXT TESTS PASSED (100% SUCCESS)")
    print("================================================================")
