# -*- coding: utf-8 -*-
"""l3_liuyao.py — L3-2 六爻排盘模块：起卦(ly-01 时间/数字)、纳甲(ly-02 najia.csv)、六亲(ly-03 京房本宫)、
六神(ly-04 日干起)、世应(ly-05 增删卜易世应诀)、旺衰辅助(ly-06 月建日辰生克冲合)。输入=北京时+东经(同 m1)。
I-7 契约：六爻止于排卦——旺衰只列五行生克冲合关系，不作断卦结论；伏神/旬空不在本模块范围。
底本：《梅花易数》时间起卦法、《周易》通行本卦辞、data/najia.csv 纳甲、data/bagong.csv 八宫、
data/shuowang.csv 朔日表(农历月日)、《增删卜易》世应诀、六神歌诀。
时间起卦两式（与元亨利贞六爻排盘对拍确认）：
  农历法：上卦=(年支数+农历月+农历日)÷8 余(0取8)，下卦=再+时辰数÷8 余，动爻=÷6 余(0取6)；分钟不计。
  公历法：上卦=(公历年+月+日)÷8 余，下卦=再+时+分÷8 余，动爻=÷6 余。
数字起卦（梅花报数，动爻加时辰）：双数 上=n1÷8 余、下=n2÷8 余、动=(n1+n2+时辰数)÷6 余；单数 上=n÷8 余、下=(n+时)÷8 余、动=(n+时)÷6 余。"""
import argparse, bisect, csv, json, os, sys
from datetime import datetime
from functools import lru_cache
import m1
from rules import ZHI, rel, wx_of_zhi

BASE = os.path.dirname(os.path.abspath(__file__))

# ---- 先天八卦：卦名→(先天数, 三爻象[自下而上], 八纯五行)；"余 0 取整"见 _num8/_num6 ----
TG = {"乾": (1, "阳阳阳", "金"), "兑": (2, "阳阳阴", "金"), "离": (3, "阳阴阳", "火"),
      "震": (4, "阳阴阴", "木"), "巽": (5, "阴阳阳", "木"), "坎": (6, "阴阳阴", "水"),
      "艮": (7, "阴阴阳", "土"), "坤": (8, "阴阴阴", "土")}
TG_NUM = {k: v[0] for k, v in TG.items()}
TG_NAME = {v[0]: k for k, v in TG.items()}  # 先天数 → 卦名

# ---- 六十四卦：{卦名: (上卦, 下卦)}；与 data/bagong.csv 逐名断言核对（assert_l3_liuyao） ----
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

# ---- 卦辞：《周易》通行本（模块内转录；对拍以元亨利贞网络电子版复核，异文如实申报） ----
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

# ---- 六神：日干起神（歌诀：甲乙起青龙，丙丁起朱雀，戊起勾陈，己起腾蛇，庚辛起白虎，壬癸起玄武）；螣蛇=腾蛇异文 ----
SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
SPIRIT_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}

# ---- 六冲/六合（冲合表；止于关系标注不作断卦） ----
CHONG = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
HE = {frozenset(p) for p in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}

# ---- 六亲：rel(爻五行, 本宫五行) → 六亲（我=本宫；生我者父母、我生者子孙、克我者官鬼、我克者妻财；变卦六亲同按本卦宫） ----
QIN = {"比和": "兄弟", "生": "父母", "泄": "子孙", "克": "官鬼", "耗": "妻财"}

# ---- 世应诀（《增删卜易》）：八宫卦序 1..8 → 世爻位；游魂(7)四爻、归魂(8)三爻；应爻=世隔三位 ----
SHI_POS = {1: 6, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 4, 8: 3}
POS = ["初", "二", "三", "四", "五", "上"]

GUACI_SOURCE = "《周易》通行本卦辞（本模块转录；元亨利贞网络电子版对拍复核，异文如实申报）"


@lru_cache(maxsize=None)
def load_bagong():
    """bagong.csv → {卦名: (宫, 卦序)}；宫五行=八纯卦五行（乾兑金、离火、震巽木、坎水、艮坤土）。"""
    with open(os.path.join(BASE, "data", "bagong.csv"), encoding="utf-8") as f:
        return {r["gua_name"]: (r["palace"], int(r["gua_order"])) for r in csv.DictReader(f)}


@lru_cache(maxsize=None)
def load_najia():
    """najia.csv → {卦名: (内外两干, 六爻纳支[自下而上])}。"""
    with open(os.path.join(BASE, "data", "najia.csv"), encoding="utf-8") as f:
        return {r["gua"]: (r["tiangan_najia"], r["dizhi_najia"]) for r in csv.DictReader(f)}


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
    """农历(年支序, 月, 日, 是否闰月)：最近上一朔时刻 → 朔日表行；闰月沿用原月数（闰月不影响六爻起卦）。
    朔表缺失/为空/越界 → ValueError（不静默回退第三方推算，同 preregister 契约）。"""
    t = dt.replace(second=0, microsecond=0)
    rows = load_shuo()
    if not rows:
        raise ValueError("data/shuowang.csv 缺失或为空：农历月日不可判定（朔日表为 L3 前置录入）")
    d = t.date()
    i = bisect.bisect_right([r[0].date() for r in rows], d) - 1  # 朔日整天=初一（民俗口径，同元亨利贞；朔日时刻前亦归当日朔月）
    if i < 0 or t < rows[0][0] or (t - rows[i][0]).days > 31:
        raise ValueError(f"农历月日不可判定：{dt.strftime('%Y-%m-%d %H:%M')} 在朔日表范围外（表 {rows[0][0]} ~ {rows[-1][0]}）")
    row = rows[i][1]
    return ZHI.index(row["lunar_year"][1]) + 1, int(row["month"]), (d - rows[i][0].date()).days + 1, row["is_ruen"] == "1"


def time_nums(dt, lon, mode="lunar"):
    """ly-01 时间起卦 → (上卦数, 下卦数, 动爻位, 组成数)；m1 错误透传。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    h = ZHI.index(r["pillars"]["hour"]["ganzhi"][1]) + 1  # 时辰数（真太阳时口径，m1 契约）
    if mode == "lunar":  # 梅花农历法：年支数+农历月+农历日（shuowang.csv），+时辰数；分钟不计
        try:
            y, mo, d = lunar_parts(dt)[:3]
        except ValueError as e:
            return {"error": f"错误: {e}"}
        h2, label = h, "时间起卦·农历（梅花）"
    elif mode == "gongli":  # 公历数字法（同元亨利贞「按公历时间起卦」）：上=公历年月日数字+时(小时数)，下=再+分，动=%6
        y, mo, d = dt.year, dt.month, dt.day
        h2, label = dt.hour + dt.minute, "时间起卦·公历"
        return _num8(y + mo + d + dt.hour), _num8(y + mo + d + dt.hour + dt.minute), \
            _num6(y + mo + d + dt.hour + dt.minute), \
            {"year": y, "month": mo, "day": d, "hour": dt.hour, "minute": dt.minute, "label": label}
    else:
        return {"error": f"错误: 起卦模式 {mode} 非法（lunar/gongli）"}
    return _num8(y + mo + d), _num8(y + mo + d + h2), _num6(y + mo + d + h2), \
        {"year": y, "month": mo, "day": d, "hour": dt.hour, "minute": dt.minute, "label": label}


def number_nums(n1, n2, hour_num, single=False):
    """ly-01 数字起卦（梅花报数）：双数 上=n1 下=n2 动=n1+n2+时；单数 上=n 下=n+时 动=n+时（各 ÷8/÷6 余 0 取整）。"""
    if n1 < 1 or (not single and n2 < 1):
        return {"error": f"错误: 起卦数须为正整数，收到 {n1},{n2}"}
    if single:
        return _num8(n1), _num8(n1 + hour_num), _num6(n1 + hour_num), {"n": n1, "hour": hour_num}
    return _num8(n1), _num8(n2), _num6(n1 + n2 + hour_num), {"n1": n1, "n2": n2, "hour": hour_num}


def _gua_info(name, order, up, down, lines):
    """单卦信息：宫/宫五行/卦序/上下卦/爻象/世应位/卦辞。"""
    palace = load_bagong()[name][0]
    return {"name": name, "palace": palace, "palace_wx": TG[palace][2], "gua_order": order,
            "up": up, "down": down, "yaoxiang": lines, "shi_pos": SHI_POS[order],
            "ying_pos": (SHI_POS[order] + 2) % 6 + 1, "guaci": GUACI[name], "guaci_source": GUACI_SOURCE}


def _build(up, down, dong, dt, lon, label, nums):
    """核心装卦：由(上卦数,下卦数,动爻位) → 全排盘 JSON。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    up_t, down_t = TG_NAME[up], TG_NAME[down]
    ben_name = next(n for n, (u, d) in GUA64.items() if u == up_t and d == down_t)
    ben = TG[down_t][1] + TG[up_t][1]  # 六爻自下而上 = 内卦(下)三爻 + 外卦(上)三爻
    flip = {"阳": "阴", "阴": "阳"}
    bian = list(ben)
    bian[dong - 1] = flip[bian[dong - 1]]
    bian = "".join(bian)
    down_b = TG_NAME[[TG[n][0] for n in "乾坤兑离震巽坎艮" if TG[n][1] == bian[:3]][0]]
    up_b = TG_NAME[[TG[n][0] for n in "乾坤兑离震巽坎艮" if TG[n][1] == bian[3:]][0]]
    bian_name = next(n for n, (u, d) in GUA64.items() if u == up_b and d == down_b)

    bag = load_bagong()
    palace_wx = TG[bag[ben_name][0]][2]
    bpalace = bag[bian_name][0]
    ben_gan2, ben_zhi6 = load_najia()[ben_name]
    bian_gan2, bian_zhi6 = load_najia()[bian_name]
    sp0 = SPIRIT_START[r["pillars"]["day"]["ganzhi"][0]]
    yue_zhi = r["pillars"]["month"]["ganzhi"][1]
    day_zhi = r["pillars"]["day"]["ganzhi"][1]

    lines = []
    for i in range(6):
        bz, vz = ben_zhi6[i], bian_zhi6[i]
        lines.append({
            "pos": POS[i], "yao": "九" if ben[i] == "阳" else "六",
            "shen": SPIRITS[(sp0 + i) % 6],
            "qin": QIN[rel(wx_of_zhi(bz), palace_wx)], "gan": ben_gan2[i >= 3], "zhi": bz, "wx": wx_of_zhi(bz),
            "shi_ying": "世" if i + 1 == SHI_POS[bag[ben_name][1]] else ("应" if i + 1 == (SHI_POS[bag[ben_name][1]] + 2) % 6 + 1 else ""),
            "dong": i + 1 == dong,
            "bian_yao": "九" if bian[i] == "阳" else "六",
            "bian_qin": QIN[rel(wx_of_zhi(vz), palace_wx)], "bian_gan": bian_gan2[i >= 3], "bian_zhi": vz,
            "bian_wx": wx_of_zhi(vz),
            "bian_shi_ying": "世" if i + 1 == SHI_POS[bag[bian_name][1]] else ("应" if i + 1 == (SHI_POS[bag[bian_name][1]] + 2) % 6 + 1 else ""),
            "yue": {"rel": rel(wx_of_zhi(yue_zhi), wx_of_zhi(bz)),
                    "chong": frozenset(yue_zhi + bz) in CHONG, "he": frozenset(yue_zhi + bz) in HE},
            "ri": {"rel": rel(wx_of_zhi(day_zhi), wx_of_zhi(bz)),
                   "chong": frozenset(day_zhi + bz) in CHONG, "he": frozenset(day_zhi + bz) in HE},
        })
    return {
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon},
        "method": {"label": label, "rule_id": "ly-01",
                   "source": "《梅花易数》时间起卦/报数起卦（÷8÷6 余 0 取 8/6）；公历法口径同元亨利贞「按公历时间起卦」；"
                             "时辰取真太阳时（m1 契约），oracle 元亨利贞按北京钟表时（I-8 口径分歧已申报 ly-smp04/05/13/15/19-l）",
                   "nums": nums},
        "yue_jian": {"zhi": yue_zhi, "ganzhi": r["pillars"]["month"]["ganzhi"],
                     "rule_id": "r4", "source": "m1 节换月（solar_terms.csv 节气月支）"},
        "ri_chen": {"ganzhi": r["pillars"]["day"]["ganzhi"],
                    "rule_id": "r1", "source": "m1 日柱（ganzhi_days.csv）"},
        "ben_gua": _gua_info(ben_name, bag[ben_name][1], up_t, down_t, ben),
        "bian_gua": _gua_info(bian_name, bag[bian_name][1], up_b, down_b, bian),
        "lines": lines,
        "rules": [
            {"rule_id": "ly-01", "source": "时间/数字起卦（《梅花易数》）"},
            {"rule_id": "ly-02", "source": "纳甲：data/najia.csv（京房纳甲歌推算存表）；变卦纳甲取变卦本表"},
            {"rule_id": "ly-03", "source": "六亲：本宫五行 vs 爻纳支五行（比和兄弟/爻生宫父母/宫生爻子孙/爻克宫官鬼/宫克爻妻财）；变卦六亲同按本卦宫"},
            {"rule_id": "ly-04", "source": "六神：日干起（甲乙青龙/丙丁朱雀/戊勾陈/己螣蛇/庚辛白虎/壬癸玄武），自初爻起六神"},
            {"rule_id": "ly-05", "source": "世应：《增删卜易》世应诀（八卦之首世六当，以下初爻轮上扬，游魂八位四爻立，归魂八卦三爻详）；应爻隔三位"},
            {"rule_id": "ly-06", "source": "旺衰：月建（节气月支）日辰（日干支）对爻支五行生克冲合关系（六冲六合表）；止于排卦不作断卦（I-7）"},
        ],
    }


def compute(dt, lon=120.0, mode="lunar"):
    """时间起卦入口：(北京时, 东经, lunar|gongli) → 排盘 JSON。"""
    t = time_nums(dt, lon, mode)
    if isinstance(t, dict):
        return t
    up, down, dong, nums = t
    return _build(up, down, dong, dt, lon, nums["label"], nums)


def compute_numbers(n1, n2, dt, lon=120.0, single=False):
    """数字起卦入口：(n1[, n2], 北京时, 东经, single) → 排盘 JSON；动爻加时辰（梅花惯例）。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    h = ZHI.index(r["pillars"]["hour"]["ganzhi"][1]) + 1
    t = number_nums(n1, n2, h, single)
    if isinstance(t, dict):
        return t
    up, down, dong, nums = t
    return _build(up, down, dong, dt, lon, "数字起卦·单数" if single else "数字起卦·双数（动爻加时辰）", nums)


def main():
    ap = argparse.ArgumentParser(description="L3-2 六爻排盘（时间起卦/数字起卦）")
    ap.add_argument("--datetime", required=True, help="北京时间，格式 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--mode", default="lunar", choices=("lunar", "gongli"), help="时间起卦口径")
    ap.add_argument("--n1", type=int, help="数字起卦第一数（双数=上卦数/单数=报数）")
    ap.add_argument("--n2", type=int, help="数字起卦第二数（下卦数）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    r = compute_numbers(a.n1, a.n2 or 0, dt, a.lon, single=a.n2 is None) if a.n1 else compute(dt, a.lon, a.mode)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        bg, vg = r["ben_gua"], r["bian_gua"]
        dong = next(l["pos"] for l in r["lines"] if l["dong"])
        print(f"{r['input']['datetime']} {r['method']['label']} → 本卦 {bg['name']}（{bg['palace']}宫，"
              f"世{bg['shi_pos']}应{bg['ying_pos']}）动爻 {dong}爻 → 变卦 {vg['name']}（{vg['palace']}宫）")
        for l in r["lines"]:
            d = "●动" if l["dong"] else "  "
            print(f"{l['pos']}{l['yao']} {l['shen']} {l['qin']}{l['gan']}{l['zhi']}{l['wx']}{l['shi_ying']}{d}"
                  f" 变:{l['bian_qin']}{l['bian_gan']}{l['bian_zhi']}{l['bian_wx']}{l['bian_shi_ying']}"
                  f"  月{l['yue']['rel']}{'冲' if l['yue']['chong'] else ''}{'合' if l['yue']['he'] else ''}"
                  f"  日{l['ri']['rel']}{'冲' if l['ri']['chong'] else ''}{'合' if l['ri']['he'] else ''}")


if __name__ == "__main__":
    main()
