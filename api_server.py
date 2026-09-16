# -*- coding: utf-8 -*-
"""api_server.py — 中国传统术数系统 高性能 RESTful API 服务

基于 FastAPI 构建现代工程化交付 API，提供统一 JSON Schema 校验：
- POST /api/v1/snapshot: 全量快照输出接口
- POST /api/v1/bazi: 八字排盘接口
- POST /api/v1/ziwei: 紫微排盘接口
- POST /api/v1/qimen: 奇门排盘接口
- POST /api/v1/liuyao: 六爻排盘接口
- POST /api/v1/reconcile: 文本对账防幻觉接口
- GET /health: 健康检查接口
- GET /api/v1/schemas: 获取全部规范 JSON Schema
"""
import argparse
import csv
from datetime import datetime
from functools import lru_cache
import os
import sys
from typing import Any, Dict, List, Optional

import starlette.routing
_orig_router_init = starlette.routing.Router.__init__
def _compat_router_init(self, *args, on_startup=None, on_shutdown=None, **kwargs):
    return _orig_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = _compat_router_init

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

FastAPI.max_body_size = None

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import m1
import rules
import l3_bazi_daliu as BD
import l3_wangshuai as WS
import l3_ziwei as ZW
import l3_qimen as QM
import l3_qimen_duanju as QMDJ
import l3_liuyao as LY
import l4_audit_output as AO

from shushu_schema import (
    BaziChartSchema, BaziRequest,
    DayunSchema, DayunStepSchema,
    HiddenStemGodSchema, InputMetaSchema,
    LiuyaoChartSchema, LiuyaoGuaInfoSchema, LiuyaoLineSchema, LiuyaoRequest,
    PillarSchema, QimenChartSchema, QimenChubuSchema, QimenDingjuSchema,
    QimenGejuSchema, QimenPalaceSchema, QimenRequest, QimenZhifuZhishiSchema,
    QiyunAgeSchema, ReconcileRequest, ReconcileResponse,
    SnapshotRequest, WangshuaiDeDiItemSchema, WangshuaiDeDiSchema,
    WangshuaiDeLingSchema, WangshuaiDeShiSchema, WangshuaiSchema,
    WangshuaiZongheSchema, ZiweiChartSchema, ZiweiLunarSchema,
    ZiweiPalaceSchema, ZiweiRequest, ZiweiSihuaItemSchema,
    HealthResponse, export_all_schemas
)

app = FastAPI(
    title="Shushu Traditional Metaphysics API",
    description="中国传统术数现代化工程 API 引擎（八字、紫微、奇门、六爻、全量快照与对账）",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 基础辅助数据与函数
# ==============================================================================

JI_STARS = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马"}
SHA_STARS = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}


@lru_cache(maxsize=1)
def get_nayin_map() -> Dict[str, tuple]:
    """读取 nayin.csv，建立干支到 (纳音名, 纳音五行) 的映射"""
    nayin_file = os.path.join(BASE, "data", "nayin.csv")
    mapping = {}
    with open(nayin_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pair = row["ganzhi_pair"]
            name = row["wuxing_name"]
            wx = name[-1]
            if len(pair) == 4:
                mapping[pair[:2]] = (name, wx)
                mapping[pair[2:]] = (name, wx)
            else:
                mapping[pair] = (name, wx)
    return mapping


def parse_datetime(dt_str: str) -> datetime:
    """标准化解析 YYYY-MM-DD HH:MM"""
    try:
        return datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的日期时间格式 '{dt_str}'，应为 'YYYY-MM-DD HH:MM'。错误：{e}"
        )


# ==============================================================================
# 八字排盘组装逻辑
# ==============================================================================

def build_bazi_chart(dt: datetime, gender: str, lon: float) -> BaziChartSchema:
    m1_res = m1.compute(dt, lon)
    if "error" in m1_res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=m1_res["error"])

    dl_steps, y, mo, d, h, jie, jiao, fwd = BD.dayun(dt, lon, gender)
    ws_res = WS.compute(dt, lon)
    if "error" in ws_res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ws_res["error"])

    nayin_map = get_nayin_map()
    dm = m1_res["ten_gods"]["day_master"]
    cg_data = m1.load_canggan()

    # 1. 四柱组装
    pillars: Dict[str, PillarSchema] = {}
    canggan_gods_map: Dict[str, List[HiddenStemGodSchema]] = {}
    pillar_names = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}

    for key, cname in pillar_names.items():
        gz = m1_res["pillars"][key]["ganzhi"]
        gan, zhi = gz[0], gz[1]
        ny_name, ny_wx = nayin_map.get(gz, ("未知", "金"))
        wx_g = rules.wx_of_gan(gan)
        wx_z = rules.wx_of_zhi(zhi)

        # 天干十神
        if key == "day":
            stem_god = "日元"
        else:
            stem_god = m1_res["ten_gods"]["stems"].get(key, m1.ten_god(dm, gan))

        # 藏干十神
        hidden_stems = []
        for hidden_gan in cg_data.get(zhi, []):
            h_god = m1.ten_god(dm, hidden_gan)
            h_wx = rules.wx_of_gan(hidden_gan)
            h_rel = rules.rel(h_wx, rules.wx_of_gan(dm))
            hidden_stems.append(HiddenStemGodSchema(
                gan=hidden_gan,
                wx=h_wx,
                god=h_god,
                relation=h_rel
            ))
        canggan_gods_map[key] = hidden_stems

        rule_id = m1_res["pillars"][key].get("rule_id")
        source = m1_res["pillars"][key].get("source")

        pillars[key] = PillarSchema(
            name=cname,
            gan=gan,
            zhi=zhi,
            ganzhi=gz,
            wx_gan=wx_g,
            wx_zhi=wx_z,
            nayin=ny_name,
            nayin_wx=ny_wx,
            stem_god=stem_god,
            hidden_stems=hidden_stems,
            rule_id=rule_id,
            source=source
        )

    # 2. 大运组装
    dayun_steps_schema = []
    base_year = jiao.year
    birth_year = dt.year
    for step in dl_steps:
        s_idx = step["index"]
        s_gz = step["ganzhi"]
        sy = step["start_year"]
        ey = step["end_year"]
        dayun_steps_schema.append(DayunStepSchema(
            index=s_idx,
            ganzhi=s_gz,
            gan=s_gz[0],
            zhi=s_gz[1],
            god=step["god"],
            start_year=sy,
            end_year=ey,
            age_start=sy - birth_year,
            age_end=ey - birth_year
        ))

    dayun_schema = DayunSchema(
        direction=fwd,
        qiyun=QiyunAgeSchema(
            years=y,
            months=mo,
            days=d,
            hours=h,
            text=f"{y}岁{mo}个月{d}天{h}小时起运",
            jie_time=jie,
            jiao_time=jiao.strftime("%Y-%m-%d %H:%M")
        ),
        steps=dayun_steps_schema
    )

    # 3. 旺衰组装
    dl_data = ws_res["de_ling"]
    dd_data = ws_res["de_di"]
    ds_data = ws_res["de_shi"]
    zh_data = ws_res["zonghe"]

    de_di_items = [
        WangshuaiDeDiItemSchema(
            pillar=it["pillar"],
            zhi=it["zhi"],
            stage=it["stage"],
            root=it["root"],
            points=it["points"],
            weight=it["weight"]
        ) for it in dd_data["items"]
    ]

    wangshuai_schema = WangshuaiSchema(
        day_master=dm,
        score=zh_data["score"],
        level=zh_data["level"],
        advice=zh_data["advice"],
        de_ling=WangshuaiDeLingSchema(
            month_zhi=dl_data["month_zhi"],
            ben_qi=dl_data["ben_qi"],
            ben_qi_wx=dl_data["ben_qi_wx"],
            status=dl_data["status"],
            score=dl_data["score"]
        ),
        de_di=WangshuaiDeDiSchema(
            score=dd_data["score"],
            max_score=dd_data["max_score"],
            score_pct=dd_data["score_pct"],
            items=de_di_items
        ),
        de_shi=WangshuaiDeShiSchema(
            score=ds_data["score"],
            max_score=ds_data["max_score"],
            score_pct=ds_data["score_pct"]
        ),
        zonghe=WangshuaiZongheSchema(
            score=zh_data["score"],
            level=zh_data["level"],
            advice=zh_data["advice"],
            weights=zh_data["weights"],
            thresholds=zh_data["thresholds"]
        )
    )

    return BaziChartSchema(
        input=InputMetaSchema(
            datetime=dt.strftime("%Y-%m-%d %H:%M"),
            gender=gender,
            lon=lon,
            true_solar_time=m1_res["true_solar_time"]
        ),
        pillars=pillars,
        day_master=dm,
        ten_gods=m1_res["ten_gods"],
        nayin={k: v.nayin for k, v in pillars.items()},
        canggan_gods=canggan_gods_map,
        dayun=dayun_schema,
        wangshuai=wangshuai_schema
    )


# ==============================================================================
# 紫微斗数排盘组装逻辑
# ==============================================================================

def build_ziwei_chart(dt: datetime, lon: float, gender: str = "女") -> ZiweiChartSchema:
    zw_res = ZW.compute(dt, lon)
    if "error" in zw_res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=zw_res["error"])

    raw_palaces = zw_res["palaces"]
    palaces_by_name = {p["name"]: p for p in raw_palaces}

    # 计算三方四正与吉煞分类
    palace_schemas: List[ZiweiPalaceSchema] = []
    palace_order = ZW.PALACES  # 12 宫标准顺序（命宫起逆排）

    for i, name in enumerate(palace_order):
        p = palaces_by_name[name]
        aux_list = p.get("aux", [])

        # 吉星与煞星分离
        ji_list = [s for s in aux_list if s in JI_STARS]
        sha_list = [s for s in aux_list if s in SHA_STARS]

        # 三方四正：本宫(i), 三合一(i+4), 三合二(i+8), 对冲(i+6)
        sanfang_names = [
            palace_order[i],
            palace_order[(i + 4) % 12],
            palace_order[(i + 8) % 12],
            palace_order[(i + 6) % 12]
        ]
        sanfang_zhis = [palaces_by_name[pname]["zhi"] for pname in sanfang_names]

        palace_schemas.append(ZiweiPalaceSchema(
            name=name,
            zhi=p["zhi"],
            gan=p["gan"],
            stars=p.get("stars", []),
            ji_stars=ji_list,
            sha_stars=sha_list,
            sihua=p.get("sihua", []),
            sanfang_sizheng=sanfang_names,
            sanfang_sizheng_zhi=sanfang_zhis,
            shen=bool(p.get("shen", False))
        ))

    sihua_list = [
        ZiweiSihuaItemSchema(star=it["star"], hua=it["hua"])
        for it in zw_res["sihua"]["items"]
    ]

    lunar_dict = zw_res["lunar"]

    return ZiweiChartSchema(
        input=InputMetaSchema(
            datetime=dt.strftime("%Y-%m-%d %H:%M"),
            gender=gender,
            lon=lon
        ),
        lunar=ZiweiLunarSchema(
            year=lunar_dict["year"],
            month=lunar_dict["month"],
            month_name=lunar_dict["month_name"],
            day=lunar_dict["day"],
            is_ruen=lunar_dict["is_ruen"]
        ),
        shichen_zhi=zw_res["shichen"]["zhi"],
        minggong=zw_res["minggong"],
        shengong=zw_res["shengong"],
        wuxing_ju=zw_res["wuxing_ju"],
        ziwei_star=zw_res["ziwei"],
        sihua=sihua_list,
        palaces=palace_schemas
    )


# ==============================================================================
# 奇门遁甲排盘组装逻辑
# ==============================================================================

def build_qimen_chart(dt: datetime, lon: float) -> QimenChartSchema:
    qm_res = QM.compute(dt, lon)
    if "error" in qm_res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=qm_res["error"])

    geju_res = QMDJ.geju(qm_res)
    chubu_res = QMDJ.chubu(geju_res, qm_res)

    # 组装 9 宫
    pan_dict: Dict[str, QimenPalaceSchema] = {}
    for p_str, c in qm_res["pan"].items():
        pan_dict[p_str] = QimenPalaceSchema(
            palace=c["palace"],
            gua=c["gua"],
            direction=c["direction"],
            dipan_gan=c["dipan_gan"],
            tianpan_gan=c["tianpan_gan"],
            star=c.get("star"),
            door=c.get("door"),
            shen=c.get("shen")
        )

    # 组装格局
    geju_list: List[QimenGejuSchema] = []
    for g in geju_res:
        geju_list.append(QimenGejuSchema(
            id=g["id"],
            name=g["name"],
            type=g["type"],
            palace=str(g["palace"]),
            basis=g["basis"],
            source=g.get("source")
        ))

    dj = qm_res["dingju"]
    zz = qm_res["zhifu_zhishi"]

    return QimenChartSchema(
        input=InputMetaSchema(
            datetime=dt.strftime("%Y-%m-%d %H:%M"),
            lon=lon,
            true_solar_time=qm_res["true_solar_time"]
        ),
        pillars={k: v["ganzhi"] for k, v in qm_res["pillars"].items()},
        dingju=QimenDingjuSchema(
            term=dj["term"],
            dun=dj["dun"],
            yuan=dj["yuan"],
            ju=dj["ju"]
        ),
        zhifu_zhishi=QimenZhifuZhishiSchema(
            xunshou=zz["xunshou"],
            yiyi=zz["yiyi"],
            zhifu_star=zz["zhifu_star"],
            zhifu_palace=zz["zhifu_palace"],
            zhishi_door=zz["zhishi_door"],
            zhishi_palace=zz["zhishi_palace"]
        ),
        month_jiang=qm_res.get("month_jiang"),
        pan=pan_dict,
        geju=geju_list,
        chubu=QimenChubuSchema(
            verdict=chubu_res["verdict"],
            level=chubu_res["level"],
            ji_count=chubu_res["ji_count"],
            xiong_count=chubu_res["xiong_count"],
            xiong_palaces=chubu_res["xiong_palaces"]
        )
    )


# ==============================================================================
# 六爻排盘组装逻辑
# ==============================================================================

def build_liuyao_chart(dt: datetime, lon: float, mode: str = "lunar",
                      n1: Optional[int] = None, n2: Optional[int] = None) -> LiuyaoChartSchema:
    if n1 is not None:
        ly_res = LY.compute_numbers(n1, n2, dt, lon=lon, single=(n2 is None))
    else:
        ly_res = LY.compute(dt, lon=lon, mode=mode)

    if "error" in ly_res:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ly_res["error"])

    lines_schema: List[LiuyaoLineSchema] = []
    dong_indices: List[int] = []

    for i, line in enumerate(ly_res["lines"]):
        is_dong = bool(line.get("dong", False))
        if is_dong:
            dong_indices.append(i + 1)
        lines_schema.append(LiuyaoLineSchema(
            pos=line["pos"],
            yao=line["yao"],
            shen=line["shen"],
            qin=line["qin"],
            gan=line["gan"],
            zhi=line["zhi"],
            wx=line["wx"],
            shi_ying=line.get("shi_ying", ""),
            dong=is_dong,
            bian_yao=line["bian_yao"],
            bian_qin=line["bian_qin"],
            bian_gan=line["bian_gan"],
            bian_zhi=line["bian_zhi"],
            bian_wx=line["bian_wx"],
            bian_shi_ying=line.get("bian_shi_ying", "")
        ))

    bg = ly_res["ben_gua"]
    vg = ly_res["bian_gua"]

    return LiuyaoChartSchema(
        input=ly_res["input"],
        method=ly_res["method"],
        yue_jian=ly_res["yue_jian"],
        ri_chen=ly_res["ri_chen"],
        ben_gua=LiuyaoGuaInfoSchema(
            name=bg["name"],
            palace=bg["palace"],
            order=bg.get("gua_order", bg.get("order", 1)),
            guaci=bg["guaci"],
            up=bg["up"],
            down=bg["down"],
            lines=bg.get("yaoxiang", bg.get("lines", ""))
        ),
        bian_gua=LiuyaoGuaInfoSchema(
            name=vg["name"],
            palace=vg["palace"],
            order=vg.get("gua_order", vg.get("order", 1)),
            guaci=vg["guaci"],
            up=vg["up"],
            down=vg["down"],
            lines=vg.get("yaoxiang", vg.get("lines", ""))
        ),
        lines=lines_schema,
        dong_yao=dong_indices
    )


# ==============================================================================
# RESTful API 端点定义
# ==============================================================================

@app.get("/health", response_model=HealthResponse, summary="服务健康检查")
def health_check():
    """返回服务运行状态、版本信息与就绪的术数模块清单"""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        modules_ready=[
            "m1_four_pillars",
            "l3_bazi_daliu",
            "l3_wangshuai",
            "l3_ziwei",
            "l3_qimen",
            "l3_qimen_duanju",
            "l3_liuyao",
            "l4_audit_output"
        ]
    )


@app.get("/api/v1/schemas", summary="获取全部 JSON Schema 规范")
def get_schemas():
    """获取八字、紫微、奇门、六爻等全部规范 JSON Schema"""
    return export_all_schemas()


@app.post("/api/v1/snapshot", summary="全量快照输出接口")
def api_snapshot(req: SnapshotRequest):
    """根据出生时间生成全量快照 JSON（含四柱、十神、大运、流年、紫微十二时辰全谱、奇门、称骨等）"""
    snap = AO.snapshot(
        dt_str=req.datetime,
        gender=req.gender,
        lon=req.lon,
        ziwei_target_year=req.ziwei_target_year
    )
    if "error" in snap:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=snap["error"])
    return snap


@app.post("/api/v1/bazi", response_model=BaziChartSchema, summary="八字排盘接口")
def api_bazi(req: BaziRequest):
    """四柱排盘：四柱、十神、纳音、藏干十神、大运起运岁数与年份序列、旺衰分值"""
    dt = parse_datetime(req.datetime)
    return build_bazi_chart(dt, req.gender, req.lon)


@app.post("/api/v1/ziwei", response_model=ZiweiChartSchema, summary="紫微排盘接口")
def api_ziwei(req: ZiweiRequest):
    """紫微斗数排盘：12 宫网格定义、主星/吉星/煞星、生年四化、三方四正关联宫位"""
    dt = parse_datetime(req.datetime)
    return build_ziwei_chart(dt, req.lon, req.gender or "女")


@app.post("/api/v1/qimen", response_model=QimenChartSchema, summary="奇门排盘接口")
def api_qimen(req: QimenRequest):
    """时家奇门排盘：9 宫九星八门八神天盘地盘干支、值符值使、吉凶格局"""
    dt = parse_datetime(req.datetime)
    return build_qimen_chart(dt, req.lon)


@app.post("/api/v1/liuyao", response_model=LiuyaoChartSchema, summary="六爻排盘接口")
def api_liuyao(req: LiuyaoRequest):
    """六爻排盘：本卦变卦六爻、纳甲干支、六亲、世应、动爻"""
    dt = parse_datetime(req.datetime)
    return build_liuyao_chart(dt, req.lon, mode=req.mode, n1=req.n1, n2=req.n2)


@app.post("/api/v1/reconcile", response_model=ReconcileResponse, summary="文本对账防幻觉接口")
def api_reconcile(req: ReconcileRequest):
    """文本对账防幻觉：针对结论草稿文本，对照快照严格核验干支溯源、大运配年、旺衰漂移与双源同引"""
    snap = req.snapshot
    if not snap:
        if not req.datetime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供已落盘快照对象 'snapshot'，或者提供 'datetime' 参数以即时生成快照"
            )
        snap = AO.snapshot(req.datetime, req.gender or "女", req.lon or 120.0)
        if "error" in snap:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=snap["error"])

    rec = AO.reconcile(req.text, snap)
    return ReconcileResponse(
        matched=rec.get("matched", []),
        unverified=rec.get("unverified", []),
        conflicts=rec.get("conflicts", [])
    )


# ==============================================================================
# 静态资源与主页挂载
# ==============================================================================

WEB_DIR = os.path.join(BASE, "web")
if os.path.isdir(WEB_DIR):
    app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")


@app.get("/", response_class=HTMLResponse, summary="首页可视化交互界面")
def root_index():
    """打开交互式前端 UI"""
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h2>Shushu API Server is running.</h2><p>Visit <a href='/docs'>/docs</a> for OpenAPI specification.</p>"
    )


# ==============================================================================
# CLI 主入口
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="中国传统术数 API Server")
    parser.add_argument("--host", default="127.0.0.1", help="绑定主机IP（默认 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8000, help="服务端口（默认 8000）")
    parser.add_argument("--reload", action="store_true", help="启用热重载")
    args = parser.parse_args()

    import uvicorn
    print(f"正在启动 Shushu API Server -> http://{args.host}:{args.port}")
    uvicorn.run("api_server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
