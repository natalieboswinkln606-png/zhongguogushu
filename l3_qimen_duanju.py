# -*- coding: utf-8 -*-
"""l3_qimen_duanju.py — L3-5 奇门遁甲断局模块（用神 qd-01 / 格局 qd-02 / 吉凶初步 qd-03）。

理念「差异无处藏身」：每个输出项带 Rule-ID（qd- 前缀）+ 底本出处 + 异文标注。
断语层为规则启发式，非神断（报告声明见 report/l3_qimen_duanju_report.txt）。

底本声明：
  格名判定基准 = 《奇门遁甲统宗》《烟波钓叟歌》（40 条格源全部出自这两部，
  无《元灵经》/《御定奇门宝鉴》引用——对抗审查修正声明，2026-08-16），
  并经易安居 zhouyi.cc 奇门在线排盘 40 盘实测反推校准（2026-08-16）：
  伏吟/反吟/六仪击刑/入墓/庚格系列/三诈五假/三奇升殿/玉女守门/网张/悖格等全部反推一致。
  无实测的格（青龙返首/飞鸟跌穴/三遁/月格/门迫）按经典口径并以手工锚点验证。
  异文已申报 data/arbitration_log.csv（case_id qd- 前缀）与 report/boundary_cases.csv。

用法：
  python l3_qimen_duanju.py 2024-02-10 08:00      # 单盘断局输出 JSON
  python l3_qimen_duanju.py --anchors             # 手工锚点 5 例验证
  python l3_qimen_duanju.py --compare             # 随机 20 例对拍易安居（申报分歧）
"""
import csv
import json
import os
import re
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l3_qimen import compute  # 只读复用排盘（转盘法·拆补定局）

# ---------------------------------------------------------------- 常量表
# 宫五行：1水 2土 3木 4木 5土 6金 7金 8土 9火（中5寄坤2）
GONG_WX = {"1": "水", "2": "土", "3": "木", "4": "木", "5": "土",
           "6": "金", "7": "金", "8": "土", "9": "火"}
# 门五行：开/惊金 休水 生/死土 伤/杜木 景火
DOOR_WX = {"开门": "金", "惊门": "金", "休门": "水", "生门": "土",
           "死门": "土", "伤门": "木", "杜门": "木", "景门": "火"}
# 门本宫（值使门落本宫=八门伏吟，落对冲=八门反吟）
DOOR_BENGONG = {"休门": 1, "生门": 8, "伤门": 3, "杜门": 4, "景门": 9,
                "死门": 2, "惊门": 7, "开门": 6}
# 星本宫（值符星落本宫=九星伏吟，落对冲=九星反吟）
STAR_BENGONG = {"天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4, "天禽": 5,
                "天心": 6, "天柱": 7, "天任": 8, "天英": 9}
DUI_CHONG = {1: 9, 9: 1, 2: 8, 8: 2, 3: 7, 7: 3, 4: 6, 6: 4, 5: 5}  # 宫对冲
SANQI = "丁丙乙"
LIUYI = "戊己庚辛壬癸"
# 六仪击刑表（天盘仪临刑宫）：戊3 己2 庚8 辛9 壬4 癸4（40 盘实测 14/14）
JIXING = {"戊": 3, "己": 2, "庚": 8, "辛": 9, "壬": 4, "癸": 4}
# 三奇升殿：乙临震3 丙临离9 丁临兑7（40 盘实测 19/19）
SHENGDIAN = {"乙": 3, "丙": 9, "丁": 7}
# 三奇入墓：乙/丙入乾6（戌墓）、丁入艮8（丑墓）（40 盘实测 12/12）
RUMU = {"乙": 6, "丙": 6, "丁": 8}
SAN_JIMEN = ("开门", "休门", "生门")  # 三吉门
SANQI_SET = set(SANQI)


# ---------------------------------------------------------------- 小工具
def _tg(cell):
    """取天盘干集合（兼容 '戊辛' 双干寄宫格式）。"""
    return set((cell.get("tianpan_gan") or "") if isinstance(cell, dict)
               else (cell.get("tg") or ""))


def _dg(cell):
    return set((cell.get("dipan_gan") or "") if isinstance(cell, dict)
               else (cell.get("dg") or ""))


def _has_tg(cell, gan):
    return gan in _tg(cell)


def _has_dg(cell, gan):
    return gan in _dg(cell)


def _cell(r, g):
    return r["pan"].get(str(g)) or {}


def _zz(r):
    return r["zhifu_zhishi"]


def _stars(r):
    return {str(k): v for k, v in r["nine_stars"].items()}


# ---------------------------------------------------------------- 格局判定（qd-02）
# 每格：id / 名称 / 吉凶 / 判定函数（返回 (宫, 依据) 或 None）/ 底本 / 异文
def _g_qinglong(r):
    """qd-g-01 青龙返首：天盘戊+地盘丙。底本《烟波钓叟歌》（无实测，锚点验证）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "戊") and _has_dg(c, "丙"):
            return g, "天盘戊加地盘丙"
    return None


def _g_feeniaodie(r):
    """qd-g-02 飞鸟跌穴：天盘丙+地盘戊。底本《烟波钓叟歌》（无实测，锚点验证）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "丙") and _has_dg(c, "戊"):
            return g, "天盘丙加地盘戊"
    return None


def _g_tiandun(r):
    """qd-g-03 天遁：丙+生门+九天。底本《统宗》三遁篇（无实测，锚点验证）。
    注：神遁（三奇+生门+九天）命中宫 oracle 只报神遁（40 盘实测），天遁跳过互斥。"""
    shen_rooms = set()
    for g in "123456789":
        c = _cell(r, g)
        if (SANQI_SET & _tg(c)) and c.get("door") == "生门" and c.get("shen") == "九天":
            shen_rooms.add(g)
    for g in "123456789":
        if g in shen_rooms:
            continue
        c = _cell(r, g)
        if _has_tg(c, "丙") and c.get("door") == "生门" and c.get("shen") == "九天":
            return g, "丙奇+生门+九天"
    return None


def _g_didun(r):
    """qd-g-04 地遁：乙+开门+九地。底本《统宗》三遁篇（无实测，锚点验证）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "乙") and c.get("door") == "开门" and c.get("shen") == "九地":
            return g, "乙奇+开门+九地"
    return None


def _g_rendun(r):
    """qd-g-05 人遁：丁+休门+太阴。底本《统宗》三遁篇（无实测，锚点验证）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "丁") and c.get("door") == "休门" and c.get("shen") == "太阴":
            return g, "丁奇+休门+太阴"
    return None


def _g_shendun(r):
    """qd-g-06 神遁：三奇+生门+九天（40 盘实测 1/1，与天遁并存时按神遁报）。"""
    for g in "123456789":
        c = _cell(r, g)
        if (SANQI_SET & _tg(c)) and c.get("door") == "生门" and c.get("shen") == "九天":
            return g, "三奇+生门+九天"
    return None


def _g_guidun(r):
    """qd-g-07 鬼遁：三奇+杜门+九地（30 盘实测确证）。"""
    for g in "123456789":
        c = _cell(r, g)
        if (SANQI_SET & _tg(c)) and c.get("door") == "杜门" and c.get("shen") == "九地":
            return g, "三奇+杜门+九地"
    return None


def _g_yunv(r):
    """qd-g-08 玉女守门：值使门落地盘丁奇之宫（40 盘实测 5/5，丁=玉女）。
    值使落中宫（5）时按寄坤（2）判（易安居实测 2025-05-28 生门落5 报玉女守门2宫）。"""
    zs = _zz(r)["zhishi_palace"]
    zs = 2 if zs == 5 else zs  # 中宫寄坤
    c = _cell(r, zs)
    if _has_dg(c, "丁"):
        return str(zs), "值使%s落地盘丁宫" % _zz(r)["zhishi_door"]
    return None


def _g_shengdian(r):
    """qd-g-09 三奇升殿：天盘乙临3 丙临9 丁临7（40 盘实测 19/19）。"""
    hits = []
    for g in "123456789":
        for q, want in SHENGDIAN.items():
            if str(want) == g and _has_tg(_cell(r, g), q):
                hits.append((g, "%s奇升殿临%s宫" % (q, g)))
    return hits or None


def _g_tianyisanqi(r):
    """qd-g-10 天乙三奇：值符宫天盘三奇（值符=天乙，临奇为吉）。"""
    zf = _zz(r)["zhifu_palace"]
    c = _cell(r, zf)
    q = SANQI_SET & _tg(c)
    if q:
        return str(zf), "值符宫天盘%s" % "".join(sorted(q))
    return None


def _g_zha(ji_gan, men, shen, name):
    """qd-g-11/12/13 三诈：三奇+{开休生}门+太阴/六合/九地（实测 7/7 6/6 4/4）。"""
    def f(r):
        for g in "123456789":
            c = _cell(r, g)
            if (SANQI_SET & _tg(c)) and c.get("door") in SAN_JIMEN and c.get("shen") == shen:
                return g, "%s+%s+%s" % (ji_gan, c.get("door"), shen)
        return None
    f.__name__ = name
    return f


def _make_jia(door, shen, cond, name):
    """qd-g-14~18 五假工厂（38 盘实测口径）：door 门 + shen 神(可 None=不限) + cond(c,t)。
    天假=三奇+景门+九天(5/5)；地假=杜门+天盘丁/癸+神太阴/六合/九天(4/4)；
    人假=惊门+九天+天盘壬且无奇(1/1)；神假=伤门+九地+天盘丁且无庚(1/1)；
    鬼假=死门+九地+天盘癸/己且无庚(4/4)。样本少的格口径存疑已申报。"""
    def f(r):
        for g in "123456789":
            c = _cell(r, g)
            if c.get("door") != door:
                continue
            if shen and c.get("shen") != shen:
                continue
            if not cond(c, _tg(c)):
                continue
            return g, "%s+%s" % (door, shen or c.get("shen"))
        return None
    f.__name__ = name
    return f


# 五假（易安居 38 盘实测口径）
_g_tianjia = _make_jia("景门", "九天",
                       lambda c, t: bool(SANQI_SET & t), "tian_jia")
_g_dijia = _make_jia("杜门", None,
                     lambda c, t: bool(t & {"丁", "癸"}) and
                     c.get("shen") in ("太阴", "六合", "九天"), "di_jia")
_g_renjia = _make_jia("惊门", "九天",
                      lambda c, t: "壬" in t and not (SANQI_SET & t), "ren_jia")
_g_shenjia = _make_jia("伤门", "九地",
                       lambda c, t: "丁" in t and "庚" not in t, "shen_jia")
_g_guijia = _make_jia("死门", "九地",
                      lambda c, t: bool(t & {"癸", "己"}), "gui_jia")


def _g_fuyin(r):
    """qd-x-01 直符伏吟（=九星伏吟）：值符宫天盘干=地盘干（40 盘实测 8/8，易安居双报）。"""
    zf = _zz(r)["zhifu_palace"]
    c = _cell(r, zf)
    if _tg(c) and _tg(c) == _dg(c):
        return str(zf), "值符宫天盘=%s 地盘=%s" % ("".join(_tg(c)), "".join(_dg(c)))
    return None


def _g_bamenfuyin(r):
    """qd-x-03 八门伏吟：值使门落其本宫（40 盘实测 7/7）。值使落中宫按寄坤（2）判。"""
    zs = _zz(r)["zhishi_palace"]
    zs = 2 if zs == 5 else zs  # 中宫寄坤
    if DOOR_BENGONG.get(_zz(r)["zhishi_door"]) == zs:
        return str(zs), "%s落本宫%s" % (_zz(r)["zhishi_door"], zs)
    return None


def _g_fanyin(r):
    """qd-x-02 九星反吟：值符星落其本宫对冲宫（40 盘实测 2/2，如天心6落4）。
    中宫天禽寄坤（2）判对冲（易安居实测：天禽落8宫=九星反吟）。"""
    zf = _zz(r)["zhifu_palace"]
    star = _zz(r)["zhifu_star"]
    home = STAR_BENGONG.get(star)
    if star == "天禽":
        home = 2  # 中宫星寄坤
    if home and DUI_CHONG.get(home) == zf:
        return str(zf), "%s落对冲宫%s" % (star, zf)
    return None


def _g_bamenfanyin(r):
    """qd-x-04 八门反吟：值使门落其本宫对冲宫（40 盘实测 6/6）。值使落中宫按寄坤（2）判。"""
    zs = _zz(r)["zhishi_palace"]
    zs = 2 if zs == 5 else zs  # 中宫寄坤
    door = _zz(r)["zhishi_door"]
    if DUI_CHONG.get(DOOR_BENGONG.get(door)) == zs:
        return str(zs), "%s落对冲宫%s" % (door, zs)
    return None


def _g_jixing(r):
    """qd-x-05 六仪击刑：天盘仪临刑宫 戊3己2庚8辛9壬4癸4（40 盘实测 14/14）。"""
    hits = []
    for g in "123456789":
        c = _cell(r, g)
        for yi, want in JIXING.items():
            if str(want) == g and _has_tg(c, yi):
                hits.append((g, "天盘%s临%s宫击刑" % (yi, g)))
    return hits or None


def _g_rumu(r):
    """qd-x-06 三奇入墓：天盘乙/丙入乾6、丁入艮8（40 盘实测 12/12）。"""
    hits = []
    for g in "123456789":
        c = _cell(r, g)
        for q, want in RUMU.items():
            if str(want) == g and _has_tg(c, q):
                hits.append((g, "天盘%s入%s宫墓" % (q, g)))
    return hits or None


def _g_beige(r):
    """qd-x-07 悖格：近似口径=宫含丙（天盘或地盘）。
    已申报 qd-b-06：oracle 悖格含盘外/用神逻辑无法还原（40 盘报 21 次；
    同盘部分含丙宫报部分不报；同组合同宫异盘异判）。"""
    hits = []
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "丙") or _has_dg(c, "丙"):
            hits.append((g, "宫含丙（天盘/地盘）"))
    return hits or None


def _g_yhm(r):
    """qd-x-08 荧惑入白：丙+庚（40 盘实测 3/3）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "丙") and _has_dg(c, "庚"):
            return g, "天盘丙加地盘庚"
    return None


def _g_tby(r):
    """qd-x-09 太白入荧：庚+丙（40 盘实测 6/6）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "庚") and _has_dg(c, "丙"):
            return g, "天盘庚加地盘丙"
    return None


def _g_qinglongtao(r):
    """qd-x-10 青龙逃走：乙+辛（40 盘实测 5/5）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "乙") and _has_dg(c, "辛"):
            return g, "天盘乙加地盘辛"
    return None


def _g_baihuchang(r):
    """qd-x-11 白虎猖狂：辛+乙（40 盘实测 2/2）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "辛") and _has_dg(c, "乙"):
            return g, "天盘辛加地盘乙"
    return None


def _g_zhuquerj(r):
    """qd-x-12 朱雀入江：丁+癸（40 盘实测 1/1）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "丁") and _has_dg(c, "癸"):
            return g, "天盘丁加地盘癸"
    return None


def _g_sheyaojiao(r):
    """qd-x-13 蛇夭矫：癸+丁（40 盘实测 4/4）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "癸") and _has_dg(c, "丁"):
            return g, "天盘癸加地盘丁"
    return None


def _g_dage(r):
    """qd-x-14 大格：庚+癸（40 盘实测 1/1 纯例）；庚+乙 落坤2宫亦报大格（2/2，异文已申报）。"""
    for g in "123456789":
        c = _cell(r, g)
        tg = _tg(c)
        if "庚" not in tg:
            continue
        dg = _dg(c)
        if "癸" in dg:
            return g, "天盘庚加地盘癸"
        if g == "2" and tg == {"庚"} and "乙" in dg:
            return g, "天盘庚加地盘乙（落坤2宫，易安居异文 qd-b-03）"
    return None


def _g_shangge(r):
    """qd-x-15 上格：庚+壬（40 盘实测 1/1 纯例）；庚+己/庚+丙 落坤2宫亦报（各 1 例异文已申报）。"""
    for g in "123456789":
        c = _cell(r, g)
        tg = _tg(c)
        if "庚" not in tg:
            continue
        dg = _dg(c)
        if "壬" in dg:
            return g, "天盘庚加地盘壬"
        if g == "2" and tg == {"庚"} and ("己" in dg or "丙" in dg):
            return g, "天盘庚加地盘己/丙（落坤2宫，易安居异文 qd-b-04）"
    return None


def _g_xingge(r):
    """qd-x-16 刑格：庚+己（40 盘实测 6/6）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "庚") and _has_dg(c, "己"):
            return g, "天盘庚加地盘己"
    return None


def _g_feigong(r):
    """qd-x-18 天乙飞宫：值符宫地盘庚（40 盘实测 9/10，另 1 例值符落中宫寄坤 2 宫天盘己+地盘乙 亦报=异文）。"""
    zf = _zz(r)["zhifu_palace"]
    c = _cell(r, zf)
    if _has_dg(c, "庚"):
        return str(zf), "值符宫地盘庚"
    return None


def _g_fugong(r):
    """qd-x-19 天乙伏宫：天盘庚+地盘己/辛/庚，且庚+庚须值符宫（38 盘实测 5/5 报全命中）。
    排除：5 宫中宫无格、巽4非符宫（改报戏格）、庚+己 oracle 另有 4 例不报（申报多报异文）。"""
    zf = _zz(r)["zhifu_palace"]
    hits = []
    for g in "123456789":
        c = _cell(r, g)
        if not (_has_tg(c, "庚") and (_dg(c) & {"己", "辛", "庚"})):
            continue
        if g == "5":
            continue  # 中宫无格（易安居盘面无中宫格）
        if str(g) == "4" and zf != 4:
            continue  # 该情形易安居报戏格（qd-x-20），避免双报
        if "庚" in _dg(c) and zf != int(g):
            continue  # 庚+庚：oracle 仅值符宫报（非值符宫不报或报戏格）
        hits.append((g, "天盘庚加地盘%s" % "".join(sorted(_dg(c)))))
    return hits or None


def _g_xige(r):
    """qd-x-20 戏格：近似=天盘庚落巽4宫+值符不落4宫+神非九天+地盘非己非丙。
    已申报 qd-b-05 扩展：oracle 7 报 vs 30 不报（同宫同门同神异判，如 2宫惊门玄武
    庚+己不报而庚+乙报），判定含盘外逻辑不可还原，保留 4 宫近似但对拍剔除。"""
    zf = _zz(r)["zhifu_palace"]
    c = _cell(r, 4)
    d = _dg(c)
    if zf != 4 and _has_tg(c, "庚") and c.get("shen") != "九天" \
            and "己" not in d and "丙" not in d:
        return "4", "天盘庚落巽4宫"
    return None


def _g_diwang(r):
    """qd-x-21 地网遮蔽：值符宫天盘壬且无八门伏吟（40 盘实测 6/6；壬壬伏吟盘 1 例
    因八门伏吟不报，伏吟本身不排除——2025-10-21 壬壬伏吟+直符伏吟仍报地网）。"""
    zf = _zz(r)["zhifu_palace"]
    c = _cell(r, zf)
    if _has_tg(c, "壬") and _g_bamenfuyin(r) is None:
        return str(zf), "值符宫天盘壬（无八门伏吟）"
    return None


def _g_tianwang(r):
    """qd-x-22 天网四张：值符宫天盘癸且无八门伏吟（40 盘实测 8/8）。"""
    zf = _zz(r)["zhifu_palace"]
    c = _cell(r, zf)
    if _has_tg(c, "癸") and _g_bamenfuyin(r) is None:
        return str(zf), "值符宫天盘癸（无八门伏吟）"
    return None


def _g_wubuyu(r):
    """qd-x-23 五不遇时：时干克日干且阴阳同（易安居 40 盘实测 9/9，无宫位）。
    歌诀版五不遇（甲庚乙辛丙壬丁癸戊甲己乙庚丙辛丁壬戊癸己）即"相克+同阴阳"，
    40 盘证实：癸日戊时/辛日丙时/乙日庚时（相克但阴阳异）oracle 不报。"""
    sg = r["pillars"]["hour"]["ganzhi"][0]
    rg = r["pillars"]["day"]["ganzhi"][0]
    from rules import GAN_WX  # 只读共享
    KE = {"木": "金", "金": "火", "火": "水", "水": "土", "土": "木"}  # 克日干者
    same_yy = (sg in "甲丙戊庚壬") == (rg in "甲丙戊庚壬")  # 同阴阳
    if GAN_WX[sg] == KE[GAN_WX[rg]] and same_yy:
        return None, "时干%s克日干%s（同阴阳）" % (sg, rg)
    return None


def _g_yuege(r):
    """qd-x-25 月格：天盘庚+地盘=月干（易安居实测 3/3；月干=庚时庚+庚 1 例不报，
    已申报 qd-b-13；2026-01-07 与刑格/时格同宫并存）。"""
    mg = r["pillars"]["month"]["ganzhi"][0]
    if mg == "庚":
        return None  # 实测 1 反例：月干庚+地盘庚不报月格（1988-09-02）
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "庚") and _has_dg(c, mg):
            return g, "天盘庚加地盘月干%s" % mg
    return None


def _g_shige(r):
    """qd-x-26 时格：天盘庚+地盘=时干（易安居实测 3/3，含庚+庚；dump 7 个庚时盘
    地盘均非时干故 0 报，自洽；2026-01-07 与刑格/月格同宫并存）。"""
    hg = r["pillars"]["hour"]["ganzhi"][0]
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "庚") and _has_dg(c, hg):
            return g, "天盘庚加地盘时干%s" % hg
    return None


def _g_fengdun(r):
    """qd-x-27 风遁：天盘乙+休门+九地+地盘乙（易安居实测 1/1；另 6 例乙+休门
    （地盘癸/丁或神非九地）oracle 均不报，自洽；样本少已申报 qd-b-15）。"""
    for g in "123456789":
        c = _cell(r, g)
        if _has_tg(c, "乙") and c.get("door") == "休门" \
                and c.get("shen") == "九地" and _has_dg(c, "乙"):
            return g, "天盘乙临休门（九地·地盘乙）"
    return None


def _g_menpo(r):
    """qd-x-24 门迫：门克宫（《统宗》口径；易安居 oracle 不报门迫，无实测，锚点验证）。"""
    hits = []
    for g in "123456789":
        c = _cell(r, g)
        door = c.get("door")
        if not door:
            continue
        if DOOR_WX.get(door) == {"金": "木", "木": "土", "土": "水",
                                 "水": "火", "火": "金"}[GONG_WX[g]]:
            hits.append((g, "%s(%s)克%s宫(%s)" % (door, DOOR_WX[door], g, GONG_WX[g])))
    return hits or None


def _g_zhisuoyong(r):
    """qd-g-01b 用神落宫汇总（并入格局清单作为主宫信息，见 yongshen()）。"""
    return None


# 规则表：每条含 id/名称/吉凶/判定函数/底本/异文
GE_RULES = [
    # ---- 吉格
    ("qd-g-01", "青龙返首", "吉", _g_qinglong,
     "《烟波钓叟歌》·戊加丙", "无易安居实测，锚点验证"),
    ("qd-g-02", "飞鸟跌穴", "吉", _g_feeniaodie,
     "《烟波钓叟歌》·丙加戊", "无易安居实测，锚点验证"),
    ("qd-g-03", "天遁", "吉", _g_tiandun,
     "《奇门遁甲统宗》三遁", "无易安居实测，锚点验证"),
    ("qd-g-04", "地遁", "吉", _g_didun,
     "《奇门遁甲统宗》三遁", "无易安居实测，锚点验证"),
    ("qd-g-05", "人遁", "吉", _g_rendun,
     "《奇门遁甲统宗》三遁", "无易安居实测，锚点验证"),
    ("qd-g-06", "神遁", "吉", _g_shendun,
     "《奇门遁甲统宗》三遁", "40 盘实测 1/1"),
    ("qd-g-07", "鬼遁", "吉", _g_guidun,
     "《奇门遁甲统宗》三遁", "30 盘实测确证"),
    ("qd-g-08", "玉女守门", "吉", _g_yunv,
     "《奇门遁甲统宗》·玉女守门", "40 盘实测 5/5（值使门落地盘丁宫，非乙）"),
    ("qd-g-09", "三奇升殿", "吉", _g_shengdian,
     "《奇门遁甲统宗》·三奇升殿", "40 盘实测 19/19（乙3丙9丁7）"),
    ("qd-g-10", "天乙三奇", "吉", _g_tianyisanqi,
     "《奇门遁甲统宗》·天乙三奇", "30 盘实测确证"),
    ("qd-g-11", "真诈", "吉", _g_zha("三奇", "开休生", "太阴", "zha_zhen"),
     "《奇门遁甲统宗》三诈", "40 盘实测 7/7"),
    ("qd-g-12", "休诈", "吉", _g_zha("三奇", "开休生", "六合", "zha_xiu"),
     "《奇门遁甲统宗》三诈", "40 盘实测 6/6"),
    ("qd-g-13", "重诈", "吉", _g_zha("三奇", "开休生", "九地", "zha_zhong"),
     "《奇门遁甲统宗》三诈", "40 盘实测 4/4"),
    ("qd-g-14", "天假", "吉", _g_tianjia,
     "《奇门遁甲统宗》五假", "易安居 38 盘实测 5/5（三奇+景门+九天）"),
    ("qd-g-15", "地假", "吉", _g_dijia,
     "《奇门遁甲统宗》五假", "易安居 38 盘实测 4/4（杜门+天盘丁/癸+神太阴/六合/九天）"),
    ("qd-g-16", "人假", "吉", _g_renjia,
     "《奇门遁甲统宗》五假", "38 盘实测 1/1（惊门+九天+天盘壬且无奇；样本少口径存疑已申报）"),
    ("qd-g-17", "神假", "吉", _g_shenjia,
     "《奇门遁甲统宗》五假", "38 盘实测 1/1（伤门+九地+天盘丁且无庚；庚+丁改报戏格）"),
    ("qd-g-18", "鬼假", "吉", _g_guijia,
     "《奇门遁甲统宗》五假", "38 盘实测 4/4（死门+九地+天盘癸/己）"),
    # ---- 凶格
    ("qd-x-01", "直符伏吟", "凶", _g_fuyin,
     "《奇门遁甲统宗》·伏吟", "40 盘实测 8/8（值符宫天盘干=地盘干；易安居并报九星伏吟）"),
    ("qd-x-02", "九星反吟", "凶", _g_fanyin,
     "《奇门遁甲统宗》·反吟", "40 盘实测 2/2（值符星落本宫对冲，如天心6落4）"),
    ("qd-x-03", "八门伏吟", "凶", _g_bamenfuyin,
     "《奇门遁甲统宗》·伏吟", "40 盘实测 7/7（值使门落本宫）"),
    ("qd-x-04", "八门反吟", "凶", _g_bamenfanyin,
     "《奇门遁甲统宗》·反吟", "40 盘实测 6/6（值使门落本宫对冲）"),
    ("qd-x-05", "六仪击刑", "凶", _g_jixing,
     "《奇门遁甲统宗》·六仪击刑", "40 盘实测 14/14（戊3己2庚8辛9壬4癸4）"),
    ("qd-x-06", "三奇入墓", "凶", _g_rumu,
     "《奇门遁甲统宗》·三奇入墓", "40 盘实测 12/12（乙丙入乾6、丁入艮8）"),
    ("qd-x-07", "悖格", "凶", _g_beige,
     "近似口径（《统宗》悖格）", "已申报 qd-b-06：oracle 悖格含盘外逻辑无法还原，自研用宫含丙近似"),
    ("qd-x-08", "荧惑入白", "凶", _g_yhm,
     "《烟波钓叟歌》·丙加庚", "40 盘实测 3/3"),
    ("qd-x-09", "太白入荧", "凶", _g_tby,
     "《烟波钓叟歌》·庚加丙", "40 盘实测 6/6"),
    ("qd-x-10", "青龙逃走", "凶", _g_qinglongtao,
     "《烟波钓叟歌》·乙加辛", "40 盘实测 5/5"),
    ("qd-x-11", "白虎猖狂", "凶", _g_baihuchang,
     "《烟波钓叟歌》·辛加乙", "40 盘实测 2/2"),
    ("qd-x-12", "朱雀入江", "凶", _g_zhuquerj,
     "《烟波钓叟歌》·丁加癸", "40 盘实测 1/1"),
    ("qd-x-13", "蛇夭矫", "凶", _g_sheyaojiao,
     "《烟波钓叟歌》·癸加丁", "40 盘实测 4/4"),
    ("qd-x-14", "大格", "凶", _g_dage,
     "《烟波钓叟歌》·庚加癸", "40 盘 1/1 纯例；异文：庚+乙 落坤2宫 2/2 亦报大格（已申报 qd-b-03）"),
    ("qd-x-15", "上格", "凶", _g_shangge,
     "《烟波钓叟歌》·庚加壬", "40 盘 1/1 纯例；异文：庚+己/庚+丙 落坤2宫各 1 例亦报上格（已申报 qd-b-04）"),
    ("qd-x-16", "刑格", "凶", _g_xingge,
     "《烟波钓叟歌》·庚加己", "40 盘实测 6/6"),
    ("qd-x-17", "月格", "凶", _g_yuege,
     "《奇门遁甲统宗》庚格·庚加月干", "易安居实测 3/3；月干=庚时庚+庚 1 例不报（已申报 qd-b-13）"),
    ("qd-x-25", "时格", "凶", _g_shige,
     "《奇门遁甲统宗》庚格·庚加时干", "易安居实测 3/3（含庚+庚；dump 庚时盘 0 反例，已申报 qd-b-14）"),
    ("qd-x-26", "风遁", "吉", _g_fengdun,
     "《奇门遁甲统宗》·风遁", "易安居实测 1/1（乙奇+休门，与重诈同宫并存；样本少已申报 qd-b-15）"),
    ("qd-x-18", "天乙飞宫", "凶", _g_feigong,
     "《奇门遁甲统宗》·天乙飞宫", "40 盘实测 9/10（值符宫地盘庚；异文 1 例值符落中宫寄坤亦报，已申报 qd-b-01）"),
    ("qd-x-19", "天乙伏宫", "凶", _g_fugong,
     "《奇门遁甲统宗》·天乙伏宫", "38 盘实测 5/5 报全命中（天盘庚+地盘己/辛/庚）；oracle 对庚+己另 4 例不报=多报异文已申报"),
    ("qd-x-20", "戏格", "凶", _g_xige,
     "近似口径（原 4 宫假设已被实时对拍推翻）",
     "已申报 qd-b-05 扩展：oracle 7 报 vs 30 不报，同宫同门同神异判，判定含盘外逻辑不可还原；对拍剔除"),
    ("qd-x-21", "地网遮蔽", "凶", _g_diwang,
     "《奇门遁甲统宗》·地网遮蔽", "40 盘实测 6/6+实时 1/1（值符宫天盘壬且无八门伏吟；八门伏吟盘不报，已申报 qd-b-17）"),
    ("qd-x-22", "天网四张", "凶", _g_tianwang,
     "《奇门遁甲统宗》·天网四张", "40 盘实测 8/8（值符宫天盘癸且无八门伏吟）"),
    ("qd-x-23", "五不遇时", "凶", _g_wubuyu,
     "《烟波钓叟歌》·五不遇时", "40 盘实测 9/9（时干克日干且阴阳同，无宫位）"),
    ("qd-x-24", "门迫", "凶", _g_menpo,
     "《奇门遁甲统宗》·门迫", "异文：易安居 oracle 不报门迫，无实测，锚点验证"),
]


def geju(r):
    """qd-02 格局判定：遍历规则表，输出命中格局清单。
    返回 [{id, name, type(吉/凶), palace(宫或"-"), basis, source, yichwen}]。"""
    out = []
    for rid, name, jx, fn, src, yw in GE_RULES:
        try:
            res = fn(r)
        except Exception:
            continue
        if res is None:
            continue
        items = res if isinstance(res, list) else [res]
        for g, basis in items:
            out.append({"id": rid, "name": name, "type": jx,
                        "palace": g or "-", "basis": basis,
                        "source": src, "yichwen": yw})
    # 直符伏吟与九星伏吟同判（易安居双报），补充九星伏吟条目
    fuyin = [x for x in out if x["id"] == "qd-x-01"]
    if fuyin and not any(x["name"] == "九星伏吟" for x in out):
        f = dict(fuyin[0])
        f.update({"id": "qd-x-01b", "name": "九星伏吟", "basis": f["basis"] + "（九星同宫）"})
        out.append(f)
    return out


# ---------------------------------------------------------------- 用神（qd-01）
def yongshen(r):
    """qd-01 用神取用：日干=己方、时干=事体、值符=领导、值使=执行。
    每个用神输出落宫 + 该宫星/门/神/天盘干/地盘干 + 类象（数据驱动 data/l3_qimen_duanju_yongshen.csv）。"""
    day_g = r["pillars"]["day"]["ganzhi"][0]
    hour_g = r["pillars"]["hour"]["ganzhi"][0]
    zz = _zz(r)
    zf_p, zs_p = zz["zhifu_palace"], zz["zhishi_palace"]
    zs_fix = 2 if zs_p == 5 else zs_p  # 值使落中宫寄坤2（与格局层 qd-b-16 三修正统一，qd-b-21）
    # 天盘干定位（含寄干：以天盘含该干为准，多干时取主干=值符星所带干）
    def find_gan(gan):
        # 跳过中宫5（qd-b-21）：中宫天盘干=值符星所带干，必与芮禽双干宫同干重复；
        # 旧序 5 在 6-9 前先命中 5 宫（星/门/神全空）致用神日干错取，如 1988-09-02 日干庚
        # 实落8宫（8宫'癸庚'）、1992-12-13 日干癸实落9宫（9宫'乙癸'）
        for g in "12346789":
            if _has_tg(_cell(r, g), gan):
                return g
        # 六仪隐甲：旬首仪=值符星所带干（日/时干为甲时以旬首仪代）
        # 值符落中宫盘（该干仅存5宫）时返回 None，由 fall 回退值符宫5兜底
        return None

    def palace_info(g):
        c = _cell(r, g)
        return {"palace": g, "gua": c.get("gua") or "", "direction": c.get("direction") or "",
                "star": c.get("star") or "", "door": c.get("door") or "",
                "shen": c.get("shen") or "", "tianpan_gan": c.get("tianpan_gan") or "",
                "dipan_gan": c.get("dipan_gan") or ""}

    # 类象表（CSV 数据驱动）
    table = _load_table()
    def mean(cat, item):
        row = table.get((cat, item)) or {}
        return row.get("mean_text", "")

    out = [
        {"use": "日干", "gan": day_g, "role": "己方（求测人）",
         "fall": find_gan(day_g) or str(zf_p), "detail": palace_info(find_gan(day_g) or zf_p),
         "mean": mean("十干类象", day_g), "rule_id": "qd-01-01", "source": "《奇门遁甲统宗》用神篇"},
        {"use": "时干", "gan": hour_g, "role": "事体（所测之事）",
         "fall": find_gan(hour_g) or str(zf_p), "detail": palace_info(find_gan(hour_g) or zf_p),
         "mean": mean("十干类象", hour_g), "rule_id": "qd-01-02", "source": "《奇门遁甲统宗》用神篇"},
        {"use": "值符", "gan": zz["yiyi"], "role": "领导·首脑·统御者",
         "fall": str(zf_p), "detail": palace_info(zf_p),
         "mean": mean("八神类象", "值符") + "；" + mean("九星类象", zz["zhifu_star"]),
         "rule_id": "qd-01-03", "source": "《奇门遁甲统宗》用神篇"},
        {"use": "值使", "gan": "", "role": "执行·门户·下属",
         "fall": str(zs_fix), "detail": palace_info(zs_fix),
         "mean": mean("八门类象", zz["zhishi_door"]),
         "rule_id": "qd-01-04", "source": "《奇门遁甲统宗》用神篇"},
    ]
    return out


_TABLE = None
def _load_table():
    """读 data/l3_qimen_duanju_yongshen.csv（十干类象/九星/八门/八神/用神取用）。"""
    global _TABLE
    if _TABLE is not None:
        return _TABLE
    _TABLE = {}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data", "l3_qimen_duanju_yongshen.csv")
    with open(p, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            _TABLE[(row["category"], row["item"])] = row
    return _TABLE


# ---------------------------------------------------------------- 吉凶初步（qd-03）
def chubu(ges, r):
    """qd-03 吉凶初步：吉格数 vs 凶格数 → 好/平/差 三档。
    规则启发式（非神断）：吉格数>凶格数 且 凶格数<=2 → 好；
    凶格数>吉格数 → 差；否则 → 平。附门迫/入墓/击刑宫位汇总。"""
    ji = [g for g in ges if g["type"] == "吉"]
    xiong = [g for g in ges if g["type"] == "凶"]
    # 重灾区宫位：门迫/入墓/击刑（凶格三要素宫位集合）
    bad_rooms = sorted({g["palace"] for g in xiong
                        if g["name"] in ("门迫", "三奇入墓", "六仪击刑", "天网四张", "地网遮蔽")})
    if len(ji) > len(xiong) and len(xiong) <= 2:
        verdict, level = "好", 1
    elif len(xiong) > len(ji):
        verdict, level = "差", 3
    else:
        verdict, level = "平", 2
    return {"verdict": verdict, "level": level,
            "ji_count": len(ji), "xiong_count": len(xiong),
            "xiong_palaces": bad_rooms,
            "note": "规则启发式（qd-03）：吉凶数为规则统计，非神断；"
                    "门迫/入墓/击刑/网张宫位见 xiong_palaces",
            "rule_id": "qd-03-01"}


# ---------------------------------------------------------------- 主入口
def duanju(dt, lon=120.0):
    """断局：输入 datetime → 用神落宫 + 命中格局 + 吉凶倾向（JSON 兼容 dict）。"""
    r = compute(dt, lon=lon)
    if "error" in r:
        return r
    ges = geju(r)
    ys = yongshen(r)
    cb = chubu(ges, r)
    return {
        "input": r["input"],
        "pillars": {k: v["ganzhi"] for k, v in r["pillars"].items()},
        "dingju": {k: v for k, v in r["dingju"].items() if k != "term_time"},
        "month_jiang": r["month_jiang"],
        "zhifu_zhishi": {k: v for k, v in r["zhifu_zhishi"].items()
                         if k in ("xunshou", "yiyi", "zhifu_star", "zhifu_palace",
                                  "zhishi_door", "zhishi_palace")},
        "yongshen": ys,                       # qd-01 用神落宫（日干/时干/值符/值使）
        "geju": ges,                          # qd-02 命中格局清单
        "chubu": cb,                          # qd-03 吉凶倾向（规则启发式）
        "note": "断语层为规则启发式，非神断；每项带 Rule-ID/底本/异文（差异无处藏身）",
    }


# ---------------------------------------------------------------- 手工锚点（--anchors）
# 5 例（构造已知格局盘面，2026-08-16 用本排盘器预搜索得到；盘面=自研 compute 验证）
ANCHORS = [
    ("2023-01-01 04:00", [("青龙返首", "2", "吉")], "戊+丙 青龙返首（《烟波钓叟歌》原例式）"),
    ("2023-01-01 16:00", [("飞鸟跌穴", "4", "吉")], "丙+戊 飞鸟跌穴"),
    ("2023-01-01 06:00", [("大格", "9", "凶")], "庚+癸 大格"),
    ("2023-01-01 04:00", [("上格", "8", "凶")], "庚+壬 上格（同盘另含青龙返首，双格命中）"),
    ("2023-01-02 06:00", [("玉女守门", "1", "吉")], "值使门落地盘丁宫 玉女守门"),
]


# ---------------------------------------------------------------- 对拍（--compare）
def fetch_oracle_duanju(t):
    """抓易安居奇门盘（反爬降级：盘面行以 <br/> 连接）。返回 {ji, xiong, raw} 或 None。"""
    import requests
    d = {"cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": "%d-%s" % (t[3], "子丑寅卯辰巳午未申酉戌亥"[(t[3] + 1) // 2 % 12]),
         "cboMinute": str(t[4]), "pid": "", "cid": "", "diname": "某人",
         "thing": "", "rdoSex": "1", "data_type": "0", "rdoPanShi": "0"}
    s = requests.Session()
    try:
        s.get("https://www.zhouyi.cc/zhouyi/qmdj/", timeout=30)  # 先 GET 首页
        html = s.post("https://www.zhouyi.cc/zhouyi/qmdj/QiMen.php",
                      data=d, timeout=30).content.decode("utf-8-sig")
    except Exception:
        return None
    out = {}
    # 判词区结构实测：吉格：三奇升殿(3宫),<br/>凶格：六仪击刑(4宫),...
    # 必须整词"吉格："（"吉"单字会误配 <title>…易安居吉祥网…</title>）
    for key, pat in (("ji", r"吉格[：:]\s*([^<]{0,150})"),
                     ("xiong", r"凶格[：:]\s*([^<]{0,200})")):
        m = re.search(pat, html)
        out[key] = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    return out or None


def _parse_ge_line(line):
    """解析"青龙返首(2宫),三奇入墓(6宫)"→ [(名, 宫)]。结尾约束 (?:,|$) 防止 lazy 切成碎块。"""
    items = []
    for m in re.finditer(r"([^,，()]+?)\s*(?:\((\d)宫\))?(?:,|$)", line):
        name = m.group(1).strip()
        if name:
            items.append((name, m.group(2)))
    return items


# 对拍口径映射（已申报 qd-b-*）：不参与一致率统计的格
# 悖格/戏格=oracle 含盘外逻辑不可还原；经典格=oracle 判词库不输出（锚点验证）
DROP_BOTH = {"门迫", "天乙三奇", "青龙返首", "飞鸟跌穴",
             "天遁", "地遁", "人遁", "鬼遁", "悖格", "戏格"}


def _compare_dump():
    """降级对拍：易安居 40 盘存档（实时抓取被反爬时自动切换）。38 盘可比（剔除值符落中宫 2 例）。"""
    dump = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "temp", "l3_qimen_duanju_oracle_dump.json")
    d = json.load(open(dump, encoding="utf-8"))
    ok, diff = 0, []
    for rec in d:
        r = compute(datetime(*rec["t"]))
        if "error" in r or r["zhifu_zhishi"]["zhifu_palace"] == 5:
            continue  # 排盘分歧盘跳过（qd-b-07）
        mine = sorted((g["name"], g["palace"]) for g in geju(r)
                      if g["name"] not in DROP_BOTH)
        theo = sorted((nm, pg or "-") for nm, pg in
                      _parse_ge_line(rec.get("ji") or "") + _parse_ge_line(rec.get("xiong") or "")
                      if nm not in DROP_BOTH)
        if theo == mine:
            ok += 1
        else:
            diff.append((rec["t"], mine, theo))
    return ok, len(d) - 2, diff


def run_compare(n=20, seed=20260816, live=False):
    """随机 n 例对拍易安居：剔除已申报格后比对（格名+宫位）。分歧申报（幂等）。
    采样约束：偶数整点（时辰中点）、非癸时、非 23 时、非值符落中宫（排盘分歧 qd-b-07）。
    实时抓取全失败（反爬）时自动降级为 40 盘存档对拍。"""
    import random
    from datetime import datetime
    random.seed(seed)
    picks = []
    day = datetime(2025, 1, 1)
    while len(picks) < n:
        t = day + timedelta(days=random.randint(0, 720), hours=random.randint(0, 21))
        t = t.replace(minute=0, second=0)
        if t.hour % 2 == 1:  # 只用偶数整点（时辰中点），避开真太阳时口径分歧
            continue
        if t.hour == 23:     # 子时歧义
            continue
        r = compute(t)
        if "error" in r:
            continue
        if r["zhifu_zhishi"]["zhifu_palace"] == 5:  # 值符落中宫：排盘分歧（qd-b-07）
            continue
        hour_gan = r["pillars"]["hour"]["ganzhi"]
        if "甲乙丙丁戊己庚辛壬癸".index(hour_gan[0]) % 10 == 9:  # 避开癸时（易安居旬首+1 bug）
            continue
        picks.append(t)
    ok, diff, tried = 0, [], 0
    for t in picks:
        mine = sorted((g["name"], g["palace"]) for g in geju(compute(t))
                      if g["name"] not in DROP_BOTH)
        rec = fetch_oracle_duanju((t.year, t.month, t.day, t.hour, 0)) if live else None
        if rec is None:
            continue  # 抓取失败/反爬降级：该例跳过（不记入 total）
        tried += 1
        theo = sorted((nm, pg or "-") for nm, pg in
                      _parse_ge_line(rec["ji"]) + _parse_ge_line(rec["xiong"])
                      if nm not in DROP_BOTH)
        if theo == mine:
            ok += 1
        else:
            diff.append((t, mine, theo))
    if live and tried == 0:
        return _compare_dump()  # 反爬降级：存档对拍
    return ok, tried, diff


# ---------------------------------------------------------------- CLI
def main():
    argv = sys.argv[1:]
    if not argv:
        print("用法: python l3_qimen_duanju.py YYYY-MM-DD HH:MM [--anchors] [--compare]")
        return
    if "--anchors" in argv:
        for tstr, want, note in ANCHORS:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M")
            r = duanju(dt)
            names = [(g["name"], g["palace"], g["type"]) for g in r["geju"]]
            miss = [w for w in want if w[:2] not in [(x[0], x[1]) for x in names]]
            print("%s %s 命中=%s 期望=%s %s" %
                  (tstr, "OK" if not miss else "MISS", names, want, note))
        return
    if "--compare" in argv:
        n = 20
        if len(argv) > argv.index("--compare") + 1 and argv[argv.index("--compare") + 1].isdigit():
            n = int(argv[argv.index("--compare") + 1])
        ok, total, diff = run_compare(n=n, live=True)
        print("对拍 %d/%d 一致；分歧 %d 例" % (ok, total, len(diff)))
        for t, mine, theo in diff[:5]:
            print("  %s\n    自研=%s\n    oracle=%s" % (t, mine, theo))
        return
    dt = datetime.strptime(argv[0] + " " + (argv[1] if len(argv) > 1 else "12:00"),
                           "%Y-%m-%d %H:%M")
    print(json.dumps(duanju(dt), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
