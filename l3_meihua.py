# -*- coding: utf-8 -*-
"""l3_meihua.py — L3-梅花 梅花易数（梅花心易）排盘模块
底本：《梅花易数》邵雍原著体系（先天八卦数/起卦三法/体用生克五态/互变卦），辅《增广校正梅花易数》；
六十四卦名与卦辞要点出《周易》通行本（模块内转录，同 l3_liuyao.py 转录底本）。
功能（每项 Rule-ID mh-01..06）：
  mh-01 时间起卦（农历法）：上卦=(年支序+农历月+农历日)÷8 余(0取8)，下卦=(上卦总数+时支序)÷8 余，
        动爻=总÷6 余(0取6)；年支=节气干支年支（m1 r3 立春换年，与 oracle 实测一致）、
        农历月日=data/shuowang.csv 朔日表（民俗农历，换算链注明）、时支=m1 时柱（真太阳时口径）。
  mh-02 报数起卦：2 数 上=n1÷8 余、下=n2÷8 余、动=(n1+n2)÷6 余；3 数 上=n1、下=n2、动=n3（第三数为动爻）。
        异文(alt)：动爻加时辰派（《梅花易数·物数占》『以时数配卦』法；易运盘 oracle 实测恒加时辰）：
        2 数动=(n1+n2+时支)÷6、3 数动=(n1+n2+n3+时支)÷6、单数 上=n÷8 下=(n+时支)÷8 动=(n+时支)÷6。
  mh-03 字数起卦：按字数 N 分上下卦：上=N//2、下=(N+1)//2（原著《字数占》『少一字为上卦（天轻清），
        多一字为下卦』→ 奇数上少下多为主表）、动=N÷6 余；奇数取法异文(alt)：上多下少派（more_up）；
        一字卦（以字笔画起卦）/二字卦（前字笔画上卦、后字笔画下卦）两流派仅 alt 标注不作实现。
  mh-04 卦象展开：本卦（上下卦）、互卦（二三四爻为下、三四五爻为上）、变卦（动爻阴阳互变）；
        八卦意象表（天象/家庭人物/身体/方位，数据驱动）。
  mh-05 体用生克断（核心）：动爻所在卦为用、另一卦为体；五态：体用比和（吉）/用生体（吉）/体克用（中吉）/
        体生用（耗泄）/用克体（凶）；四季旺衰加权：春木旺火相、夏火旺土相、秋金旺水相、冬水旺木相、
        四季月（辰戌丑未）土旺金相，旺2相1休0囚-1死-2，囚=克旺者、死=旺所克（《五行大义》四时休王，
        通行定义；规则加权，非原著原文，注明）；
        动爻在初/上之体用判定有异文（『初上无位』派以变卦为用），alt 标注。
  mh-06 断事接口：问事分类（事业/婚姻/求财/出行/失物/疾病/通用）× 体用五态 + 用卦意象 → 倾向断语
        （规则启发式，非神断）。
I-7 契约：断语止于规则启发式（五态+意象映射），不声称神断；输出格式与六爻 l3_liuyao.py 互认
（input/method/ben_gua/bian_gua/rules 字段同构）。输入=北京时+东经（同 m1，1949-2100）。"""
import argparse, bisect, csv, json, os, re, sys
from datetime import datetime
from functools import lru_cache
import m1
from rules import ZHI, sheng, ke, rel, wx_of_zhi

BASE = os.path.dirname(os.path.abspath(__file__))

# ---- 先天八卦：卦名→(先天数, 三爻象[自下而上], 五行)；余 0 取整见 _num8/_num6 ----
TG = {"乾": (1, "阳阳阳", "金"), "兑": (2, "阳阳阴", "金"), "离": (3, "阳阴阳", "火"),
      "震": (4, "阳阴阴", "木"), "巽": (5, "阴阳阳", "木"), "坎": (6, "阴阳阴", "水"),
      "艮": (7, "阴阴阳", "土"), "坤": (8, "阴阴阴", "土")}
TG_NAME = {v[0]: k for k, v in TG.items()}   # 先天数 → 卦名

# ---- 八卦意象表（《梅花易数·八卦万物属类》：天象/家庭人物/身体/方位；数据驱动供 mh-04/mh-06） ----
IMAGE = {
    "乾": {"nature": "天", "family": "父", "body": "首", "dir": "西北"},
    "兑": {"nature": "泽", "family": "少女", "body": "口", "dir": "西"},
    "离": {"nature": "火", "family": "中女", "body": "目", "dir": "南"},
    "震": {"nature": "雷", "family": "长男", "body": "足", "dir": "东"},
    "巽": {"nature": "风", "family": "长女", "body": "股", "dir": "东南"},
    "坎": {"nature": "水", "family": "中男", "body": "耳", "dir": "北"},
    "艮": {"nature": "山", "family": "少男", "body": "手", "dir": "东北"},
    "坤": {"nature": "地", "family": "母", "body": "腹", "dir": "西南"},
}

# ---- 六十四卦：{卦名: (上卦, 下卦)}；与 l3_liuyao.py GUA64 同源（通行本卦序） ----
GUA64 = {
    "乾为天": ("乾", "乾"), "天泽履": ("乾", "兑"), "天火同人": ("乾", "离"), "天雷无妄": ("乾", "震"),
    "天风姤": ("乾", "巽"), "天水讼": ("乾", "坎"), "天山遁": ("乾", "艮"), "天地否": ("乾", "坤"),
    "泽天夬": ("兑", "乾"), "兑为泽": ("兑", "兑"), "泽火革": ("兑", "离"), "泽雷随": ("兑", "震"),
    "泽风大过": ("兑", "巽"), "泽水困": ("兑", "坎"), "泽山咸": ("兑", "艮"), "泽地萃": ("兑", "坤"),
    "火天大有": ("离", "乾"), "火泽睽": ("离", "兑"), "离为火": ("离", "离"), "火雷噬嗑": ("离", "震"),
    "火风鼎": ("离", "巽"), "火水未济": ("离", "坎"), "火山旅": ("离", "艮"), "火地晋": ("离", "坤"),
    "雷天大壮": ("震", "乾"), "雷泽归妹": ("震", "兑"), "雷火丰": ("震", "离"), "震为雷": ("震", "震"),
    "雷风恒": ("震", "巽"), "雷水解": ("震", "坎"), "雷山小过": ("震", "艮"), "雷地豫": ("震", "坤"),
    "风天小畜": ("巽", "乾"), "风泽中孚": ("巽", "兑"), "风火家人": ("巽", "离"), "风雷益": ("巽", "震"),
    "巽为风": ("巽", "巽"), "风水涣": ("巽", "坎"), "风山渐": ("巽", "艮"), "风地观": ("巽", "坤"),
    "水天需": ("坎", "乾"), "水泽节": ("坎", "兑"), "水火既济": ("坎", "离"), "水雷屯": ("坎", "震"),
    "水风井": ("坎", "巽"), "坎为水": ("坎", "坎"), "水山蹇": ("坎", "艮"), "水地比": ("坎", "坤"),
    "山天大畜": ("艮", "乾"), "山泽损": ("艮", "兑"), "山火贲": ("艮", "离"), "山雷颐": ("艮", "震"),
    "山风蛊": ("艮", "巽"), "山水蒙": ("艮", "坎"), "艮为山": ("艮", "艮"), "山地剥": ("艮", "坤"),
    "地天泰": ("坤", "乾"), "地泽临": ("坤", "兑"), "地火明夷": ("坤", "离"), "地雷复": ("坤", "震"),
    "地风升": ("坤", "巽"), "地水师": ("坤", "坎"), "地山谦": ("坤", "艮"), "坤为地": ("坤", "坤"),
}
NAME_BY = {v: k for k, v in GUA64.items()}   # (上, 下) → 卦名

# ---- 卦辞要点：《周易》通行本（模块内转录；同 l3_liuyao.py 底本，64 键全覆盖） ----
GUACI = {
    "乾为天": "乾：元亨利贞。", "坤为地": "坤：元亨，利牝马之贞。君子有攸往，先迷后得主，利。西南得朋，东北丧朋。安贞吉。",
    "水雷屯": "屯：元亨，利贞。勿用有攸往，利建侯。", "山水蒙": "蒙：亨。匪我求童蒙，童蒙求我。初筮告，再三渎，渎则不告。利贞。",
    "水天需": "需：有孚，光亨，贞吉。利涉大川。", "天水讼": "讼：有孚窒惕，中吉，终凶。利见大人，不利涉大川。",
    "地水师": "师：贞，丈人吉，无咎。", "水地比": "比：吉。原筮，元永贞，无咎。不宁方来，后夫凶。",
    "风天小畜": "小畜：亨。密云不雨，自我西郊。", "天泽履": "履：履虎尾，不咥人，亨。",
    "地天泰": "泰：小往大来，吉亨。", "天地否": "否：否之匪人，不利君子贞，大往小来。",
    "天火同人": "同人：同人于野，亨。利涉大川，利君子贞。", "火天大有": "大有：元亨。",
    "地山谦": "谦：亨，君子有终。", "雷地豫": "豫：利建侯行师。",
    "泽雷随": "随：元亨利贞，无咎。", "山风蛊": "蛊：元亨，利涉大川。先甲三日，后甲三日。",
    "地泽临": "临：元亨利贞。至于八月有凶。", "风地观": "观：盥而不荐，有孚颙若。",
    "火雷噬嗑": "噬嗑：亨。利用狱。", "山火贲": "贲：亨。小利有攸往。",
    "山地剥": "剥：不利有攸往。", "地雷复": "复：亨。出入无疾，朋来无咎。反复其道，七日来复，利有攸往。",
    "天雷无妄": "无妄：元亨利贞。其匪正有眚，不利有攸往。", "山天大畜": "大畜：利贞。不家食吉，利涉大川。",
    "山雷颐": "颐：贞吉。观颐，自求口实。", "泽风大过": "大过：栋桡。利有攸往，亨。",
    "坎为水": "坎：习坎，有孚，维心亨，行有尚。", "离为火": "离：利贞，亨。畜牝牛吉。",
    "泽山咸": "咸：亨，利贞。取女吉。", "雷风恒": "恒：亨，无咎，利贞。利有攸往。",
    "天山遁": "遁：亨，小利贞。", "雷天大壮": "大壮：利贞。",
    "火地晋": "晋：康侯用锡马蕃庶，昼日三接。", "地火明夷": "明夷：利艰贞。",
    "风火家人": "家人：利女贞。", "火泽睽": "睽：小事吉。",
    "水山蹇": "蹇：利西南，不利东北。利见大人，贞吉。", "雷水解": "解：利西南。无所往，其来复吉。有攸往，夙吉。",
    "山泽损": "损：有孚，元吉，无咎，可贞，利有攸往。曷之用？二簋可用享。", "风雷益": "益：利有攸往，利涉大川。",
    "泽天夬": "夬：扬于王庭，孚号有厉。告自邑，不利即戎，利有攸往。", "天风姤": "姤：女壮，勿用取女。",
    "泽地萃": "萃：亨。王假有庙，利见大人，亨，利贞。用大牲吉，利有攸往。", "地风升": "升：元亨，用见大人，勿恤，南征吉。",
    "泽水困": "困：亨，贞，大人吉，无咎。有言不信。", "水风井": "井：改邑不改井，无丧无得，往来井井。汔至亦未繘井，羸其瓶，凶。",
    "泽火革": "革：己日乃孚，元亨利贞，悔亡。", "火风鼎": "鼎：元吉，亨。",
    "震为雷": "震：亨。震来虩虩，笑言哑哑。震惊百里，不丧匕鬯。", "艮为山": "艮：艮其背，不获其身；行其庭，不见其人，无咎。",
    "风山渐": "渐：女归吉，利贞。", "雷泽归妹": "归妹：征凶，无攸利。",
    "雷火丰": "丰：亨，王假之。勿忧，宜日中。", "火山旅": "旅：小亨，旅贞吉。",
    "巽为风": "巽：小亨。利有攸往，利见大人。", "兑为泽": "兑：亨，利贞。",
    "风水涣": "涣：亨。王假有庙，利涉大川，利贞。", "水泽节": "节：亨。苦节不可贞。",
    "风泽中孚": "中孚：豚鱼吉。利涉大川，利贞。", "雷山小过": "小过：亨，利贞。可小事，不可大事。飞鸟遗之音，不宜上，宜下，大吉。",
    "水火既济": "既济：亨小，利贞。初吉终乱。", "火水未济": "未济：亨。小狐汔济，濡其尾，无攸利。",
}
GUACI_SOURCE = "《周易》通行本卦辞（模块内转录，同 l3_liuyao 底本）"

# ---- 体用五态（《梅花易数·体用生克》）：用对体关系 → (名, 吉凶, 断语基调) ----
TIYONG = {
    "比和": ("体用比和", "吉", "诸事顺遂，得同气之助"),
    "生":   ("用生体", "吉", "得外力生扶，诸事有助"),
    "耗":   ("体克用", "中吉", "主动权在己，宜努力争取"),
    "泄":   ("体生用", "耗泄", "自身耗泄，事费力而迟成"),
    "克":   ("用克体", "凶", "受克受阻，宜谨慎缓行"),
}

# ---- 四季旺衰（规则加权，非原著原文）：季 → 旺五行；旺2相1休0囚-1死-2；
#      通行定义（《五行大义》四时休王）：当令者旺、令生者相、生令者休、克令者囚、令克者死 ----
SEASON_OF_ZHI = {"寅": "春", "卯": "春", "巳": "夏", "午": "夏", "申": "秋", "酉": "秋",
                 "亥": "冬", "子": "冬", "辰": "四季", "戌": "四季", "丑": "四季", "未": "四季"}
SEASON_WANG = {"春": "木", "夏": "火", "秋": "金", "冬": "水", "四季": "土"}
WEIGHT_NAME = {"旺": 2, "相": 1, "休": 0, "囚": -1, "死": -2}

# ---- 断事分类表（mh-06 规则启发式）：五态 → 分类断语模板，{用卦意象} 占位 ----
DUAN = {
    "事业": {"比和": "谋事顺遂，同侪相扶。", "生": "得上司或外缘相助，进益可期。", "耗": "事在人为，付出可成。",
            "泄": "费力耗神，宜稳扎稳打。", "克": "阻力不小，宜待时而动。"},
    "婚姻": {"比和": "两情相悦，婚恋和合。", "生": "情缘受生，进展顺利。", "耗": "宜主动经营，可成。",
            "泄": "付出多而回应少，宜沟通。", "克": "情缘受阻，勿强求。"},
    "求财": {"比和": "财运平顺，得利见机。", "生": "外财来助，见利可获。", "耗": "谋财须力，勤可得。",
            "泄": "破耗之象，宜量入为出。", "克": "求财受阻，慎防破耗。"},
    "出行": {"比和": "出行平安，遇事有解。", "生": "出行得助，途中顺遂。", "耗": "出行可成，费些周折。",
            "泄": "舟车劳顿，宜早作准备。", "克": "出行不利，宜缓行或改期。"},
    "失物": {"比和": "失物尚在，可复寻。", "生": "失物可寻，有人代收。", "耗": "需费心力，向{用卦意象}方位寻。",
            "泄": "失物难寻，恐已远移。", "克": "失物难归，宜放宽心。"},
    "疾病": {"比和": "病势平稳，渐可向愈。", "生": "得良医良药，可望康复。", "耗": "病势可控，须遵医嘱。",
            "泄": "体气耗损，宜养不宜劳。", "克": "体受其克，宜早诊治，切勿拖延。"},
    "通用": {"比和": "诸事顺遂，进退有据。", "生": "得外力生扶，谋为有成。", "耗": "事可成而须亲为。",
            "泄": "事费心力，宜缓图。", "克": "事多阻隔，宜守勿进。"},
}
CATEGORIES = ["事业", "婚姻", "求财", "出行", "失物", "疾病", "通用"]


@lru_cache(maxsize=None)
def load_shuo():
    """shuowang.csv → 按朔时刻升序的 (datetime, 行)；农历月日唯一权威（UTC+8）。"""
    rows = list(csv.DictReader(open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8")))
    rows.sort(key=lambda r: r["shuo_time"])
    return [(datetime.strptime(r["shuo_time"][:16], "%Y-%m-%dT%H:%M"), r) for r in rows]


def _num8(n):
    """÷8 余 0 取 8（坤）。"""
    return (n - 1) % 8 + 1


def _num6(n):
    """÷6 余 0 取 6（上爻动）。"""
    return (n - 1) % 6 + 1


def lunar_parts(dt):
    """农历(年支序, 月, 日, 是否闰月)：最近上一朔时刻 → 朔日表行；闰月沿用原月数（民俗口径，朔日整天=初一）。
    朔表缺失/越界 → ValueError（不静默回退第三方推算，同 m1/preregister 契约）。"""
    rows = load_shuo()
    if not rows:
        raise ValueError("data/shuowang.csv 缺失或为空：农历月日不可判定（朔日表为 L3 前置录入）")
    t = dt.replace(second=0, microsecond=0)
    d = t.date()
    i = bisect.bisect_right([r[0].date() for r in rows], d) - 1
    if i < 0 or t < rows[0][0] or (t - rows[i][0]).days > 31:
        raise ValueError(f"农历月日不可判定：{dt.strftime('%Y-%m-%d %H:%M')} 在朔日表范围外（表 {rows[0][0]} ~ {rows[-1][0]}）")
    row = rows[i][1]
    return ZHI.index(row["lunar_year"][1]) + 1, int(row["month"]), (d - rows[i][0].date()).days + 1, row["is_ruen"] == "1"


def _base(dt, lon):
    """m1 四柱取 年支序/月支/时支（真太阳时口径）+ 节气年干支；m1 错误透传。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r, None
    p = r["pillars"]
    return r, {"year_zhi": ZHI.index(p["year"]["ganzhi"][1]) + 1,
               "month_zhi": p["month"]["ganzhi"][1], "hour_zhi": ZHI.index(p["hour"]["ganzhi"][1]) + 1}


# ================= mh-01 时间起卦（农历法） =================

def time_meihua(dt, lon=120.0):
    """mh-01 时间起卦 → (上卦数, 下卦数, 动爻位, chain)；chain 注明换算链（年支/农历月日/时支来源）。
    年支数=节气干支年支序（m1 r3 立春换年，同 oracle 实测与《梅花易数》观梅占『辰年』口径；
    民俗农历年支（shuowang lunar_year，正月初一换年）仅链内展示不作起卦数）。"""
    r, base = _base(dt, lon)
    if base is None:
        return r
    try:
        ly, mo, d, ruen = lunar_parts(dt)
    except ValueError as e:
        return {"error": f"错误: {e}"}
    y = base["year_zhi"]  # 起卦年支 = 干支纪年支（节气年）
    up = _num8(y + mo + d)
    down = _num8(y + mo + d + base["hour_zhi"])
    dong = _num6(y + mo + d + base["hour_zhi"])
    chain = {"year_zhi": y, "lunar_year_zhi": ly, "lunar_month": mo, "lunar_day": d, "is_ruen": ruen,
             "hour_zhi": base["hour_zhi"],
             "steps": [
                 {"year_zhi": "m1 r3 节气年（立春换年）干支年支序——起卦年支；民俗农历年支（shuowang lunar_year）仅展示",
                  "lunar": "data/shuowang.csv 朔日表农历月日", "hour_zhi": "m1 r2 时柱（真太阳时口径）"},
                 {"formula": "上=(年支序+农历月+农历日)÷8 余；下=(上卦总数+时支序)÷8 余；动=总÷6 余（0取8/6）"}],
             "sum_up": y + mo + d, "sum_down": y + mo + d + base["hour_zhi"],
             "year_ganzhi": r["pillars"]["year"]["ganzhi"], "month_ganzhi": r["pillars"]["month"]["ganzhi"],
             "day_ganzhi": r["pillars"]["day"]["ganzhi"], "hour_ganzhi": r["pillars"]["hour"]["ganzhi"]}
    return up, down, dong, chain


# ================= mh-02 报数起卦 =================

def number_meihua(nums, hour_zhi=0, variant="standard"):
    """mh-02 报数起卦 → (上卦数, 下卦数, 动爻位, info)。
    variant=standard：2 数 动=(n1+n2)÷6；3 数 动=n3（第三数为动爻，任务书口径）。
    variant=add_hour：动爻加时辰派（易运盘 oracle 实测口径，alt）：2 数动=(n1+n2+时)÷6、3 数动=和÷6、1 数 上=n 下=(n+时)。"""
    n = len(nums)
    if n not in (1, 2, 3) or any(x < 1 for x in nums):
        return {"error": f"错误: 报数须 1~3 个正整数，收到 {nums}"}
    if variant == "add_hour":  # alt 加时辰派（同 oracle 实测）
        if n == 1:
            return _num8(nums[0]), _num8(nums[0] + hour_zhi), _num6(nums[0] + hour_zhi), {"variant": variant, "nums": nums}
        return _num8(nums[0]), _num8(nums[1]), _num6(sum(nums) + hour_zhi), {"variant": variant, "nums": nums}
    if n == 1:  # 主表仅支持 2/3 数；1 数时退加时辰派（《梅花易数》物数占原文法）并 alt 标注
        return _num8(nums[0]), _num8(nums[0] + hour_zhi), _num6(nums[0] + hour_zhi), {"variant": "single", "nums": nums}
    if n == 2:
        return _num8(nums[0]), _num8(nums[1]), _num6(nums[0] + nums[1]), {"variant": "standard", "nums": nums}
    return _num8(nums[0]), _num8(nums[1]), _num6(nums[2]), {"variant": "standard", "nums": nums}


# ================= mh-03 字数起卦 =================

def word_meihua(text, hour_zhi=0, variant="standard"):
    """mh-03 字数起卦 → (上卦数, 下卦数, 动爻位, info)。按字数 N 平分：上=N//2、下=(N+1)//2、动=N÷6 余。
    《梅花易数·字数占》原文『少一字为上卦（天轻清），多一字为下卦』→ 奇数上少下多为主表；
    variant=more_up：奇数取上多下少（异文 alt）；一字卦（笔画起卦）/二字卦（前字笔画上、后字笔画下）为另派 alt 仅标注。"""
    n = len(re.sub(r"\s", "", text) if isinstance(text, str) else "")
    if n < 1:
        return {"error": "错误: 字数起卦须至少 1 字"}
    if n == 1:  # 一字卦：以笔画起卦属另派（alt），主表按物数法以 1 字当 1 数
        return _num8(n), _num8(n + hour_zhi), _num6(n + hour_zhi), {"variant": "standard", "chars": n, "alt": "一字卦另派以字之笔画起卦（《梅花易数·字数占》），本模块按字数 1 计"}
    if variant == "more_up":
        up, down = (n + 1) // 2, n // 2
    else:
        up, down = n // 2, (n + 1) // 2
    return _num8(up), _num8(down), _num6(n), {"variant": variant, "chars": n, "up_chars": up, "down_chars": down,
                                               "alt": "奇数字数取法异文：上少下多（主表，原著『少一字为上卦』）vs 上多下少（more_up 派）；二字卦另派以前字笔画为上卦、后字笔画为下卦"}


# ================= mh-04 卦象展开 =================

def _gua_info(name, up, down, yaoxiang):
    """单卦信息：卦名/上下卦/爻象/卦辞/意象。"""
    return {"name": name, "up": up, "down": down, "yaoxiang": yaoxiang, "guaci": GUACI[name],
            "guaci_source": GUACI_SOURCE, "images": {"up": IMAGE[up], "down": IMAGE[down]},
            "rule_id": "mh-04", "source": "《梅花易数》卦象展开（互卦取二三四爻为下、三四五爻为上；变卦动爻阴阳互变）"}


def expand(up, down, dong):
    """(上卦数, 下卦数, 动爻位) → (ben, hu, bian, dong) 卦名与爻象。"""
    up_t, down_t = TG_NAME[up], TG_NAME[down]
    ben = TG[down_t][1] + TG[up_t][1]                      # 六爻自下而上 = 内(下)三爻 + 外(上)三爻
    flip = {"阳": "阴", "阴": "阳"}
    bian = "".join(flip[c] if i == dong - 1 else c for i, c in enumerate(ben))
    hu_down = ben[1:4]                                     # 二三四爻
    hu_up = ben[2:5]                                       # 三四五爻
    t = {v[1]: k for k, v in TG.items()}
    ben_name = NAME_BY[(up_t, down_t)]
    hu_name = NAME_BY[(t[hu_up], t[hu_down])]
    bian_name = NAME_BY[(t[bian[3:]], t[bian[:3]])]
    return (_gua_info(ben_name, up_t, down_t, ben), _gua_info(hu_name, t[hu_up], t[hu_down], hu_up + hu_down),
            _gua_info(bian_name, t[bian[3:]], t[bian[:3]], bian), dong)


# ================= mh-05 体用生克断 =================

def ti_yong(up_t, down_t, dong, month_zhi):
    """体用判定 + 五态吉凶 + 四季旺衰加权。
    动爻在下卦（初二三爻）→ 用=下卦、体=上卦；动爻在上卦（四五上爻）→ 用=上卦、体=下卦。
    alt：动爻在初/上时『初上无位』派以变卦为用（《增广校正梅花易数》注疏异文）。"""
    dong_in_down = dong <= 3
    yong, ti = (down_t, up_t) if dong_in_down else (up_t, down_t)
    r = rel(TG[yong][2], TG[ti][2])
    if r == "比和":
        name, verdict, tone = TIYONG["比和"]
    elif r == "生":
        name, verdict, tone = TIYONG["生"]
    elif r == "耗":                      # 体克用：体五行克用五行
        name, verdict, tone = TIYONG["耗"]
    elif r == "泄":                      # 体生用：体五行生用五行
        name, verdict, tone = TIYONG["泄"]
    else:                                # r == "克"：用克体
        name, verdict, tone = TIYONG["克"]
    # 四季旺衰（规则加权非原著原文）：季 → 旺五行 → 各五行旺相休囚死
    # 通行定义（《五行大义》四时休王）：当令者旺、令生者相、生令者休、克令者囚、令克者死
    season = SEASON_OF_ZHI[month_zhi]
    wang = SEASON_WANG[season]
    status = {wx: ("旺" if wx == wang else "相" if sheng(wang, wx) else "休" if sheng(wx, wang)
                   else "囚" if ke(wx, wang) else "死") for wx in ("木", "火", "土", "金", "水")}
    weight = lambda wx: WEIGHT_NAME[status[wx]]
    return {"ti": {"gua": ti, "wx": TG[ti][2], "side": "上卦" if ti == up_t else "下卦",
                   "wangshuai": status[TG[ti][2]], "weight": weight(TG[ti][2])},
            "yong": {"gua": yong, "wx": TG[yong][2], "side": "上卦" if yong == up_t else "下卦",
                     "wangshuai": status[TG[yong][2]], "weight": weight(TG[yong][2])},
            "dong_in": "下卦" if dong_in_down else "上卦", "relation": r, "name": name, "verdict": verdict,
            "tone": tone, "season": season, "season_wang": wang, "status": status,
            "weight_note": "四季旺衰加权为规则加权（旺2相1休0囚-1死-2；囚=克旺者、死=旺所克，《五行大义》四时休王通行定义），非《梅花易数》原著原文",
            "rule_id": "mh-05", "source": "《梅花易数·体用生克》：动爻所在卦为用，另一卦为体；体用比和吉、用生体吉、体克用中吉、体生用耗泄、用克体凶",
            "alt": ["动爻在初爻/上爻之体用判定异文：『初上无位』派（《增广校正梅花易数》注疏）以本卦为体、变卦为用；本模块主表仍按动爻所在卦为用"]}


# ================= mh-06 断事接口 =================

def duan(category, tiy):
    """问事分类 × 体用五态 + 用卦意象 → 倾向断语（规则启发式，非神断）。"""
    if category not in CATEGORIES:
        category = "通用"
    img = IMAGE[tiy["yong"]["gua"]]
    text = DUAN[category][tiy["relation"]].replace("{用卦意象}", f"{img['nature']}（{img['dir']}）")
    if category == "通用":
        text += f"；用卦为{tiy['yong']['gua']}（{img['nature']}），可参{img['family']}、{img['body']}之象。"
    return {"category": category, "ti_yong": tiy["name"], "verdict": tiy["verdict"], "text": text,
            "rule_id": "mh-06",
            "source": "规则启发式（体用生克五态 × 用卦意象映射表），非神断；与 l3_liuyao 断卦契约 I-7 同"}


# ================= 入口 =================

def _build(dt, lon, label, rule_id, nums, up, down, dong, chain, tiy_extra):
    """统一排盘 JSON：本卦/互卦/变卦/体用/断语全字段带 rule_id/source/alt。"""
    ben, hu, bian, _ = expand(up, down, dong)
    tiy = ti_yong(ben["up"], ben["down"], dong, tiy_extra["month_zhi"])
    method = {"label": label, "rule_id": rule_id, "source": "《梅花易数》起卦三法（先天八卦数 乾1兑2离3震4巽5坎6艮7坤8，÷8÷6 余 0 取整）",
              "nums": nums}
    if tiy_extra.get("method_alt"):   # 无异文说明时省略 alt 键，不输出 null
        method["alt"] = tiy_extra["method_alt"]
    out = {"input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon},
           "method": method,
           "ben_gua": ben, "hu_gua": hu, "bian_gua": bian, "dong": dong,
           "ti_yong": tiy, "duan": duan(tiy_extra.get("category", "通用"), tiy),
           "rules": [
               {"rule_id": "mh-01", "source": "时间起卦（农历法）：上=(年支序+农历月+农历日)÷8、下=(+时支序)÷8、动=÷6；年支=节气年支(m1 r3)、农历月日=shuowang.csv、时支=m1 r2 真太阳时"},
               {"rule_id": "mh-02", "source": "报数起卦：2 数 上=n1 下=n2 动=(n1+n2)÷6；3 数 动=第三数÷6；加时辰派为异文(alt)"},
               {"rule_id": "mh-03", "source": "字数起卦：字数平分上下卦（主表奇数上少下多，原著『少一字为上卦』）、动=字数÷6；奇数取法异文(alt)"},
               {"rule_id": "mh-04", "source": "卦象展开：本卦/互卦（二三四爻为下、三四五爻为上）/变卦（动爻变）"},
               {"rule_id": "mh-05", "source": "体用生克五态（《梅花易数》）+ 四季旺衰加权（规则加权非原文）"},
               {"rule_id": "mh-06", "source": "断事接口：规则启发式，非神断（I-7）"},
           ]}
    if chain is not None:
        out["chain"] = chain
    return out


def compute_time(dt, lon=120.0, category="通用"):
    """mh-01 时间起卦入口：北京时+东经 → 排盘 JSON。"""
    t = time_meihua(dt, lon)
    if isinstance(t, dict):
        return t
    up, down, dong, chain = t
    return _build(dt, lon, "时间起卦·农历（梅花）", "mh-01", {"year_zhi": chain["year_zhi"],
                 "lunar_month": chain["lunar_month"], "lunar_day": chain["lunar_day"],
                 "hour_zhi": chain["hour_zhi"], "sum_up": chain["sum_up"], "sum_down": chain["sum_down"]},
                 up, down, dong, chain, {"month_zhi": chain["month_ganzhi"][1], "category": category})


def compute_numbers(nums, dt, lon=120.0, variant="standard", category="通用"):
    """mh-02 报数起卦入口：(nums=[n1,n2[,n3]], 北京时, 东经, variant) → 排盘 JSON。
    variant：standard（主表，第三数为动爻）/ add_hour（加时辰派，alt，同易运盘 oracle 口径）。"""
    r, base = _base(dt, lon)
    if base is None:
        return r
    t = number_meihua(nums, base["hour_zhi"], variant)
    if isinstance(t, dict):
        return t
    up, down, dong, info = t
    alt = (["动爻加时辰派（《梅花易数·物数占》时数配卦法；易运盘 oracle 实测恒加时辰）："
            f"2 数动=(n1+n2+时{base['hour_zhi']})÷6、3 数动=(n1+n2+n3+时)÷6"]
           if variant == "standard" else None)
    return _build(dt, lon, "报数起卦" + ("·加时辰派(alt)" if variant == "add_hour" else ""), "mh-02",
                  {"nums": nums, "hour_zhi": base["hour_zhi"]}, up, down, dong, None,
                  {"month_zhi": base["month_zhi"], "category": category, "method_alt": alt})


def compute_words(text, dt, lon=120.0, variant="standard", category="通用"):
    """mh-03 字数起卦入口：(文本, 北京时, 东经, variant) → 排盘 JSON。"""
    r, base = _base(dt, lon)
    if base is None:
        return r
    t = word_meihua(text, base["hour_zhi"], variant)
    if isinstance(t, dict):
        return t
    up, down, dong, info = t
    return _build(dt, lon, "字数起卦" + ("·上多下少派(alt)" if variant == "more_up" else ""), "mh-03",
                  {"chars": info["chars"], "split": f"{info['up_chars']}/{info['down_chars']}" if "up_chars" in info else "一字"},
                  up, down, dong, None,
                  {"month_zhi": base["month_zhi"], "category": category, "method_alt": [info["alt"]]})


def main():
    ap = argparse.ArgumentParser(description="L3-梅花 梅花易数排盘（时间/报数/字数起卦 + 体用生克 + 断事启发式）")
    ap.add_argument("--datetime", required=True, help="北京时间，格式 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--nums", help="报数起卦：逗号分隔 1~3 数（如 8,15 或 3,7,5）")
    ap.add_argument("--text", help="字数起卦文本")
    ap.add_argument("--variant", default="standard", choices=("standard", "add_hour", "more_up"))
    ap.add_argument("--category", default="通用", choices=CATEGORIES)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    if a.nums:
        r = compute_numbers([int(x) for x in a.nums.split(",")], dt, a.lon, a.variant, a.category)
    elif a.text:
        r = compute_words(a.text, dt, a.lon, a.variant, a.category)
    else:
        r = compute_time(dt, a.lon, a.category)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        t = r["ti_yong"]
        d = r["duan"]["text"]
        print(f"{r['input']['datetime']} {r['method']['label']} → 本卦 {r['ben_gua']['name']}"
              f"（动{r['dong']}爻，{r['ben_gua']['yaoxiang']}）互卦 {r['hu_gua']['name']} → 变卦 {r['bian_gua']['name']}")
        print(f"体={t['ti']['gua']}({t['ti']['wx']}, {t['ti']['wangshuai']}) 用={t['yong']['gua']}({t['yong']['wx']}, {t['yong']['wangshuai']})"
              f" → {t['name']}（{t['verdict']}）季={t['season']}")
        print(f"断[{r['duan']['category']}]: {d}")


if __name__ == "__main__":
    main()
