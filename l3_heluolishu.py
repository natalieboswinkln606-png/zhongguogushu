# -*- coding: utf-8 -*-
"""l3_heluolishu.py — L3 河洛理数模块（hlyl-01..hlyl-05）。
底本如实声明（2026-08-16 第三方案对抗审查修订）：本模块实现的是【网传太玄数起卦派】（现代排盘软件通行体系，干支同数取太玄数起卦）；
古籍《河洛理数》原书（陈抟撰、邵雍述、明史应选重订）起卦取数实为纳甲洛书数派——"天干取数定局：戊一乙癸二、庚三辛四同、壬甲从六数、
丁七丙八宫、己九无差别、五数寄于中；地支取数定局：亥子一六、寅卯三八、巳午二七、申酉四九、辰戌丑未五十总生成"，与 oracle 同派；
太玄数在原书仅见于"论五行纳音"条文数，非起卦取数（纪大奎《考订河洛理数便览》《河洛真数》起例、四库提要均洛书数）。
本模块按任务要求实现网传太玄数派，不改所依体系；古籍正法（洛书数派）以 oracle_school 复现供对拍，两派分歧如实申报。
5 手工锚点全链手算（太玄数 甲己子午9乙庚丑未8丙辛寅申7丁壬卯酉6戊癸辰戌5巳亥4；奇数之和=天数、偶数之和=地数；
天数%8=上卦、地数%8=下卦，先天八卦序 乾1兑2离3震4巽5坎6艮7坤8，余 0 取坤）：
  A1 1990-12-19 12:00 男(121.51) 庚午戊子戊午戊午 → 天数51(9+5+9+5+9+5+9) 地数8 → 51%8=3离上、8%8=0坤下 → 火地晋
     元堂=男天数%6=51%6=3 九三；男顺 爻3→4→5→6→1→2，晋爻阴阳 阴阴阴阳阴阳 → 年数 6,9,6,9,6,6=42年
  A2 1988-03-15 09:00 女(121.51) 戊辰乙卯己巳戊辰 → 天数29(5+5+9+5+5) 地数18(8+6+4) → 29%8=5巽上、18%8=2兑下 → 风泽中孚
     元堂=女地数%6=18%6=0→6 上九；女逆 爻6→5→4→3→2→1，中孚爻阴阳 阳阳阴阴阳阳 → 9,9,6,6,9,9=48年
  A3 2000-01-01 08:00 男 己卯丙子戊午丙辰 → 天数51 地数6 → 51%8=3离上、6%8=6坎下 → 火水未济；元堂=51%6=3 九三
  A4 1965-07-20 14:00 女 乙巳癸未乙亥癸未 → 天数10 地数40 → 10%8=2兑上、40%8=0坤下 → 泽地萃；元堂=40%6=4 六四
  A5 2024-06-11 12:00 男 甲辰庚午丙午甲午 → 天数57(9+5+9+7+9+9+9) 地数8 → 57%8=1乾上、8%8=0坤下 → 天地否；元堂=57%6=3 九三
oracle（destiny.to/app/holo 两浏览器样本实测 2026-08-16，算法经 28/12→豫、31/32→泰 两样本复算吻合，见 oracle_school；
其取数/取卦与古籍《河洛理数》原书正法同派，见上底本声明）：
  纳甲洛书干数 甲6乙2丙8丁7戊1己9庚3辛4壬6癸2 + 河图支双数 亥子1/6 寅卯3/8 巳午2/7 申酉4/9 辰戌丑未5/10（古籍原书起卦取数正法）；
  单数和=天数、双数和=地数；天数减25（≥25 时）、地数减30（≥30 时）取个位 → 后天数（坎1坤2震3巽4中5乾6兑7艮8离9，
  古籍正法：余数配洛书后天图、余 5 寄中宫）；
  男命天数作上卦、女命地数作上卦（易位）；元堂=男天数%9、女地数%6；大运从元堂起男顺女逆、阳9阴6；
  后天卦=元堂爻变（女命再取综卦）；后天元堂=先天元堂+3。
两体系在取数/取卦/元堂上为实质分歧（I-8 申报 data/arbitration_log.csv hlyl-a01..a06；方向修正：oracle=古籍正法洛书数派，
模块所依=网传太玄数派，hlyl-a01/a02 已按此修订标注；本模块按任务要求实现网传太玄数派，不改所依体系）。
"""
import csv, json, os, random, sys
from datetime import datetime, timedelta
import m1

BASE = os.path.dirname(os.path.abspath(__file__))
GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
NOTE = "规则启发式，非神断"

# ---- hlyl-01 四柱取数（网传太玄数起卦派：干支同数取太玄数） ----
GAN_SHU = {g: {"甲": 9, "己": 9, "乙": 8, "庚": 8, "丙": 7, "辛": 7,
               "丁": 6, "壬": 6, "戊": 5, "癸": 5}[g] for g in GAN}
ZHI_SHU = {z: {"子": 9, "午": 9, "丑": 8, "未": 8, "寅": 7, "申": 7,
               "卯": 6, "酉": 6, "辰": 5, "戌": 5, "巳": 4, "亥": 4}[z] for z in ZHI}
# 古籍《河洛理数》原书起卦取数正法（与 oracle 同派，本模块未采用）：天干纳甲洛书数 甲6乙2丙8丁7戊1己9庚3辛4壬6癸2（"戊一乙癸二…"口诀）
# 古籍原书地支取数：河图支双数 亥子1/6 寅卯3/8 巳午2/7 申酉4/9 辰戌丑未5/10（奇进天数、偶进地数）
# 异文（本模块未采用）：天干河图生成数 甲3乙8丙7丁2戊5己10庚9辛4壬6癸1；地支序数 子1丑2寅3卯4辰5巳6午7未8申9酉10戌11亥12
ALT_GAN = {"甲": 6, "乙": 2, "丙": 8, "丁": 7, "戊": 1, "己": 9, "庚": 3, "辛": 4, "壬": 6, "癸": 2}   # 古籍正法天干洛书数（oracle 同）
ALT_ZHI_JI = {"子": 1, "亥": 1, "寅": 3, "卯": 3, "巳": 7, "午": 7, "申": 9, "酉": 9, "辰": 5, "戌": 5, "丑": 5, "未": 5}   # 古籍正法地支河图数（奇）
ALT_ZHI_OU = {"子": 6, "亥": 6, "寅": 8, "卯": 8, "巳": 2, "午": 2, "申": 4, "酉": 4, "辰": 10, "戌": 10, "丑": 10, "未": 10}  # 古籍正法地支河图数（偶）

# 先天八卦序（hlyl-02：余 0 取坤）
XIANTIAN = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]  # 序数 1..8
XIANTIAN_SH = {"乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8}
# 后天八卦数（oracle 取卦用）：坎1坤2震3巽4中5乾6兑7艮8离9
HOUTIAN_SH = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "乾": 6, "兑": 7, "艮": 8, "离": 9}
YIN_YANG = {"阴": 0, "阳": 1}

# ---- 64 卦名表：key=(上卦, 下卦)（先天八卦名） ----
GUANAME = {
    ("乾", "乾"): "乾为天", ("乾", "兑"): "天泽履", ("乾", "离"): "天火同人", ("乾", "震"): "天雷无妄",
    ("乾", "巽"): "天风姤", ("乾", "坎"): "天水讼", ("乾", "艮"): "天山遁", ("乾", "坤"): "天地否",
    ("兑", "乾"): "泽天夬", ("兑", "兑"): "兑为泽", ("兑", "离"): "泽火革", ("兑", "震"): "泽雷随",
    ("兑", "巽"): "泽风大过", ("兑", "坎"): "泽水困", ("兑", "艮"): "泽山咸", ("兑", "坤"): "泽地萃",
    ("离", "乾"): "火天大有", ("离", "兑"): "火泽睽", ("离", "离"): "离为火", ("离", "震"): "火雷噬嗑",
    ("离", "巽"): "火风鼎", ("离", "坎"): "火水未济", ("离", "艮"): "火山旅", ("离", "坤"): "火地晋",
    ("震", "乾"): "雷天大壮", ("震", "兑"): "雷泽归妹", ("震", "离"): "雷火丰", ("震", "震"): "震为雷",
    ("震", "巽"): "雷风恒", ("震", "坎"): "雷水解", ("震", "艮"): "雷山小过", ("震", "坤"): "雷地豫",
    ("巽", "乾"): "风天小畜", ("巽", "兑"): "风泽中孚", ("巽", "离"): "风火家人", ("巽", "震"): "风雷益",
    ("巽", "巽"): "巽为风", ("巽", "坎"): "风水涣", ("巽", "艮"): "风山渐", ("巽", "坤"): "风地观",
    ("坎", "乾"): "水天需", ("坎", "兑"): "水泽节", ("坎", "离"): "水火既济", ("坎", "震"): "水雷屯",
    ("坎", "巽"): "水风井", ("坎", "坎"): "坎为水", ("坎", "艮"): "水山蹇", ("坎", "坤"): "水地比",
    ("艮", "乾"): "山天大畜", ("艮", "兑"): "山泽损", ("艮", "离"): "山火贲", ("艮", "震"): "山雷颐",
    ("艮", "巽"): "山风蛊", ("艮", "坎"): "山水蒙", ("艮", "艮"): "艮为山", ("艮", "坤"): "山地剥",
    ("坤", "乾"): "地天泰", ("坤", "兑"): "地泽临", ("坤", "离"): "地火明夷", ("坤", "震"): "地雷复",
    ("坤", "巽"): "地风升", ("坤", "坎"): "地水师", ("坤", "艮"): "地山谦", ("坤", "坤"): "坤为地",
}
# 64 卦辞（《周易》卦辞原文，hlyl-05 断语出处）
GUACI = {
    "乾为天": "元亨利贞", "坤为地": "元亨，利牝马之贞", "水雷屯": "元亨利贞，勿用有攸往，利建侯",
    "山水蒙": "亨，匪我求童蒙，童蒙求我", "水天需": "有孚，光亨，贞吉，利涉大川",
    "天水讼": "有孚窒惕，中吉，终凶，利见大人，不利涉大川", "地水师": "贞，丈人吉，无咎",
    "水地比": "吉，原筮，元永贞，无咎，不宁方来，后夫凶", "风天小畜": "亨，密云不雨，自我西郊",
    "天泽履": "履虎尾，不咥人，亨", "地天泰": "小往大来，吉亨", "天地否": "否之匪人，不利君子贞，大往小来",
    "天火同人": "同人于野，亨，利涉大川，利君子贞", "火天大有": "元亨", "地山谦": "亨，君子有终",
    "雷地豫": "利建侯行师", "泽雷随": "元亨利贞，无咎", "山风蛊": "元亨，利涉大川，先甲三日，后甲三日",
    "地泽临": "元亨利贞，至于八月有凶", "风地观": "盥而不荐，有孚颙若", "火雷噬嗑": "亨，利用狱",
    "山火贲": "亨，小利有攸往", "山地剥": "不利有攸往", "地雷复": "亨，出入无疾，朋来无咎，反复其道，七日来复，利有攸往",
    "天雷无妄": "元亨利贞，其匪正有眚，不利有攸往", "山天大畜": "利贞，不家食吉，利涉大川",
    "山雷颐": "贞吉，观颐，自求口实", "泽风大过": "栋桡，利有攸往，亨", "坎为水": "习坎，有孚，维心亨，行有尚",
    "离为火": "利贞，亨，畜牝牛吉", "泽山咸": "亨，利贞，取女吉", "雷风恒": "亨，无咎，利贞，利有攸往",
    "天山遁": "亨，小利贞", "雷天大壮": "利贞", "火地晋": "康侯用锡马蕃庶，昼日三接",
    "地火明夷": "利艰贞", "风火家人": "利女贞", "火泽睽": "小事吉", "水山蹇": "利西南，不利东北，利见大人，贞吉",
    "雷水解": "利西南，无所往，其来复吉，有攸往，夙吉", "山泽损": "有孚，元吉，无咎，可贞，利有攸往，曷之用？二簋可用享",
    "风雷益": "利有攸往，利涉大川", "泽天夬": "扬于王庭，孚号有厉，告自邑，不利即戎，利有攸往",
    "天风姤": "女壮，勿用取女", "泽地萃": "亨，王假有庙，利见大人，亨，利贞，用大牲吉，利有攸往",
    "地风升": "元亨，用见大人，勿恤，南征吉", "泽水困": "亨，贞，大人吉，无咎，有言不信",
    "水风井": "改邑不改井，无丧无得，往来井井，汔至亦未繘井，羸其瓶，凶",
    "泽火革": "巳日乃孚，元亨利贞，悔亡", "火风鼎": "元吉，亨", "震为雷": "亨，震来虩虩，笑言哑哑，震惊百里，不丧匕鬯",
    "艮为山": "艮其背，不获其身，行其庭，不见其人，无咎", "风山渐": "女归吉，利贞",
    "雷泽归妹": "征凶，无攸利", "雷火丰": "亨，王假之，勿忧，宜日中", "火山旅": "小亨，旅贞吉",
    "巽为风": "小亨，利有攸往，利见大人", "兑为泽": "亨，利贞", "风水涣": "亨，王假有庙，利涉大川，利贞",
    "水泽节": "亨，苦节不可贞", "风泽中孚": "豚鱼吉，利涉大川，利贞", "雷山小过": "亨，利贞，可小事，不可大事，飞鸟遗之音，不宜上，宜下，大吉",
    "水火既济": "亨小，利贞，初吉终乱", "火水未济": "亨，小狐汔济，濡其尾，无攸利",
}
GUA_WX = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
WX_KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}  # 上克下


def gua_yao(shang, xia):
    """六爻卦象：爻1(初)..爻6(上)，0=阴 1=阳；下卦三爻为爻1-3，上卦三爻为爻4-6。"""
    b = {g: i for i, g in enumerate("乾坤震巽坎离艮兑")}
    iy = {"阴": 0, "阳": 1}
    yao_map = {"乾": "阳阳阳", "坤": "阴阴阴", "震": "阳阴阴", "巽": "阴阳阳",
               "坎": "阴阳阴", "离": "阳阴阳", "艮": "阴阴阳", "兑": "阳阳阴"}
    yao = [iy[c] for c in yao_map[xia]] + [iy[c] for c in yao_map[shang]]
    return yao


def yao_label(yao_0, pos):
    """爻题：阳=九、阴=六，初/二/三/四/五/上。pos=1..6（初=1）。"""
    name = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}[pos]
    return ("九" if yao_0 else "六") + name


def bian_gua(yao, pos):
    """变卦：第 pos 爻（1..6）阴阳反转。返回 6 爻数组。"""
    y = yao[:]
    y[pos - 1] = 1 - y[pos - 1]
    return y


def yao_to_guaming(yao):
    """6 爻数组 → 卦名：下卦=爻1-3（自下而上），上卦=爻4-6。"""
    def tri(ys):
        name = {"阳阳阳": "乾", "阴阴阴": "坤", "阳阴阴": "震", "阴阳阳": "巽",
                "阴阳阴": "坎", "阳阴阳": "离", "阴阴阳": "艮", "阳阳阴": "兑"}[ys]
        return name
    xia = tri("".join("阳" if v else "阴" for v in yao[0:3]))
    shang = tri("".join("阳" if v else "阴" for v in yao[3:6]))
    return GUANAME[(shang, xia)]


def zong_gua(yao):
    """综卦（反对）：上下倒置，爻序反转（初↔上）。"""
    return yao[::-1]


# ---- hlyl-01 四柱取数 ----
def tiandi_shu(pillars):
    """太玄数干支同数取数：奇数之和=天数、偶数之和=地数。items 逐柱逐干支列数。"""
    items = []
    tianshu = dishu = 0
    for key in ("year", "month", "day", "hour"):
        gz = pillars[key]["ganzhi"]
        gs, zs = GAN_SHU[gz[0]], ZHI_SHU[gz[1]]
        for name, v in (("天干", gs), ("地支", zs)):
            if v % 2:
                tianshu += v
            else:
                dishu += v
            items.append({"pillar": key, "part": name, "ganzhi": gz, "shu": v,
                          "parity": "奇" if v % 2 else "偶"})
    return {"tianshu": tianshu, "dishu": dishu, "items": items,
            "rule_id": "hlyl-01", "source": "网传太玄数起卦派：太玄数干支同数 甲己子午9 乙庚丑未8 丙辛寅申7 丁壬卯酉6 戊癸辰戌5 巳亥4（古籍原书此数仅用于五行纳音，非起卦取数）",
            "alt": "异文：天干河图生成数（甲3乙8丙7丁2戊5己10庚9辛4壬6癸1）；地支序数（子1..亥12）；古籍《河洛理数》原书起卦取数=纳甲洛书数+河图支双数（与 oracle 同派，本模块未采用，见 oracle_school）"}


# ---- hlyl-02 河洛数起卦 ----
def qu_gua(tianshu, dishu):
    """天数%8=上卦、地数%8=下卦（先天序 乾1..坤8，余 0 取坤）；命卦=上下卦合成。"""
    shang = XIANTIAN[tianshu % 8 - 1] if tianshu % 8 else "坤"
    xia = XIANTIAN[dishu % 8 - 1] if dishu % 8 else "坤"
    return {"shang_gua": shang, "xia_gua": xia,
            "shang_shu": XIANTIAN_SH[shang], "xia_shu": XIANTIAN_SH[xia],
            "ming_gua": GUANAME[(shang, xia)],
            "rule_id": "hlyl-02",
            "source": "天数÷8 余数=上卦、地数÷8 余数=下卦（先天八卦序 乾1兑2离3震4巽5坎6艮7坤8，余 0 取坤）",
            "alt": "古籍正法（oracle 同派）：天数减25/地数减30取个位配后天数（坎1坤2震3巽4中5乾6兑7艮8离9，余数配洛书后天图、余 5 寄中宫），本模块未采用；又有以天数卦为命、地数卦为身不重合之说"}


# ---- hlyl-03 身命卦与元堂 ----
def yuan_yao(tianshu, dishu, gender):
    """元堂（动爻）定位：男取天数%6、女取地数%6，余 0 取 6（6 爻位，自下而上）。"""
    n = tianshu if gender == "男" else dishu
    pos = n % 6 or 6
    return {"pos": pos, "rule_id": "hlyl-03",
            "source": "按数取爻：男以天数、女以地数除 6，余数自初爻上数（余 0 取上爻）",
            "alt": "异文：六爻飞支法（阳时飞阳爻/阴时飞阴爻，纪晓岚例=晋四爻）；世爻即元堂说（河洛理数论坛）；oracle 派男天数%9、女地数%6"}


def shen_gua(ming_yao, pos):
    """身卦（后天卦）：元堂爻动之变卦。"""
    new = bian_gua(ming_yao, pos)
    return {"shen_gua": yao_to_guaming(new), "yao": new, "pos": pos}


# ---- hlyl-04 大运流年卦 ----
def dayun(ming_yao, pos, gender):
    """大运：从元堂爻起、男顺女逆逐爻，每运=该爻动之变卦，阳爻 9 年阴爻 6 年（异文：每运 10 年派）。
    返回 [{"gua", "years", "start", "end", "pos"}]，起运自出生年起。"""
    seq = []
    p = pos
    for _ in range(6):
        seq.append(p)
        p = p + 1 if gender == "男" else p - 1
        if p > 6:
            p = 1
        elif p < 1:
            p = 6
    out, rel = [], 0
    for p in seq:
        years = 9 if ming_yao[p - 1] else 6
        out.append({"pos": p, "yao": yao_label(ming_yao[p - 1], p),
                    "gua": yao_to_guaming(bian_gua(ming_yao, p)), "years": years,
                    "start": rel, "end": rel + years - 1})
        rel += years
    return {"items": out, "rule_id": "hlyl-04",
            "source": "以元堂爻进退取卦：男顺女逆逐爻，每运=该爻动变卦；阳爻 9 年、阴爻 6 年（起运自出生年，简化不分起运岁数）",
            "alt": "异文：每运 10 年派；大运卦以命卦逐爻变之卦系而非独立变卦；起运以出生节令距立春日数/3 起岁"}


def liunian_gua(ganzhi):
    """流年卦（网传太玄数派流年法）：流年干支取太玄数，奇数之和=天数、偶数之和=地数，除 8 起卦（与 hlyl-02 同法）。"""
    gs, zs = GAN_SHU[ganzhi[0]], ZHI_SHU[ganzhi[1]]
    tianshu = (gs if gs % 2 else 0) + (zs if zs % 2 else 0)
    dishu = (gs if not gs % 2 else 0) + (zs if not zs % 2 else 0)
    r = qu_gua(tianshu, dishu)
    r["rule_id"] = "hlyl-04"
    r["source"] = "网传太玄数派流年法：流年干支取太玄数，奇数和为天数、偶数和为地数，除 8 起卦（与 hlyl-02 同法）"
    return r


def liunian_year(dt0, n=10):
    """未来 n 年逐年流年卦。"""
    out = []
    y = dt0.year
    for i in range(n):
        yi = y + i
        gz = GAN[(yi - 4) % 10] + ZHI[(yi - 4) % 12]
        r = liunian_gua(gz)
        out.append({"year": yi, "ganzhi": gz, "gua": r["ming_gua"],
                    "shang": r["shang_gua"], "xia": r["xia_gua"]})
    return out


# ---- hlyl-05 断语 ----
def duan_ci(ming_gua, shang, xia, yuan_yao_pos, gua_yaos):
    """断语：卦辞原文（《周易》出处）+ 河洛派简断（上下卦五行生克启发式）。"""
    ci = GUACI.get(ming_gua, "")
    ke = WX_KE.get(GUA_WX[shang]) == GUA_WX[xia]
    if ke:
        ji = "上卦克下卦，主先难后得、以力制内，宜守不宜攻"
    elif WX_KE.get(GUA_WX[xia]) == GUA_WX[shang]:
        ji = "下卦克上卦，主内强外弱、下犯上之象，慎行"
    elif GUA_WX[shang] == GUA_WX[xia]:
        ji = "上下卦比和，五行同气，主顺遂"
    else:
        ji = "上下卦相生有情，主和气生财"
    return {"gua": ming_gua, "guaci": ci, "brief": ji,
            "yao": yao_label(gua_yaos[yuan_yao_pos - 1], yuan_yao_pos),
            "rule_id": "hlyl-05",
            "source": "《周易》卦辞（通行本）+ 河洛派上下卦五行生克简断；" + NOTE,
            "alt": "异文：各派另有爻辞断、河洛数断（化工/反化工）等层级，本模块仅取卦辞层"}


# ---- compute 主入口 ----
def compute(dt, gender, lon=120.0):
    """(北京时 datetime, 性别 男/女, 东经) → 河洛理数全 JSON。"""
    m = m1.compute(dt, lon)
    if "error" in m:
        return m
    t = tiandi_shu(m["pillars"])
    g = qu_gua(t["tianshu"], t["dishu"])
    y = yuan_yao(t["tianshu"], t["dishu"], gender)
    yao = gua_yao(g["shang_gua"], g["xia_gua"])
    sg = shen_gua(yao, y["pos"])
    dy = dayun(yao, y["pos"], gender)
    for x in dy["items"]:  # 相对年 → 绝对年（起运自出生年，简化不分起运岁数）
        x["start"], x["end"] = dt.year + x["start"], dt.year + x["end"]
    ln = liunian_year(dt)
    dc = duan_ci(g["ming_gua"], g["shang_gua"], g["xia_gua"], y["pos"], yao)
    dy_cur = next((x for x in dy["items"] if x["start"] <= dt.year <= x["end"]), dy["items"][0])
    return {
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "gender": gender},
        "pillars": m["pillars"],
        "hlyl01": t,
        "hlyl02": g,
        "hlyl03": {"yuan_yao": y, "shen_gua": sg, "ming_gua": g["ming_gua"],
                   "note": "身卦=后天卦（元堂爻动变卦）；命卦=先天卦（天数上地数下）；异文：有以天数卦为命、地数卦为身之说"},
        "hlyl04": {"dayun": dy, "current": dy_cur, "liunian_10y": ln,
                   "note": "大运=元堂爻进退逐爻变卦，阳9阴6；流年=流年干支起卦（未来 10 年逐年）"},
        "hlyl05": dc,
    }


# ---- oracle 复现算法（destiny.to/app/holo 两浏览器样本实测 2026-08-16） ----
def oracle_school(pillars, gender):
    """destiny.to/app/holo 派算法复现（两样本 28/12→雷地豫+初六、31/32→地天泰+九二 完全复算，见 report；
    该派取数/取卦与古籍《河洛理数》原书正法同派，见模块 docstring 底本声明）。
    纳甲洛书干数+河图支双数（古籍原书起卦取数正法）；单=天数双=地数；天数-25/地数-30 个位→后天数（余数配洛书后天图、余 5 寄中宫）；
    男天数上、女地数上（易位）；元堂=男天数%9、女地数%6；后天卦=元堂变（女命再取综）；大运男顺女逆阳9阴6，后天元堂=先天元堂+3。"""
    tianshu = dishu = 0
    for key in ("year", "month", "day", "hour"):
        gz = pillars[key]["ganzhi"]
        for v in (ALT_GAN[gz[0]], ALT_ZHI_JI[gz[1]], ALT_ZHI_OU[gz[1]]):  # 干洛书数+支河图双数
            if v % 2:
                tianshu += v
            else:
                dishu += v
    def houtian(n, base):
        n -= base * (n // base)  # 减 base 整数倍（地数 12<30 不减），再取个位
        while n > 9:
            n -= 10
        return n
    ts, ds = houtian(tianshu, 25), houtian(dishu, 30)
    def name_of(ht):
        return {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兑", 8: "艮", 9: "离"}[ht]
    if ts not in {1, 2, 3, 4, 6, 7, 8, 9} or ds not in {1, 2, 3, 4, 6, 7, 8, 9}:
        return None  # 天数/地数减 25/30 后余 0 或 5（中宫无后天卦）：oracle 未观测口径，跳过并记边界
    if gender == "男":
        shang, xia = name_of(ts), name_of(ds)
    else:
        shang, xia = name_of(ds), name_of(ts)  # 女命易位：地数上、天数下
    gua = GUANAME[(shang, xia)]
    pos = (tianshu % 9 or 9) if gender == "男" else (dishu % 6 or 6)
    if pos > 6:
        pos = (pos - 1) % 6 + 1  # 男命 %9 得 7/8/9 时折回 1..6（样本1=1 已验证，折回为推断待更多样本）
    yao = gua_yao(shang, xia)
    ht_gua = yao_to_guaming(bian_gua(yao, pos))
    if gender == "女":
        ht_gua = yao_to_guaming(zong_gua(bian_gua(yao, pos)))  # 女命后天卦取变卦之综
    ht_pos = (pos + 3 - 1) % 6 + 1  # 后天元堂=先天元堂+3
    return {"tianshu": tianshu, "dishu": dishu, "shang": shang, "xia": xia, "gua": gua,
            "yuan_pos": pos, "ht_gua": ht_gua, "ht_pos": ht_pos,
            "source": "destiny.to/app/holo 实测（两样本复算吻合）；女命易位/女命变卦取综/元堂男%9女%6 为两样本归纳，待更多样本"}


# ---- 对拍 ----
ANCHORS = [
    ((1990, 12, 19, 12, 0), "男", 121.51, "庚午戊子戊午戊午", 51, 8, "火地晋", 3),
    ((1988, 3, 15, 9, 0), "女", 121.51, "戊辰乙卯己巳戊辰", 29, 18, "风泽中孚", 6),
    ((2000, 1, 1, 8, 0), "男", 120.0, "己卯丙子戊午丙辰", 51, 6, "火水未济", 3),
    ((1965, 7, 20, 14, 0), "女", 120.0, "乙巳癸未乙亥癸未", 10, 40, "泽地萃", 4),
    ((2024, 6, 11, 12, 0), "男", 120.0, "甲辰庚午丙午甲午", 57, 8, "天地否", 3),
]

def _rand_dt(rng):
    """随机样本：1949-2100 均匀，避 23-02 时（换日界）、避 12 节±30 分（换月界）、避立春日。"""
    terms = m1.load_terms()
    while True:
        dt = datetime(1949, 1, 1) + timedelta(days=rng.randint(0, 55500))  # 1949-01-01~2100-12-31 全历日
        dt = dt.replace(hour=rng.randint(3, 22), minute=rng.choice([0, 30]), second=0)
        s = dt.strftime("%Y-%m-%d %H:%M")
        if not m1.RANGE_LO <= s <= m1.RANGE_HI:
            continue
        bad = False
        for r in terms:
            t = r["datetime"]
            if t <= s <= (datetime.strptime(t, "%Y-%m-%d %H:%M") + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"):
                bad = True
                break
        if not bad:
            return dt

def compare(seed=20260816, n=15):
    """对拍：5 手工锚点（全链手算）+ n 随机样本（1949-2100）。oracle 侧 = oracle_school（destiny.to 两浏览器样本实测提炼），
    另附 2 真实浏览器样本逐字段表（写入 boundary_cases.csv hlyl-b01/b02）。分歧 I-8 申报（幂等：hlyl- 行 case_id 唯一，重跑不重复）。"""
    rows = []
    print("== l3_heluolishu 对拍（网传太玄数派 vs oracle 纳甲洛书派[古籍原书正法同派]）==")
    print("一、真实浏览器样本 2 例（destiny.to/app/holo，2026-08-16 抓取）")
    real = [((1990, 12, 19, 12, 0), "男", "庚午戊子戊午戊午", "雷地豫", 28, 12, 1, "震为雷"),
            ((1988, 3, 15, 9, 0), "女", "戊辰乙卯己巳戊辰", "地天泰", 31, 32, 2, "火地晋")]
    for t, gender, gz, ogua, ot, od, opos, oht in real:
        r = compute(datetime(*t), gender, 121.51)
        ok = 1 if r["hlyl02"]["ming_gua"] == ogua else 0
        print(f"  {t} {gender} {gz}：oracle 卦={ogua}(天{ot}地{od} 元堂爻{opos} 后卦{oht}) "
              f"vs 网传太玄数卦={r['hlyl02']['ming_gua']}(天{r['hlyl01']['tianshu']}地{r['hlyl01']['dishu']} 元堂爻{r['hlyl03']['yuan_yao']['pos']}) "
              f"→ 卦层{'一致' if ok else '分歧'}")
        rows.append(("hlyl-b0%d" % (1 + len(rows)), "真实浏览器样本分歧", "%d-%02d-%02d %02d:%02d" % t,
                     r["hlyl02"]["ming_gua"], ogua, "arbitrated",
                     f"destiny.to 实测样本（2026-08-16）：网传太玄数(天{r['hlyl01']['tianshu']}地{r['hlyl01']['dishu']}) "
                     f"vs oracle 纳甲洛书(天{ot}地{od})，同挂 hlyl-a01/a02"))
    print("二、5 手工锚点（全链手算，见模块 docstring）")
    for t, gender, lon, gz, ts, ds, gua, yp in ANCHORS:
        r = compute(datetime(*t), gender, lon)
        assert r["hlyl01"]["tianshu"] == ts and r["hlyl01"]["dishu"] == ds
        assert r["hlyl02"]["ming_gua"] == gua and r["hlyl03"]["yuan_yao"]["pos"] == yp
        o = oracle_school(r["pillars"], gender)
        print(f"  {t} {gender} {gz}：天{ts}地{ds} → {gua}（元堂爻{yp}）| oracle 复现：天{o['tianshu']}地{o['dishu']} → {o['gua']}（元堂爻{o['yuan_pos']}）")
    print(f"三、随机 {n} 例（1949-2100，seed={seed}，避 23-02 时/12 节±30 分）——体系一致性统计")
    rng = random.Random(seed)
    same = {"tianshu": 0, "dishu": 0, "gua": 0, "yuan": 0}
    skips = 0
    for i in range(n):
        dt = _rand_dt(rng)
        gender = "男" if i % 2 == 0 else "女"
        r = compute(dt, gender, 120.0)
        o = oracle_school(r["pillars"], gender)
        if o is None:
            skips += 1
            rows.append(("hlyl-b%02d" % (3 + i), "oracle 复现未覆盖", dt.strftime("%Y-%m-%d %H:%M"),
                         r["hlyl02"]["ming_gua"], "无法取卦", "fail",
                         f"oracle 派天数/地数减 25/30 后余 0 或 5（中宫无后天卦），网传太玄数法不受影响（天{r['hlyl01']['tianshu']}地{r['hlyl01']['dishu']}）"))
            continue
        same["tianshu"] += r["hlyl01"]["tianshu"] == o["tianshu"]
        same["dishu"] += r["hlyl01"]["dishu"] == o["dishu"]
        same["gua"] += r["hlyl02"]["ming_gua"] == o["gua"]
        same["yuan"] += r["hlyl03"]["yuan_yao"]["pos"] == o["yuan_pos"]
        if r["hlyl02"]["ming_gua"] == o["gua"]:
            rows.append(("hlyl-b%02d" % (3 + i), "体系巧合一致", dt.strftime("%Y-%m-%d %H:%M"),
                         r["hlyl02"]["ming_gua"], o["gua"], "pass",
                         f"两派取数虽异但卦名恰同（天{r['hlyl01']['tianshu']}地{r['hlyl01']['dishu']} vs 天{o['tianshu']}地{o['dishu']}）"))
        else:
            rows.append(("hlyl-b%02d" % (3 + i), "取数体系分歧", dt.strftime("%Y-%m-%d %H:%M"),
                         r["hlyl02"]["ming_gua"], o["gua"], "arbitrated",
                         f"网传太玄数(天{r['hlyl01']['tianshu']}地{r['hlyl01']['dishu']}) vs oracle 纳甲洛书(天{o['tianshu']}地{o['dishu']})，同挂 hlyl-a01/a02"))
    eff = n - skips
    print(f"  随机 {n} 例（oracle 复现未覆盖 {skips} 例，有效 {eff}）：天数 {same['tianshu']}/{eff}、地数 {same['dishu']}/{eff}、"
          f"卦 {same['gua']}/{eff}、元堂爻 {same['yuan']}/{eff}")
    _log(rows)
    return same


def _log(rows):
    """幂等申报：arbitration_log.csv（hlyl-a01..a06）+ boundary_cases.csv（hlyl-b 行）。"""
    arb = os.path.join(BASE, "data", "arbitration_log.csv")
    bcs = os.path.join(BASE, "report", "boundary_cases.csv")
    arbs = [("hlyl-a01", "天数/地数", "网传太玄数起卦派：太玄数干支同数（甲己9乙庚8丙辛7丁壬6戊癸5；子午9丑未8寅申7卯酉6辰戌5巳亥4）",
             "纳甲洛书干数+河图支双数（甲6乙2丙8丁7戊1己9庚3辛4壬6癸2；亥子1/6寅卯3/8巳午2/7申酉4/9辰戌丑未5/10）——古籍《河洛理数》原书起卦取数正法",
             "复核者", "alt", "修订（2026-08-16 三案查证）：取数体系实质分歧——oracle 派（destiny.to）与古籍《河洛理数》原书同派，均纳甲洛书数+河图支双数（戊一乙癸二…口诀），太玄数在原书仅用于五行纳音条文非起卦；本模块所依为网传太玄数起卦派（现代排盘软件通行体系）。原申报误标“通行本=太玄数”方向颠倒，特此修订，两派同源不同流，本模块不改所依体系"),
            ("hlyl-a02", "取卦法", "天数%8=上卦、地数%8=下卦（先天序 乾1..坤8，余0取坤）——网传太玄数派",
             "天数减25/地数减30取个位→后天数（坎1坤2震3巽4中5乾6兑7艮8离9，余5寄中宫）——古籍正法（余数配洛书后天图）",
             "复核者", "alt", "修订（2026-08-16 三案查证）：oracle 派取卦先归后天数序，非除 8；天数减25/地数减30 配后天数实为古籍正法（余数配洛书后天图，余 5 寄中宫），原申报误标为 oracle 派异文，修订归位。卦层面系统性分歧（样本1 模块=火地晋 vs oracle=雷地豫）"),
            ("hlyl-a03", "元堂爻", "男取天数%6、女取地数%6（余0取6）",
             "男取天数%9、女取地数%6（两样本归纳，待更多样本）",
             "复核者", "alt", "男命口径分歧（样本1：51%6=3 vs oracle 28%9=1）；女命两派同以地数取爻（样本2 均=爻2，恰吻合）"),
            ("hlyl-a04", "上下卦定位", "男命天数上/地数下，女命同",
             "女命易位：地数上/天数下（样本2：32→坤上、31→乾下=地天泰）",
             "复核者", "alt", "oracle 派女命先天卦上下易位，网传太玄数派不分男女；两派体系不同，均保留并申报"),
            ("hlyl-a05", "大运年限", "阳爻 9 年、阴爻 6 年，男顺女逆从元堂起",
             "阳爻 9 年、阴爻 6 年，男顺女逆从元堂起（与网传派一致）；异文有每运 10 年派",
             "复核者", "alt", "大运年限两样本（男豫/女泰）均验证阳9阴6；与网传太玄数派一致，仅 10 年派为异文"),
            ("hlyl-a06", "后天卦", "元堂爻动之变卦",
             "元堂爻动之变卦；女命再取综卦（样本2：九二变明夷→综=晋）",
             "复核者", "alt", "oracle 派女命后天卦取变卦之综，网传太玄数派不分男女；男命两派一致（样本1 初六变=震为雷）")]
    with open(arb, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for cid, field, va, vb, arbiter, dec, reason in arbs:
            if cid not in open(arb, encoding="utf-8").read():
                w.writerow([cid, field, va, vb, arbiter, dec, reason, "oracle 对拍",
                            "自研（网传太玄数派）", "destiny.to/app/holo（oracle，古籍正法同派）"])
    with open(bcs, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for row in rows:
            if row[0] not in open(bcs, encoding="utf-8").read():
                w.writerow(row)


if __name__ == "__main__":
    compare()
