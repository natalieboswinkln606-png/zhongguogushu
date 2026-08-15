# -*- coding: utf-8 -*-
"""l3_ziwei.py — L3-1 紫微斗数排盘模块（zw-01..zw-07）。
输入=北京时间(UTC+8)+东经经度（同 m1 口径）；农历盘=shuowang.csv 朔日表（zw-01）；真太阳时=子正换日；
命宫身宫=寅起正月顺/逆数生时（zw-02，闰月按次月顺延起宫，oracle 实测）；五行局=命宫干支纳音（zw-03）；安紫微=局数日进一宫（zw-04，易安居口径）；
十四主星=紫微/天府两系（zw-05）；辅星=左辅右弼/文昌文曲/天魁天钺/禄存/擎羊陀罗/火铃/天马（zw-06）；四化=生年干表（zw-07）。
差异无处藏身：每输出项带 rule_id（zw-xx）+ source（底本出处）+ alt（异文标注，如有）。
底本声明：主对拍 oracle=易安居紫微斗数（zhouyi.cc，2026-08-16 全字段对拍一致）；
安紫微口径=中州派「局数日进一宫」（陆斌兆《紫微斗数讲义》系统，与易安居一致），
异文=通行「一日一宫」派（《紫微斗数全书》系统，初一宫同为 丑辰亥午酉，仅步长不同），差异以 alt 异文标注说明，不另出副值。
"""
import argparse, csv, json, os, sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import m1  # 真太阳时/时辰/年柱（共享文件，只读）

GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
MONTH_CN = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]
PALACES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]

# --- zw-04 安紫微诀（易安居 oracle 对拍定稿，62 点全验证；2026-08-16） ---
# 初一宫=水二丑/木三辰/金四亥/土五午/火六酉；步长表=火六表 [酉午亥辰丑寅] 的后 K 项（K=局数），
# 每 K 日进一宫：紫微=(初一宫 + 表[(日-1)%K] + (日-1)//K) mod 12
ZIMI_BASE = {"水二": 1, "木三": 4, "金四": 11, "土五": 6, "火六": 9}  # 初一宫（子=0）
ZIMI_TAB = {"水二": (1, 2), "木三": (4, 1, 2), "金四": (11, 4, 1, 2),
            "土五": (6, 11, 4, 1, 2), "火六": (9, 6, 11, 4, 1, 2)}  # 步长表（绝对宫位，后 K 项嵌套）
MAIN14 = ("紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军")

# --- zw-05 星系偏移（绝对宫位偏移；紫微=0 参照，mod 12） ---
ZI = {"天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8}  # 紫微星系（逆去天机、隔一阳武、天同隔二廉贞）
FENG = {"天府": 0, "太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4, "天梁": 5, "七杀": 6, "破军": 10}  # 天府系顺推

# --- zw-06 辅星表（oracle 全字段对拍一致） ---
TIANKUI = {"甲": 1, "乙": 0, "丙": 11, "丁": 11, "戊": 1, "己": 0, "庚": 1, "辛": 6, "壬": 3, "癸": 3}
TIANYUE = {"甲": 7, "乙": 8, "丙": 9, "丁": 9, "戊": 7, "己": 8, "庚": 7, "辛": 2, "壬": 5, "癸": 5}
LUCUN = {"甲": 2, "乙": 3, "丙": 5, "丁": 6, "戊": 5, "己": 6, "庚": 8, "辛": 9, "壬": 11, "癸": 0}
HUOXING = {"申子辰": (2, 10), "寅午戌": (1, 3), "巳酉丑": (3, 10), "亥卯未": (9, 10)}  # (火起宫, 铃起宫)，子时起顺数至生时；口诀「申子辰人寅戌扬…」=火寅起/铃戌起
TIANMA = {"申子辰": 2, "寅午戌": 8, "巳酉丑": 11, "亥卯未": 5}
SANYANG_GAN = {g: i for i, g in enumerate(GAN[:3])}  # 未用，仅备忘
SIHUA = {  # zw-07 生年四化（禄权科忌），易安居图例对拍一致
    "甲": (("廉贞", "禄"), ("破军", "权"), ("武曲", "科"), ("太阳", "忌")),
    "乙": (("天机", "禄"), ("天梁", "权"), ("紫微", "科"), ("太阴", "忌")),
    "丙": (("天同", "禄"), ("天机", "权"), ("文昌", "科"), ("廉贞", "忌")),
    "丁": (("太阴", "禄"), ("天同", "权"), ("天机", "科"), ("巨门", "忌")),
    "戊": (("贪狼", "禄"), ("太阴", "权"), ("右弼", "科"), ("天机", "忌")),
    "己": (("武曲", "禄"), ("贪狼", "权"), ("天梁", "科"), ("文曲", "忌")),
    "庚": (("太阳", "禄"), ("武曲", "权"), ("天同", "科"), ("太阴", "忌")),  # oracle/中州派：阳武同阴（天同科/太阴忌）；异文=通行《全书》派阳武阴同
    "辛": (("巨门", "禄"), ("太阳", "权"), ("文曲", "科"), ("文昌", "忌")),
    "壬": (("天梁", "禄"), ("紫微", "权"), ("左辅", "科"), ("武曲", "忌")),
    "癸": (("破军", "禄"), ("巨门", "权"), ("太阴", "科"), ("贪狼", "忌")),
}


def load_shuowang():
    """shuowang.csv（只读共享表）→ [(朔日, 月序, 闰, 农历年干支)]，按朔日排序。"""
    with open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8") as f:
        return [(datetime.strptime(r["shuo_time"][:10], "%Y-%m-%d"), int(r["month"]),
                 int(r["is_ruen"]), r["lunar_year"]) for r in csv.DictReader(f)]


def load_nayin():
    """nayin.csv（只读共享表）→ {干支串(60): 纳音五行}。纳音名末字即五行（海中金→金…）。"""
    wx = {}
    with open(os.path.join(BASE, "data", "nayin.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pair = r["ganzhi_pair"]
            five = r["wuxing_name"][-1]
            for i in range(2):
                wx[pair[i * 2:i * 2 + 2]] = five
    return wx


def lunar_day(shuo, d):
    """由朔日表 + 公历日期 → (农历年干支, 月序, 闰标志, 日序 1-30, 月名)。d 取真太阳时日期（子正换日口径）。"""
    for i, (s0, mo, ruen, ly) in enumerate(shuo):
        s1 = shuo[i + 1][0] if i + 1 < len(shuo) else s0 + timedelta(days=60)
        if s0.date() <= d < s1.date():
            return ly, mo, ruen, (d - s0.date()).days + 1, MONTH_CN[mo - 1]
    return None, None, None, None, None


def compute(dt, lon=120.0, shuo=None, nayin=None):
    """(北京时 datetime, 东经) → 紫微全盘 JSON dict（zw-01..zw-07，每项带 rule_id/source/alt）。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    shuo = shuo if shuo is not None else load_shuowang()
    nayin = nayin if nayin is not None else load_nayin()
    ts = datetime.strptime(r["true_solar_time"][:16], "%Y-%m-%dT%H:%M")  # 真太阳时
    shichen = m1.shichen(ts.hour)  # 时辰地支序（子正 0:00 换日，真太阳时同轨）
    ygz = r["pillars"]["year"]["ganzhi"]  # 干支纪年=立春换年（m1 r3，仅显示层参考）
    lyr, lmo, lruen, lday, lmon = lunar_day(shuo, ts.date())
    if lmo is None:
        return {"error": f"错误: 真太阳时 {ts.date()} 落 shuowang 朔日表外（1948-2101）"}
    # 紫微斗数年干 = 民俗农历年（正月初一换年，oracle 实测：2025-01-29 正月初一四化=乙年，立春前但按乙巳排盘）
    yg = GAN.index(lyr[0])

    # zw-02 命宫身宫：命宫=寅(2)起正月顺数生月、逆数生时；身宫=顺数生月、顺数生时
    # 闰月起宫=按次月顺延（oracle 实测：2023-04-04 闰二月十四→命子/身子=三月起宫；
    # 2025-07-25 闰六月初一→命辰/身子=七月起宫）；异文=「闰月按本月起宫」派
    qi_mo = lmo + (1 if lruen else 0)
    ming = (2 + qi_mo - 1 - shichen) % 12
    shen = (2 + qi_mo - 1 + shichen) % 12
    # zw-03 五行局：命宫宫干=五虎遁（寅起丙，同 m1 月柱式；宫干=(2·年干+2+月支序)%10，月支序=(支序-2)%12）→ 纳音 → 五行局
    ming_gan = GAN[(2 * yg + 2 + (ming - 2) % 12) % 10]
    ju = {"金": "金四", "木": "木三", "水": "水二", "火": "火六", "土": "土五"}[nayin[ming_gan + ZHI[ming]]]

    # zw-04/05 安十四主星
    k = {"二": 2, "三": 3, "四": 4, "五": 5, "六": 6}[ju[1]]  # 局数=进一宫所需天数
    tab = ZIMI_TAB[ju]  # 步长表=火六表后 K 项（含初一宫绝对宫位）
    ziwei = (tab[(lday - 1) % k] + (lday - 1) // k) % 12  # 每 K 日进一宫
    tianfu = (4 - ziwei) % 12  # 寅申同宫：天府=(4-紫微)mod 12
    pos = {n: (ziwei + o) % 12 for n, o in ZI.items()}
    pos["紫微"] = ziwei
    for n, o in FENG.items():
        pos[n] = (tianfu + o) % 12

    # zw-06 辅星（左辅右弼=月系星，随闰月顺延同命宫口径：oracle 实测 2023-04-04 闰二月左辅午/右弼申=按三月起算）
    aux = {}
    aux["左辅"] = (4 + qi_mo - 1) % 12  # 辰起正月顺数
    aux["右弼"] = (10 - (qi_mo - 1)) % 12  # 戌起正月逆数
    aux["文昌"] = (10 - shichen) % 12  # 戌起逆数生时
    aux["文曲"] = (4 + shichen) % 12  # 辰起顺数生时
    aux["天魁"], aux["天钺"] = TIANKUI[lyr[0]], TIANYUE[lyr[0]]
    aux["禄存"] = LUCUN[lyr[0]]
    aux["擎羊"] = (aux["禄存"] + 1) % 12
    aux["陀罗"] = (aux["禄存"] - 1) % 12
    year_zhi_group = next(g for g in ("申子辰", "寅午戌", "巳酉丑", "亥卯未") if lyr[1] in g)
    hx0, lx0 = HUOXING[year_zhi_group]
    aux["火星"] = (hx0 + shichen) % 12
    aux["铃星"] = (lx0 + shichen) % 12
    aux["天马"] = TIANMA[year_zhi_group]

    # zw-07 生年四化（按民俗农历年干，oracle 实测：2025-01-29 正月初一四化=乙年）
    sihua = SIHUA[lyr[0]]

    # 十二宫组装（命宫起逆排：命/兄弟/夫妻/子女/财帛/疾厄/迁移/仆役/官禄/田宅/福德/父母）
    out_palaces = []
    for i in range(12):
        zhi = (ming - i) % 12
        gan = GAN[(2 * yg + 2 + (zhi - 2) % 12) % 10]  # 宫干=五虎遁（与命宫宫干同式）
        stars = sorted([n for n, z in pos.items() if z == zhi], key=MAIN14.index)
        auxs = sorted([n for n, z in aux.items() if z == zhi], key=list(aux).index)
        shen_flag = (zhi == shen)
        sih = [s for s in sihua if s[0] in stars]
        out_palaces.append({
            "name": PALACES[i], "zhi": ZHI[zhi], "gan": gan,
            "stars": stars, "aux": auxs, "sihua": [s[1] for s in sih], "shen": shen_flag,
            "rule_id": "zw-05", "source": "紫微星系偏移口诀（紫微逆去天机星…）+天府星系（天府太阴顺贪狼…）+辅星表（zw-06），oracle 对拍一致",
        })

    notes = [
        f"真太阳时 {ts.strftime('%Y-%m-%dT%H:%M:%S')}（EOT {m1.eot_minutes(dt):+.2f} 分）；子正换日，时辰={ZHI[shichen]}时",
        f"年干项（四化/魁钺/禄存等）按民俗农历年 {lyr}（正月初一换年，oracle 实测）；干支纪年 {ygz}（立春换年）仅显示层参考",
        "安紫微=中州派「局数日进一宫」（易安居 oracle 对拍口径）；异文：通行「一日一宫」派（《紫微斗数全书》系统，初一宫同为丑辰亥午酉，仅步长不同）",
    ]

    return {
        "rule": "zw-01", "source": "shuowang.csv 朔日表（L0）+ m1.py 真太阳时（子正换日）",
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "tz": "UTC+8 北京时间"},
        "lunar": {"year": lyr, "month": lmo, "month_name": ("闰" if lruen else "") + lmon, "is_ruen": bool(lruen),
                  "day": lday, "rule_id": "zw-01",
                  "source": "shuowang.csv（朔日定月内日序；闰月 is_ruen；子正换日口径取真太阳时日期）",
                  "alt": f"显示层纪年={ygz}（立春换年，oracle 农历显示行口径）；判定层={lyr}（民俗年，正月初一换年）"},
        "shichen": {"zhi": ZHI[shichen], "rule_id": "zw-01"},
        "minggong": {"zhi": ZHI[ming], "gan": ming_gan, "rule_id": "zw-02",
                     "source": "命宫=寅起正月顺数生月、逆数生时（身宫顺数生时），oracle 对拍一致"},
        "shengong": {"zhi": ZHI[shen], "rule_id": "zw-02"},
        "wuxing_ju": {"name": ju + "局", "rule_id": "zw-03",
                      "source": f"命宫干支 {ming_gan}{ZHI[ming]} 纳音 → {nayin[ming_gan + ZHI[ming]]}（nayin.csv），oracle 对拍一致"},
        "ziwei": {"zhi": ZHI[ziwei], "rule_id": "zw-04",
                  "source": f"安紫微诀（{ju}局，初一{ZHI[ZIMI_BASE[ju]]}，{k}日进一宫；生日 {lday}）——易安居口径",
                  "alt": f"异文：一日一宫派（初一宫同，日{lday}→按日顺一宫）"},
        "palaces": out_palaces,
        "sihua": {"items": [{"star": s, "hua": h} for s, h in sihua], "rule_id": "zw-07",
                  "source": f"生年四化（{lyr[0]} 干）表，oracle 图例对拍一致"},
        "notes": notes,
    }


def main():
    ap = argparse.ArgumentParser(description="L3-1 紫微斗数排盘")
    ap.add_argument("--datetime", required=True, help="北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    r = compute(dt, a.lon)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        print(f"输入: {r['input']['datetime']} 东经 {r['input']['lon']}°")
        print(f"农历: {r['lunar']['month_name']}{'（闰）' if r['lunar']['is_ruen'] else ''}初{r['lunar']['day']}日? 时={r['shichen']['zhi']}时")
        print(f"命宫: {r['minggong']['gan']}{r['minggong']['zhi']}  身宫: {r['shengong']['zhi']}  五行局: {r['wuxing_ju']['name']}")
        print(f"紫微: {r['ziwei']['zhi']}")
        for p in r["palaces"]:
            print(f"  {p['name']}({p['gan']}{p['zhi']}{'身' if p['shen'] else ''}): {','.join(p['stars'])}"
                  + (f"  [化:{','.join(p['sihua'])}]" if p["sihua"] else ""))
        print("四化: " + " ".join(f"{s['star']}{s['hua']}" for s in r["sihua"]["items"]))


if __name__ == "__main__":
    main()
