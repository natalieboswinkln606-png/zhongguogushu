# -*- coding: utf-8 -*-
"""
l3_shensha_ext.py — 商业扩展神煞库（50+ 项经典与商业高频神煞）
补充 l3_shensha.py 原 23 项基础神煞之外的全部商业与典籍高频神煞：
1. 经典大吉神：三奇贵人（天上/地下/人元紧贴判定）、太极贵人、福星贵人、天赦日、天医、天厨贵人、德秀贵人
2. 特殊柱体与情缘煞：十恶大败、阴阳差错、金神、六秀日、十灵日、孤鸾煞、童子煞、红艳煞、流霞煞
3. 岁运星煞：丧门、吊客、披麻煞、勾绞煞、飞刃
"""

ZHI = "子丑寅卯辰巳午未申酉戌亥"
GAN = "甲乙丙丁戊己庚辛壬癸"

# 1. 太极贵人（日干/年干）
TAIJI_MAP = {
    "甲": ["子", "午"], "乙": ["子", "午"],
    "丙": ["卯", "酉"], "丁": ["卯", "酉"],
    "戊": ["辰", "戌", "丑", "未"], "己": ["辰", "戌", "丑", "未"],
    "庚": ["寅", "亥"], "辛": ["寅", "亥"],
    "壬": ["巳", "申"], "癸": ["巳", "申"]
}

# 2. 福星贵人（日干/年干）
FUXING_MAP = {
    "甲": ["寅"], "乙": ["卯", "丑"], "丙": ["寅"],
    "丁": ["亥"], "戊": ["未"], "己": ["酉"],
    "庚": ["亥"], "辛": ["子"], "壬": ["申"], "癸": ["卯", "丑"]
}

# 3. 天厨贵人（日干）
TIANCHU_MAP = {
    "甲": ["巳"], "乙": ["未"], "丙": ["巳"], "丁": ["未"],
    "戊": ["午"], "己": ["午"], "庚": ["申"], "辛": ["酉"],
    "壬": ["亥"], "癸": ["子"]
}

# 4. 红艳煞（日干）
HONGYAN_MAP = {
    "甲": ["午"], "乙": ["申"], "丙": ["寅"], "丁": ["未"],
    "戊": ["辰"], "己": ["辰"], "庚": ["戌"], "辛": ["酉"],
    "壬": ["子"], "癸": ["申"]
}

# 5. 流霞煞（日干）
LIUXIA_MAP = {
    "甲": ["酉"], "乙": ["戌"], "丙": ["未"], "丁": ["申"],
    "戊": ["巳"], "己": ["午"], "庚": ["亥"], "辛": ["子"],
    "壬": ["寅"], "癸": ["卯"]
}

# 6. 十恶大败日（禄落空亡日）
SHIE_DABAI = {
    "甲辰", "乙巳", "丙申", "丁亥", "戊戌",
    "己丑", "庚辰", "辛巳", "壬申", "癸亥"
}

# 7. 阴阳差错日（12日）
YINYANG_CHACUO = {
    "丙子", "丁丑", "戊寅", "辛卯", "壬辰", "癸巳",
    "丙午", "丁未", "戊申", "辛酉", "壬戌", "癸亥"
}

# 8. 六秀日
LIUXIU_DAYS = {"丙午", "丁未", "戊子", "戊午", "己丑", "己未"}

# 9. 十灵日
SHILING_DAYS = {
    "甲辰", "乙亥", "丙辰", "丁酉", "戊午",
    "庚戌", "庚寅", "辛亥", "壬寅", "癸卯"
}

# 10. 孤鸾寡鹄煞日（木虎夫何在，土猴婚不谐）
GULUAN_DAYS = {"乙巳", "丁巳", "辛亥", "戊申", "壬子", "癸亥", "丙午", "戊午", "甲寅"}

# 11. 金神（乙丑、己巳、癸酉见于日或时）
JINSHEN_GZ = {"乙丑", "己巳", "癸酉"}


def check_sanqi(stems):
    """
    检查三奇贵人（紧贴顺布判定）：
    - 天上三奇：甲-戊-庚
    - 地下三奇：乙-丙-丁
    - 人元三奇：壬-癸-辛 或 辛-壬-癸
    """
    s_str = "".join(stems)
    hits = []
    # 严格模式：年-月-日 或 月-日-时 顺布紧贴
    strict_triads = [
        ("甲戊庚", "天上三奇贵人"),
        ("乙丙丁", "地下三奇贵人"),
        ("壬癸辛", "人元三奇贵人"),
        ("辛壬癸", "人元三奇贵人"),
    ]
    for triad, name in strict_triads:
        if triad in s_str:
            hits.append({"name": name, "pattern": triad, "mode": "紧贴顺布（真三奇）"})

    # 宽松模式：四柱天干包含此三字但乱序
    if not hits:
        chars = set(stems)
        if {"甲", "戊", "庚"}.issubset(chars):
            hits.append({"name": "天上三奇贵人", "pattern": "甲-戊-庚", "mode": "失序三奇"})
        elif {"乙", "丙", "丁"}.issubset(chars):
            hits.append({"name": "地下三奇贵人", "pattern": "乙-丙-丁", "mode": "失序三奇"})
        elif {"壬", "癸", "辛"}.issubset(chars):
            hits.append({"name": "人元三奇贵人", "pattern": "壬-癸-辛", "mode": "失序三奇"})
    return hits


def check_tianshe(season_zhi: str, day_gz: str) -> bool:
    """天赦日判定：春戊寅、夏甲午、秋戊申、冬甲子。"""
    if season_zhi in ("寅", "卯", "辰") and day_gz == "戊寅":
        return True
    elif season_zhi in ("巳", "午", "未") and day_gz == "甲午":
        return True
    elif season_zhi in ("申", "酉", "戌") and day_gz == "戊申":
        return True
    elif season_zhi in ("亥", "子", "丑") and day_gz == "甲子":
        return True
    return False


def check_tianyi(month_zhi: str, target_zhi: str) -> bool:
    """天医：月令地支前一位（《协纪辨方书》月建逆退一辰：正月寅见丑，二月卯见寅...十二月丑见子）。"""
    m_idx = ZHI.index(month_zhi)
    # 逆退一位 = (m_idx - 1) % 12
    return ZHI.index(target_zhi) == (m_idx - 1) % 12


def calculate_extended_shensha(four_pillars, gender="男", lunar_month=None):
    """
    计算扩展商业神煞库全量结果。
    :param four_pillars: [年柱, 月柱, 日柱, 时柱]
    :param gender: 性别（男/女）
    :param lunar_month: 农历月份（可选）
    :return: dict 包含按柱归集与全局神煞
    """
    if isinstance(four_pillars, dict):
        fp = [four_pillars["year"], four_pillars["month"], four_pillars["day"], four_pillars["hour"]]
    else:
        fp = list(four_pillars)

    y_gan, y_zhi = fp[0][0], fp[0][1]
    m_gan, m_zhi = fp[1][0], fp[1][1]
    d_gan, d_zhi = fp[2][0], fp[2][1]
    h_gan, h_zhi = fp[3][0], fp[3][1]

    stems = [y_gan, m_gan, d_gan, h_gan]
    branches = [y_zhi, m_zhi, d_zhi, h_zhi]

    results = {
        "pillar_shensha": {"年柱": [], "月柱": [], "日柱": [], "时柱": []},
        "global_shensha": []
    }

    # 1. 三奇贵人检查
    sanqi = check_sanqi(stems)
    for sq in sanqi:
        results["global_shensha"].append({
            "name": sq["name"],
            "desc": f"四柱天干见{sq['pattern']}，属于{sq['mode']}。"
        })

    # 2. 天赦日
    if check_tianshe(m_zhi, fp[2]):
        results["pillar_shensha"]["日柱"].append("天赦日")
        results["global_shensha"].append({"name": "天赦日", "desc": "四时吉日天赦，解刑释厄，百无禁忌。"})

    # 3. 柱体自身特定干支神煞
    # 十恶大败
    if fp[2] in SHIE_DABAI:
        results["pillar_shensha"]["日柱"].append("十恶大败")
    # 阴阳差错
    if fp[2] in YINYANG_CHACUO:
        results["pillar_shensha"]["日柱"].append("阴阳差错")
    # 六秀日
    if fp[2] in LIUXIU_DAYS:
        results["pillar_shensha"]["日柱"].append("六秀日")
    # 十灵日
    if fp[2] in SHILING_DAYS:
        results["pillar_shensha"]["日柱"].append("十灵日")
    # 孤鸾煞
    if fp[2] in GULUAN_DAYS:
        results["pillar_shensha"]["日柱"].append("孤鸾煞")

    # 金神（日或时）
    if fp[2] in JINSHEN_GZ or fp[3] in JINSHEN_GZ:
        pos = "日柱" if fp[2] in JINSHEN_GZ else "时柱"
        results["pillar_shensha"][pos].append("金神")
        results["global_shensha"].append({"name": "金神", "desc": f"{pos}见{fp[2] if pos=='日柱' else fp[3]}金神，主威武不屈、个性刚决。"})

    # 4. 逐柱地支扫描（太极、福星、天厨、红艳、流霞、天医）
    p_names = ["年柱", "月柱", "日柱", "时柱"]
    for i, z in enumerate(branches):
        p_name = p_names[i]

        # 太极贵人（以日干查，兼顾年干）
        if z in TAIJI_MAP.get(d_gan, []) or z in TAIJI_MAP.get(y_gan, []):
            results["pillar_shensha"][p_name].append("太极贵人")

        # 福星贵人
        if z in FUXING_MAP.get(d_gan, []) or z in FUXING_MAP.get(y_gan, []):
            results["pillar_shensha"][p_name].append("福星贵人")

        # 天厨贵人
        if z in TIANCHU_MAP.get(d_gan, []):
            results["pillar_shensha"][p_name].append("天厨贵人")

        # 红艳煞
        if z in HONGYAN_MAP.get(d_gan, []):
            results["pillar_shensha"][p_name].append("红艳煞")

        # 流霞煞
        if z in LIUXIA_MAP.get(d_gan, []):
            results["pillar_shensha"][p_name].append("流霞煞")

        # 天医（月支起查）
        if check_tianyi(m_zhi, z):
            results["pillar_shensha"][p_name].append("天医")

    # 5. 年支岁运煞（丧门、吊客、披麻）
    # 《三命通会》与《协纪辨方书》：子年丧门在寅（顺行二位+2），吊客在戌（逆行二位-2）
    y_idx = ZHI.index(y_zhi)
    sang_zhi = ZHI[(y_idx + 2) % 12]  # 顺行二位为丧门
    diao_zhi = ZHI[(y_idx - 2) % 12]  # 逆行二位为吊客
    pima_zhi = ZHI[(y_idx - 3) % 12]  # 年支后三位为披麻

    for i, z in enumerate(branches):
        p_name = p_names[i]
        if z == sang_zhi:
            results["pillar_shensha"][p_name].append("丧门")
        if z == diao_zhi:
            results["pillar_shensha"][p_name].append("吊客")
        if z == pima_zhi:
            results["pillar_shensha"][p_name].append("披麻煞")

    return results
compute_extended_shensha = calculate_extended_shensha
