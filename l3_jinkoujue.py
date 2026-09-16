# -*- coding: utf-8 -*-
"""
l3_jinkoujue.py — 大六壬金口诀推命排盘引擎
基于经典《大六壬金口诀》古籍规范：
1. 四位结构：人元（日干遁干）、贵神（昼夜天乙起将）、将神（月将加时）、地分
2. 五动克应：妻动（神克将）、财动（将克神）、鬼动（干克神）、贼动（神克干）、子动（将克干）
3. 三动克应：方动（干克方）、神动（方克神）、将动（方克将）
"""

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 天干五行
GAN_WX = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}

# 地支五行
ZHI_WX = {
    "寅": "木", "卯": "木", "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金", "亥": "水", "子": "水"
}

# 十二贵神（天将）及其固定地支与五行
GUI_SHEN_LIST = [
    ("贵人", "丑", "土"),
    ("腾蛇", "巳", "火"),
    ("朱雀", "午", "火"),
    ("六合", "卯", "木"),
    ("勾陈", "辰", "土"),
    ("青龙", "寅", "木"),
    ("天空", "戌", "土"),
    ("白虎", "申", "金"),
    ("太常", "未", "土"),
    ("玄武", "子", "水"),
    ("太阴", "酉", "金"),
    ("天后", "亥", "水"),
]

# 十二月将（太阳过宫）
YUE_JIANG_MAP = {
    "雨水": ("亥", "登明"), "惊蛰": ("亥", "登明"),
    "春分": ("戌", "河魁"), "清明": ("戌", "河魁"),
    "谷雨": ("酉", "从魁"), "立夏": ("酉", "从魁"),
    "小满": ("申", "传送"), "芒种": ("申", "传送"),
    "夏至": ("未", "小吉"), "小暑": ("未", "小吉"),
    "大暑": ("午", "胜光"), "立秋": ("午", "胜光"),
    "处暑": ("巳", "太乙"), "白露": ("巳", "太乙"),
    "秋分": ("辰", "天罡"), "寒露": ("辰", "天罡"),
    "霜降": ("卯", "太冲"), "立冬": ("卯", "太冲"),
    "小雪": ("寅", "功曹"), "大雪": ("寅", "功曹"),
    "冬至": ("丑", "大吉"), "小寒": ("丑", "大吉"),
    "大寒": ("子", "神后"), "立春": ("子", "神后"),
}

# 日干起贵人基准（昼夜贵人：《大六壬金口诀大全》卷一〈起贵神法〉）
# 歌诀：甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎
# 阳贵（日贵）在前，阴贵（夜贵）在后
GUI_MAP = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("巳", "卯"), "癸": ("巳", "卯"),
    "辛": ("午", "寅"),
}

# 五行生克
WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 季节月令当旺五行（春木夏火秋金冬水四季土）
SEASON_WX = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土"
}

# 地支六合
LIU_HE = {
    frozenset(["子", "丑"]): "子丑合化土", frozenset(["寅", "亥"]): "寅亥合化木",
    frozenset(["卯", "戌"]): "卯戌合化火", frozenset(["辰", "酉"]): "辰酉合化金",
    frozenset(["巳", "申"]): "巳申合化水", frozenset(["午", "未"]): "午未合化土",
}

# 地支六冲
LIU_CHONG = {
    frozenset(["子", "午"]): "子午相冲", frozenset(["丑", "未"]): "丑未相冲",
    frozenset(["寅", "申"]): "寅申相冲", frozenset(["卯", "酉"]): "卯酉相冲",
    frozenset(["辰", "戌"]): "辰戌相冲", frozenset(["巳", "亥"]): "巳亥相冲",
}

# 地支相刑（三刑与自刑）
XING_MAP = {
    frozenset(["子", "卯"]): "子卯无礼之刑",
    frozenset(["寅", "巳"]): "寅巳相刑",
    frozenset(["巳", "申"]): "巳申相刑",
    frozenset(["寅", "申"]): "寅申相刑",
    frozenset(["丑", "戌"]): "丑戌相刑",
    frozenset(["戌", "未"]): "戌未相刑",
    frozenset(["丑", "未"]): "丑未相刑",
}

# 地支六害
LIU_HAI = {
    frozenset(["子", "未"]): "子未相害", frozenset(["丑", "午"]): "丑午相害",
    frozenset(["寅", "巳"]): "寅巳相害", frozenset(["卯", "辰"]): "卯辰相害",
    frozenset(["申", "亥"]): "申亥相害", frozenset(["酉", "戌"]): "酉戌相害",
}

# 地支六破
LIU_PO = {
    frozenset(["子", "酉"]): "子酉相破", frozenset(["卯", "午"]): "卯午相破",
    frozenset(["辰", "丑"]): "辰丑相破", frozenset(["戌", "未"]): "戌未相破",
    frozenset(["寅", "亥"]): "寅亥相破", frozenset(["巳", "申"]): "巳申相破",
}


def get_wangxiang_status(target_wx: str, month_zhi: str) -> str:
    """计算五行在当前月令中的旺相休囚死状态。"""
    s_wx = SEASON_WX.get(month_zhi, "土")
    if target_wx == s_wx:
        return "旺"
    elif WX_SHENG[s_wx] == target_wx:
        return "相"
    elif WX_SHENG[target_wx] == s_wx:
        return "休"
    elif WX_KE[target_wx] == s_wx:
        return "囚"
    elif WX_KE[s_wx] == target_wx:
        return "死"
    return "平"


def wushu_dun(day_gan: str, target_zhi: str) -> str:
    """日干起五鼠遁（推算地支上的遁干）。"""
    y_idx = GAN.index(day_gan)
    # 甲己起甲子(0), 乙庚起丙子(2), 丙辛起戊子(4), 丁壬起庚子(6), 戊癸起壬子(8)
    start_gan_idx = (y_idx % 5) * 2
    z_idx = ZHI.index(target_zhi)
    return GAN[(start_gan_idx + z_idx) % 10]


def get_renyuan(day_gan: str, difen: str) -> str:
    """人元：日干起五鼠遁推至地分所临天干。"""
    return wushu_dun(day_gan, difen)


def get_jiangshen(month_jiang_zhi: str, hour_zhi: str, difen: str):
    """
    将神（月将加时方到地分）：
    月将置于时辰支上，顺数至地分所临之支。
    """
    j_idx = ZHI.index(month_jiang_zhi)
    h_idx = ZHI.index(hour_zhi)
    d_idx = ZHI.index(difen)
    # 顺步步长 = (d_idx - h_idx) % 12
    # 将神落支 = (j_idx + (d_idx - h_idx)) % 12
    step = (d_idx - h_idx) % 12
    res_zhi = ZHI[(j_idx + step) % 12]
    return res_zhi


def get_guishen(day_gan: str, hour_zhi: str, difen: str):
    """
    贵神：分昼夜起天乙贵人加临地分。
    昼夜判定：卯至申为昼，酉至寅为夜。
    """
    is_day = hour_zhi in ("卯", "辰", "巳", "午", "未", "申")
    yang_gui, yin_gui = GUI_MAP[day_gan]
    tian_yi_zhi = yang_gui if is_day else yin_gui

    # 贵人顺逆：天乙落于阳宫（亥子丑寅卯辰）顺布十二将；落于阴宫（巳午未申酉戌）逆布十二将
    is_shun = tian_yi_zhi in ("亥", "子", "丑", "寅", "卯", "辰")
    ty_idx = ZHI.index(tian_yi_zhi)
    d_idx = ZHI.index(difen)

    if is_shun:
        steps = (d_idx - ty_idx) % 12
    else:
        steps = (ty_idx - d_idx) % 12

    shen_name, shen_zhi, shen_wx = GUI_SHEN_LIST[steps]
    return shen_name, shen_zhi, shen_wx


def calculate_jinkoujue(day_gan: str, hour_zhi: str, month_jiang_zhi: str, difen: str, month_zhi: str = "寅"):
    """
    大六壬金口诀全排盘计算。
    :param day_gan: 占日天干 (如 "甲")
    :param hour_zhi: 占时地支 (如 "午")
    :param month_jiang_zhi: 月将地支 (如 "亥" 登明)
    :param difen: 地分地支 (如 "卯")
    :param month_zhi: 占月地支 (如 "寅"，用于推算四位旺相休囚死)
    :return: dict 包含四位、干支五行、旺相休囚死、合冲刑害、五动三动克应断语
    """
    # 1. 人元
    ren_gan = get_renyuan(day_gan, difen)
    ren_wx = GAN_WX[ren_gan]

    # 2. 贵神
    gui_name, gui_zhi, gui_wx = get_guishen(day_gan, hour_zhi, difen)
    gui_gan = wushu_dun(day_gan, gui_zhi)

    # 3. 将神
    jiang_zhi = get_jiangshen(month_jiang_zhi, hour_zhi, difen)
    jiang_gan = wushu_dun(day_gan, jiang_zhi)
    jiang_wx = ZHI_WX[jiang_zhi]

    # 4. 地分
    difen_wx = ZHI_WX[difen]

    # 5. 旺相休囚死判定
    wangxiang = {
        "renyuan": get_wangxiang_status(ren_wx, month_zhi),
        "guishen": get_wangxiang_status(gui_wx, month_zhi),
        "jiangshen": get_wangxiang_status(jiang_wx, month_zhi),
        "difen": get_wangxiang_status(difen_wx, month_zhi),
    }

    # 6. 四位地支合冲刑害破分析
    interactions = []
    branches = [("贵神", gui_zhi), ("将神", jiang_zhi), ("地分", difen)]
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            name1, z1 = branches[i]
            name2, z2 = branches[j]
            pair = frozenset([z1, z2])
            if pair in LIU_HE:
                interactions.append({"type": "六合", "desc": f"{name1}{z1}与{name2}{z2}{LIU_HE[pair]}"})
            if pair in LIU_CHONG:
                interactions.append({"type": "六冲", "desc": f"{name1}{z1}与{name2}{z2}{LIU_CHONG[pair]}"})
            if pair in XING_MAP:
                interactions.append({"type": "相刑", "desc": f"{name1}{z1}与{name2}{z2}{XING_MAP[pair]}"})
            if pair in LIU_HAI:
                interactions.append({"type": "六害", "desc": f"{name1}{z1}与{name2}{z2}{LIU_HAI[pair]}"})
            if pair in LIU_PO:
                interactions.append({"type": "六破", "desc": f"{name1}{z1}与{name2}{z2}{LIU_PO[pair]}"})

    # 7. 五动分析 (克应系统)
    dong_list = []

    # 妻动：神克将
    if WX_KE[gui_wx] == jiang_wx:
        dong_list.append({
            "name": "妻动",
            "relation": f"贵神{gui_wx}克将神{jiang_wx}",
            "desc": "神克将为妻动，主妻妾之灾、内外不和、求谋艰难，下人反逆。"
        })
    # 财动：将克神
    if WX_KE[jiang_wx] == gui_wx:
        dong_list.append({
            "name": "财动",
            "relation": f"将神{jiang_wx}克贵神{gui_wx}",
            "desc": "将克神为财动，主财帛亨通、谋望吉昌、妇女内助、经营有利。"
        })
    # 鬼动：干克神
    if WX_KE[ren_wx] == gui_wx:
        dong_list.append({
            "name": "鬼动",
            "relation": f"人元{ren_wx}克贵神{gui_wx}",
            "desc": "干克神为鬼动，主官司词讼、小人连累、疾病缠身、长上不悦。"
        })
    # 贼动：神克干
    if WX_KE[gui_wx] == ren_wx:
        dong_list.append({
            "name": "贼动",
            "relation": f"贵神{gui_wx}克人元{ren_wx}",
            "desc": "神克干为贼动，主门户不和、失脱盗贼、忧患破耗、谋事受阻。"
        })
    # 子动：将克干
    if WX_KE[jiang_wx] == ren_wx:
        dong_list.append({
            "name": "子动",
            "relation": f"将神{jiang_wx}克人元{ren_wx}",
            "desc": "将克干为子动，主子孙喜庆、外出通达、求名得遂、田宅添益。"
        })

    # 8. 三动分析
    san_dong = []
    # 方动：干克方
    if WX_KE[ren_wx] == difen_wx:
        san_dong.append({
            "name": "方动",
            "relation": f"人元{ren_wx}克地分{difen_wx}",
            "desc": "干克方为方动，主远行移居、去住不定、百事不安。"
        })
    # 神动：方克神
    if WX_KE[difen_wx] == gui_wx:
        san_dong.append({
            "name": "神动",
            "relation": f"地分{difen_wx}克贵神{gui_wx}",
            "desc": "方克神为神动，主有事在外、亲朋病患、下犯上之扰。"
        })
    # 将动：方克将
    if WX_KE[difen_wx] == jiang_wx:
        san_dong.append({
            "name": "将动",
            "relation": f"地分{difen_wx}克将神{jiang_wx}",
            "desc": "方克将为将动，主小人阴害、斗打官司、勾连不利。"
        })

    return {
        "day_gan": day_gan,
        "hour_zhi": hour_zhi,
        "month_jiang_zhi": month_jiang_zhi,
        "difen": difen,
        "month_zhi": month_zhi,
        "four_positions": {
            "renyuan": {"gan": ren_gan, "wuxing": ren_wx},
            "guishen": {"name": gui_name, "gan": gui_gan, "zhi": gui_zhi, "wuxing": gui_wx},
            "jiangshen": {"gan": jiang_gan, "zhi": jiang_zhi, "wuxing": jiang_wx},
            "difen": {"zhi": difen, "wuxing": difen_wx},
        },
        "wangxiang": wangxiang,
        "interactions": interactions,
        "wudong": dong_list,
        "sandong": san_dong,
        "source": "《大六壬金口诀》古籍定本"
    }
