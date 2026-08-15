# -*- coding: utf-8 -*-
"""l3_ziwei_liunian.py — L3-1b 紫微斗数大限/小限/流年/斗君模块（zl-01..zl-04）。
输入=北京时间+东经+性别+指定流年（公历年）；复用 l3_ziwei.compute 排盘（命宫/五行局/十二宫干支/生年四化表）。
大限（zl-01）=命宫起限、五行局数起岁（水二 2 岁…火六 6 岁）、阳男阴女顺行/阴男阳女逆行、每限 10 年排 12 限；
  大限四化=大限宫干四化（中州派《中州派紫微斗数》口径，alt=传统派《紫微斗数全书》按生年干四化）；
小限（zl-02）=《紫微斗数全书》定小限「先将生年分四局，墓库冲处小限起，男顺女逆一路行，不论阴阳各排比」，
  寅午戌→辰起、亥卯未→丑起、申子辰→戌起、巳酉丑→未起，1 岁起宫，男顺女逆（alt=「子午卯酉人寅宫起」派）；
流年（zl-03）=指定公历年→民俗农历年号（shuowang.csv 正月初一换年，与 l3_ziwei 判定层同轨），
  流年支落地支固定宫位、流年干四化按流年天干（zw-07 表）；
斗君（zl-04）=《紫微斗数全书》卷二·安斗君诀「太岁宫中便起正，逆寻生月即留停，又从生月宫轮子，顺至生时镇斗星」，
  即斗君=(太岁支序−生月序+生时支序)mod12（生月序正月=0、闰月按次月+1，oracle「子年斗君」全样对拍一致；
  任务书「正月起寅」描述与实测不符，弃用并以 alt 注明）。
差异无处藏身：每输出项带 rule_id（zl-xx）+ source（底本出处）+ alt（异文标注）。
"""
import argparse, csv, json, os, sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import l3_ziwei  # 复用排盘（只读共享）
import m1

GAN, ZHI = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
JUSHU = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}  # 局数=大限起始岁数（zl-01）
# zl-02 定小限：墓库冲处（生年三合局墓库宫位的对冲宫）→ 1 岁起宫
XIAOXIAN_START = {"申子辰": 10, "寅午戌": 4, "亥卯未": 1, "巳酉丑": 7}  # 戌/辰/丑/未（子=0）


def liunian_year_ganzhi(target_year, shuo):
    """指定公历年 → 民俗农历年号（shuowang.csv 正月初一换年，同 l3_ziwei 判定层；zl-03）。
    整年按该年正月初一的年号计（如 2026→丙午）；正月前的日别歧义以 alt 注明。"""
    ly = next((r[3] for r in shuo if r[1] == 1 and not r[2] and r[0].year == target_year), None)
    if ly is None:
        return None
    return ly


def palace_gan(yg, zhi):
    """宫干=五虎遁（寅起丙，同 l3_ziwei 宫干式）：(2·年干+2+宫支序)%10。"""
    return GAN[(2 * yg + 2 + (zhi - 2) % 12) % 10]


def compute(dt, lon=120.0, sex="男", target_year=None):
    """(北京时 datetime, 东经, 性别 男/女, 流年公历年) → 大限/小限/流年/斗君 JSON dict。
    出生信息以 l3_ziwei.compute 排盘为唯一输入（真太阳时子正、民俗年判定层等口径全继承）。"""
    r = l3_ziwei.compute(dt, lon)
    if "error" in r:
        return r
    shuo = l3_ziwei.load_shuowang()
    ming = ZHI.index(r["minggong"]["zhi"])          # 命宫支序（大限起宫）
    ju_name = r["wuxing_ju"]["name"]                 # 如 火六局
    ju = JUSHU[ju_name]
    ly = r["lunar"]["year"]                          # 民俗农历年（判定层，正月初一换年）
    yg = GAN.index(ly[0])                            # 判定层年干
    lmo = r["lunar"]["month"]                        # 生月序（1-12）
    lruen = int(r["lunar"]["is_ruen"])
    shichen = ZHI.index(r["shichen"]["zhi"])         # 真太阳时时辰支序
    yzhi = ZHI.index(ly[1])                          # 生年支序（小限定宫）
    yang = yg % 2 == 0                               # 年干阴阳：甲丙戊庚壬=阳
    dir_ = 1 if (yang and sex == "男") or (not yang and sex == "女") else -1  # 阳男阴女顺/阴男阳女逆
    m_eff = lmo + lruen - 1                          # 生月序（正月=0；闰月按次月+1，同命宫口径）

    # --- zl-01 大限：命宫起、局数起岁、每限 10 年、排 12 限（至 100+ 岁） ---
    items = []
    for i in range(12):
        start, end = ju + 10 * i, ju + 10 * i + 9
        z = (ming + dir_ * i) % 12
        gz = palace_gan(yg, z) + ZHI[z]
        sihua = l3_ziwei.SIHUA[gz[0]]                # 中州派：大限干四化（底本注明）
        years = [dt.year + start - 1 + k for k in range(10)]  # 虚岁 A 岁=出生年+(A-1)
        items.append({
            "ages": f"{start}-{end}", "age_start": start, "age_end": end,
            "zhi": ZHI[z], "gan": gz[0], "ganzhi": gz,
            "palace": next(p["name"] for p in r["palaces"] if p["zhi"] == ZHI[z]),
            "sihua": [{"star": s, "hua": h} for s, h in sihua],
            "liunian_years": [f"{y}({ZHI[(y - 4) % 12]})" for y in years],  # 该限内流年支（公历干支纪年，alt 口径）
        })
    daxian = {
        "start_age": ju, "direction": "顺行" if dir_ == 1 else "逆行",
        "birth_ganzhi_sex": f"{'阳' if yang else '阴'}{'男' if sex == '男' else '女'}({ly})",
        "items": items, "rule_id": "zl-01",
        "source": ("大限=命宫起限、五行局数起岁（水二 2 岁…火六 6 岁）、阳男阴女顺行/阴男阳女逆行、每限 10 年，"
                   "oracle（易安居紫微盘）对拍一致；大限四化=大限宫干四化（中州派《中州派紫微斗数》，王亭之系统）"),
        "alt": "异文：① 传统派（《紫微斗数全书》系统）大限/流年四化一律按生年干四化，不按大限干；"
               "② 流年支对应按公历干支纪年（立春换年）标注，非民俗年号",
    }

    # --- zl-02 小限：《全书》定小限「墓库冲处小限起，男顺女逆」，1 岁起宫 ---
    xstart = XIAOXIAN_START[next(g for g in XIAOXIAN_START if yzhi in [ZHI.index(x) for x in g])]
    xdir = 1 if sex == "男" else -1                    # 男顺女逆，不论阴阳（《全书》）
    xtable = {str(a): ZHI[(xstart + xdir * (a - 1)) % 12] for a in range(1, 121)}
    xiaoxian = {
        "start_age": 1, "start_palace": ZHI[xstart], "direction": "顺行" if xdir == 1 else "逆行",
        "table": xtable, "rule_id": "zl-02",
        "source": ("《紫微斗数全书》定小限「先将生年分四局，墓库冲处小限起，男顺女逆一路行，不论阴阳各排比」："
                   "生年三合局墓库宫之对冲宫起 1 岁（寅午戌→辰、申子辰→戌、亥卯未→丑、巳酉丑→未），男顺女逆"),
        "alt": "异文：「子午卯酉人寅宫起、辰戌丑未人申宫起、寅申巳亥人午宫起」派（另传口诀，起点不同）；"
               "易安居紫微盘不显示小限，本表未对拍 oracle",
    }

    # --- zl-03 流年：指定公历年 → 民俗年号 → 流年支宫位 + 流年干四化 ---
    liunian = None
    if target_year is not None:
        lgz = liunian_year_ganzhi(target_year, shuo)
        if lgz is None:
            liunian = {"error": f"流年 {target_year} 落 shuowang 表外（1948-2101）", "rule_id": "zl-03"}
        else:
            lz = ZHI.index(lgz[1])
            lp = next(p for p in r["palaces"] if p["zhi"] == ZHI[lz])
            lsihua = l3_ziwei.SIHUA[lgz[0]]
            liunian = {
                "year": target_year, "ganzhi": lgz, "zhi": ZHI[lz],
                "palace": lp["name"], "palace_ganzhi": lp["gan"] + lp["zhi"],
                "sihua": [{"star": s, "hua": h} for s, h in lsihua],
                "doujun_zhi": ZHI[(lz - m_eff + shichen) % 12],  # zl-04 安斗君诀（流年太岁宫起）
                "rule_id": "zl-03",
                "source": ("流年=公历年→民俗农历年号（shuowang.csv 正月初一换年，同排盘判定层）；"
                           "流年支落地支固定宫位；流年干四化=zw-07 生年四化表按流年干"),
                "alt": "异文：① 立春换年派流年（干支纪年），正月前差一干支；② oracle 静态盘不含流年层（JS 动态），未对拍",
            }

    # --- zl-04 斗君：《全书》安斗君诀 = 太岁支序 − 生月序 + 生时支序（mod 12）；闰月按次月 ---
    doujun = {
        "zi_year_zhi": ZHI[(0 - m_eff + shichen) % 12],      # 子年斗君（oracle 显示口径）
        "birth_year_zhi": ZHI[(yzhi - m_eff + shichen) % 12],  # 本命（生年太岁）斗君
        "formula": f"斗君=(太岁支序−生月序+生时支序)mod12；本盘 生月={r['lunar']['month_name']}(序{m_eff}) 生时={ZHI[shichen]}时",
        "rule_id": "zl-04",
        "source": ("《紫微斗数全书》卷二·安斗君诀「大岁宫中便起正，逆寻生月即留停，又从生月宫轮子，顺至生时镇斗星」"
                   "（太岁宫起正月逆数至生月，生月宫起子时顺数至生时）；oracle「子年斗君」全样对拍一致"),
        "alt": ("任务书「正月起寅、按生时定斗君月建」描述与《全书》诀及 oracle 实测均不符，弃用；"
                "斗君为流年正月建，随流年太岁宫位而变（子年斗君即太岁=子之斗君），非固定宫"),
    }

    return {
        "rule": "zl-01", "source": "l3_ziwei.py 排盘（zw-01..07）+ shuowang.csv 朔日表（流年年号）",
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "sex": sex,
                  "target_year": target_year, "tz": "UTC+8 北京时间"},
        "lunar": {"year": ly, "month_name": r["lunar"]["month_name"], "is_ruen": bool(lruen)},
        "minggong": r["minggong"], "wuxing_ju": r["wuxing_ju"],
        "daxian": daxian, "xiaoxian": xiaoxian, "liunian": liunian, "doujun": doujun,
        "notes": [
            f"阴阳按民俗年干 {ly[0]}（{'阳' if yang else '阴'}干）判定，同 l3_ziwei 判定层；大限起岁={ju_name}局 {ju} 岁",
            "大限四化按大限宫干（中州派）；传统派按生年干，两派并存，本模块以中州派为默认值",
            "斗君与流年关系：流年 X 年太岁宫 = 流年支所在宫，斗君=(流年支序−生月序+生时支序)mod12；子年斗君即太岁=子",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description="L3-1b 紫微斗数大限/小限/流年/斗君")
    ap.add_argument("--datetime", required=True, help="出生北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--sex", default="男", choices=("男", "女"))
    ap.add_argument("--target-year", type=int, default=None, help="指定流年公历年（可选）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    r = compute(dt, a.lon, a.sex, a.target_year)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        print(f"输入: {r['input']['datetime']} 东经 {r['input']['lon']}° {r['input']['sex']}命 "
              f"流年={r['input']['target_year']}")
        print(f"农历: {r['lunar']['year']}年{r['lunar']['month_name']}  命宫: {r['minggong']['gan']}{r['minggong']['zhi']}"
              f"  {r['wuxing_ju']['name']}")
        d = r["daxian"]
        print(f"大限(zl-01): {d['birth_ganzhi_sex']} {d['direction']} {d['start_age']} 岁起命宫，12 限：")
        for it in d["items"]:
            hua = "".join(f"{s['star']}{s['hua']}" for s in it["sihua"])
            print(f"  {it['ages']:>8}岁 {it['palace']}({it['ganzhi']}) 四化[{hua}] 流年支[{','.join(y.split('(')[1][0] for y in it['liunian_years'])}]")
        x = r["xiaoxian"]
        print(f"小限(zl-02): {x['start_palace']}宫起 {x['direction']}（男顺女逆不论阴阳）")
        l = r["liunian"]
        if l:
            hua = "".join(f"{s['star']}{s['hua']}" for s in l["sihua"])
            print(f"流年(zl-03): {l['ganzhi']}年 → 支{l['zhi']}落{l['palace']}({l['palace_ganzhi']}) 四化[{hua}] 流年斗君={l['doujun_zhi']}")
        dj = r["doujun"]
        print(f"斗君(zl-04): 子年={dj['zi_year_zhi']} 本命({r['lunar']['year'][1]}年太岁)={dj['birth_year_zhi']}  [{dj['formula']}]")


if __name__ == "__main__":
    main()
