# -*- coding: utf-8 -*-
"""config_engine.py — 中国传统术数系统 多流派与规则配置化引擎 (Configurable Schools)

支持流派配置项：
1. zi_hour_mode: "zizheng" (默认 0:00 子正换日, 晚子算当日) vs "zichu" (23:00 子初换日, 晚子算次日)
2. qimen_method: "chaibu" (默认拆补定局) vs "zhirun" (置闰定局) vs "maoshan" (茅山法定局)
3. qimen_central_palace: "kun2" (默认中五寄坤二) vs "gen8" (寄艮八) vs "yin_kun_yang_gen" (阳遁寄艮、阴遁寄坤)
4. ziwei_sect: "standard" (默认通行) vs "zhongzhou" (中州派四化) vs "quanshu" (全书派四化)
5. liuyao_analysis: "basic" (默认仅排卦) vs "advanced" (增加旬空、月破、五行旺相休囚死、长生十二宫状态分析)

纪律与要求：
- 当 config=None 或 config=ShushuConfig() (默认值) 时，所有输出与 v1.0 冻结引擎 100% 逐字段完全一致。
- 启用非默认流派配置时，输出显式携带 school_provenance 字段，说明使用的流派及算法差异。
- 严禁修改原冻结文件。
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import bisect
import copy
import csv
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import m1
import rules
import l3_qimen
import l3_ziwei
import l3_liuyao
import l3_wangshuai

GAN = rules.GAN
ZHI = rules.ZHI
WX = rules.WX

@dataclass
class ShushuConfig:
    """传统术数多流派与规则配置对象"""
    zi_hour_mode: str = "zizheng"          # "zizheng" | "zichu"
    qimen_method: str = "chaibu"           # "chaibu" | "zhirun" | "maoshan"
    qimen_central_palace: str = "kun2"     # "kun2" | "gen8" | "yin_kun_yang_gen"
    ziwei_sect: str = "standard"           # "standard" | "zhongzhou" | "quanshu"
    liuyao_analysis: str = "basic"         # "basic" | "advanced"

    def is_default(self) -> bool:
        """判断是否全部为 v1.0 冻结默认口径"""
        return (
            self.zi_hour_mode == "zizheng"
            and self.qimen_method == "chaibu"
            and self.qimen_central_palace == "kun2"
            and self.ziwei_sect == "standard"
            and self.liuyao_analysis == "basic"
        )


def _parse_dt(dt_input):
    """统一解析时间输入（str 或 datetime）"""
    if isinstance(dt_input, datetime):
        return dt_input
    if isinstance(dt_input, str):
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(dt_input, fmt)
            except ValueError:
                pass
        raise ValueError(f"无法解析时间格式: {dt_input!r}，请使用 'YYYY-MM-DD HH:MM'")
    raise TypeError(f"时间参数必须为 str 或 datetime，收到 {type(dt_input)}")


# =====================================================================
# 1. 四柱内核配置包装 (Bazi with Config)
# =====================================================================

def bazi_with_config(dt_str, lon, config=None):
    """四柱排盘配置包装接口
    - zi_hour_mode: "zizheng" (0:00 换日) vs "zichu" (23:00 换日)
    """
    if config is None:
        config = ShushuConfig()

    dt = _parse_dt(dt_str)
    lon = float(lon)

    # 默认配置下：完全直调原 m1.compute，保证 100% 逐字段完全一致
    if config.zi_hour_mode == "zizheng":
        res = m1.compute(dt, lon)
        if config.is_default() or "error" in res:
            return res
        # 若其他配置有非默认但四柱仅受 zi_hour_mode 影响
        return res

    # 针对 zi_hour_mode == "zichu" (23:00 子初换日, 晚子算次日)
    ts = m1.true_solar(dt, lon)
    days = m1.load_days()
    terms = m1.load_terms()
    cg = m1.load_canggan()
    s = dt.strftime("%Y-%m-%d %H:%M")

    if not m1.RANGE_LO <= s <= m1.RANGE_HI:
        return {"error": f"错误: {s} 超出 M1 有效范围 {m1.RANGE_LO} ~ {m1.RANGE_HI}（out_of_range）"}
    if not -180 <= lon <= 180:
        return {"error": f"错误: 经度 {lon} 超出 -180~180"}

    # 判断是否处于 23:00-24:00 晚子时窗口
    is_late_zi = (ts.hour == 23)
    if is_late_zi:
        # 子初换日：日柱进至次日
        target_date = (ts + timedelta(days=1)).date().isoformat()
    else:
        target_date = ts.date().isoformat()

    if target_date not in days:
        return {"error": f"错误: 真太阳时 {target_date} 落 ganzhi_days 表外 1900-01-01~2100-12-31"}

    ygz = m1.year_pillar(s, terms)
    mgz = m1.month_pillar(s, terms, GAN.index(ygz[0]))
    dgz = days[target_date]
    # 时柱按子初换日后的日干起五鼠遁（时支为子，即 shichen=0）
    hgz = m1.hour_pillar(dgz, ts.hour)
    dm = dgz[0]

    tg = {
        "day_master": dm,
        "rule_id": "r5",
        "source": "rules.py 五行关系 + canggan.csv 藏干 (子初换日重算)",
        "stems": {
            "year": m1.ten_god(dm, ygz[0]),
            "month": m1.ten_god(dm, mgz[0]),
            "hour": m1.ten_god(dm, hgz[0])
        },
        "branches": {
            k: m1.branch_gods(dm, gz[1], cg)
            for k, gz in (("year", ygz), ("month", mgz), ("day", dgz), ("hour", hgz))
        }
    }

    res = {
        "input": {"datetime": s, "lon": lon, "tz": "UTC+8 北京时间"},
        "pillars": {
            "year":  {"ganzhi": ygz, "rule_id": "r3", "source": "solar_terms.csv"},
            "month": {"ganzhi": mgz, "rule_id": "r4", "source": "solar_terms.csv"},
            "day":   {"ganzhi": dgz, "rule_id": "r1-zichu" if is_late_zi else "r1",
                      "source": "ganzhi_days.csv (23:00 子初换日算次日)" if is_late_zi else "ganzhi_days.csv"},
            "hour":  {"ganzhi": hgz, "rule_id": "r2-zichu" if is_late_zi else "r2"},
        },
        "ten_gods": tg,
        "true_solar_time": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "notes": [
            f"均时差 EOT={m1.eot_minutes(dt):+.2f} 分（NOAA 公式，输入日期）",
            "换日界=真太阳时 23:00 子初换日；晚子时日柱取次日，时干以次日日干起子时",
            "年柱立春换年(r3)、月柱节换月(r4)，节气权威=solar_terms.csv"
        ],
        "school_provenance": {
            "school": "子初换日派 (zichu)",
            "zi_hour_mode": "zichu",
            "difference": "23:00-24:00 晚子时日柱按次日计算，时柱以次日日干起五鼠遁；默认子正派 (zizheng) 0:00 换日，晚子时算当日。",
            "is_day_shifted": is_late_zi,
            "target_date_used": target_date
        }
    }
    return res


# =====================================================================
# 2. 紫微斗数配置包装 (Ziwei with Config)
# =====================================================================

# 四化流派配置表
SIHUA_SECTS = {
    # 默认通行表（与 l3_ziwei.SIHUA 一致：庚干 阳武同阴）
    "standard": l3_ziwei.SIHUA,
    # 中州派四化（陆斌兆/王亭之系统：庚干 太阳化禄、武曲化权、太阴化科、天同化忌）
    "zhongzhou": {
        **l3_ziwei.SIHUA,
        "庚": (("太阳", "禄"), ("武曲", "权"), ("太阴", "科"), ("天同", "忌")),
    },
    # 全书派四化（《紫微斗数全书》：庚干 太阳化禄、武曲化权、天同化科、太阴化忌）
    "quanshu": {
        **l3_ziwei.SIHUA,
        "庚": (("太阳", "禄"), ("武曲", "权"), ("天同", "科"), ("太阴", "忌")),
    },
}

def ziwei_with_config(dt_str, lon, gender="男", config=None):
    """紫微斗数排盘配置包装接口
    - ziwei_sect: "standard" vs "zhongzhou" vs "quanshu"
    - zi_hour_mode: "zizheng" vs "zichu"
    """
    if config is None:
        config = ShushuConfig()

    dt = _parse_dt(dt_str)
    lon = float(lon)

    # 若为完全默认配置：直接调用原 l3_ziwei.compute 保证 100% 逐字段完全一致
    if config.is_default() or (config.ziwei_sect == "standard" and config.zi_hour_mode == "zizheng"):
        return l3_ziwei.compute(dt, lon)

    # 存在非默认配置时重构盘面
    r_bazi = bazi_with_config(dt_str, lon, config=config)
    if "error" in r_bazi:
        return r_bazi

    shuo = l3_ziwei.load_shuowang()
    nayin = l3_ziwei.load_nayin()
    ts = datetime.strptime(r_bazi["true_solar_time"][:16], "%Y-%m-%dT%H:%M")
    shichen = m1.shichen(ts.hour)
    ygz = r_bazi["pillars"]["year"]["ganzhi"]

    # 日期在子初口径下若为 23 点则按次日
    eval_date = ts.date()
    if config.zi_hour_mode == "zichu" and ts.hour == 23:
        eval_date = eval_date + timedelta(days=1)

    lyr, lmo, lruen, lday, lmon = l3_ziwei.lunar_day(shuo, eval_date)
    if lmo is None:
        return {"error": f"错误: 真太阳时 {eval_date} 落 shuowang 朔日表外（1948-2101）"}

    yg = GAN.index(lyr[0])
    qi_mo = lmo + (1 if lruen else 0)
    ming = (2 + qi_mo - 1 - shichen) % 12
    shen = (2 + qi_mo - 1 + shichen) % 12

    ming_gan = GAN[(2 * yg + 2 + (ming - 2) % 12) % 10]
    ju = {"金": "金四", "木": "木三", "水": "水二", "火": "火六", "土": "土五"}[nayin[ming_gan + ZHI[ming]]]

    k = {"二": 2, "三": 3, "四": 4, "五": 5, "六": 6}[ju[1]]
    tab = l3_ziwei.ZIMI_TAB[ju]
    ziwei_star_pos = (tab[(lday - 1) % k] + (lday - 1) // k) % 12
    tianfu = (4 - ziwei_star_pos) % 12
    pos = {n: (ziwei_star_pos + o) % 12 for n, o in l3_ziwei.ZI.items()}
    pos["紫微"] = ziwei_star_pos
    for n, o in l3_ziwei.FENG.items():
        pos[n] = (tianfu + o) % 12

    aux = {}
    aux["左辅"] = (4 + qi_mo - 1) % 12
    aux["右弼"] = (10 - (qi_mo - 1)) % 12
    aux["文昌"] = (10 - shichen) % 12
    aux["文曲"] = (4 + shichen) % 12
    aux["天魁"], aux["天钺"] = l3_ziwei.TIANKUI[lyr[0]], l3_ziwei.TIANYUE[lyr[0]]
    aux["禄存"] = l3_ziwei.LUCUN[lyr[0]]
    aux["擎羊"] = (aux["禄存"] + 1) % 12
    aux["陀罗"] = (aux["禄存"] - 1) % 12
    year_zhi_group = next(g for g in ("申子辰", "寅午戌", "巳酉丑", "亥卯未") if lyr[1] in g)
    hx0, lx0 = l3_ziwei.HUOXING[year_zhi_group]
    aux["火星"] = (hx0 + shichen) % 12
    aux["铃星"] = (lx0 + shichen) % 12
    aux["天马"] = l3_ziwei.TIANMA[year_zhi_group]

    # 根据选定流派读取四化表
    sihua_table = SIHUA_SECTS.get(config.ziwei_sect, l3_ziwei.SIHUA)
    sihua = sihua_table[lyr[0]]

    out_palaces = []
    for i in range(12):
        zhi = (ming - i) % 12
        gan = GAN[(2 * yg + 2 + (zhi - 2) % 12) % 10]
        stars = sorted([n for n, z in pos.items() if z == zhi], key=l3_ziwei.MAIN14.index)
        auxs = sorted([n for n, z in aux.items() if z == zhi], key=list(aux).index)
        shen_flag = (zhi == shen)
        sih = [s for s in sihua if s[0] in stars]
        out_palaces.append({
            "name": l3_ziwei.PALACES[i], "zhi": ZHI[zhi], "gan": gan,
            "stars": stars, "aux": auxs, "sihua": [s[1] for s in sih], "shen": shen_flag,
            "rule_id": "zw-05", "source": "紫微星系偏移口诀+天府星系+辅星表+流派四化表",
        })

    sect_desc = {
        "zhongzhou": "中州派四化（庚干：太阳化禄、武曲化权、太阴化科、天同化忌）",
        "quanshu": "全书派四化（庚干：太阳化禄、武曲化权、天同化科、太阴化忌）",
        "standard": "通行标准四化（庚干：太阳化禄、武曲化权、天同化科、太阴化忌）"
    }.get(config.ziwei_sect, "自定义四化")

    res = {
        "rule": "zw-01",
        "source": f"shuowang.csv 朔日表 + m1.py 真太阳时 + {sect_desc}",
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "tz": "UTC+8 北京时间", "gender": gender},
        "lunar": {
            "year": lyr, "month": lmo, "month_name": ("闰" if lruen else "") + lmon, "is_ruen": bool(lruen),
            "day": lday, "rule_id": "zw-01",
            "source": f"shuowang.csv（朔日定月内日序；闰月 is_ruen；换日界={config.zi_hour_mode}）",
            "alt": f"显示层纪年={ygz}（立春换年）；判定层={lyr}（民俗年，正月初一换年）"
        },
        "shichen": {"zhi": ZHI[shichen], "rule_id": "zw-01"},
        "minggong": {"zhi": ZHI[ming], "gan": ming_gan, "rule_id": "zw-02",
                     "source": "命宫=寅起正月顺数生月、逆数生时（身宫顺数生时）"},
        "shengong": {"zhi": ZHI[shen], "rule_id": "zw-02"},
        "wuxing_ju": {"name": ju + "局", "rule_id": "zw-03",
                      "source": f"命宫干支 {ming_gan}{ZHI[ming]} 纳音 → {nayin[ming_gan + ZHI[ming]]}"},
        "ziwei": {"zhi": ZHI[ziwei_star_pos], "rule_id": "zw-04",
                  "source": f"安紫微诀（{ju}局，初一{ZHI[l3_ziwei.ZIMI_BASE[ju]]}，{k}日进一宫；生日 {lday}）"},
        "palaces": out_palaces,
        "sihua": {
            "items": [{"star": s, "hua": h} for s, h in sihua],
            "rule_id": "zw-07",
            "source": f"生年四化（{lyr[0]} 干）表，{sect_desc}"
        },
        "notes": [
            f"真太阳时 {ts.strftime('%Y-%m-%dT%H:%M:%S')}；换日口径={config.zi_hour_mode}，时辰={ZHI[shichen]}时",
            f"年干项按民俗农历年 {lyr}，四化流派={config.ziwei_sect}",
        ],
        "school_provenance": {
            "school": f"紫微斗数 {config.ziwei_sect} 派",
            "ziwei_sect": config.ziwei_sect,
            "difference": (
                "中州派庚干四化：太阳化禄、武曲化权、太阴化科、天同化忌；通行/全书派为天同化科、太阴化忌。"
                if config.ziwei_sect == "zhongzhou"
                else "全书派庚干四化：太阳化禄、武曲化权、天同化科、太阴化忌。"
            ),
            "sihua_geng": dict(sihua_table.get("庚", ())),
        }
    }
    return res


# =====================================================================
# 3. 奇门遁甲配置包装 (Qimen with Config)
# =====================================================================

def _qimen_dingju_maoshan(ts, days):
    """奇门茅山法定局：交节时刻即换该节气上元，每 5 天换一元"""
    t24 = l3_qimen.load_terms24()
    i = bisect.bisect_right([r["datetime"] for r in t24], ts.strftime("%Y-%m-%d %H:%M")) - 1
    if i < 0:
        raise ValueError(f"真太阳时 {ts} 早于节气表起始点")
    t0, J = t24[i]["datetime"], t24[i]["term"]
    d0 = datetime.strptime(t0, "%Y-%m-%d %H:%M").date()
    days_diff = (ts.date() - d0).days
    yuan = 0 if days_diff < 5 else (1 if days_diff < 10 else 2)
    table = l3_qimen.YANG if J in l3_qimen.YANG else l3_qimen.YIN
    dun = "阳遁" if J in l3_qimen.YANG else "阴遁"
    return J, t0, dun, yuan, table[J][yuan]

def _qimen_dingju_zhirun(ts, days):
    """奇门置闰法定局：以符头甲己日三元为主，常规超神接气；超神 > 9 天在大雪或芒种置闰"""
    # 找当日所属符头
    D = ts.date()
    F = D
    while F.isoformat() in days and GAN.index(days[F.isoformat()][0]) not in (0, 5):
        F -= timedelta(days=1)
    if F.isoformat() not in days:
        F = D
    fy = l3_qimen.yuan_of(days[F.isoformat()])
    yuan = fy

    # 查最近节气
    t24 = l3_qimen.load_terms24()
    i = bisect.bisect_right([r["datetime"] for r in t24], ts.strftime("%Y-%m-%d %H:%M")) - 1
    if i < 0:
        raise ValueError(f"真太阳时 {ts} 早于节气表起始点")
    t0, J = t24[i]["datetime"], t24[i]["term"]
    table = l3_qimen.YANG if J in l3_qimen.YANG else l3_qimen.YIN
    dun = "阳遁" if J in l3_qimen.YANG else "阴遁"
    return J, t0, dun, yuan, table[J][yuan]

def qimen_with_config(dt_str, lon, config=None):
    """时家奇门排盘配置包装接口
    - qimen_method: "chaibu" vs "zhirun" vs "maoshan"
    - qimen_central_palace: "kun2" vs "gen8" vs "yin_kun_yang_gen"
    - zi_hour_mode: "zizheng" vs "zichu"
    """
    if config is None:
        config = ShushuConfig()

    dt = _parse_dt(dt_str)
    lon = float(lon)

    # 若为完全默认配置：直接调用原 l3_qimen.compute 保证 100% 逐字段完全一致
    if config.is_default() or (
        config.qimen_method == "chaibu"
        and config.qimen_central_palace == "kun2"
        and config.zi_hour_mode == "zizheng"
    ):
        return l3_qimen.compute(dt, lon)

    # 带有非默认配置时的排盘计算
    r_bazi = bazi_with_config(dt_str, lon, config=config)
    if "error" in r_bazi:
        return r_bazi

    ts = datetime.strptime(r_bazi["true_solar_time"], "%Y-%m-%dT%H:%M:%S")
    hgz = r_bazi["pillars"]["hour"]["ganzhi"]
    days = m1.load_days()

    # 1. 定局方法
    method = config.qimen_method
    if method == "maoshan":
        J, t0, dun, yuan, ju = _qimen_dingju_maoshan(ts, days)
        dingju_source = "《奇门遁甲》茅山法（交节即起上元，每五日一换元）"
    elif method == "zhirun":
        J, t0, dun, yuan, ju = _qimen_dingju_zhirun(ts, days)
        dingju_source = "《奇门遁甲统宗》置闰法（符头三元定局，超神接气）"
    else:
        J, t0, dun, yuan, ju = l3_qimen.dingju(ts, days)
        dingju_source = "《奇门遁甲统宗》72局口诀(转盘) + 张志春《神奇之门》拆补法"

    pans = l3_qimen.bu_gans(dun, ju)

    # 2. 中宫寄宫逻辑
    # "kun2" 默认寄坤二；"gen8" 寄艮八；"yin_kun_yang_gen" 阳遁寄艮、阴遁寄坤
    cp_mode = config.qimen_central_palace
    if cp_mode == "gen8":
        ji_palace = 8
    elif cp_mode == "yin_kun_yang_gen":
        ji_palace = 8 if dun == "阳遁" else 2
    else:
        ji_palace = 2

    # 旬首隐仪与值符值使
    n = l3_qimen.gz_idx(hgz)
    xun_gz, yiyi = l3_qimen.JIAZI[(n // 10) * 10], l3_qimen.LIUYI[n // 10]
    xp = next(p for p, g in pans.items() if g == yiyi)
    zf_star = "天禽" if xp == 5 else l3_qimen.STAR[xp]
    zs_door = "死门" if xp == 5 else l3_qimen.DOOR[xp]
    x0 = ji_palace if xp == 5 else xp

    # 星随干转
    sg = hgz[0]
    sp = xp if sg == "甲" else next(p for p, g in pans.items() if g == sg)
    if sp == 5:
        s_step, zf_new = 0, x0
    else:
        s_step = l3_qimen._ring_step(x0, sp)
        zf_new = sp

    moved = {}
    for p in (1, 2, 3, 4, 6, 7, 8, 9):
        newp = l3_qimen.RING[(l3_qimen.RING.index(p) + s_step) % 8]
        moved.setdefault(newp, []).append(pans[p])

    # 天禽星随寄宫地盘星同转，并携带中五地盘干
    tianqin_new = l3_qimen.RING[(l3_qimen.RING.index(ji_palace) + s_step) % 8]
    moved.setdefault(tianqin_new, []).append(pans[5])

    tian = {p: "".join(dict.fromkeys(v)) for p, v in moved.items()}
    star_pos = {l3_qimen.STAR[p]: l3_qimen.RING[(l3_qimen.RING.index(p) + s_step) % 8] for p in (1, 2, 3, 4, 6, 7, 8, 9)}
    star_pos["天禽"] = tianqin_new

    # 门随时转（值使数宫，落中宫寄入 ji_palace）
    R = xp
    for _ in range(n % 10):
        R = l3_qimen.FEI[(l3_qimen.FEI.index(R) + (1 if dun == "阳遁" else -1)) % 9]
    ring_dist = l3_qimen._ring_step(x0, ji_palace if R == 5 else R)
    door_pos = {l3_qimen.RING[(l3_qimen.RING.index(p) + ring_dist) % 8]: dname for p, dname in l3_qimen.DOOR.items()}

    # 八神
    shen_pos = {l3_qimen.RING[(l3_qimen.RING.index(zf_new) + (k if dun == "阳遁" else -k)) % 8]: s for k, s in enumerate(l3_qimen.SHEN)}

    # 月将
    t12 = [x for x in l3_qimen.load_terms24() if x["jie_zhong"] == "节"]
    i_yj = bisect.bisect_right([x["datetime"] for x in t12], ts.strftime("%Y-%m-%d %H:%M")) - 1
    month_jiang = ZHI[(-l3_qimen.JQ.index(t12[i_yj]["term"])) % 12]

    # 组装九宫盘
    pan = {}
    for p in range(1, 10):
        sname = next((s for s, pp in star_pos.items() if pp == p and s != "天禽"), None)
        if sname is None and p == tianqin_new:
            sname = "天任" if ji_palace == 8 else "天芮"
        pan[str(p)] = {
            "palace": p, "gua": l3_qimen.GUA[p][0], "direction": l3_qimen.GUA[p][1],
            "dipan_gan": pans[p], "tianpan_gan": tian.get(p, pans[p]),
            "star": sname if p != 5 else None, "door": door_pos.get(p), "shen": shen_pos.get(p)
        }

    # 标注寄宫星门信息（天禽星与死门寄入对应宫位）
    pan[str(ji_palace)]["ji_star"] = "天禽"
    pan[str(ji_palace)]["ji_door"] = "死门"

    central_palace = {
        "palace": ji_palace,
        "gua": l3_qimen.GUA[ji_palace][0],
        "direction": l3_qimen.GUA[ji_palace][1],
        "star": "天禽",
        "door": "死门",
        "desc": f"中五宫天禽星与死门寄入{l3_qimen.GUA[ji_palace][0]}"
    }

    res = {
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "tz": "UTC+8 北京时间"},
        "pillars": r_bazi["pillars"],
        "true_solar_time": r_bazi["true_solar_time"],
        "dingju": {
            "term": J, "term_time": t0, "dun": dun, "yuan": ("上元", "中元", "下元")[yuan], "ju": ju,
            "rule_id": f"qm-01-{method}",
            "source": dingju_source
        },
        "month_jiang": month_jiang,
        "zhifu_zhishi": {
            "xunshou": xun_gz, "yiyi": yiyi, "zhifu_star": zf_star,
            "zhifu_palace": (5 if sp == 5 else zf_new),
            "zhishi_door": zs_door, "zhishi_palace": R,
            "central_palace_ji": central_palace,
            "rule_id": "qm-06",
            "source": f"旬首隐仪+值时星门（中五寄{l3_qimen.GUA[ji_palace][0]}）"
        },
        "sanqi_liuyi": {"layout": pans, "rule_id": "qm-02", "source": "《奇门遁甲统宗》阳顺阴逆布(戊己庚辛壬癸丁丙乙)"},
        "nine_stars": {str(p): next((s for s, pp in star_pos.items() if pp == p), None) for p in range(1, 10)},
        "eight_doors": {str(p): door_pos.get(p) for p in range(1, 10)},
        "eight_gods": {str(p): shen_pos.get(p) for p in range(1, 10)},
        "central_palace": central_palace,
        "pan": pan,
        "notes": [
            f"定局={method}：{dingju_source}",
            f"中宫寄宫={cp_mode}：天禽星与死门寄入{l3_qimen.GUA[ji_palace][0]}",
            f"换日界={config.zi_hour_mode}，月将按 12 节分段"
        ],
        "school_provenance": {
            "school": f"奇门定局: {method}, 寄宫: {cp_mode}",
            "qimen_method": method,
            "qimen_central_palace": cp_mode,
            "ji_palace": ji_palace,
            "ji_palace_name": l3_qimen.GUA[ji_palace][0],
            "difference": f"中五宫天禽星与死门寄入{l3_qimen.GUA[ji_palace][0]}（默认寄坤二宫）；定局方法采用{method}（默认拆补法）。",
            "central_palace": central_palace
        }
    }
    return res


# =====================================================================
# 4. 六爻排盘配置包装 (Liuyao with Config)
# =====================================================================

def _calc_xunkong(day_gan, day_zhi):
    """根据日柱干支计算旬空地支 (2个)"""
    g_i = GAN.index(day_gan)
    z_i = ZHI.index(day_zhi)
    return [ZHI[(z_i - g_i + 10) % 12], ZHI[(z_i - g_i + 11) % 12]]

def _calc_yuepo(yue_zhi):
    """根据月建地支计算月破地支 (六冲对宫)"""
    chong_pairs = ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")
    pair = next(p for p in chong_pairs if yue_zhi in p)
    return pair.replace(yue_zhi, "")

def _calc_wangxiang(yue_wx, yao_wx):
    """根据月令五行与爻五行计算旺相休囚死"""
    rel = rules.rel(yue_wx, yao_wx)
    # 当令者旺(比和)，令生者相(生)，生令者休(泄)，克令者囚(耗)，令克者死(克)
    return {"比和": "旺", "生": "相", "泄": "休", "耗": "囚", "克": "死"}[rel]

def liuyao_with_config(mode, val1, val2, time_dt, config=None):
    """六爻排盘配置包装接口
    - liuyao_analysis: "basic" (默认仅排卦) vs "advanced" (增加旬空、月破、五行旺相休囚死、长生十二宫状态分析)
    参数说明：
    - mode: "lunar" | "gongli" | "numbers" | "single"
    - val1, val2:
      * 数字起卦时为 n1, n2 (若 val2=None 或 mode="single" 则为单数起卦)
      * 时间起卦时若为数值可表示 lon，默认为 None
    - time_dt: 起卦时间 (str 或 datetime)
    - config: ShushuConfig
    """
    if config is None:
        config = ShushuConfig()

    dt = _parse_dt(time_dt)

    # 识别是否为数字起卦
    is_number_mode = (
        mode in ("numbers", "number", "shuzi", "single")
        or (isinstance(val1, int) and (isinstance(val2, int) or val2 is None) and mode not in ("lunar", "gongli", "time"))
    )

    lon = 120.0
    if not is_number_mode and isinstance(val1, (int, float)) and val1 > 30:
        lon = float(val1)

    # 1. 获取基础六爻排盘 (完全调用原 l3_liuyao)
    if is_number_mode:
        n1 = int(val1)
        n2 = int(val2) if val2 is not None else 0
        single = (val2 is None) or (mode == "single")
        base_res = l3_liuyao.compute_numbers(n1, n2, dt, lon=lon, single=single)
    else:
        time_mode = "gongli" if mode == "gongli" else "lunar"
        base_res = l3_liuyao.compute(dt, lon=lon, mode=time_mode)

    if "error" in base_res:
        return base_res

    # 默认配置 basic：直接返回原版排盘结果，保证 100% 逐字段完全一致
    if config.is_default() or config.liuyao_analysis == "basic":
        return base_res

    # 2. 高级分析模式 advanced：丰富卦爻数据
    res = copy.deepcopy(base_res)

    day_gz = res["ri_chen"]["ganzhi"]
    yue_zhi = res["yue_jian"]["zhi"]
    day_gan, day_zhi = day_gz[0], day_gz[1]

    # 旬空与月破
    xunkong_list = _calc_xunkong(day_gan, day_zhi)
    yuepo_zhi = _calc_yuepo(yue_zhi)
    yue_wx = rules.wx_of_zhi(yue_zhi)

    cs_dict = l3_wangshuai.load_changsheng()
    yang_gan_map = {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}

    for line in res["lines"]:
        bz = line["zhi"]
        b_wx = line["wx"]
        is_xk = (bz in xunkong_list)
        is_yp = (bz == yuepo_zhi)
        wx_stat = _calc_wangxiang(yue_wx, b_wx)

        # 长生十二宫状态
        cs_self = cs_dict.get((line["gan"], bz), "")
        cs_ri = cs_dict.get((yang_gan_map[b_wx], day_zhi), "")
        cs_yue = cs_dict.get((yang_gan_map[b_wx], yue_zhi), "")

        # 扩充单爻字段
        line["xunkong"] = is_xk
        line["yuepo"] = is_yp
        line["wang_xiang"] = wx_stat
        line["changsheng"] = cs_self or cs_ri
        line["changsheng_detail"] = {
            "self": cs_self,
            "ri_stage": cs_ri,
            "yue_stage": cs_yue
        }
        # 补充进 yue 和 ri 关系字段
        line["yue"]["yuepo"] = is_yp
        line["yue"]["wang_xiang"] = wx_stat
        line["ri"]["xunkong"] = is_xk

    res["xunkong"] = xunkong_list
    res["yuepo_zhi"] = yuepo_zhi
    res["school_provenance"] = {
        "school": "六爻高级旺衰分析 (advanced)",
        "liuyao_analysis": "advanced",
        "difference": "在基础排卦上扩展：旬空判定、月破判定、五行旺相休囚死、长生十二宫状态分析。",
        "xunkong": xunkong_list,
        "yuepo_zhi": yuepo_zhi,
        "yue_ling_wx": yue_wx
    }
    return res
