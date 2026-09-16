# -*- coding: utf-8 -*-
"""
l3_bazi_geju.py — 八字格局自动化判定引擎
基于《子平真诠》、《滴天髓》、《渊海子平》与《三命通会》经典规范：
1. 化气格 (甲己化土、乙庚化金、丙辛化水、丁壬化木、戊癸化火)
2. 专旺格 (曲直、炎上、稼穑、从革、润下)
3. 弃命从弱格 (从儿格、从财格、从杀格、真从/假从)
4. 月令透干正八格 (正官、七杀、正印、偏印、正财、偏财、食神、伤官) 与禄刃格 (建禄、阳刃)
"""

# 五行与干支映射
GAN_WX = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

GAN_YY = {
    "甲": 1, "乙": 0, "丙": 1, "丁": 0, "戊": 1,
    "己": 0, "庚": 1, "辛": 0, "壬": 1, "癸": 0
}

ZHI_WX = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水"
}

# 地支藏干规范表 (本气, 中气, 余气)
ZHI_CANGGAN = {
    "寅": [("甲", "本气"), ("丙", "中气"), ("戊", "余气")],
    "卯": [("乙", "本气")],
    "辰": [("戊", "本气"), ("乙", "中气"), ("癸", "余气")],
    "巳": [("丙", "本气"), ("庚", "中气"), ("戊", "余气")],
    "午": [("丁", "本气"), ("己", "中气")],
    "未": [("己", "本气"), ("丁", "中气"), ("乙", "余气")],
    "申": [("庚", "本气"), ("壬", "中气"), ("戊", "余气")],
    "酉": [("辛", "本气")],
    "戌": [("戊", "本气"), ("辛", "中气"), ("丁", "余气")],
    "亥": [("壬", "本气"), ("甲", "中气")],
    "子": [("癸", "本气")],
    "丑": [("己", "本气"), ("癸", "中气"), ("辛", "余气")],
}

# 五行生克关系
WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 天干五合
GAN_HE = {
    ("甲", "己"): "土", ("己", "甲"): "土",
    ("乙", "庚"): "金", ("庚", "乙"): "金",
    ("丙", "辛"): "水", ("辛", "丙"): "水",
    ("丁", "壬"): "木", ("壬", "丁"): "木",
    ("戊", "癸"): "火", ("癸", "戊"): "火",
}


# 五阳干阳刃月支（必须在帝旺之位，《子平真诠》卷三第十九章〈论阳刃〉）
YANGREN_ZHI_MAP = {
    "甲": "卯",
    "丙": "午",
    "戊": "午",
    "庚": "酉",
    "壬": "子",
}


def get_shishen(day_gan, target_gan):
    """求 target_gan 相对于 day_gan 的十神名称。"""
    d_wx = GAN_WX[day_gan]
    t_wx = GAN_WX[target_gan]
    d_yy = GAN_YY[day_gan]
    t_yy = GAN_YY[target_gan]
    same_polarity = (d_yy == t_yy)

    if d_wx == t_wx:
        return "比肩" if same_polarity else "劫财"
    elif WX_SHENG[d_wx] == t_wx:
        return "食神" if same_polarity else "伤官"
    elif WX_KE[d_wx] == t_wx:
        return "偏财" if same_polarity else "正财"
    elif WX_KE[t_wx] == d_wx:
        return "七杀" if same_polarity else "正官"
    elif WX_SHENG[t_wx] == d_wx:
        return "偏印" if same_polarity else "正印"
    return "未知"


def _check_huaqi(day_gan, month_gan, hour_gan, month_zhi, four_pillars):
    """判定是否成化气格（含妒合争合防御、月令引化与无根校验）。"""
    all_stems = [p[0] for p in four_pillars]
    other_stems = [four_pillars[0][0], four_pillars[1][0], four_pillars[3][0]]

    partner_gan = None
    target_wx = None
    position = ""
    for g, pos in [(month_gan, "月干"), (hour_gan, "时干")]:
        if (day_gan, g) in GAN_HE:
            partner_gan = g
            target_wx = GAN_HE[(day_gan, g)]
            position = pos
            break

    if not partner_gan:
        return None

    # 《滴天髓》“两干争合一干，争妒不化”：若有双合竞争或日主透出双干，严禁成格
    if other_stems.count(partner_gan) > 1 or all_stems.count(day_gan) > 1:
        return None

    # 月令需为化神本气或月令生助化神之五行
    m_wx = ZHI_WX[month_zhi]
    m_benqi_wx = GAN_WX[ZHI_CANGGAN[month_zhi][0][0]]
    is_season_match = (m_wx == target_wx or m_benqi_wx == target_wx or WX_SHENG[m_wx] == target_wx)
    if not is_season_match:
        return None

    # 日主在地支中不可有本气强根破局
    day_wx = GAN_WX[day_gan]
    has_strong_root = False
    for p in four_pillars:
        z = p[1]
        if ZHI_CANGGAN[z][0][0] == day_gan or ZHI_WX[z] == day_wx:
            has_strong_root = True
            break

    if not has_strong_root:
        name_map = {"土": "甲己化土格", "金": "乙庚化金格", "水": "丙辛化水格", "木": "丁壬化木格", "火": "戊癸化火格"}
        return {
            "category": "化气格",
            "pattern_name": name_map.get(target_wx, f"化{target_wx}格"),
            "main_element": target_wx,
            "evidence": f"日干{day_gan}与{position}{partner_gan}天干中和相合（无争妒），生于{month_zhi}月化神有力，地支无强根破格。",
            "source": "《滴天髓》天干化命章"
        }
    return None


ZHUANWANG_VALID_MONTHS = {
    "木": ("寅", "卯", "辰", "亥"),
    "火": ("巳", "午", "未", "寅"),
    "土": ("辰", "戌", "丑", "未", "巳", "午"),
    "金": ("申", "酉", "戌", "巳", "丑"),
    "水": ("亥", "子", "丑", "申", "辰"),
}


def _check_zhuanwang(day_gan, month_zhi, all_stems, all_branches):
    """判定是否成专旺格 (从强格)，含当令时节硬约束与月令加权。"""
    day_wx = GAN_WX[day_gan]

    # 《子平真诠》《滴天髓》：专旺格必须得令乘旺，死绝休囚之月一票否决
    if month_zhi not in ZHUANWANG_VALID_MONTHS.get(day_wx, ()):
        return None

    wx_counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for g in all_stems:
        wx_counts[GAN_WX[g]] += 1
    for i, z in enumerate(all_branches):
        is_month = (i == 1)
        mult = 1.5 if is_month else 1.0
        for cg, kind in ZHI_CANGGAN[z]:
            w = (1.0 if kind == "本气" else (0.5 if kind == "中气" else 0.2)) * mult
            wx_counts[GAN_WX[cg]] += w

    same_wx = day_wx
    mother_wx = [k for k, v in WX_SHENG.items() if v == day_wx][0]
    officer_wx = [k for k, v in WX_KE.items() if v == day_wx][0]

    self_and_mother_score = wx_counts[same_wx] + wx_counts[mother_wx]
    total_score = sum(wx_counts.values())

    # 专旺条件：印比得分占比 > 70%，且官杀受制微弱
    if total_score > 0 and (self_and_mother_score / total_score >= 0.70) and wx_counts[officer_wx] <= 1.0:
        names = {
            "木": ("曲直格", "曲直仁寿格"),
            "火": ("炎上格", "炎上格"),
            "土": ("稼穑格", "稼穑格"),
            "金": ("从革格", "从革格"),
            "水": ("润下格", "润下格")
        }
        p_name, full_name = names.get(day_wx, ("专旺格", "专旺格"))
        return {
            "category": "专旺格",
            "pattern_name": p_name,
            "main_element": day_wx,
            "evidence": f"日主{day_gan}{day_wx}旺极，得令于{month_zhi}月，印比能量占比达 {self_and_mother_score/total_score:.1%}，官杀失令受制，成{full_name}。",
            "source": "《子平真诠》专旺从强篇"
        }
    return None


def _check_congruo(day_gan, month_zhi, four_pillars):
    """判定是否成弃命从弱格 (从儿、从财、从杀、从弱)。
    严格遵循《子平真诠》‘微根不从’：墓库微根（辰未乙、戌未丁、丑戌辛、辰丑癸）存在即不从。
    """
    day_wx = GAN_WX[day_gan]
    all_branches = [p[1] for p in four_pillars]

    # 1. 检查日主在地支是否有任何根气（本气、中气、余气微根一律排查）
    for z in all_branches:
        for cg, _ in ZHI_CANGGAN[z]:
            if GAN_WX[cg] == day_wx:
                return None  # 有根（哪怕墓库微根）不入从格

    # 2. 计算异党（食伤、财星、官杀）得分，仅排除日主天干自身 (fp[2][0])
    wx_scores = {"食伤": 0.0, "财星": 0.0, "官杀": 0.0, "印比": 0.0}
    for i, p in enumerate(four_pillars):
        if i == 2:
            continue  # 仅跳过日干自身，年月时透出的比劫正常计入印比
        g = p[0]
        ss = get_shishen(day_gan, g)
        if ss in ("比肩", "劫财", "正印", "偏印"):
            wx_scores["印比"] += 1.0
        elif ss in ("食神", "伤官"):
            wx_scores["食伤"] += 1.0
        elif ss in ("正财", "偏财"):
            wx_scores["财星"] += 1.0
        elif ss in ("正官", "七杀"):
            wx_scores["官杀"] += 1.0

    for z in all_branches:
        for cg, kind in ZHI_CANGGAN[z]:
            w = 1.0 if kind == "本气" else (0.4 if kind == "中气" else 0.2)
            ss = get_shishen(day_gan, cg)
            if ss in ("比肩", "劫财", "正印", "偏印"):
                wx_scores["印比"] += w
            elif ss in ("食神", "伤官"):
                wx_scores["食伤"] += w
            elif ss in ("正财", "偏财"):
                wx_scores["财星"] += w
            elif ss in ("正官", "七杀"):
                wx_scores["官杀"] += w

    total = sum(wx_scores.values())
    if total > 0 and (wx_scores["印比"] / total <= 0.15):
        other_total = total - wx_scores["印比"]
        if wx_scores["食伤"] / other_total >= 0.50:
            return {
                "category": "从格",
                "pattern_name": "从儿格",
                "main_element": "食伤",
                "evidence": "日主无根无气，食伤旺气主导全盘，达弃命从儿之象。",
                "source": "《滴天髓》从儿论"
            }
        elif wx_scores["财星"] / other_total >= 0.50:
            return {
                "category": "从格",
                "pattern_name": "从财格",
                "main_element": "财星",
                "evidence": "日主弃命从财，局中财星群聚乘旺当令。",
                "source": "《子平真诠》从财论"
            }
        elif wx_scores["官杀"] / other_total >= 0.50:
            return {
                "category": "从格",
                "pattern_name": "从杀格",
                "main_element": "官杀",
                "evidence": "局中官杀势众，日主孤立无援，顺从杀势为格。",
                "source": "《子平真诠》从杀论"
            }
        else:
            return {
                "category": "从格",
                "pattern_name": "从弱格",
                "main_element": "异党",
                "evidence": "日元虚浮无根，财官食伤并见，成弃命从弱局。",
                "source": "《渊海子平》从弱篇"
            }
    return None


def _check_ziping_zhengge(day_gan, month_zhi, four_pillars):
    """判定《子平真诠》月令透干正八格与禄刃格，含中余气双透权重裁定。"""
    canggan_list = ZHI_CANGGAN[month_zhi]
    benqi = canggan_list[0][0]
    other_stems = [four_pillars[0][0], four_pillars[1][0], four_pillars[3][0]]
    month_gan = four_pillars[1][0]

    # 1. 优先检查月令本气是否透干
    if benqi in other_stems:
        ss = get_shishen(day_gan, benqi)
        if ss == "比肩":
            return {
                "category": "禄刃格",
                "pattern_name": "建禄格",
                "main_element": GAN_WX[benqi],
                "evidence": f"生于{month_zhi}月，月令本气{benqi}比肩透干，立建禄格。",
                "source": "《子平真诠》建禄月劫篇"
            }
        elif ss == "劫财":
            if day_gan in YANGREN_ZHI_MAP and month_zhi == YANGREN_ZHI_MAP[day_gan]:
                return {
                    "category": "禄刃格",
                    "pattern_name": "阳刃格",
                    "main_element": GAN_WX[benqi],
                    "evidence": f"生于{month_zhi}月，为日主{day_gan}帝旺阳刃之地，月令本气{benqi}劫财透干，立阳刃格。",
                    "source": "《子平真诠》阳刃篇"
                }
            else:
                return {
                    "category": "禄刃格",
                    "pattern_name": "月劫格",
                    "main_element": GAN_WX[benqi],
                    "evidence": f"生于{month_zhi}月，月令本气{benqi}劫财司权透干，立月劫格（建禄月劫篇）。",
                    "source": "《子平真诠》建禄月劫篇"
                }
        else:
            return {
                "category": "正八格",
                "pattern_name": f"{ss}格",
                "main_element": GAN_WX[benqi],
                "evidence": f"生于{month_zhi}月，月令本气{benqi}透于天干，为日主之{ss}，立{ss}格。",
                "source": "《子平真诠》提纲定格篇"
            }

    # 2. 本气未透，检查中气与余气是否透干（若双透，以月干紧贴与中气强力优先裁决）
    candidates = []
    for idx, (cg, kind) in enumerate(canggan_list[1:], start=1):
        if cg in other_stems:
            ss = get_shishen(day_gan, cg)
            if ss not in ("比肩", "劫财"):
                weight = 0
                if cg == month_gan:
                    weight += 10  # 月干紧贴同出月支力量最显
                if kind == "中气":
                    weight += 5
                else:
                    weight += 2
                candidates.append((weight, cg, kind, ss))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0]
        cg, kind, ss = best[1], best[2], best[3]
        return {
            "category": "正八格",
            "pattern_name": f"{ss}格",
            "main_element": GAN_WX[cg],
            "evidence": f"生于{month_zhi}月，月令本气未透，中余气{cg}({kind})透干化出{ss}立格。",
            "source": "《子平真诠》用神变化篇"
        }

    # 3. 藏干均不透，直取月令本气立格
    ss_benqi = get_shishen(day_gan, benqi)
    if ss_benqi == "比肩":
        return {
            "category": "禄刃格",
            "pattern_name": "建禄格",
            "main_element": GAN_WX[benqi],
            "evidence": f"生于{month_zhi}月，月令藏干未透，直取月令本气{benqi}立建禄格。",
            "source": "《子平真诠》建禄篇"
        }
    elif ss_benqi == "劫财":
        if day_gan in YANGREN_ZHI_MAP and month_zhi == YANGREN_ZHI_MAP[day_gan]:
            return {
                "category": "禄刃格",
                "pattern_name": "阳刃格",
                "main_element": GAN_WX[benqi],
                "evidence": f"生于{month_zhi}月帝旺阳刃之位，月令藏干未透，直取月令本气{benqi}立阳刃格。",
                "source": "《子平真诠》阳刃篇"
            }
        else:
            return {
                "category": "禄刃格",
                "pattern_name": "月劫格",
                "main_element": GAN_WX[benqi],
                "evidence": f"生于{month_zhi}月，月令藏干未透，直取月令本气{benqi}劫财司权，立月劫格（建禄月劫篇）。",
                "source": "《子平真诠》建禄月劫篇"
            }
    else:
        return {
            "category": "正八格",
            "pattern_name": f"{ss_benqi}格",
            "main_element": GAN_WX[benqi],
            "evidence": f"生于{month_zhi}月，月令藏干不透，依典籍直取月令本气{benqi}之{ss_benqi}立格。",
            "source": "《子平真诠》提纲本气取用篇"
        }


def determine_bazi_geju(four_pillars, gender="男"):
    """
    八字格局自动化判定主入口。
    :param four_pillars: [年柱, 月柱, 日柱, 时柱] 或 {"year":.., "month":.., "day":.., "hour":..}
    :param gender: "男" | "女"
    :return: dict 包含 category, pattern_name, main_element, evidence, source
    """
    if isinstance(four_pillars, dict):
        fp = [four_pillars["year"], four_pillars["month"], four_pillars["day"], four_pillars["hour"]]
    else:
        fp = list(four_pillars)

    year_gan, year_zhi = fp[0][0], fp[0][1]
    month_gan, month_zhi = fp[1][0], fp[1][1]
    day_gan, day_zhi = fp[2][0], fp[2][1]
    hour_gan, hour_zhi = fp[3][0], fp[3][1]

    all_stems = [year_gan, month_gan, day_gan, hour_gan]
    all_branches = [year_zhi, month_zhi, day_zhi, hour_zhi]

    # 阶段 1: 化气格判定（含妒合争合排查）
    res_hua = _check_huaqi(day_gan, month_gan, hour_gan, month_zhi, fp)
    if res_hua:
        return res_hua

    # 阶段 2: 专旺从强格判定（含当令硬约束）
    res_zhuan = _check_zhuanwang(day_gan, month_zhi, all_stems, all_branches)
    if res_zhuan:
        return res_zhuan

    # 阶段 3: 弃命从弱格判定（含墓库微根排查）
    res_congruo = _check_congruo(day_gan, month_zhi, fp)
    if res_congruo:
        return res_congruo

    # 阶段 4: 子平真诠正八格与禄刃判定
    return _check_ziping_zhengge(day_gan, month_zhi, fp)
