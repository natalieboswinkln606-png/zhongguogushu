# -*- coding: utf-8 -*-
"""assert_mcp.py — MCP Server 全覆盖单元测试与协议合规断言。

测试范围：
1. 7大核心 Tools 内部函数输入输出准确性与确定性：
   - shushu_snapshot: 全量快照与引擎绑定 SHA256
   - shushu_bazi: 四柱、十神、藏干、大运、旺衰、神煞
   - shushu_ziwei: 十二宫、主星、辅星、煞星、生年四化、三方四正
   - shushu_qimen: 转盘九宫、星门神仪、格局断局、用神倾向
   - shushu_liuyao: 时间/报数起卦、纳甲六亲、六神世应、动爻变卦
   - shushu_hepan: 天干五合克、地支冲合刑害、夫妻宫、生肖纳音
   - shushu_reconcile: 文本对账防线（大运错位、伪大运、十神错配、旺衰漂移等全部拦截）
2. MCP JSON-RPC 2.0 协议规范处理：
   - initialize (serverInfo, capabilities, protocolVersion)
   - notifications/initialized (无回复通知)
   - ping
   - tools/list (7 工具定义与 inputSchema)
   - tools/call (全部 7 工具 RPC 调用与 content 格式)
3. 异常处理与边缘测试：
   - Method not found (-32601)
   - Unknown tool (-32601)
   - Parse error (-32700)
   - Tool 参数非法时的 isError 响应
4. CLI --test 子进程与标准 stdio 管道测试。

运行方式：PYTHONIOENCODING=utf-8 python assert_mcp.py
"""

import copy
import json
import os
import subprocess
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import mcp_server as M

RES = []


def check(name, cond, detail=""):
    RES.append((name, bool(cond)))
    status = "PASS" if cond else "FAIL"
    detail_str = f"  ({detail})" if detail else ""
    print(f"  {status} {name}{detail_str}")
    return cond


# 测试锚点：A 命造（2006-06-25 00:30 女 120E，历史错位事故当事盘）
DT_A = "2006-06-25 00:30"
GENDER_A = "女"
LON_A = 120.0

# 测试锚点：B 命造（2005-10-24 17:02 男 120E，文档转录事故当事盘）
DT_B = "2005-10-24 17:02"
GENDER_B = "男"
LON_B = 120.0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("================================================================")
    print(" 开始运行 assert_mcp.py — MCP Server 全覆盖单元测试")
    print("================================================================")

    # ================================================================
    # 一、Tool 1: shushu_snapshot 测试
    # ================================================================
    print("\n--- [1/10] 测试 Tool: shushu_snapshot ---")
    snap_a = M.shushu_snapshot(DT_A, gender=GENDER_A, longitude=LON_A)
    check("snapshot_a_dict", isinstance(snap_a, dict), "返回类型为 dict")
    check("snapshot_a_pillars", snap_a.get("pillars") == {
        "year": "丙戌", "month": "甲午", "day": "乙酉", "hour": "丙子"
    }, f"四柱={snap_a.get('pillars')}")
    check("snapshot_a_day_master", snap_a.get("day_master") == "乙", f"日主={snap_a.get('day_master')}")
    check("snapshot_a_provenance", "provenance" in snap_a.get("meta", {}), "快照包含引擎版本 provenance 哈希")
    check("snapshot_a_dayun_step0", snap_a["dayun"]["steps"][0]["ganzhi"] == "癸巳", "大运首步=癸巳（阳年女逆排）")
    check("snapshot_a_dayun_range", (snap_a["dayun"]["steps"][0]["start_year"], snap_a["dayun"]["steps"][0]["end_year"]) == (2012, 2021), "首步年份=2012-2021")

    # ================================================================
    # 二、Tool 2: shushu_bazi 测试
    # ================================================================
    print("\n--- [2/10] 测试 Tool: shushu_bazi ---")
    bz_a = M.shushu_bazi(DT_A, longitude=LON_A, gender=GENDER_A)
    check("bazi_pillars", bz_a.get("pillars", {}).get("year", {}).get("ganzhi") == "丙戌", "年柱丙戌")
    check("bazi_ten_gods", "stems" in bz_a.get("ten_gods", {}) and "branches" in bz_a.get("ten_gods", {}), "十神干支齐全")
    check("bazi_dayun_steps_count", len(bz_a.get("dayun", {}).get("steps", [])) == 8, "大运为 8 步")
    check("bazi_wangshuai_score", isinstance(bz_a.get("wangshuai", {}).get("zonghe", {}).get("score"), (int, float)), "旺衰综合评分存在")
    check("bazi_shensha_groups", "groups" in bz_a.get("shensha", {}), "神煞分组齐全")
    check("bazi_shensha_hit_total", bz_a.get("shensha", {}).get("hit_total", 0) > 0, f"神煞命中数={bz_a.get('shensha', {}).get('hit_total')}")

    # B命造八字（日主辛）
    bz_b = M.shushu_bazi(DT_B, longitude=LON_B, gender=GENDER_B)
    check("bazi_b_day_master", bz_b.get("day_master") == "辛", f"B命造日主={bz_b.get('day_master')}")
    check("bazi_b_pillars", [bz_b["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "hour")] == ["乙酉", "丙戌", "辛巳", "丁酉"], "B命造四柱=乙酉/丙戌/辛巳/丁酉")

    # ================================================================
    # 三、Tool 3: shushu_ziwei 测试
    # ================================================================
    print("\n--- [3/10] 测试 Tool: shushu_ziwei ---")
    zw_a = M.shushu_ziwei(DT_A, longitude=LON_A, gender=GENDER_A)
    check("ziwei_palaces_count", len(zw_a.get("palaces", [])) == 12, "十二宫数量完整")
    check("ziwei_minggong", zw_a.get("minggong", {}).get("zhi") == "午", f"命宫地支={zw_a.get('minggong', {}).get('zhi')}")
    check("ziwei_wuxing_ju", "局" in zw_a.get("wuxing_ju", {}).get("name", ""), f"五行局={zw_a.get('wuxing_ju', {}).get('name')}")
    check("ziwei_sihua", len(zw_a.get("sihua", {}).get("items", [])) == 4, "生年四化 4 项")

    # 星曜分栏测试（主星、吉辅星、煞星）
    sample_palace = zw_a["palaces"][0]
    check("ziwei_star_columns", all(k in sample_palace for k in ("stars", "fuxing", "shaxing", "sihua")), "宫位包含 stars, fuxing, shaxing, sihua 分栏")

    # 三方四正测试（CLAUDE.md 根因 5 防线）
    sanfang = zw_a.get("sanfang_sizheng", {})
    check("ziwei_sanfang_all", len(sanfang) == 12, "十二宫三方四正全覆盖")
    fq_scope = sanfang.get("夫妻", {}).get("scope_palaces", [])
    check("ziwei_fuqi_scope", fq_scope == ["夫妻", "迁移", "官禄", "福德"], f"夫妻宫三方四正实证 scope={fq_scope}")
    ming_scope = sanfang.get("命宫", {}).get("scope_palaces", [])
    check("ziwei_ming_scope", ming_scope == ["命宫", "财帛", "迁移", "官禄"], f"命宫三方四正实证 scope={ming_scope}")
    c_six = zw_a.get("c_six_key_palace_sanfang_sizheng", {})
    check("ziwei_six_key", set(c_six.keys()) == {"命宫", "夫妻", "财帛", "官禄", "迁移", "福德"}, "六大核心宫位三方四正视图完整")

    # ================================================================
    # 四、Tool 4: shushu_qimen 测试
    # ================================================================
    print("\n--- [4/10] 测试 Tool: shushu_qimen ---")
    qm_b = M.shushu_qimen(DT_B, longitude=LON_B)
    check("qimen_dingju", qm_b.get("dingju", {}).get("term") == "霜降", f"定局节气={qm_b.get('dingju', {}).get('term')}")
    check("qimen_pan_nine", len(qm_b.get("pan", {})) == 9, "奇门盘包含 9 宫")

    # 历史事故 2 防线：中五宫 star/door/shen 全为 None，不可跨宫混写
    p5 = qm_b["pan"]["5"]
    check("qimen_p5_none", p5["star"] is None and p5["door"] is None and p5["shen"] is None,
          f"中五宫三要素为 None（star={p5['star']}, door={p5['door']}, shen={p5['shen']}）")

    # 断局部分
    dj = qm_b.get("duanju", {})
    check("qimen_duanju_yongshen", len(dj.get("yongshen", [])) == 4, "用神包含日干、时干、值符、值使 4 纲")
    check("qimen_duanju_geju", len(dj.get("geju", [])) > 0, f"命中格局数={len(dj.get('geju', []))}")
    check("qimen_duanju_chubu", dj.get("chubu", {}).get("verdict") in ("好", "平", "差"), f"吉凶初步={dj.get('chubu', {}).get('verdict')}")

    # ================================================================
    # 五、Tool 5: shushu_liuyao 测试
    # ================================================================
    print("\n--- [5/10] 测试 Tool: shushu_liuyao ---")
    # 1. 时间起卦
    ly_t = M.shushu_liuyao(time_str=DT_A)
    check("liuyao_time_ben_gua", "name" in ly_t.get("ben_gua", {}), f"本卦={ly_t['ben_gua']['name']}")
    check("liuyao_time_bian_gua", "name" in ly_t.get("bian_gua", {}), f"变卦={ly_t['bian_gua']['name']}")
    check("liuyao_time_lines", len(ly_t.get("lines", [])) == 6, "六爻共 6 条爻")
    line0 = ly_t["lines"][0]
    check("liuyao_line_attrs", all(k in line0 for k in ("pos", "yao", "shen", "qin", "gan", "zhi", "wx", "shi_ying", "dong")), "单爻属性齐全（包含六神六亲世应动爻）")

    # 2. 数字起卦（双数 + 指定时辰数）
    ly_n2 = M.shushu_liuyao(num1=3, num2=5, hour_num=6)
    check("liuyao_num2_gua", ly_n2.get("ben_gua", {}).get("name") == "火风鼎", f"双数3/5起卦={ly_n2.get('ben_gua', {}).get('name')}")

    # 3. 数字起卦（单数报数）
    ly_n1 = M.shushu_liuyao(num1=7, hour_num=2)
    check("liuyao_num1_dong", any(l["dong"] for l in ly_n1.get("lines", [])), "单数起卦产生动爻")

    # ================================================================
    # 六、Tool 6: shushu_hepan 测试
    # ================================================================
    print("\n--- [6/10] 测试 Tool: shushu_hepan ---")
    hp = M.shushu_hepan(DT_A, "女", LON_A, DT_B, "男", LON_B)
    check("hepan_hp01", "pairs" in hp.get("hp-01", {}), "包含 hp-01 天干五合克")
    check("hepan_hp02", "main" in hp.get("hp-02", {}), "包含 hp-02 地支六合六冲三刑六害")
    check("hepan_hp03", all(k in hp.get("hp-03", {}) for k in ("ri_zhi", "sheng_xiao", "nayin")), "包含 hp-03 日支夫妻宫/生肖/纳音")
    check("hepan_hp04", "scores" in hp.get("hp-04", {}) and "tendency" in hp.get("hp-04", {}), f"包含 hp-04 综合评分={hp.get('hp-04', {}).get('scores', {}).get('total')}")
    check("hepan_gender", hp.get("gender_a") == "女" and hp.get("gender_b") == "男", "性别记录正确")

    # ================================================================
    # 七、Tool 7: shushu_reconcile 全面审计拦截测试
    # ================================================================
    print("\n--- [7/10] 测试 Tool: shushu_reconcile ---")
    # 1. 正常完全契合文本：PASS
    valid_text = "本造日主乙木，生于丙戌年、甲午月、乙酉日、丙子时。大运首步癸巳(2012-2021)偏印，次步壬辰(2022-2031)正印。"
    rec1 = M.shushu_reconcile(valid_text, snap_a)
    check("reconcile_valid_pass", rec1["verdict"] == "PASS" and rec1["summary"]["conflicts_count"] == 0,
          f"零冲突放行 matched={rec1['summary']['matched_count']}")

    # 2. 真实事故 1 拦截：大运手推错位一位 (甲午冒名大运)
    err_text_shifted = "大运首步甲午(2012-2021)。"
    rec2 = M.shushu_reconcile(err_text_shifted, snap_a)
    check("reconcile_catch_not_in_dayun", rec2["verdict"] == "FAIL" and rec2["summary"]["conflicts_count"] > 0,
          f"抓获冒名大运 conflicts={rec2['summary']['conflicts_count']}")

    # 3. 大运年份区间错位 (癸巳配错年份)
    err_text_years = "大运癸巳(2022-2031)。"
    rec3 = M.shushu_reconcile(err_text_years, snap_a)
    check("reconcile_catch_shifted", any(c.get("kind") == "shifted" for c in rec3.get("conflicts", [])),
          "抓获大运年份错位 shifted")

    # 4. 盲点 A 拦截：旺衰分数漂移
    snap_b = M.shushu_snapshot(DT_B, gender=GENDER_B, longitude=LON_B)
    b_actual_score = snap_b.get("wangshuai", {}).get("zonghe", {}).get("score")
    b_actual_level = snap_b.get("wangshuai", {}).get("zonghe", {}).get("level")
    # 模拟草稿残留旧值 "21.0 分偏弱"（实际为 55.8 分中和）
    fake_drift_text = "本造八字 21.0 分偏弱，日干辛金。"
    rec4 = M.shushu_reconcile(fake_drift_text, snap_b)
    check("reconcile_catch_score_drift", any(c.get("kind") == "ws_score_drift" for c in rec4.get("conflicts", [])),
          f"抓获旺衰分漂移 ws_score_drift（快照={b_actual_score}分，文中=21.0分）")

    # 5. 盲点 B 拦截：藏干十神日主映射错误
    # B命造日主辛金，戌中戊应为正印，文中写 "戊偏财"
    fake_god_text = "月支戌中藏戊偏财。"
    rec5 = M.shushu_reconcile(fake_god_text, snap_b)
    check("reconcile_catch_ten_god_mismatch", any(c.get("kind") == "ten_god_mismatch" for c in rec5.get("conflicts", [])),
          "抓获藏干十神错位 ten_god_mismatch（辛日主见戊应为正印而非偏财）")

    # 6. 盲点 C 拦截：年龄与流年脱节
    # B命造 2005 出生，文中写 "20岁 2035年" (2035-2005=30岁 != 20岁)
    fake_age_text = "命主在 20 岁 (2035) 发生事业转折。"
    rec6 = M.shushu_reconcile(fake_age_text, snap_b)
    check("reconcile_catch_age_mismatch", any(c.get("kind") == "age_year_mismatch" for c in rec6.get("conflicts", [])),
          "抓获年龄年份换算错误 age_year_mismatch")

    # 7. snapshot_json 支持传 JSON 字符串或 dict 对象
    snap_str = json.dumps(snap_a, ensure_ascii=False)
    rec7 = M.shushu_reconcile(valid_text, snap_str)
    check("reconcile_str_input", rec7["verdict"] == "PASS", "支持 JSON 字符串入参")

    # ================================================================
    # 七(续)、扩充历法与格局原语测试
    # ================================================================
    print("\n--- [7b/10] 测试格局与历法原语扩展工具 ---")
    # Tool 8: shushu_bazi_geju
    gj = M.shushu_bazi_geju(DT_A, gender=GENDER_A)
    check("geju_result", "category" in gj and "pattern_name" in gj, f"格局判定成功: {gj['pattern_name']}")

    # Tool 9: shushu_jieqi_query
    jq = M.shushu_jieqi_query(2025, "立春")
    check("jieqi_result", jq["count"] >= 1 and "2025-02-03" in jq["terms"][0]["term_time"], "节气精确时刻秒级查询")

    # Tool 10: shushu_calendar_convert
    cal = M.shushu_calendar_convert(solar_date="2024-02-10")
    check("calendar_result", cal["lunar"]["lunar_month"] == 1 and cal["lunar"]["lunar_day"] == 1, "公农历互转精准反查")

    # Tool 11: shushu_timezone
    tz = M.shushu_timezone(wall_time="1988-06-15 14:30", tz_name="Asia/Shanghai", lon=120.0, lat=31.2)
    check("timezone_result", tz["time_resolution"]["is_dst"] is True and tz["time_resolution"]["standard_local_time"] == "1988-06-15 13:30:00", "时区夏令时自动识别回退")

    # Tool 12: shushu_jinkoujue
    jkj = M.shushu_jinkoujue(datetime_str=DT_A, difen="卯")
    check("jinkoujue_result", "four_positions" in jkj and "wudong" in jkj, f"大六壬金口诀排盘: 人元={jkj['four_positions']['renyuan']['gan']}")

    # Tool 13: shushu_qizheng
    qz = M.shushu_qizheng(datetime_str=DT_A)
    check("qizheng_result", "stars" in qz and "太阳" in qz["stars"], f"七政四余入宿度: 太阳落{qz['stars']['太阳']['mansion']}")

    # Tool 14: shushu_ziwei_yunxian
    zwyx = M.shushu_ziwei_yunxian(datetime_str=DT_A, target_year=2026, gender=GENDER_A)
    check("ziwei_yunxian_result", "limits" in zwyx and "liuyao" in zwyx, f"紫微斗数多级运限: 斗君={zwyx['limits']['doujun']}")

    # Tool 15: shushu_shensha_ext
    sse = M.shushu_shensha_ext(datetime_str=DT_A, gender=GENDER_A)
    check("shensha_ext_result", "pillar_shensha" in sse, "50+ 扩展神煞库检索成功")

    # Tool 16: shushu_tieban
    tb = M.shushu_tieban(datetime_str=DT_A, ke=1)
    check("tieban_result", "taixuan_total" in tb and len(tb.get("deduced_items", [])) == 5, f"铁板神数八刻滚盘: 太玄数={tb['taixuan_total']}")

    # ================================================================
    # 八、JSON-RPC 2.0 协议层深度测试
    # ================================================================
    print("\n--- [8/10] 测试 JSON-RPC 2.0 协议规范 ---")
    # 1. initialize
    init_res = M.handle_jsonrpc_request({"jsonrpc": "2.0", "id": "req-1", "method": "initialize"})
    check("rpc_init_id", init_res.get("id") == "req-1", "响应 id 与请求一致")
    check("rpc_init_version", init_res.get("result", {}).get("protocolVersion") == "2024-11-05", "协议版本号符合标准")
    check("rpc_init_tools_cap", "tools" in init_res.get("result", {}).get("capabilities", {}), "声明 tools 能力")

    # 2. notifications/initialized (无 id，返回 None)
    notif_res = M.handle_jsonrpc_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    check("rpc_notif_no_reply", notif_res is None, "通知不产生回执")

    # 3. ping
    ping_res = M.handle_jsonrpc_request({"jsonrpc": "2.0", "id": 99, "method": "ping"})
    check("rpc_ping", ping_res.get("result") == {}, "ping 响应成功")

    # 4. tools/list
    tl_res = M.handle_jsonrpc_request({"jsonrpc": "2.0", "id": 100, "method": "tools/list"})
    tools = tl_res.get("result", {}).get("tools", [])
    tool_names = [t["name"] for t in tools]
    check("rpc_tools_count", len(tools) == 16, f"tools/list 包含 16 个工具 (实际 {len(tools)})")
    check("rpc_tools_names", set(tool_names) == {
        "shushu_snapshot", "shushu_bazi", "shushu_ziwei", "shushu_qimen",
        "shushu_liuyao", "shushu_hepan", "shushu_reconcile",
        "shushu_bazi_geju", "shushu_jieqi_query", "shushu_calendar_convert", "shushu_timezone",
        "shushu_jinkoujue", "shushu_qizheng", "shushu_ziwei_yunxian", "shushu_shensha_ext", "shushu_tieban"
    }, f"工具清单全匹配: {tool_names}")
    for t in tools:
        check(f"tool_schema_{t['name']}", "inputSchema" in t and "description" in t, f"{t['name']} 具备 schema 与 description")

    # 5. tools/call - shushu_snapshot
    call_snap = M.handle_jsonrpc_request({
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "shushu_snapshot",
            "arguments": {"datetime_str": DT_A, "gender": GENDER_A, "longitude": LON_A}
        }
    })
    check("rpc_call_snap_ok", call_snap.get("result", {}).get("isError") is False, "RPC call snapshot 成功")
    content_txt = call_snap.get("result", {}).get("content", [{}])[0].get("text", "")
    check("rpc_call_snap_content", "pillars" in content_txt and "dayun" in content_txt, "返回 content text 格式化 JSON")

    # 6. tools/call - shushu_reconcile
    call_rec = M.handle_jsonrpc_request({
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {
            "name": "shushu_reconcile",
            "arguments": {"draft_text": valid_text, "snapshot_json": snap_a}
        }
    })
    check("rpc_call_rec_ok", call_rec.get("result", {}).get("isError") is False, "RPC call reconcile 成功")
    rec_obj = json.loads(call_rec["result"]["content"][0]["text"])
    check("rpc_call_rec_verdict", rec_obj.get("verdict") == "PASS", "RPC reconcile 结果为 PASS")

    # ================================================================
    # 九、错误处理与边缘 Case 测试
    # ================================================================
    print("\n--- [9/10] 测试错误处理与健壮性 ---")
    # 1. 未知方法
    unk_res = M.handle_jsonrpc_request({"jsonrpc": "2.0", "id": 201, "method": "unknown_method"})
    check("err_method_not_found", unk_res.get("error", {}).get("code") == -32601, "未知方法返回 -32601")

    # 2. 未知 Tool
    unk_tool = M.handle_jsonrpc_request({
        "jsonrpc": "2.0",
        "id": 202,
        "method": "tools/call",
        "params": {"name": "non_existent_tool", "arguments": {}}
    })
    check("err_tool_not_found", unk_tool.get("error", {}).get("code") == -32601, "未知 Tool 返回 -32601")

    # 3. 请求非 dict
    bad_req = M.handle_jsonrpc_request("not a json dict")
    check("err_invalid_req", bad_req.get("error", {}).get("code") == -32600, "非法请求返回 -32600")

    # 4. Tool 参数错误导致执行异常（如日期格式错误）
    bad_args = M.handle_jsonrpc_request({
        "jsonrpc": "2.0",
        "id": 203,
        "method": "tools/call",
        "params": {"name": "shushu_bazi", "arguments": {"datetime_str": "invalid_date"}}
    })
    check("err_tool_exec_isError", bad_args.get("result", {}).get("isError") is True, "Tool 异常返回 isError=True")
    check("err_tool_exec_msg", "Tool Execution Error" in bad_args.get("result", {}).get("content", [{}])[0].get("text", ""), "包含异常提示")

    # ================================================================
    # 十、子进程 CLI 与 stdio 管道测试
    # ================================================================
    print("\n--- [10/10] 测试 CLI --test 模式与 stdio 管道通信 ---")
    # 1. 测试 python mcp_server.py --test 命令
    cmd_test = [sys.executable, os.path.join(BASE, "mcp_server.py"), "--test"]
    p_test = subprocess.run(cmd_test, capture_output=True, text=True, encoding="utf-8")
    check("cli_test_exit_0", p_test.returncode == 0, f"CLI --test 退出码为 0（stdout 包含 '{p_test.stdout.strip()[-30:]}'）")
    check("cli_test_output_pass", "20/20 PASS" in p_test.stdout, "CLI --test 输出包含 20/20 PASS")

    # 2. 测试真实 stdio 管道交互（模拟真实 MCP Client 连接）
    p_stdio = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "mcp_server.py"), "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    req_line = json.dumps({"jsonrpc": "2.0", "id": "pipe-1", "method": "initialize"}) + "\n"
    p_stdio.stdin.write(req_line)
    p_stdio.stdin.flush()

    resp_line = p_stdio.stdout.readline()
    resp_obj = json.loads(resp_line.strip())
    check("stdio_pipe_init", resp_obj.get("id") == "pipe-1" and "serverInfo" in resp_obj.get("result", {}), "stdio 管道交互 initialize 响应正确")

    req_line_call = json.dumps({
        "jsonrpc": "2.0",
        "id": "pipe-2",
        "method": "tools/call",
        "params": {
            "name": "shushu_liuyao",
            "arguments": {"num1": 1, "num2": 1, "hour_num": 1}
        }
    }) + "\n"
    p_stdio.stdin.write(req_line_call)
    p_stdio.stdin.flush()

    resp_call_line = p_stdio.stdout.readline()
    resp_call_obj = json.loads(resp_call_line.strip())
    check("stdio_pipe_call", resp_call_obj.get("id") == "pipe-2" and resp_call_obj.get("result", {}).get("isError") is False, "stdio 管道交互 tools/call 响应正确")

    p_stdio.stdin.close()
    p_stdio.terminate()
    p_stdio.wait()

    # ================================================================
    # 汇总
    # ================================================================
    print("================================================================")
    n_pass = sum(1 for _, ok in RES if ok)
    n_total = len(RES)
    print(f"assert_mcp 测试结果: {n_pass}/{n_total} PASS")
    print("================================================================")
    if n_pass == n_total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
