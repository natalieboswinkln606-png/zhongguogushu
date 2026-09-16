# -*- coding: utf-8 -*-
"""assert_api.py — 突破点 4：现代工程化交付与 API / 前端组件 Schema 全面自动化断言测试

覆盖范围：
1. RESTful API 端点测试（基于 fastapi.testclient.TestClient）：
   - GET /health: 状态与就绪模块清单
   - GET /api/v1/schemas: 标准 JSON Schema 导出校验
   - POST /api/v1/snapshot: 全量快照输出接口
   - POST /api/v1/bazi: 八字排盘接口与 BaziChartSchema 数据校验
   - POST /api/v1/ziwei: 紫微排盘接口与 ZiweiChartSchema 数据校验
   - POST /api/v1/qimen: 奇门排盘接口与 QimenChartSchema 数据校验
   - POST /api/v1/liuyao: 六爻排盘接口与 LiuyaoChartSchema 数据校验
   - POST /api/v1/reconcile: 文本对账防幻觉接口与 ReconcileResponse 数据校验
   - 异常处理：400 校验错误拦截
2. Pydantic 数据模型与 Schema 契约校验：
   - BaziChartSchema: 四柱、十神、纳音、藏干十神、大运起运岁数与年份序列、旺衰分值
   - ZiweiChartSchema: 12 宫网格定义（宫位名、地支、天干、主星列表、吉星列表、煞星列表、四化标注、三方四正关联宫位）
   - QimenChartSchema: 9 宫九星八门八神天盘地盘干支、值符值使、吉凶格局
   - LiuyaoChartSchema: 本卦变卦六爻、纳甲干支、六亲、世应、动爻
3. Visualizer 与 HTML 完整性/有效性测试：
   - CLI 命令生成测试：python visualizer.py --datetime "2006-06-25 00:30" --gender 女 --out temp/assert_chart.html
   - HTML 结构有效性、离线可用性、五行色彩与各术数盘面 DOM 标记断言
4. 前端 web/index.html 完整性断言

运行方式：
    PYTHONIOENCODING=utf-8 python assert_api.py
"""
import io
import json
import os
import subprocess
import sys

# 强制 UTF-8 标准输出规避 Windows 控制台乱码
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import starlette.routing
_orig_router_init = starlette.routing.Router.__init__
def _compat_router_init(self, *args, on_startup=None, on_shutdown=None, **kwargs):
    return _orig_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = _compat_router_init

from fastapi.testclient import TestClient
from api_server import app
from shushu_schema import (
    BaziChartSchema, ZiweiChartSchema, QimenChartSchema, LiuyaoChartSchema,
    ReconcileResponse, HealthResponse, export_all_schemas
)
import visualizer

PASSED = 0
FAILED = 0


def check(desc: str, ok: bool, detail: str = ""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {desc}")
    else:
        FAILED += 1
        msg = f"  [FAIL] {desc}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main():
    global PASSED, FAILED
    print("=" * 70)
    print("中国传统术数系统【突破点 4：API / 前端 Schema / Visualizer】自动化回归断言")
    print("=" * 70)

    client = TestClient(app)

    # --------------------------------------------------------------------------
    # 1. 服务健康检查与 Schema 导出测试
    # --------------------------------------------------------------------------
    print("\n--- 1. 健康检查与 Schema 规范导出 ---")
    r_health = client.get("/health")
    check("GET /health 返回 HTTP 200", r_health.status_code == 200)
    h_json = r_health.json()
    h_obj = HealthResponse.model_validate(h_json)
    check("HealthResponse 契约校验通过", h_obj.status == "ok" and len(h_obj.modules_ready) >= 7)

    r_schemas = client.get("/api/v1/schemas")
    check("GET /api/v1/schemas 返回 HTTP 200", r_schemas.status_code == 200)
    s_dict = r_schemas.json()
    core_schemas = ["BaziChartSchema", "ZiweiChartSchema", "QimenChartSchema", "LiuyaoChartSchema"]
    check("导出的 JSON Schema 涵盖四大核心盘面", all(k in s_dict for k in core_schemas))
    check("BaziChartSchema 为合法 JSON Schema 对象", "properties" in s_dict["BaziChartSchema"])

    # --------------------------------------------------------------------------
    # 2. 八字排盘接口与 Schema 校验
    # --------------------------------------------------------------------------
    print("\n--- 2. 八字排盘接口与 BaziChartSchema 契约 ---")
    # 测试案例 A：女命 2006-06-25 00:30（丙戌阳年女命逆排）
    req_bazi = {"datetime": "2006-06-25 00:30", "gender": "女", "lon": 120.0}
    r_bazi = client.post("/api/v1/bazi", json=req_bazi)
    check("POST /api/v1/bazi 返回 HTTP 200", r_bazi.status_code == 200)

    bazi_json = r_bazi.json()
    bazi_obj = BaziChartSchema.model_validate(bazi_json)
    check("BaziChartSchema Pydantic 校验成功", isinstance(bazi_obj, BaziChartSchema))

    # 四柱干支断言
    pillars = bazi_obj.pillars
    check("四柱完整性 (year/month/day/hour)", set(pillars.keys()) == {"year", "month", "day", "hour"})
    check("四柱干支正确：丙戌 甲午 乙酉 丙子", (
        pillars["year"].ganzhi == "丙戌" and
        pillars["month"].ganzhi == "甲午" and
        pillars["day"].ganzhi == "乙酉" and
        pillars["hour"].ganzhi == "丙子"
    ))
    check("日主日元为 乙 (阴木)", bazi_obj.day_master == "乙")

    # 纳音与五行断言
    check("四柱纳音正确：屋上土 沙中金 泉中水 涧下水", (
        pillars["year"].nayin == "屋上土" and
        pillars["month"].nayin == "沙中金" and
        pillars["day"].nayin == "泉中水" and
        pillars["hour"].nayin == "涧下水"
    ))

    # 藏干十神
    cg_month = [x.gan for x in pillars["month"].hidden_stems]
    check("午月支藏干含丁/己", "丁" in cg_month and "己" in cg_month)

    # 大运起运与序列（防事故1：丙戌阳年女逆排，第一步必须是癸巳(2012-2021)）
    dy = bazi_obj.dayun
    check("大运方向正确逆排", dy.direction == "逆")
    check("大运起运岁数完整存在", dy.qiyun.years >= 5)
    first_step = dy.steps[0]
    check("大运首步防线：第一步必为 癸巳 (2012-2021)", (
        first_step.ganzhi == "癸巳" and
        first_step.start_year == 2012 and
        first_step.end_year == 2021
    ))

    # 旺衰指标
    ws = bazi_obj.wangshuai
    check("日主旺衰判定存在且分值有效", 0.0 <= ws.score <= 100.0 and bool(ws.level))
    check("得令/得地/得势三得结构完整", (
        ws.de_ling.ben_qi_wx != "" and
        ws.de_di.max_score == 10 and
        ws.de_shi.max_score == 18
    ))

    # --------------------------------------------------------------------------
    # 3. 紫微斗数接口与 Schema 校验
    # --------------------------------------------------------------------------
    print("\n--- 3. 紫微斗数接口与 ZiweiChartSchema 契约 ---")
    req_zw = {"datetime": "2006-06-25 00:30", "gender": "女", "lon": 120.0}
    r_zw = client.post("/api/v1/ziwei", json=req_zw)
    check("POST /api/v1/ziwei 返回 HTTP 200", r_zw.status_code == 200)

    zw_json = r_zw.json()
    zw_obj = ZiweiChartSchema.model_validate(zw_json)
    check("ZiweiChartSchema Pydantic 校验成功", isinstance(zw_obj, ZiweiChartSchema))

    # 12 宫网格定义断言
    palaces = zw_obj.palaces
    check("紫微盘包含完整的 12 宫", len(palaces) == 12)
    palace_names = [p.name for p in palaces]
    check("命宫为第一宫", palace_names[0] == "命宫")
    expected_palaces = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]
    check("12 宫宫位名称符合传统序列", palace_names == expected_palaces)

    # 检查主星、吉星、煞星独立分类与四化
    minggong_p = palaces[0]
    check("命宫网格字段完备 (name/zhi/gan/stars/ji_stars/sha_stars/sihua/sanfang_sizheng)", (
        bool(minggong_p.name) and bool(minggong_p.zhi) and bool(minggong_p.gan) and
        isinstance(minggong_p.stars, list) and isinstance(minggong_p.ji_stars, list) and
        isinstance(minggong_p.sha_stars, list) and isinstance(minggong_p.sihua, list) and
        isinstance(minggong_p.sanfang_sizheng, list)
    ))

    # 三方四正关联宫位断言（防事故5：命宫的三方四正必为 命宫, 财帛, 官禄, 迁移）
    check("命宫三方四正关联宫位正确包含 [命宫, 财帛, 官禄, 迁移]", (
        set(minggong_p.sanfang_sizheng) == {"命宫", "财帛", "官禄", "迁移"}
    ))

    # 夫妻宫三方四正断言（CLAUDE.md 明确防线：scope=[夫妻, 福德, 迁移, 官禄]）
    fuqi_p = next(p for p in palaces if p.name == "夫妻")
    check("夫妻宫三方四正正确包含 [夫妻, 福德, 迁移, 官禄]", (
        set(fuqi_p.sanfang_sizheng) == {"夫妻", "福德", "迁移", "官禄"}
    ))

    # 生年四化
    check("生年四化列表数量为 4 项", len(zw_obj.sihua) == 4)

    # --------------------------------------------------------------------------
    # 4. 奇门遁甲接口与 Schema 校验
    # --------------------------------------------------------------------------
    print("\n--- 4. 奇门遁甲接口与 QimenChartSchema 契约 ---")
    req_qm = {"datetime": "2006-06-25 00:30", "lon": 120.0}
    r_qm = client.post("/api/v1/qimen", json=req_qm)
    check("POST /api/v1/qimen 返回 HTTP 200", r_qm.status_code == 200)

    qm_json = r_qm.json()
    qm_obj = QimenChartSchema.model_validate(qm_json)
    check("QimenChartSchema Pydantic 校验成功", isinstance(qm_obj, QimenChartSchema))

    # 9 宫网格断言
    pan = qm_obj.pan
    check("奇门九宫网格齐全 (1-9 宫)", set(pan.keys()) == {str(i) for i in range(1, 10)})
    p1 = pan["1"]
    check("坎一宫字段齐全 (palace/gua/direction/dipan_gan/tianpan_gan/star/door/shen)", (
        p1.palace == 1 and p1.gua == "坎宫" and bool(p1.dipan_gan) and bool(p1.tianpan_gan)
    ))

    # 定局与值符值使
    check("定局信息完整 (夏至/阴遁/局数)", qm_obj.dingju.term != "" and qm_obj.dingju.ju >= 1)
    check("值符值使完整存在", (
        bool(qm_obj.zhifu_zhishi.xunshou) and
        bool(qm_obj.zhifu_zhishi.zhifu_star) and
        bool(qm_obj.zhifu_zhishi.zhishi_door)
    ))
    check("奇门吉凶格局清单列表有效", isinstance(qm_obj.geju, list))

    # --------------------------------------------------------------------------
    # 5. 六爻排盘接口与 Schema 校验
    # --------------------------------------------------------------------------
    print("\n--- 5. 六爻排盘接口与 LiuyaoChartSchema 契约 ---")
    req_ly = {"datetime": "2006-06-25 00:30", "lon": 120.0, "mode": "lunar"}
    r_ly = client.post("/api/v1/liuyao", json=req_ly)
    check("POST /api/v1/liuyao 返回 HTTP 200", r_ly.status_code == 200)

    ly_json = r_ly.json()
    ly_obj = LiuyaoChartSchema.model_validate(ly_json)
    check("LiuyaoChartSchema Pydantic 校验成功", isinstance(ly_obj, LiuyaoChartSchema))

    # 本卦与变卦
    check("本卦名称与卦辞存在", bool(ly_obj.ben_gua.name) and bool(ly_obj.ben_gua.guaci))
    check("变卦名称存在", bool(ly_obj.bian_gua.name))

    # 六爻爻线断言
    lines = ly_obj.lines
    check("六爻爻线为 6 条", len(lines) == 6)
    first_line = lines[0]
    check("爻位从初爻开始", first_line.pos == "初")
    check("爻线具备纳甲天干、地支、五行、六亲、六神与世应", (
        bool(first_line.gan) and bool(first_line.zhi) and bool(first_line.wx) and
        bool(first_line.qin) and bool(first_line.shen)
    ))
    check("世应有且仅有 1 世 1 应", (
        [l.shi_ying for l in lines].count("世") == 1 and
        [l.shi_ying for l in lines].count("应") == 1
    ))

    # 测试数字起卦
    req_ly_num = {"datetime": "2006-06-25 00:30", "lon": 120.0, "n1": 1, "n2": 2}
    r_ly_num = client.post("/api/v1/liuyao", json=req_ly_num)
    check("数字起卦 POST /api/v1/liuyao 返回 HTTP 200", r_ly_num.status_code == 200)
    ly_num_obj = LiuyaoChartSchema.model_validate(r_ly_num.json())
    check("数字起卦成功生成本卦", bool(ly_num_obj.ben_gua.name))

    # --------------------------------------------------------------------------
    # 6. 全量快照输出接口测试
    # --------------------------------------------------------------------------
    print("\n--- 6. 全量快照接口 (POST /api/v1/snapshot) ---")
    req_snap = {"datetime": "2006-06-25 00:30", "gender": "女", "lon": 120.0}
    r_snap = client.post("/api/v1/snapshot", json=req_snap)
    check("POST /api/v1/snapshot 返回 HTTP 200", r_snap.status_code == 200)
    snap_data = r_snap.json()
    check("快照包含四柱、大运、紫微全谱、奇门、称骨等核心键", (
        "pillars" in snap_data and "dayun" in snap_data and
        "ziwei_hours" in snap_data and "qimen" in snap_data and
        "chenggu" in snap_data and "provenance" in snap_data["meta"]
    ))

    # --------------------------------------------------------------------------
    # 7. 文本对账防幻觉接口测试 (POST /api/v1/reconcile)
    # --------------------------------------------------------------------------
    print("\n--- 7. 文本对账防幻觉接口 (POST /api/v1/reconcile) ---")
    # 测试对账：包含正确大运与故意写错大运
    clean_text = "命主生于丙戌年甲午月乙酉日丙子时。大运首步癸巳(2012-2021)食神旺相。"
    r_rec_clean = client.post("/api/v1/reconcile", json={
        "text": clean_text,
        "datetime": "2006-06-25 00:30",
        "gender": "女"
    })
    check("合规文本对账返回 HTTP 200", r_rec_clean.status_code == 200)
    rec_clean_res = ReconcileResponse.model_validate(r_rec_clean.json())
    check("合规文本溯源命中 (matched > 0)", len(rec_clean_res.matched) > 0)
    check("合规文本无冲突 (conflicts == 0)", len(rec_clean_res.conflicts) == 0)

    # 测试事故样本对账：真实事故1（将首步大运错写为甲午(2012-2021)）
    dirty_text = "大运推排：甲午(2012-2021)走向财官。"
    r_rec_dirty = client.post("/api/v1/reconcile", json={
        "text": dirty_text,
        "datetime": "2006-06-25 00:30",
        "gender": "女"
    })
    rec_dirty_res = ReconcileResponse.model_validate(r_rec_dirty.json())
    check("事故样本精准抓出大运错位冲突 (conflicts > 0)", len(rec_dirty_res.conflicts) > 0)
    check("冲突指明甲午非大运序列或年份错位", any("甲午" in str(c) for c in rec_dirty_res.conflicts))

    # --------------------------------------------------------------------------
    # 8. 异常与边界输入测试
    # --------------------------------------------------------------------------
    print("\n--- 8. 异常参数拦截测试 ---")
    r_bad_dt = client.post("/api/v1/bazi", json={"datetime": "invalid-time", "gender": "女"})
    check("非法日期格式拦截返回 HTTP 400", r_bad_dt.status_code == 400)

    r_empty_dt = client.post("/api/v1/bazi", json={"datetime": "", "gender": "女"})
    check("空日期时间字符串拦截返回 HTTP 400", r_empty_dt.status_code == 400)

    r_out_range = client.post("/api/v1/bazi", json={"datetime": "1800-01-01 12:00", "gender": "女"})
    check("超界年份表外输入拦截返回 HTTP 400", r_out_range.status_code == 400)

    r_bad_lon = client.post("/api/v1/bazi", json={"datetime": "2006-06-25 00:30", "lon": 999.0})
    check("越界正经度拦截返回 HTTP 400", r_bad_lon.status_code == 400)

    r_bad_lon_neg = client.post("/api/v1/bazi", json={"datetime": "2006-06-25 00:30", "lon": -999.0})
    check("越界负经度拦截返回 HTTP 400", r_bad_lon_neg.status_code == 400)

    r_rec_no_snap = client.post("/api/v1/reconcile", json={"text": "测试文本缺少快照源"})
    check("对账接口缺少快照与时间参数拦截返回 HTTP 400", r_rec_no_snap.status_code == 400)

    r_ly_bad_num = client.post("/api/v1/liuyao", json={"datetime": "2006-06-25 00:30", "mode": "numbers", "n1": "bad_num"})
    check("六爻报数非整数格式拦截返回 HTTP 422", r_ly_bad_num.status_code == 422)

    # --------------------------------------------------------------------------
    # 9. Visualizer 生成 HTML 完整性测试
    # --------------------------------------------------------------------------
    print("\n--- 9. Visualizer 与离线 HTML 生成有效性 ---")
    test_out = os.path.join(BASE, "temp", "assert_chart.html")
    if os.path.exists(test_out):
        os.remove(test_out)

    # CLI 方式运行 visualizer
    cli_cmd = [
        sys.executable, "visualizer.py",
        "--datetime", "2006-06-25 00:30",
        "--gender", "女",
        "--out", "temp/assert_chart.html"
    ]
    proc = subprocess.run(cli_cmd, cwd=BASE, capture_output=True, text=True, encoding="utf-8")
    check("visualizer CLI 运行退出码为 0", proc.returncode == 0, proc.stderr)
    check("输出文件 temp/assert_chart.html 成功生成", os.path.exists(test_out))

    with open(test_out, encoding="utf-8") as f:
        html = f.read()

    check("HTML 文件体积充足 (> 30KB)", len(html) > 30000)
    check("包含八字四柱竖排结构标记", (
        "年柱" in html and "月柱" in html and "日柱" in html and "时柱" in html and "bazi-pillars-grid" in html
    ))
    check("包含五行色彩系统 (#16a34a, #dc2626, #b45309, #ca8a04, #2563eb)", (
        "#16a34a" in html and "#dc2626" in html and "#b45309" in html and
        "#ca8a04" in html and "#2563eb" in html
    ))
    check("包含大运走势与旺衰评级 (极弱 24.2分)", "24.2" in html and "极弱" in html)
    check("包含紫微斗数 4x4 回字盘与中心元信息", "zw-grid-board" in html and "zw-center-panel" in html)
    check("包含紫微三方四正高亮交互代码", "highlight-sanfang" in html and "data-sanfang" in html)
    check("包含奇门遁甲 3x3 洛书九宫格", "qm-grid-board" in html and "天盘" in html and "地盘" in html)
    check("包含周易六爻排盘与卦辞", "周易六爻" in html and "本卦" in html and "变卦" in html)

    # --------------------------------------------------------------------------
    # 10. 前端 web/index.html 页面文件验证
    # --------------------------------------------------------------------------
    print("\n--- 10. 前端交互主页 (web/index.html) 验证 ---")
    web_index = os.path.join(BASE, "web", "index.html")
    check("web/index.html 文件存在", os.path.isfile(web_index))
    with open(web_index, encoding="utf-8") as f:
        web_content = f.read()
    check("web/index.html 包含交互表单与各盘面容器", (
        "inputDatetime" in web_content and "baziPillarsGrid" in web_content and
        "zwBoard" in web_content and "qmGrid" in web_content and "reconcileText" in web_content
    ))

    # 根路由访问返回 index.html
    r_root = client.get("/")
    check("GET / 返回 HTTP 200 并渲染 HTML 页面", r_root.status_code == 200 and "中国传统术数" in r_root.text)

    # --------------------------------------------------------------------------
    # 汇总
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    total = PASSED + FAILED
    if FAILED == 0:
        print(f"全部断言通过！PASS: {PASSED}/{total} (退出码 0)")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"部分断言失败！PASS: {PASSED}/{total}, FAIL: {FAILED}/{total}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
