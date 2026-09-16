# -*- coding: utf-8 -*-
"""
l3_ziwei_yunxian.py — 紫微斗数多级运限（流月/流日/流时）与动态流曜飞星引擎
1. 斗君与四级运限推导：
   - 斗君定正月：DouJun = (流年太岁支 - 出生农历月 + 出生时辰支) % 12
   - 流月命宫：斗君为正月，逐月顺布
   - 流日命宫：流月命宫起初一，逐日顺布
   - 流时命宫：流日命宫起子时，逐时辰顺布
2. 动态流曜系统：
   - 流年禄存、流年擎羊、流年陀罗、流年天魁、流年天钺、流年红鸾、流年天喜、流年天马
   - 流年四化（化禄、化权、化科、化忌）
"""

ZHI = "子丑寅卯辰巳午未申酉戌亥"
GAN = "甲乙丙丁戊己庚辛壬癸"

# 禄存所落宫位（十天干禄神）
LU_CUN_MAP = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"
}

# 魁钺贵人（十天干阳贵阴贵）
KUI_YUE_MAP = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "辛": ("午", "寅")
}

# 天马三合驿马位
TIAN_MA_MAP = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳"
}

# 流年文昌口诀（甲乙巳午报君知，丙戊申宫丁己鸡，庚猪辛鼠壬逢虎，癸人见卯入云梯）
LIU_CHANG_MAP = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"
}

# 流年文曲口诀（甲邑在亥乙在子，丙戊在寅丁己卯，庚逢巳位辛逢午，壬居申位癸居酉）
LIU_QU_MAP = {
    "甲": "亥", "乙": "子", "丙": "寅", "丁": "卯", "戊": "寅",
    "己": "卯", "庚": "巳", "辛": "午", "壬": "申", "癸": "酉"
}

# 流年四化口诀（明刻《全书》派定本）
SIHUA_MAP = {
    "甲": (("廉贞", "禄"), ("破军", "权"), ("武曲", "科"), ("太阳", "忌")),
    "乙": (("天机", "禄"), ("天梁", "权"), ("紫微", "科"), ("太阴", "忌")),
    "丙": (("天同", "禄"), ("天机", "权"), ("文昌", "科"), ("廉贞", "忌")),
    "丁": (("太阴", "禄"), ("天同", "权"), ("天机", "科"), ("巨门", "忌")),
    "戊": (("贪狼", "禄"), ("太阴", "权"), ("右弼", "科"), ("天机", "忌")),
    "己": (("武曲", "禄"), ("贪狼", "权"), ("天梁", "科"), ("文曲", "忌")),
    "庚": (("太阳", "禄"), ("武曲", "权"), ("天同", "科"), ("太阴", "忌")),
    "辛": (("巨门", "禄"), ("太阳", "权"), ("文曲", "科"), ("文昌", "忌")),
    "壬": (("天梁", "禄"), ("紫微", "权"), ("左辅", "科"), ("武曲", "忌")),
    "癸": (("破军", "禄"), ("巨门", "权"), ("太阴", "科"), ("贪狼", "忌")),
}


def calculate_doujun(target_year_zhi: str, birth_lunar_month: int, birth_hour_zhi: str) -> str:
    """
    计算流年斗君宫位（流年农历正月命宫所在）：
    《紫微斗数全书》卷一〈起斗君诀〉：太岁宫中便起正，逆寻生月即留停；又从生月宫轮子，顺至生时镇斗星。
    数学公式：斗君 = (流年太岁支 - (出生农历月 - 1) + 出生时支) % 12
                    = (taisui_idx - birth_lunar_month + 1 + hour_idx) % 12
    """
    taisui_idx = ZHI.index(target_year_zhi)
    hour_idx = ZHI.index(birth_hour_zhi)
    doujun_idx = (taisui_idx - birth_lunar_month + 1 + hour_idx) % 12
    return ZHI[doujun_idx]


def calculate_four_tier_limits(target_year_zhi: str, birth_lunar_month: int, birth_hour_zhi: str,
                               lunar_month: int = 1, lunar_day: int = 1, query_hour_zhi: str = "子"):
    """
    推导紫微斗数四级运限（流年/流月/流日/流时）命宫地支。
    """
    # 1. 流年命宫：恒在流年太岁地支
    liunian_ming = target_year_zhi

    # 2. 流月命宫：斗君为正月，顺数至目标农历月
    doujun = calculate_doujun(target_year_zhi, birth_lunar_month, birth_hour_zhi)
    doujun_idx = ZHI.index(doujun)
    liuyue_ming_idx = (doujun_idx + lunar_month - 1) % 12
    liuyue_ming = ZHI[liuyue_ming_idx]

    # 3. 流日命宫：流月命宫起初一，逐日顺布
    liuri_ming_idx = (liuyue_ming_idx + lunar_day - 1) % 12
    liuri_ming = ZHI[liuri_ming_idx]

    # 4. 流时命宫：流日命宫起子时，逐时顺布
    h_idx = ZHI.index(query_hour_zhi)
    liushi_ming_idx = (liuri_ming_idx + h_idx) % 12
    liushi_ming = ZHI[liushi_ming_idx]

    return {
        "doujun": doujun,
        "liunian_ming": liunian_ming,
        "liuyue_ming": liuyue_ming,
        "liuri_ming": liuri_ming,
        "liushi_ming": liushi_ming,
    }


def calculate_dynamic_liuyao(target_year_gan: str, target_year_zhi: str):
    """
    计算流年动态流曜飞星排布：
    流禄、流羊、流陀、流魁、流钺、流鸾、流喜、流马、流年四化。
    """
    # 1. 流年禄存
    lu_zhi = LU_CUN_MAP[target_year_gan]
    lu_idx = ZHI.index(lu_zhi)

    # 2. 流年擎羊（禄前一位）与流年陀罗（禄后一位）
    yang_zhi = ZHI[(lu_idx + 1) % 12]
    tuo_zhi = ZHI[(lu_idx - 1) % 12]

    # 3. 流年天魁与流年天钺
    kui_zhi, yue_zhi = KUI_YUE_MAP[target_year_gan]

    # 4. 流年红鸾与天喜
    # 红鸾：从卯宫起子年逆数至流年支 -> 卯(3) - taisui_idx
    taisui_idx = ZHI.index(target_year_zhi)
    luan_idx = (3 - taisui_idx) % 12
    luan_zhi = ZHI[luan_idx]
    xi_zhi = ZHI[(luan_idx + 6) % 12]

    # 5. 流年天马
    ma_zhi = TIAN_MA_MAP[target_year_zhi]

    # 6. 流年四化
    sihua_list = SIHUA_MAP[target_year_gan]
    sihua_dict = {
        "化禄": sihua_list[0][0],
        "化权": sihua_list[1][0],
        "化科": sihua_list[2][0],
        "化忌": sihua_list[3][0],
    }

    # 7. 流年文昌与流年文曲
    chang_zhi = LIU_CHANG_MAP[target_year_gan]
    qu_zhi = LIU_QU_MAP[target_year_gan]

    return {
        "liunian_lucun": lu_zhi,
        "liunian_qingyang": yang_zhi,
        "liunian_tuoluo": tuo_zhi,
        "liunian_tiankui": kui_zhi,
        "liunian_tianyue": yue_zhi,
        "liunian_hongluan": luan_zhi,
        "liunian_tianxi": xi_zhi,
        "liunian_tianma": ma_zhi,
        "liunian_wenchang": chang_zhi,
        "liunian_wenqu": qu_zhi,
        "liunian_sihua": sihua_dict,
    }


def get_full_ziwei_yunxian(birth_lunar_month: int, birth_hour_zhi: str,
                           target_year_gan: str, target_year_zhi: str,
                           lunar_month: int = 1, lunar_day: int = 1, query_hour_zhi: str = "子"):
    """
    紫微斗数多级运限与流曜完整推导入口。
    """
    limits = calculate_four_tier_limits(
        target_year_zhi, birth_lunar_month, birth_hour_zhi,
        lunar_month, lunar_day, query_hour_zhi
    )
    liuyao = calculate_dynamic_liuyao(target_year_gan, target_year_zhi)

    return {
        "target_time": {
            "year_ganzhi": target_year_gan + target_year_zhi,
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "query_hour": query_hour_zhi,
        },
        "limits": limits,
        "liuyao": liuyao,
        "source": "《紫微斗数全书》流曜运限卷"
    }
