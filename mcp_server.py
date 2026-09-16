# -*- coding: utf-8 -*-
"""mcp_server.py — 中国传统术数系统 (D:\\shushu) 官方标准 MCP Server

实现标准 Model Context Protocol (MCP) JSON-RPC 2.0 stdio 服务。
为 AI Agent / 大模型提供确定性、防手推、抗幻觉的传统术数计算与审计对账能力。

暴露核心 Tools：
1. shushu_snapshot: 端到端全量快照（m1 + 16大术种直出确定性 JSON Facts）。
2. shushu_bazi: 八字排盘（四柱、十神、藏干、大运、旺衰、神煞）。
3. shushu_ziwei: 紫微斗数（十二宫、主星、辅星、煞星、生年四化、三方四正）。
4. shushu_qimen: 奇门遁甲（转盘九宫、星门神仪、格局断局、用神倾向）。
5. shushu_liuyao: 六爻排盘（时间/报数起卦、纳甲、八宫六亲、六神、世应、动爻）。
6. shushu_hepan: 两人合盘互动分析（天干五合克、地支冲合刑害、日支夫妻宫、生肖纳音、互补）。
7. shushu_reconcile: 报告文本与快照对账审计（排查大运错位、旺衰漂移、十神错配、虚构数据）。

CLI 测试模式：python mcp_server.py --test
标准 stdio 模式：python mcp_server.py
"""

import argparse
import copy
import json
import os
import sys
import traceback
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 保证当前工程根目录优先导入
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 导入底层冻结引擎模块（只读复用，绝不修改）
import m1
import rules
import l3_bazi_daliu as BD
import l3_wangshuai as WS
import l3_shensha as SS
import l3_ziwei as ZW
import l3_ziwei_liunian as ZL
import l3_qimen as QM
import l3_qimen_duanju as QMDJ
import l3_liuyao as LY
import l3_hepan as HP
import l3_chenggu as CG
import l4_audit_output as L4AO
import data_static_tables as dst
import l3_jinkoujue as JKJ
import l3_qizheng as QZ
import l3_ziwei_yunxian as ZWYX
import l3_shensha_ext as SSE
import l3_tieban_ext as TBE
from shushu_context import ShushuContext, StandardPillars

# 星曜分类常量
SHAS_SET = {"火星", "铃星", "擎羊", "陀罗", "地空", "地劫"}
FU_SET = {"文昌", "文曲", "左辅", "右弼", "天魁", "天钺", "禄存", "天马"}

PALACE_NAMES_12 = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]


def _parse_dt(dt_val):
    """灵活解析日期时间，支持 str 与 datetime（强制归零秒与微秒，符合 m1 内核契约）"""
    if isinstance(dt_val, datetime):
        return dt_val.replace(second=0, microsecond=0)
    if not isinstance(dt_val, str):
        raise ValueError(f"日期格式不合法: {dt_val}")
    s = dt_val.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(second=0, microsecond=0)
        except ValueError:
            pass
    raise ValueError(f"无法解析日期时间 '{s}'，推荐格式: YYYY-MM-DD HH:MM")


# ================================================================
# Tool 1: shushu_snapshot
# ================================================================
def shushu_snapshot(datetime_str, gender="男", longitude=120.0):
    """端到端全量快照（调用 l4_audit_output.snapshot 逻辑，返回确定性 JSON Facts）。"""
    dt = _parse_dt(datetime_str)
    dt_str_clean = dt.strftime("%Y-%m-%d %H:%M")
    snap = L4AO.snapshot(dt_str_clean, gender=gender, lon=float(longitude))
    return snap


# ================================================================
# Tool 2: shushu_bazi
# ================================================================
def shushu_bazi(datetime_str, longitude=120.0, gender="男"):
    """四柱、十神、藏干、大运、旺衰、神煞。"""
    dt = _parse_dt(datetime_str)
    lon = float(longitude)
    dt_str = dt.strftime("%Y-%m-%d %H:%M")

    # 1. 四柱与十神
    r_m1 = m1.compute(dt, lon)
    if "error" in r_m1:
        return r_m1
    dm = r_m1["ten_gods"]["day_master"]

    # 2. 大运序列
    dl, qy, jie, jiao, fwd = L4AO._dayun_pack(dt, lon, gender, steps=8)

    # 3. 旺衰判定
    r_ws = WS.compute(dt, lon)
    ws_data = {}
    if "error" not in r_ws:
        ws_data = {
            "day_master": r_ws.get("day_master"),
            "de_ling": r_ws.get("de_ling"),
            "de_di": r_ws.get("de_di"),
            "de_shi": r_ws.get("de_shi"),
            "zonghe": r_ws.get("zonghe"),
        }

    # 4. 神煞
    r_ss = SS.compute(dt, lon)
    ss_data = {}
    if "error" not in r_ss:
        ss_data = r_ss.get("shensha", {})

    return {
        "input": {"datetime": dt_str, "gender": gender, "longitude": lon},
        "true_solar_time": r_m1["true_solar_time"],
        "day_master": dm,
        "pillars": r_m1["pillars"],
        "ten_gods": r_m1["ten_gods"],
        "dayun": {
            "direction": fwd,
            "qiyun": qy,
            "jie_time": jie,
            "jiao_time": jiao.strftime("%Y-%m-%d %H:%M") if isinstance(jiao, datetime) else str(jiao),
            "steps": dl,
        },
        "wangshuai": ws_data,
        "shensha": ss_data,
        "rule_sources": {
            "m1": "m1.py 四柱内核(立春换年/节换月/子正换日)",
            "dayun": "l3_bazi_daliu.py 起运数与顺逆大运",
            "wangshuai": "l3_wangshuai.py 得令得地得势综合权重",
            "shensha": "l3_shensha.py 23项主流神煞",
        },
    }


# ================================================================
# Tool 3: shushu_ziwei
# ================================================================
def shushu_ziwei(datetime_str, longitude=120.0, gender="男"):
    """十二宫、主星、辅星、煞星、生年四化、三方四正。"""
    dt = _parse_dt(datetime_str)
    lon = float(longitude)
    dt_str = dt.strftime("%Y-%m-%d %H:%M")

    zr = ZW.compute(dt, lon)
    if "error" in zr:
        return zr

    # 处理十二宫星曜分栏（主星、吉辅星、煞星）
    palaces_processed = []
    palace_map = {}
    for p in zr.get("palaces", []):
        p_name = p["name"]
        stars = p.get("stars", [])
        aux = p.get("aux", [])
        fuxing = [s for s in aux if s in FU_SET]
        shaxing = [s for s in aux if s in SHAS_SET]
        p_info = {
            "name": p_name,
            "zhi": p["zhi"],
            "gan": p["gan"],
            "ganzhi": p["gan"] + p["zhi"],
            "stars": stars,
            "fuxing": fuxing,
            "shaxing": shaxing,
            "aux_all": aux,
            "sihua": p.get("sihua", []),
            "shen": p.get("shen", False),
        }
        palaces_processed.append(p_info)
        palace_map[p_name] = p_info

    # 计算三方四正（每个宫位的 本宫、对宫、三合方一、三合方二）
    sanfang_sizheng = {}
    for i, name in enumerate(PALACE_NAMES_12):
        ben = name
        dui = PALACE_NAMES_12[(i + 6) % 12]
        he1 = PALACE_NAMES_12[(i + 4) % 12]
        he2 = PALACE_NAMES_12[(i + 8) % 12]
        scope = [ben, he1, dui, he2]
        
        scope_stars = []
        scope_fu = []
        scope_sha = []
        scope_sihua = []
        for p_name in scope:
            p_data = palace_map.get(p_name, {})
            scope_stars.extend(p_data.get("stars", []))
            scope_fu.extend(p_data.get("fuxing", []))
            scope_sha.extend(p_data.get("shaxing", []))
            scope_sihua.extend(p_data.get("sihua", []))

        sanfang_sizheng[name] = {
            "target_palace": name,
            "scope_palaces": scope,
            "structure": {
                "ben_gong": ben,
                "dui_gong": dui,
                "san_he_1": he1,
                "san_he_2": he2,
            },
            "stars_summary": {
                "main_stars": scope_stars,
                "fuxing": scope_fu,
                "shaxing": scope_sha,
                "sihua": scope_sihua,
            },
        }

    # 六大核心宫位三方四正视图（命宫、夫妻、财帛、官禄、迁移、福德）
    six_key_palaces = ["命宫", "夫妻", "财帛", "官禄", "迁移", "福德"]
    six_key_sanfang = {k: sanfang_sizheng[k] for k in six_key_palaces if k in sanfang_sizheng}

    # 紫微大限流年
    liunian_info = None
    try:
        zl = ZL.compute(dt, lon, gender=gender, target_year=dt.year)
        if "error" not in zl:
            liunian_info = zl
    except Exception as e:
        liunian_info = {"error": f"ziwei_liunian_error: {e}"}

    return {
        "input": {"datetime": dt_str, "gender": gender, "longitude": lon},
        "lunar": zr["lunar"],
        "minggong": zr["minggong"],
        "shengong": zr["shengong"],
        "wuxing_ju": zr["wuxing_ju"],
        "ziwei": zr.get("ziwei"),
        "sihua": zr["sihua"],
        "palaces": palaces_processed,
        "sanfang_sizheng": sanfang_sizheng,
        "c_six_key_palace_sanfang_sizheng": six_key_sanfang,
        "ziwei_liunian": liunian_info,
        "notes": zr.get("notes", []),
    }


# ================================================================
# Tool 4: shushu_qimen
# ================================================================
def shushu_qimen(datetime_str, longitude=120.0):
    """奇门转盘九宫、星门神仪、格局断局。"""
    dt = _parse_dt(datetime_str)
    lon = float(longitude)
    dt_str = dt.strftime("%Y-%m-%d %H:%M")

    # 1. 奇门排盘
    qm_pan = QM.compute(dt, lon)
    if "error" in qm_pan:
        return qm_pan

    # 2. 奇门断局（用神、格局、吉凶倾向）
    qm_dj = QMDJ.duanju(dt, lon=lon)
    dj_data = {}
    if isinstance(qm_dj, dict) and "error" not in qm_dj:
        dj_data = {
            "yongshen": qm_dj.get("yongshen"),
            "geju": qm_dj.get("geju"),
            "chubu": qm_dj.get("chubu"),
        }

    return {
        "input": {"datetime": dt_str, "longitude": lon},
        "pillars": qm_pan["pillars"],
        "true_solar_time": qm_pan["true_solar_time"],
        "dingju": qm_pan["dingju"],
        "month_jiang": qm_pan["month_jiang"],
        "zhifu_zhishi": qm_pan["zhifu_zhishi"],
        "sanqi_liuyi": qm_pan["sanqi_liuyi"],
        "nine_stars": qm_pan["nine_stars"],
        "eight_doors": qm_pan["eight_doors"],
        "eight_gods": qm_pan["eight_gods"],
        "pan": qm_pan["pan"],
        "duanju": dj_data,
    }


# ================================================================
# Tool 5: shushu_liuyao
# ================================================================
def shushu_liuyao(time_str=None, num1=None, num2=None, hour_num=None):
    """六爻起卦、纳甲、八宫六亲、六神、世应。"""
    dt = _parse_dt(time_str) if time_str else datetime.now().replace(second=0, microsecond=0)
    lon = 120.0

    if num1 is not None:
        # 数字报数起卦
        n1 = int(num1)
        single = (num2 is None)
        n2 = int(num2) if num2 is not None else 0
        
        # 确定时辰数（1-12）
        if hour_num is not None:
            h = int(hour_num)
        else:
            r_m1 = m1.compute(dt, lon)
            if "error" in r_m1:
                h = (dt.hour + 1) // 2 % 12 + 1
            else:
                h = rules.ZHI.index(r_m1["pillars"]["hour"]["ganzhi"][1]) + 1

        t = LY.number_nums(n1, n2, h, single=single)
        if isinstance(t, dict) and "error" in t:
            return t
        up, down, dong, nums = t
        label = "数字起卦·单数" if single else "数字起卦·双数（动爻加时辰）"
        res = LY._build(up, down, dong, dt, lon, label, nums)
        return res
    else:
        # 时间起卦（农历法）
        res = LY.compute(dt, lon=lon, mode="lunar")
        return res


# ================================================================
# Tool 6: shushu_hepan
# ================================================================
def shushu_hepan(dt1, gender1="男", lon1=120.0, dt2=None, gender2="女", lon2=120.0):
    """两人合盘互动分析。"""
    if not dt2:
        return {"error": "合盘需要双方出生时间 dt1 与 dt2"}
    
    dt1_parsed = _parse_dt(dt1).strftime("%Y-%m-%d %H:%M")
    dt2_parsed = _parse_dt(dt2).strftime("%Y-%m-%d %H:%M")
    lon_a = float(lon1) if lon1 is not None else 120.0
    lon_b = float(lon2) if lon2 is not None else 120.0

    res = HP.compute(
        dt1_parsed,
        dt2_parsed,
        lon_a=lon_a,
        lon_b=lon_b,
        scene="婚姻"
    )
    if isinstance(res, dict):
        res["gender_a"] = gender1
        res["gender_b"] = gender2
    return res


# ================================================================
# Tool 7: shushu_reconcile
# ================================================================
def shushu_reconcile(draft_text, snapshot_json):
    """运行 l4_audit_output.reconcile 对账，检查文本中是否存在数据幻觉、十神错位或分数漂移。"""
    if isinstance(snapshot_json, dict):
        snap = snapshot_json
    elif isinstance(snapshot_json, str):
        s_clean = snapshot_json.strip()
        if s_clean.startswith("{"):
            snap = json.loads(s_clean)
        elif os.path.isfile(s_clean):
            with open(s_clean, "r", encoding="utf-8") as f:
                snap = json.load(f)
        else:
            raise ValueError("snapshot_json 必须为 JSON 字符串、dict 对象或已存在的文件路径")
    else:
        raise ValueError(f"不支持的 snapshot_json 类型: {type(snapshot_json)}")

    rec = L4AO.reconcile(draft_text, snap)

    conflicts_count = len(rec.get("conflicts", []))
    unverified_count = len(rec.get("unverified", []))
    matched_count = len(rec.get("matched", []))

    return {
        "verdict": "PASS" if conflicts_count == 0 else "FAIL",
        "summary": {
            "conflicts_count": conflicts_count,
            "unverified_count": unverified_count,
            "matched_count": matched_count,
            "status": "PASS: 零数据冲突" if conflicts_count == 0 else f"FAIL: 存在 {conflicts_count} 处冲突，禁止出报告！",
        },
        "conflicts": rec.get("conflicts", []),
        "unverified": rec.get("unverified", []),
        "matched": rec.get("matched", []),
    }


# ================================================================
# Tool 8: shushu_bazi_geju
# ================================================================
def shushu_bazi_geju(dt=None, four_pillars=None, gender="男", lon=120.0, longitude=None):
    """判定八字格局（正八格、专旺格、从格、化气格、禄刃格）。"""
    from l3_bazi_geju import determine_bazi_geju
    if longitude is not None:
        lon = longitude
    if four_pillars is None:
        if dt is None:
            raise ValueError("必须提供 dt 或 four_pillars 参数")
        bazi_res = shushu_bazi(datetime_str=dt, longitude=lon, gender=gender)
        if isinstance(bazi_res, dict) and ("error" in bazi_res or "pillars" not in bazi_res):
            return bazi_res
        four_pillars = [
            bazi_res["pillars"]["year"]["ganzhi"],
            bazi_res["pillars"]["month"]["ganzhi"],
            bazi_res["pillars"]["day"]["ganzhi"],
            bazi_res["pillars"]["hour"]["ganzhi"],
        ]
    return determine_bazi_geju(four_pillars, gender)


# ================================================================
# Tool 9: shushu_jieqi_query
# ================================================================
def shushu_jieqi_query(year: int, term_name: str = None):
    """查询指定年份的二十四节气精确交节时刻（精确到秒，静态只读零 I/O）。"""
    all_terms = dst.get_terms_for_year(int(year))
    terms = [
        t for t in all_terms
        if term_name is None or t["term_name"] == term_name
    ]
    return {"year": int(year), "count": len(terms), "terms": terms}


# ================================================================
# Tool 10: shushu_calendar_convert
# ================================================================
def shushu_calendar_convert(solar_date: str = None, lunar_year: int = None, lunar_month: int = None, lunar_day: int = None, is_leap: bool = False):
    """公历与农历精准互转历法原语（静态只读零 I/O）。"""
    from datetime import date
    if solar_date:
        d = date.fromisoformat(solar_date[:10])
        shuo = dst.get_shuo_for_date(d)
        b = m1.compute(datetime(d.year, d.month, d.day, 12, 0), 120.0)
        return {
            "mode": "solar_to_lunar",
            "solar_date": solar_date,
            "lunar": {
                "lunar_year_gz": shuo["lunar_year_gz"],
                "lunar_month": shuo["lunar_month"],
                "lunar_day": shuo["lunar_day"],
                "is_leap": shuo["is_leap"],
            },
            "four_pillars": {
                "year": b["pillars"]["year"]["ganzhi"],
                "month": b["pillars"]["month"]["ganzhi"],
                "day": b["pillars"]["day"]["ganzhi"],
                "hour": b["pillars"]["hour"]["ganzhi"],
            },
        }
    else:
        sol_d = dst.lunar_to_solar_date(int(lunar_year), int(lunar_month), is_leap, int(lunar_day or 1))
        return {
            "mode": "lunar_to_solar",
            "lunar": {"year": lunar_year, "month": lunar_month, "day": lunar_day, "is_leap": is_leap},
            "solar_date": sol_d.isoformat(),
        }


# ================================================================
# Tool 11: shushu_timezone
# ================================================================
def shushu_timezone(wall_time: str, tz_name: str = "Asia/Shanghai", lon: float = 120.0, lat: float = 35.0, school: str = "astronomical"):
    """全球时区、夏令时回退与南半球排盘路由。"""
    from l1_timezone import resolve_global_time, resolve_southern_hemisphere_pillars
    clean_time = wall_time.strip()
    fmt = "%Y-%m-%d %H:%M:%S" if len(clean_time) > 16 else "%Y-%m-%d %H:%M"
    dt = datetime.strptime(clean_time, fmt)
    time_res = resolve_global_time(dt, tz_name, lon, lat)
    # 取换算后的基准北京时间（精确到分）传给 m1.compute
    bj_clean = time_res["beijing_time"][:16]
    bj_dt = datetime.strptime(bj_clean, "%Y-%m-%d %H:%M")
    b = m1.compute(bj_dt, lon)
    base_pillars = [
        b["pillars"]["year"]["ganzhi"],
        b["pillars"]["month"]["ganzhi"],
        b["pillars"]["day"]["ganzhi"],
        b["pillars"]["hour"]["ganzhi"],
    ]
    route_res = resolve_southern_hemisphere_pillars(base_pillars, lat, school)
    return {
        "time_resolution": time_res,
        "base_pillars": base_pillars,
        "resolved_pillars": route_res["pillars"],
        "school": route_res["school"],
        "description": route_res["description"],
    }


# ================================================================
# Tool 12: shushu_jinkoujue
# ================================================================
def shushu_jinkoujue(datetime_str: str = None, difen: str = "卯", day_gan: str = None, hour_zhi: str = None, month_jiang_zhi: str = None, month_zhi: str = None, longitude: float = 120.0):
    """大六壬金口诀推命排盘：四位（人元、贵神、将神、地分）、五动、三动、旺相休囚死与刑冲克害。"""
    if datetime_str:
        ctx = ShushuContext.build(datetime_str, longitude=longitude)
        d_gan = ctx.pillars.day.gan
        h_zhi = ctx.pillars.hour.zhi
        m_zhi = ctx.pillars.month.zhi
        curr_term = ctx.solar_term.current_term
        m_jiang = JKJ.YUE_JIANG_MAP.get(curr_term, ("亥", "登明"))[0]
        return JKJ.calculate_jinkoujue(
            day_gan=d_gan,
            hour_zhi=h_zhi,
            month_jiang_zhi=m_jiang,
            difen=difen,
            month_zhi=m_zhi,
        )
    elif day_gan and hour_zhi and month_jiang_zhi and difen:
        return JKJ.calculate_jinkoujue(
            day_gan=day_gan,
            hour_zhi=hour_zhi,
            month_jiang_zhi=month_jiang_zhi,
            difen=difen,
            month_zhi=month_zhi or "寅",
        )
    else:
        raise ValueError("必须提供 datetime_str 或提供完整的 (day_gan, hour_zhi, month_jiang_zhi, difen) 参数")


# ================================================================
# Tool 13: shushu_qizheng
# ================================================================
def shushu_qizheng(datetime_str: str, longitude: float = 120.0, latitude: float = 35.0, tz_name: str = "Asia/Shanghai"):
    """果老星宗七政四余（十一曜）星历、二十八宿 IAU J2000 真黄经入宿度与十二宫位。"""
    ctx = ShushuContext.build(datetime_str, longitude=longitude, latitude=latitude, tz_name=tz_name)
    qz_res = QZ.calculate_qizheng_siyu(ctx.utc_time)
    qz_res["context"] = {
        "wall_time": ctx.wall_time.strftime("%Y-%m-%d %H:%M"),
        "beijing_time": ctx.beijing_time.strftime("%Y-%m-%d %H:%M"),
        "true_solar_time": ctx.true_solar_time.strftime("%Y-%m-%d %H:%M"),
        "four_pillars": ctx.pillars.to_list(),
    }
    return qz_res


# ================================================================
# Tool 14: shushu_ziwei_yunxian
# ================================================================
def shushu_ziwei_yunxian(datetime_str: str, target_year: int, target_lunar_month: int = 1, target_lunar_day: int = 1, target_hour_zhi: str = "子", longitude: float = 120.0, gender: str = "男"):
    """紫微斗数多级运限与流曜飞星：流年斗君、流月/流日/流时命宫、流年九大动态流曜与流年四化。"""
    from datetime import date
    ctx = ShushuContext.build(datetime_str, longitude=longitude, gender=gender)
    birth_lunar_m = ctx.lunar_date.lunar_month
    birth_hour_z = ctx.pillars.hour.zhi
    mid_year = date(int(target_year), 6, 1)
    shuo_rec = dst.get_shuo_for_date(mid_year)
    ly_gz = shuo_rec["lunar_year_gz"]
    target_y_gan, target_y_zhi = ly_gz[0], ly_gz[1]
    res = ZWYX.get_full_ziwei_yunxian(
        birth_lunar_month=birth_lunar_m,
        birth_hour_zhi=birth_hour_z,
        target_year_gan=target_y_gan,
        target_year_zhi=target_y_zhi,
        lunar_month=int(target_lunar_month),
        lunar_day=int(target_lunar_day),
        query_hour_zhi=target_hour_zhi,
    )
    res["birth_info"] = {
        "solar_datetime": datetime_str,
        "birth_four_pillars": ctx.pillars.to_list(),
        "birth_lunar_month": birth_lunar_m,
        "birth_hour_zhi": birth_hour_z,
    }
    return res


# ================================================================
# Tool 15: shushu_shensha_ext
# ================================================================
def shushu_shensha_ext(datetime_str: str = None, four_pillars: list = None, lunar_month: int = None, gender: str = "男", longitude: float = 120.0):
    """50+ 扩展全谱命理神煞：三奇贵人紧贴裁定、太极、天赦、天医、十恶大败、阴阳差错、孤鸾、金神、丧门吊客等。"""
    if datetime_str:
        ctx = ShushuContext.build(datetime_str, longitude=longitude, gender=gender)
        fp = ctx.pillars.to_list()
        lm = ctx.lunar_date.lunar_month
    elif four_pillars:
        fp = four_pillars
        lm = lunar_month or 1
    else:
        raise ValueError("必须提供 datetime_str 或 four_pillars 参数")
    return SSE.compute_extended_shensha(four_pillars=fp, lunar_month=lm, gender=gender)


# ================================================================
# Tool 16: shushu_tieban
# ================================================================
def shushu_tieban(datetime_str: str = None, four_pillars: list = None, ke: int = 1, longitude: float = 120.0):
    """邵子神数 / 铁板神数算盘八刻滚盘取数：四柱太玄配数、考八刻分、考父母配偶兄弟功名寿元定数条文检索。"""
    if datetime_str:
        ctx = ShushuContext.build(datetime_str, longitude=longitude)
        fp = ctx.pillars.to_list()
    elif four_pillars:
        fp = four_pillars
    else:
        raise ValueError("必须提供 datetime_str 或 four_pillars 参数")
    return TBE.rolling_deduction(four_pillars=fp, ke=int(ke))


# ================================================================
# Tool 17: shushu_decision_simulate
# ================================================================
def shushu_decision_simulate(datetime_str: str, scenario: str = "career_track", profession_stage: str = "未定/通用", education_level: str = "高等教育/在读", gender: str = "男", longitude: float = 120.0):
    """现代战略决策树与心理原型推演：彻底废除封建迷信单点盲猜，基于三层能量释放管道评估体制大平台、商业创业与硬核技术等不同路径的契合度与致命陷阱。"""
    import l3_decision_tree as DT
    ctx = ShushuContext.build(datetime_str, longitude=longitude, gender=gender)
    anchor = {
        "profession_stage": profession_stage,
        "education_level": education_level,
    }
    if scenario == "relationship_strategy":
        return DT.simulate_relationship_dynamics(ctx.pillars.day.ganzhi, ctx.pillars.hour.ganzhi, gender)
    elif scenario == "archetype_spectrum":
        return DT.evaluate_archetype_spectrum(ctx.pillars.to_full_dict())
    else:  # career_track
        return DT.simulate_career_decision(ctx.pillars.to_list(), ctx.pillars.day_master, anchor)


# ================================================================
# MCP Tool 注册表定义
# ================================================================
TOOLS_REGISTRY = {
    "shushu_snapshot": {
        "func": shushu_snapshot,
        "description": "端到端全量术数快照：输出四柱、十神、大运、流年、紫微十二时辰全谱、奇门、称骨、神煞、旺衰、五运六气、六爻、六壬、梅花、河洛等确定性事实 Facts JSON。AI 撰写报告前必须作为首要基准数据源。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间，格式 'YYYY-MM-DD HH:MM'，如 '2006-06-25 00:30'",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "性别（影响大运顺逆排盘及称骨歌诀）",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "出生地东经经度（用于真太阳时子正换日计算），默认 120.0",
                },
            },
            "required": ["datetime_str"],
        },
    },
    "shushu_bazi": {
        "func": shushu_bazi,
        "description": "八字命理排盘：输出四柱干支、十神、地支藏干、8步大运干支与起止年份、日主旺衰评分（得令/得地/得势三得综合）及23项主流神煞命中表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间，格式 'YYYY-MM-DD HH:MM'",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "东经经度，默认 120.0",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "性别（男/女）",
                },
            },
            "required": ["datetime_str"],
        },
    },
    "shushu_ziwei": {
        "func": shushu_ziwei,
        "description": "紫微斗数排盘：输出命宫身宫、五行局、十二宫星曜排布（严格按主星、吉辅星、煞星分栏）、生年四化落宫、十二宫全谱三方四正合宫星系（scope）及大限流年。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间，格式 'YYYY-MM-DD HH:MM'",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "东经经度，默认 120.0",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "性别（男/女）",
                },
            },
            "required": ["datetime_str"],
        },
    },
    "shushu_qimen": {
        "func": shushu_qimen,
        "description": "时家奇门排盘与断局：拆补定局（阴阳遁局数、三元）、转盘九宫星门神仪排布、旬首值符值使、用神落宫定位、格局判定（吉格/凶格清单）及吉凶初步倾向。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "求测或起局北京时间，格式 'YYYY-MM-DD HH:MM'",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "东经经度，默认 120.0",
                },
            },
            "required": ["datetime_str"],
        },
    },
    "shushu_liuyao": {
        "func": shushu_liuyao,
        "description": "六爻排盘：支持时间起卦（农历梅花法）或报数起卦（单数/双数报数）、京房八宫本宫纳甲六亲、日干起六神、增删卜易世应诀定位、动爻变卦及月建日辰生克冲合。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "time_str": {
                    "type": "string",
                    "description": "起卦北京时间 'YYYY-MM-DD HH:MM'，不提供则使用当前系统时间",
                },
                "num1": {
                    "type": "integer",
                    "description": "数字起卦第一数（双数起卦时为上卦，单数起卦时为报数）",
                },
                "num2": {
                    "type": "integer",
                    "description": "数字起卦第二数（双数起卦时为下卦；单数起卦时不填）",
                },
                "hour_num": {
                    "type": "integer",
                    "description": "时辰序号 1-12（如子=1，丑=2...），留空则自动根据 time_str 推算",
                },
            },
        },
    },
    "shushu_hepan": {
        "func": shushu_hepan,
        "description": "两人合盘互动分析：分析两人天干五合相克、地支六合六冲三刑六害、日支夫妻宫互动、生肖亲和、年柱纳音五行生克、双方五行互补平衡及流年太岁引动。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dt1": {
                    "type": "string",
                    "description": "A方出生时间 'YYYY-MM-DD HH:MM' 或 'YYYY-MM-DD'",
                },
                "gender1": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "A方性别",
                },
                "lon1": {
                    "type": "number",
                    "default": 120.0,
                    "description": "A方出生地经度",
                },
                "dt2": {
                    "type": "string",
                    "description": "B方出生时间 'YYYY-MM-DD HH:MM' 或 'YYYY-MM-DD'",
                },
                "gender2": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "女",
                    "description": "B方性别",
                },
                "lon2": {
                    "type": "number",
                    "default": 120.0,
                    "description": "B方出生地经度",
                },
            },
            "required": ["dt1", "dt2"],
        },
    },
    "shushu_reconcile": {
        "func": shushu_reconcile,
        "description": "审计层强制对账门禁：在正式对外输出测算报告前调用。深度校验草稿文本中的干支溯源、大运十年区间错位、旺衰综合分值漂移、藏干十神日主映射、年龄与流年换算等，零冲突（conflicts=0）方可放行。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "draft_text": {
                    "type": "string",
                    "description": "待对账的测算报告草稿文本内容",
                },
                "snapshot_json": {
                    "description": "对应的确定性快照（可以是 JSON 字符串、dict 对象或快照文件路径）",
                },
            },
            "required": ["draft_text", "snapshot_json"],
        },
    },
    "shushu_bazi_geju": {
        "func": shushu_bazi_geju,
        "description": "八字格局自动化判定：基于《子平真诠》与《滴天髓》，自动识别正八格（正官/七杀/正印/偏印/正财/偏财/食神/伤官）、专旺格（曲直/炎上/稼穑/从革/润下）、从弱格（从儿/从财/从杀/从弱）、化气格（甲己化土等）及禄刃格（建禄/阳刃），输出判定证据链。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dt": {
                    "type": "string",
                    "description": "出生北京时间 'YYYY-MM-DD HH:MM'（与 four_pillars 二选一）",
                },
                "four_pillars": {
                    "description": "四柱干支，如 ['甲子', '丙寅', '戊辰', '丁巳'] 或 dict 对象",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                },
                "lon": {
                    "type": "number",
                    "default": 120.0,
                },
            },
        },
    },
    "shushu_jieqi_query": {
        "func": shushu_jieqi_query,
        "description": "历法原语——二十四节气精确交节时刻查询：基于高精天文历表，返回指定年份内节气交节的精确时刻（秒级，北京时间）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "year": {
                    "type": "integer",
                    "description": "查询年份（如 2024、2025、2026）",
                },
                "term_name": {
                    "type": "string",
                    "description": "指定节气名称（如 '立春'、'冬至'，可选）",
                },
            },
            "required": ["year"],
        },
    },
    "shushu_calendar_convert": {
        "func": shushu_calendar_convert,
        "description": "历法原语——公历与农历精准互转：支持公历转农历（含闰月、干支、生肖），以及农历转公历精确日历反查。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "solar_date": {
                    "type": "string",
                    "description": "公历日期 'YYYY-MM-DD'（用于公历转农历）",
                },
                "lunar_year": {
                    "type": "integer",
                    "description": "农历年份（用于农历转公历）",
                },
                "lunar_month": {
                    "type": "integer",
                    "description": "农历月份 1-12",
                },
                "lunar_day": {
                    "type": "integer",
                    "description": "农历日 1-30",
                },
                "is_leap": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否为闰月",
                },
            },
        },
    },
    "shushu_timezone": {
        "func": shushu_timezone,
        "description": "全球时区、历史夏令时与南半球排盘路由：自动识别并回退中国 1986-1991 夏令时及海外 IANA 时区，计算经度+均时差真太阳时，支持南半球派系 A（纯天文黄经不变）与派系 B（对冲月建五虎遁）动态仲裁。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wall_time": {
                    "type": "string",
                    "description": "当地钟表记录时间 'YYYY-MM-DD HH:MM'",
                },
                "tz_name": {
                    "type": "string",
                    "default": "Asia/Shanghai",
                    "description": "IANA 时区名称（如 'Asia/Shanghai'、'Australia/Sydney'、'America/New_York'）",
                },
                "lon": {
                    "type": "number",
                    "default": 120.0,
                    "description": "出生地经度",
                },
                "lat": {
                    "type": "number",
                    "default": 35.0,
                    "description": "出生地纬度（负数代表南半球）",
                },
                "school": {
                    "type": "string",
                    "enum": ["astronomical", "clash_month"],
                    "default": "astronomical",
                    "description": "南半球仲裁派系：'astronomical' 纯天文黄经派（默认），'clash_month' 对冲月建派",
                },
            },
            "required": ["wall_time"],
        },
    },
    "shushu_jinkoujue": {
        "func": shushu_jinkoujue,
        "description": "大六壬金口诀推命排盘：四位（人元、贵神、将神、地分）、五动克应、三动克应、旺相休囚死与地支刑冲克害。支持通过出生时间自动排课或直接指定四位地支。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "占卜时间 'YYYY-MM-DD HH:MM'（可选，自动求人元、贵神与月将）",
                },
                "difen": {
                    "type": "string",
                    "default": "卯",
                    "description": "地分地支（如 '子', '丑', '寅', '卯'...）",
                },
                "day_gan": {
                    "type": "string",
                    "description": "占日天干（手工模式使用，如 '甲'）",
                },
                "hour_zhi": {
                    "type": "string",
                    "description": "占时地支（手工模式使用，如 '午'）",
                },
                "month_jiang_zhi": {
                    "type": "string",
                    "description": "月将地支（手工模式使用，如 '亥' 登明）",
                },
                "month_zhi": {
                    "type": "string",
                    "description": "占月地支（手工模式使用，如 '寅'，用于旺相休囚死判别）",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "经度（时间模式使用，默认 120.0）",
                },
            },
        },
    },
    "shushu_qizheng": {
        "func": shushu_qizheng,
        "description": "果老星宗七政四余（十一曜）真黄经高精星历与二十八宿入宿度：输出太阳、太阴、五星、罗睺、计都、月孛、紫气之真视黄经、黄道十二宫落宫、度数及二十八宿 IAU J2000 真黄经入宿度。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "观测日期时间 'YYYY-MM-DD HH:MM'",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "观测地经度，默认 120.0",
                },
                "latitude": {
                    "type": "number",
                    "default": 35.0,
                    "description": "观测地纬度，默认 35.0",
                },
                "tz_name": {
                    "type": "string",
                    "default": "Asia/Shanghai",
                    "description": "时区名称，默认 Asia/Shanghai",
                },
            },
            "required": ["datetime_str"],
        },
    },
    "shushu_ziwei_yunxian": {
        "func": shushu_ziwei_yunxian,
        "description": "紫微斗数四级运限与动态流曜飞星：基于明刻《全书》斗君起正月诀，推导流年/流月/流日/流时四级命宫地支，排布流年禄存、擎羊、陀罗、魁钺、红鸾、天喜、天马、昌曲及流年四化。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间 'YYYY-MM-DD HH:MM'",
                },
                "target_year": {
                    "type": "integer",
                    "description": "流年年份（如 2026）",
                },
                "target_lunar_month": {
                    "type": "integer",
                    "default": 1,
                    "description": "流月农历月份 1-12，默认 1",
                },
                "target_lunar_day": {
                    "type": "integer",
                    "default": 1,
                    "description": "流日农历日 1-30，默认 1",
                },
                "target_hour_zhi": {
                    "type": "string",
                    "default": "子",
                    "description": "流时地支（如 '子', '丑'...），默认 '子'",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "东经经度，默认 120.0",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "性别",
                },
            },
            "required": ["datetime_str", "target_year"],
        },
    },
    "shushu_shensha_ext": {
        "func": shushu_shensha_ext,
        "description": "50+ 扩展商业与典籍高频神煞排盘：三奇贵人紧贴裁定、太极贵人、福星贵人、天赦日、天医、天厨、十恶大败、阴阳差错、金神、孤鸾煞、丧门、吊客、披麻煞等全谱检索。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间 'YYYY-MM-DD HH:MM'（与 four_pillars 二选一）",
                },
                "four_pillars": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "四柱干支数组，如 ['丙戌', '甲午', '乙酉', '丙子']",
                },
                "lunar_month": {
                    "type": "integer",
                    "description": "农历月份 1-12（用于天医神煞查询）",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "性别",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "经度，默认 120.0",
                },
            },
        },
    },
    "shushu_tieban": {
        "func": shushu_tieban,
        "description": "邵子神数 / 铁板神数算盘八刻滚盘取数：计算四柱八字太玄数总和，按八刻分卦（坤集96刻基数滚雪球推数），推导考父母生肖、考婚姻配偶、考兄弟姊妹、考功名事业、考寿元定数条文及经典原文检索。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间 'YYYY-MM-DD HH:MM'（与 four_pillars 二选一）",
                },
                "four_pillars": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "四柱干支数组，如 ['丙戌', '甲午', '乙酉', '丙子']",
                },
                "ke": {
                    "type": "integer",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 8,
                    "description": "一时八刻分纳八卦刻数（1乾、2兑、3离、4震、5巽、6坎、7艮、8坤），默认 1",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "经度，默认 120.0",
                },
            },
        },
    },
    "shushu_decision_simulate": {
        "func": shushu_decision_simulate,
        "description": "现代战略决策树与心理原型推演：彻底废除封建迷信单点盲猜，基于三层能量释放管道评估体制大平台、商业创业与硬核技术等不同路径的契合度与致命陷阱。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "出生北京时间 'YYYY-MM-DD HH:MM'",
                },
                "scenario": {
                    "type": "string",
                    "enum": ["career_track", "relationship_strategy", "archetype_spectrum"],
                    "default": "career_track",
                    "description": "模拟场景：职业赛道(career_track)、亲密关系(relationship_strategy)、心理原型矩阵(archetype_spectrum)",
                },
                "profession_stage": {
                    "type": "string",
                    "default": "未定/通用",
                    "description": "现实职业状态基线（如 '在读学生', '体制内/公职', '企业员工', '自由职业/创业'）",
                },
                "education_level": {
                    "type": "string",
                    "default": "高等教育/在读",
                    "description": "教育背景基线（如 '本科在读', '硕博深造', '已步入社会'）",
                },
                "gender": {
                    "type": "string",
                    "enum": ["男", "女"],
                    "default": "男",
                    "description": "性别",
                },
                "longitude": {
                    "type": "number",
                    "default": 120.0,
                    "description": "经度，默认 120.0",
                },
            },
            "required": ["datetime_str"],
        },
    },
}


# ================================================================
# MCP Server JSON-RPC 2.0 调度与运行
# ================================================================
def handle_jsonrpc_request(req):
    """处理单条 JSON-RPC 请求，返回响应 dict（或 None 表示无需回复的通知）。"""
    if not isinstance(req, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
        }

    req_id = req.get("id")
    method = req.get("method")

    # 通知 (Notification)：无 id
    if req_id is None and method in ("notifications/initialized", "$/cancelRequest"):
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "shushu-mcp-server",
                    "version": "1.0.0",
                    "description": "中国传统术数系统官方 MCP Server（防手推、抗幻觉、审计对账）",
                },
            },
        }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    elif method == "tools/list":
        tools_list = []
        for name, meta in TOOLS_REGISTRY.items():
            tools_list.append({
                "name": name,
                "description": meta["description"],
                "inputSchema": meta["inputSchema"],
            })
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools_list},
        }

    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name not in TOOLS_REGISTRY:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: '{tool_name}'",
                },
            }

        tool_meta = TOOLS_REGISTRY[tool_name]
        try:
            fn = tool_meta["func"]
            res = fn(**args)
            res_str = json.dumps(res, ensure_ascii=False, indent=2) if not isinstance(res, str) else res
            has_error = isinstance(res, dict) and "error" in res
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": res_str,
                        }
                    ],
                    "isError": has_error,
                },
            }
        except Exception as e:
            tb = traceback.format_exc()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tool Execution Error ({type(e).__name__}): {str(e)}\n{tb}",
                        }
                    ],
                    "isError": True,
                },
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: '{method}'",
            },
        }


def run_stdio_server():
    """以 stdio 方式运行 MCP Server"""
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line_clean = line.strip()
        if not line_clean:
            continue

        try:
            req = json.loads(line_clean)
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_jsonrpc_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


# ================================================================
# CLI 测试模式 (--test)
# ================================================================
def run_cli_test():
    """命令行自检测试套件：验证全部 7 个核心工具与 JSON-RPC 消息处理"""
    sys.stdout.reconfigure(encoding="utf-8")
    print("================================================================")
    print(" 传统术数官方标准 MCP Server 自检测试 (python mcp_server.py --test)")
    print("================================================================")

    dt_anchor = "2006-06-25 00:30"
    gender_anchor = "女"
    lon_anchor = 120.0

    passed = 0
    total = 0

    def t_assert(cond, name, msg=""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"  [PASS] {name}" + (f" -> {msg}" if msg else ""))
        else:
            print(f"  [FAIL] {name} -> {msg}")

    # 1. shushu_snapshot 测试
    try:
        snap = shushu_snapshot(dt_anchor, gender=gender_anchor, longitude=lon_anchor)
        t_assert(isinstance(snap, dict) and "pillars" in snap, "Tool 1: shushu_snapshot 返回格式正确",
                 f"四柱={snap['pillars']['year']}/{snap['pillars']['month']}/{snap['pillars']['day']}/{snap['pillars']['hour']}")
    except Exception as e:
        t_assert(False, "Tool 1: shushu_snapshot 异常", str(e))
        snap = {}

    # 2. shushu_bazi 测试
    try:
        bz = shushu_bazi(dt_anchor, longitude=lon_anchor, gender=gender_anchor)
        dm = bz.get("day_master")
        ws_score = bz.get("wangshuai", {}).get("zonghe", {}).get("score")
        t_assert(dm == "乙" and ws_score is not None, "Tool 2: shushu_bazi 核心字段正确",
                 f"日主={dm}, 旺衰分={ws_score}, 神煞数={bz.get('shensha', {}).get('hit_total')}")
    except Exception as e:
        t_assert(False, "Tool 2: shushu_bazi 异常", str(e))

    # 3. shushu_ziwei 测试
    try:
        zw = shushu_ziwei(dt_anchor, longitude=lon_anchor, gender=gender_anchor)
        ming = zw.get("minggong", {})
        c_six = zw.get("c_six_key_palace_sanfang_sizheng", {})
        t_assert(len(zw.get("palaces", [])) == 12 and "命宫" in c_six, "Tool 3: shushu_ziwei 十二宫与三方四正",
                 f"命宫干支={ming.get('gan')}{ming.get('zhi')}, 夫妻宫三方四正={c_six.get('夫妻', {}).get('scope_palaces')}")
    except Exception as e:
        t_assert(False, "Tool 3: shushu_ziwei 异常", str(e))

    # 4. shushu_qimen 测试
    try:
        qm = shushu_qimen(dt_anchor, longitude=lon_anchor)
        dj = qm.get("dingju", {})
        t_assert("pan" in qm and "yongshen" in qm.get("duanju", {}), "Tool 4: shushu_qimen 九宫与格局断局",
                 f"定局={dj.get('term')} {dj.get('dun')}{dj.get('ju')}局 {dj.get('yuan')}, 格局数={len(qm.get('duanju', {}).get('geju', []))}")
    except Exception as e:
        t_assert(False, "Tool 4: shushu_qimen 异常", str(e))

    # 5. shushu_liuyao 测试（时间起卦与数字起卦）
    try:
        ly_time = shushu_liuyao(time_str=dt_anchor)
        ly_num = shushu_liuyao(num1=3, num2=5, hour_num=6)
        t_assert("ben_gua" in ly_time and "ben_gua" in ly_num, "Tool 5: shushu_liuyao 时间/报数起卦",
                 f"时间卦={ly_time['ben_gua']['name']}->{ly_time['bian_gua']['name']}, 报数卦={ly_num['ben_gua']['name']}")
    except Exception as e:
        t_assert(False, "Tool 5: shushu_liuyao 异常", str(e))

    # 6. shushu_hepan 测试
    try:
        hp = shushu_hepan(dt_anchor, "女", 120.0, "2005-10-24 17:02", "男", 120.0)
        t_assert("hp-01" in hp and "hp-04" in hp, "Tool 6: shushu_hepan 两人合盘分析",
                 f"倾向={hp.get('hp-04', {}).get('tendency')}, 总分={hp.get('hp-04', {}).get('scores', {}).get('total')}")
    except Exception as e:
        t_assert(False, "Tool 6: shushu_hepan 异常", str(e))

    # 7. shushu_reconcile 测试（对账清零门禁）
    try:
        # 构造正常引用文本与篡改错位文本进行双向校验
        normal_text = "本造日主乙木，生于丙戌年、甲午月、乙酉日、丙子时。大运首步癸巳(2012-2021)偏印。"
        rec_pass = shushu_reconcile(normal_text, snap)
        t_assert(rec_pass["verdict"] == "PASS" and rec_pass["summary"]["conflicts_count"] == 0,
                 "Tool 7: shushu_reconcile 正常文本 PASS", f"matched={rec_pass['summary']['matched_count']}")

        # 错位文本测试（真实事故：手推误写大运序列错位）
        tampered_text = "大运甲午(2012-2021)伤官。"
        rec_fail = shushu_reconcile(tampered_text, snap)
        t_assert(rec_fail["verdict"] == "FAIL" and rec_fail["summary"]["conflicts_count"] > 0,
                 "Tool 7: shushu_reconcile 错位文本拦截 FAIL",
                 f"抓获冲突={rec_fail['conflicts'][0]['kind']}")
    except Exception as e:
        t_assert(False, "Tool 7: shushu_reconcile 异常", str(e))

    # 8. shushu_bazi_geju 测试
    try:
        geju_res = shushu_bazi_geju(dt_anchor, gender="女")
        t_assert("category" in geju_res and "pattern_name" in geju_res, "Tool 8: shushu_bazi_geju 八字格局判定",
                 f"格局={geju_res['pattern_name']} ({geju_res['category']})")
    except Exception as e:
        t_assert(False, "Tool 8: shushu_bazi_geju 异常", str(e))

    # 9. shushu_jieqi_query 测试
    try:
        jq_res = shushu_jieqi_query(2025, "立春")
        t_assert(jq_res["count"] >= 1 and "2025-02-03" in jq_res["terms"][0]["term_time"], "Tool 9: shushu_jieqi_query 节气查询",
                 f"2025立春时刻={jq_res['terms'][0]['term_time']}")
    except Exception as e:
        t_assert(False, "Tool 9: shushu_jieqi_query 异常", str(e))

    # 10. shushu_calendar_convert 测试
    try:
        cal_res = shushu_calendar_convert(solar_date="2024-02-10")
        t_assert(cal_res["lunar"]["lunar_month"] == 1 and cal_res["lunar"]["lunar_day"] == 1, "Tool 10: shushu_calendar_convert 公农历互转",
                 f"2024-02-10转农历={cal_res['lunar']['lunar_year_gz']}年正月初一")
    except Exception as e:
        t_assert(False, "Tool 10: shushu_calendar_convert 异常", str(e))

    # 11. shushu_timezone 测试
    try:
        tz_res = shushu_timezone(wall_time="1988-06-15 14:30", tz_name="Asia/Shanghai", lon=120.0, lat=31.2)
        t_assert(tz_res["time_resolution"]["is_dst"] is True and tz_res["time_resolution"]["standard_local_time"] == "1988-06-15 13:30:00",
                 "Tool 11: shushu_timezone 历史夏令时与全球路由", "自动扣减1小时夏令时并排盘")
    except Exception as e:
        t_assert(False, "Tool 11: shushu_timezone 异常", str(e))

    # 12. shushu_jinkoujue 测试
    try:
        jkj_res = shushu_jinkoujue(datetime_str=dt_anchor, difen="卯")
        t_assert("four_positions" in jkj_res and "wudong" in jkj_res, "Tool 12: shushu_jinkoujue 金口诀四位五动",
                 f"人元={jkj_res['four_positions']['renyuan']['gan']}, 贵神={jkj_res['four_positions']['guishen']['name']}")
    except Exception as e:
        t_assert(False, "Tool 12: shushu_jinkoujue 异常", str(e))

    # 13. shushu_qizheng 测试
    try:
        qz_res = shushu_qizheng(datetime_str=dt_anchor)
        t_assert("stars" in qz_res and "太阳" in qz_res["stars"], "Tool 13: shushu_qizheng 七政四余天星入宿度",
                 f"太阳宿度={qz_res['stars']['太阳']['mansion']}{qz_res['stars']['太阳']['degree_in_mansion']}度")
    except Exception as e:
        t_assert(False, "Tool 13: shushu_qizheng 异常", str(e))

    # 14. shushu_ziwei_yunxian 测试
    try:
        zwyx_res = shushu_ziwei_yunxian(datetime_str=dt_anchor, target_year=2026, gender="女")
        t_assert("limits" in zwyx_res and "liuyao" in zwyx_res, "Tool 14: shushu_ziwei_yunxian 紫微流年运限流曜",
                 f"斗君={zwyx_res['limits']['doujun']}, 流年四化={zwyx_res['liuyao']['liunian_sihua']}")
    except Exception as e:
        t_assert(False, "Tool 14: shushu_ziwei_yunxian 异常", str(e))

    # 15. shushu_shensha_ext 测试
    try:
        sse_res = shushu_shensha_ext(datetime_str=dt_anchor, gender="女")
        t_assert("pillar_shensha" in sse_res and "global_shensha" in sse_res, "Tool 15: shushu_shensha_ext 50+ 扩展神煞",
                 f"命中总神煞数={len(sse_res.get('global_shensha', []))}")
    except Exception as e:
        t_assert(False, "Tool 15: shushu_shensha_ext 异常", str(e))

    # 16. shushu_tieban 测试
    try:
        tb_res = shushu_tieban(datetime_str=dt_anchor, ke=1)
        t_assert("taixuan_total" in tb_res and "deduced_items" in tb_res, "Tool 16: shushu_tieban 邵子铁板滚盘算盘",
                 f"太玄总数={tb_res['taixuan_total']}, 考刻条文数={len(tb_res['deduced_items'])}")
    except Exception as e:
        t_assert(False, "Tool 16: shushu_tieban 异常", str(e))

    # 17. shushu_decision_simulate 测试
    try:
        dt_res = shushu_decision_simulate(datetime_str=dt_anchor, scenario="career_track")
        t_assert("pathways" in dt_res and "path_A_institutional" in dt_res["pathways"],
                 "Tool 17: shushu_decision_simulate 决策树推演",
                 f"体制契合度={dt_res['pathways']['path_A_institutional']['fit_score']}%")
    except Exception as e:
        t_assert(False, "Tool 17: shushu_decision_simulate 异常", str(e))

    # 18. JSON-RPC 协议测试 (initialize, tools/list, tools/call)
    try:
        init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        init_resp = handle_jsonrpc_request(init_req)
        t_assert(init_resp.get("result", {}).get("serverInfo", {}).get("name") == "shushu-mcp-server",
                 "JSON-RPC: initialize 响应正常")

        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        list_resp = handle_jsonrpc_request(list_req)
        t_assert(len(list_resp.get("result", {}).get("tools", [])) == 17,
                 "JSON-RPC: tools/list 包含全部 17 个工具")

        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "shushu_bazi",
                "arguments": {"datetime_str": dt_anchor, "gender": "女"}
            }
        }
        call_resp = handle_jsonrpc_request(call_req)
        t_assert(call_resp.get("result", {}).get("isError") is False,
                 "JSON-RPC: tools/call 执行并返回 text 内容")
    except Exception as e:
        t_assert(False, "JSON-RPC 协议处理异常", str(e))

    print("----------------------------------------------------------------")
    print(f"自检测试汇总: {passed}/{total} PASS")
    print("================================================================")
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="中国传统术数系统 MCP Server")
    parser.add_argument("--test", action="store_true", help="运行 CLI 单元自检测试套件")
    parser.add_argument("--stdio", action="store_true", help="启动 stdio MCP 服务（默认）")
    args = parser.parse_args()

    if args.test:
        run_cli_test()
    else:
        run_stdio_server()
