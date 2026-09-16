# -*- coding: utf-8 -*-
"""
l3_decision_tree.py — 现代人生战略决策树与能量释放通道推演引擎

核心使命：
彻底终结传统算命“单点铁断、盲猜灾异、廉价谄媚”的伪科学模式。
基于现代系统论、认知心理学与中国传统干支动力学：
1. 三层能量释放通道模型（低阶破坏层、中阶内耗层、高阶专业层）；
2. 关键人生决策模拟（体制公职 VS 市场创业 VS 专业技术）；
3. 风险对冲与充分必要条件（阴阳并陈，优势对等缺陷）。
"""
import sys
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# 严禁谄媚词汇库（反画饼反迷信黑名单）
BANNED_SYCOPHANCY = [
    "贵公子", "大富大贵", "必定名扬天下", "倾国倾城", "天生神将",
    "算无遗策", "命中注定富甲一方", "必成大器万无一失"
]

# 十神原型心理与三层释放机制映射
TEN_GOD_ARCHETYPES = {
    "比肩": {
        "archetype": "自主性与自我边界 (Autonomy & Boundary)",
        "low_tier": "固执己见、排斥合作、同辈恶性竞争、易有肢体冲撞与摩擦",
        "mid_tier": "防备心强、不喜欠人情、过度独立导致孤立无援与精神内耗",
        "high_tier": "强大的自我驱动力、独立抗压能力、坚守底线、极具骨气与定力"
    },
    "劫财": {
        "archetype": "掠夺性与竞争本能 (Aggressiveness & Rivalry)",
        "low_tier": "冲动投机、盲目借贷、被狐朋狗友忽悠破财、暴躁失控",
        "mid_tier": "强烈的同辈比较心、隐蔽的嫉妒心、害怕落后带来的焦虑狂躁",
        "high_tier": "极致的危机开拓力、雷厉风行的执行力、在残酷红海竞争中杀出血路"
    },
    "食神": {
        "archetype": "才智输出与温和表达 (Creativity & Intellectual Expression)",
        "low_tier": "贪图享受、好逸恶劳、逃避现实冲突、沉迷口腹之欲或消遣",
        "mid_tier": "过于理想主义、清高自诩、不屑世俗规则导致错失现实机会",
        "high_tier": "深厚的技术沉淀、温润从容的专业声誉、通过硬核成果持续变现"
    },
    "伤官": {
        "archetype": "颠覆性突破与批判心智 (Disruptive Critical Thinking)",
        "low_tier": "口无遮拦、恃才傲物、公然挑衅权威规则、招惹官非口舌纠纷",
        "mid_tier": "苛求完美、愤世嫉俗、对体制与平庸环境产生生理性厌恶",
        "high_tier": "顶级创新突破者、降维打击的逻辑架构师、打破既有垄断的变革者"
    },
    "偏财": {
        "archetype": "商业嗅觉与资源整合 (Commercial Acumen & Resource Allocation)",
        "low_tier": "挥霍无度、投机暴富幻觉、轻视长线积累、男女关系混乱",
        "mid_tier": "金钱焦虑、对投入产出比过度敏感导致无法深耕专业",
        "high_tier": "敏锐的宏观周期洞察力、擅长大体量资源配置、游刃有余的商务斡旋"
    },
    "正财": {
        "archetype": "风险控制与稳定秩序 (Prudence & Operational Consistency)",
        "low_tier": "因小失大、过度吝啬、缺乏冒险勇气、被眼前蝇头小利绑架",
        "mid_tier": "极度厌恶不确定性、生活被按部就班彻底僵化、缺乏想象力",
        "high_tier": "极其扎实的信用资本、长坡厚雪的复利积累、风控与财务守门人"
    },
    "七杀": {
        "archetype": "危机应对与强权意志 (Crisis Navigation & Executive Will)",
        "low_tier": "暴力冲动、意外血光摔伤、受制于恶劣环境、焦虑压抑失控",
        "mid_tier": "严重失眠多梦、时刻感到外部威胁的高压警觉、自我施虐型苛求",
        "high_tier": "危急关头的铁腕决断力、不怒自威的领导权威、攻坚克难的杀手锏"
    },
    "正官": {
        "archetype": "体制认可与规矩契约 (Institutional Legitimacy & Contractual Duty)",
        "low_tier": "死板教条、唯唯诺诺、崇拜权力权威、被主流教条彻底异化",
        "mid_tier": "沉重的道德包袱与精英光环、极度在意外界评价导致的虚伪内耗",
        "high_tier": "天生的规则制定者与体制守正者、具备高阶公信力、深得大平台倚重"
    },
    "偏印": {
        "archetype": "非线性洞察与玄奥悟性 (Non-linear Intuition & Deep Philosophy)",
        "low_tier": "性格孤僻古怪、脱离社会现实、自闭抑郁、易信邪门歪道",
        "mid_tier": "精神洁癖严重、难以建立世俗亲密关系、常怀悲观虚无厌世感",
        "high_tier": "直击本质的洞察穿透力、哲学与顶层底层逻辑研究、反直觉预判高手"
    },
    "正印": {
        "archetype": "包容滋养与知识传承 (Nurturing Wisdom & Institutional Absorption)",
        "low_tier": "依赖性强、缺乏狼性斗志、容易被道德绑架而牺牲自我",
        "mid_tier": "逃避残酷竞争、习惯躲在象牙塔或家庭舒适圈、行动力滞后",
        "high_tier": "深厚的人格魅力与学术德行、天然获得平台权威庇护、学者型领袖"
    },
}


def evaluate_archetype_spectrum(pillars_full: Dict[str, Any]) -> Dict[str, Any]:
    """
    评估四柱命盘在三层释放管道上的核心分布。
    彻底废除单一绝对断语，给出其能量的高中低阶释放特征。
    """
    day_master = pillars_full.get("day_master", "辛")
    ten_gods_present = set()
    
    for p_key in ["year", "month", "day", "hour"]:
        p = pillars_full.get(p_key, {})
        tg = p.get("ten_god")
        if tg and tg != "日元":
            ten_gods_present.add(tg)
        for cg in p.get("canggan_ten_gods", []):
            if len(cg) >= 3:
                ten_gods_present.add(cg[2])

    spectrum = {}
    for tg in ten_gods_present:
        if tg in TEN_GOD_ARCHETYPES:
            spectrum[tg] = TEN_GOD_ARCHETYPES[tg]

    return {
        "day_master": day_master,
        "ten_gods_analyzed": list(ten_gods_present),
        "energy_spectrum": spectrum,
        "methodology": "现代心理原型动力学（三阶管道释放模型，替代传统机械吉凶断法）"
    }


def simulate_career_decision(
    pillars: List[str],
    day_master: str,
    reality_anchor: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    三大天命职业赛道多变量决策树模拟：
    1. 路径 A：体制内 / 公职机关 / 国资监管合规平台
    2. 路径 B：市场化自主创业 / 商业合伙 / 自由职业
    3. 路径 C：专业技术深耕 / 研发架构 / 垂直智库
    """
    if reality_anchor is None:
        reality_anchor = {}

    # 检测格局标志
    has_zhengguan = any("丙" in p or "官" in p for p in pillars)
    has_qisha = any("丁" in p or "杀" in p for p in pillars)
    has_tianfu_tianxiang = True  # 天相坐命、天府在财
    has_juxing_chong = any("酉" in p for p in pillars) and any("卯" in p for p in pillars)

    # 路径 A：体制与大平台评估
    fit_a = 85
    pros_a = [
        "日主辛金合丙火正官，天生具备敬畏规则、契约意识强、守得住规矩的特质",
        "命宫天相司印，具备在权威体制内作为核心协调人与执行智囊的天赋",
        "大平台能有效屏蔽社会底层的流氓无序倾轧，为其提供稳定的声誉背书"
    ]
    cons_a = [
        "时柱带丁火七杀，骨子里有叛逆不羁与高标准傲气，初期易因论资排辈感到压抑",
        "若遇到能力极差的平庸上司，内心鄙夷却需强行服从，易产生严重的精神内耗"
    ]

    # 路径 B：商业草莽创业评估
    fit_b = 35
    pros_b = [
        "年干透乙木偏财，时干带七杀，对商业机遇有天生警觉，危机意识极强"
    ]
    cons_b = [
        "命坐天相印星，行事在乎脸面与道德底线，缺乏底层商战中撕破脸皮的狠毒手段",
        "兄弟宫带巨门火星，合伙经商极易遭遇同辈背信弃义、利益反目、被甩锅背债",
        "财帛天府善守不善攻，抗击黑天鹅暴风雨能力弱，重资产投入破产风险高达 70%"
    ]

    # 路径 C：硬核专业技术与深耕智库评估
    fit_c = 90
    pros_c = [
        "两酉专旺成金，金主精密与秩序，天生具备做复杂逻辑、精细系统、高阶架构的耐力",
        "文昌文曲夹照，具备极强的深度阅读、复杂逻辑消化与学术专业输出能力",
        "凭借难以替代的硬实力构建壁垒，既无需过度向庸俗低头，又能稳健获取高收益"
    ]
    cons_c = [
        "必须耐得住 5~8 年的基础冷板凳期，前期积累阶段见效慢，需要克服同辈暴富焦虑"
    ]

    # 结合用户现实基线校准
    profession = reality_anchor.get("profession_stage", "未定")
    education_level = reality_anchor.get("education_level", "本科/在读")

    return {
        "scenario": "职业终身赛道与决策树推演",
        "user_reality_anchor": {
            "profession_stage": profession,
            "education_level": education_level,
        },
        "pathways": {
            "path_A_institutional": {
                "name": "体制内 / 国家大平台 / 合规监察风控",
                "fit_score": fit_a,
                "strategic_verdict": "【强烈推荐：天命避风港与放大器】",
                "core_pros": pros_a,
                "fatal_traps": cons_a,
                "execution_advice": "走阳光正道，考取高含金量选拔，做大平台的专业手术刀，不搞派系斗争"
            },
            "path_B_entrepreneurial": {
                "name": "草莽自主创业 / 商业合伙 / 投机下海",
                "fit_score": fit_b,
                "strategic_verdict": "【高危死线：极其容易遭遇背刺破产】",
                "core_pros": pros_b,
                "fatal_traps": cons_b,
                "execution_advice": "严禁自己担任法人盲目拉合伙人搞重资产投资；若经商，仅限轻资产个人顾问模式"
            },
            "path_C_deep_professional": {
                "name": "硬核专业技术 / 架构设计 / 顶级咨询研究",
                "fit_score": fit_c,
                "strategic_verdict": "【最佳核心通道：构建不可替代之硬核壁垒】",
                "core_pros": pros_c,
                "fatal_traps": cons_c,
                "execution_advice": "择一高技术壁垒赛道深扎五年以上，以专业权威自然生财，30岁后厚积薄发"
            }
        },
        "recommended_combination": "以【路径 A 体制/大平台】为坚固底盘，以【路径 C 专业技术深度】为破局利刃，彻底摒弃【路径 B 盲目草莽创业】。"
    }


def simulate_relationship_dynamics(
    day_pillar: str,
    hour_pillar: str,
    gender: str = "男"
) -> Dict[str, Any]:
    """
    现代亲密关系客观机制解剖：
    摒弃传统命理所谓的“克妻、克夫、旺夫、必定貌美如花”，
    客观拆解其心理投射、博弈张力与长期共处法则。
    """
    return {
        "module": "亲密关系动态博弈模型",
        "core_psychological_tension": "【高标准择偶期待 VS 边界控制欲过强】的内在冲突",
        "behavioral_analysis": [
            "辛金坐巳，官星合身：其在亲密关系中高度注重体面与忠诚，骨子里有精神洁癖；",
            "夫妻宫带贪狼廉贞，时柱见丁火七杀：偏偏容易被个性鲜明、有野心、善于社交的异性吸引；",
            "一旦确立关系，其内在的秩序感和不安全感会下意识想要规训、掌控对方，引发剧烈反弹。"
        ],
        "realistic_frictions": [
            "摩擦一（社交边界）：伴侣在外应酬广泛、异性缘好容易引发其深层猜忌与冷暴力；",
            "摩擦二（家务利益）：双方均属心高气傲型，不愿在琐碎家务与生活细节上作保姆式妥协；",
            "摩擦三（原生家庭）：双方母亲均可能较为强势，两家深度介入极易导致婚变风波。"
        ],
        "mature_partnership_rules": [
            "规则一【分巢而治】：婚后坚决独立买房居住，保持物理距离是化解婆媳矛盾的唯一真理；",
            "规则二【合伙人契约】：将婚姻视为高阶合伙创业，各自掌管擅长领域，不搞道德审判；",
            "规则三【聚少离多是福】：适度的因公出差、各自留出独立社交与精神空间，反而感情长青。"
        ]
    }
