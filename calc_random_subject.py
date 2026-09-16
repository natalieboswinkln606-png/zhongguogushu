# -*- coding: utf-8 -*-
"""
calc_random_subject.py — 针对随机测试样本进行全谱术数极致深度推演
样本参数：1996-01-22 12:10 北京时间，男，出生地广州 (113.27°E, 23.13°N)
"""
import json
import os
import sys
from datetime import datetime

BASE = r"D:\shushu"
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import mcp_server as M
from shushu_context import ShushuContext

DT_STR = "1996-01-22 12:10"
GENDER = "男"
LON = 113.27
LAT = 23.13

results = {}

# Step 1: 时空基准与历法对账
ctx = ShushuContext.build(DT_STR, longitude=LON, latitude=LAT, gender=GENDER)
results["step1_context"] = {
    "wall_time": str(ctx.wall_time),
    "utc_time": str(ctx.utc_time),
    "beijing_time": str(ctx.beijing_time),
    "true_solar_time": str(ctx.true_solar_time),
    "longitude": ctx.longitude,
    "latitude": ctx.latitude,
    "is_dst": ctx.is_dst,
    "dst_offset_minutes": ctx.dst_offset_minutes,
    "solar_term": {
        "current_term": ctx.solar_term.current_term,
        "current_term_time": ctx.solar_term.current_term_time,
        "current_jie_zhong": ctx.solar_term.current_jie_zhong,
        "next_term": ctx.solar_term.next_term,
        "next_term_time": ctx.solar_term.next_term_time,
    },
    "lunar": {
        "lunar_year_gz": ctx.lunar_date.lunar_year_gz,
        "lunar_year": ctx.lunar_date.lunar_year,
        "lunar_month": ctx.lunar_date.lunar_month,
        "lunar_day": ctx.lunar_date.lunar_day,
        "is_leap": ctx.lunar_date.is_leap,
        "shuo_date": ctx.lunar_date.shuo_date,
    }
}

# Step 2: 四柱八字、十神藏干、纳音五行与格局判定
bazi_res = M.shushu_bazi(DT_STR, longitude=LON, gender=GENDER)
geju_res = M.shushu_bazi_geju(DT_STR, longitude=LON, gender=GENDER)
results["step2_bazi_and_geju"] = {
    "pillars_list": ctx.pillars.to_list(),
    "pillars_full": ctx.pillars.to_full_dict(),
    "day_master": ctx.pillars.day_master,
    "geju": geju_res,
}

# Step 3: 日主旺衰综合评分与顺逆大运排盘
results["step3_wangshuai_and_dayun"] = {
    "wangshuai": bazi_res.get("wangshuai"),
    "dayun": bazi_res.get("dayun"),
}

# Step 4: 全谱神煞矩阵 (基础 23 项 + 扩展 50+ 项)
shensha_basic = bazi_res.get("shensha")
shensha_ext = M.shushu_shensha_ext(DT_STR, longitude=LON, gender=GENDER)
results["step4_shensha"] = {
    "basic": shensha_basic,
    "extended": shensha_ext,
}

# Step 5: 紫微斗数排盘 (命身宫、五行局、十二宫星曜排布、生年四化、三方四正合宫星系)
ziwei_res = M.shushu_ziwei(DT_STR, longitude=LON, gender=GENDER)
results["step5_ziwei"] = ziwei_res

# Step 6: 紫微斗数多级运限与动态流曜 (2026年流年)
ziwei_yunxian_res = M.shushu_ziwei_yunxian(DT_STR, target_year=2026, target_lunar_month=1, target_lunar_day=1, target_hour_zhi="子", longitude=LON, gender=GENDER)
results["step6_ziwei_yunxian"] = ziwei_yunxian_res

# Step 7: 时家奇门遁甲转盘排盘
qimen_res = M.shushu_qimen(DT_STR, longitude=LON)
results["step7_qimen"] = qimen_res

# Step 8: 大六壬金口诀推命排盘
jinkoujue_res = M.shushu_jinkoujue(datetime_str=DT_STR, difen="卯", longitude=LON)
results["step8_jinkoujue"] = jinkoujue_res

# Step 9: 果老星宗七政四余天星算力
qizheng_res = M.shushu_qizheng(DT_STR, longitude=LON, latitude=LAT)
results["step9_qizheng"] = qizheng_res

# Step 10: 邵子神数 / 铁板神数八刻滚盘算盘算法
tieban_res = M.shushu_tieban(DT_STR, ke=1, longitude=LON)
results["step10_tieban"] = tieban_res

# Step 11: 综合全景事实快照
snap_res = M.shushu_snapshot(DT_STR, gender=GENDER, longitude=LON)
results["step11_snapshot"] = snap_res

out_path = os.path.join(BASE, "temp", "random_subject_full_deduction.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Successfully calculated all 11 steps -> {out_path}")
