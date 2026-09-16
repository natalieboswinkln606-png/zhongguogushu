# -*- coding: utf-8 -*-
"""l3_tieban.py — L3-3b 铁板条文层（tb-01..tb-04）。v1.1 新增文件（不改任何冻结模块）。

定位声明（随件）：铁板神数（邵子神数一系）为"条文+考刻"系统；考刻是方法内核——
用已知事实反推刻数，本质为用已知数据拟合参数，拟合≠预测验证；"纯查表"只描述考刻成功后的下半程。
本模块只做四件事，不实现任何具体传本的条文编号演算（先天数/加减乘除/条文号码各传本互异）：

- tb-01 四柱太玄数结构键：八数 = 年/月/日/时 柱各 (干太玄数, 支太玄数)；
  表 import 自 l3_heluolishu（hlyl-01 同源网传太玄数派），并以固定值断言交叉锁死防上游漂移。
- tb-02 刻框架：默认"一时八刻"（96 刻制，每刻 15 分钟）；alt 古百刻制（每刻 14.4 分钟，自 00:00 子正起）。
  每刻窗"起点 + 1 分钟"取样，防真太阳时反解四舍五入越界。子时候选跨午夜时逐候选重算四柱
  （m1 换日界=真太阳时子正，日柱随真太阳日期分裂，不做合并）。
- tb-03 条文结构键匹配：(刻位 + 八位干支) 与外部条文库行匹配，库行各字段空=通配；
  引擎不自造传本编号与条文——id/正文一律直引库列（data/tieban_tiaowen.csv，库由使用者自备）。
- tb-04 考刻-验证交互回路：候选刻枚举 → 键匹配检索 → 逐条判定（claim+facts 自动判定，
  人工 verdicts 优先）→ 计分排序（hit +1 / miss -1 / unknown 0）→ 输出排序候选清单，不作确定性论断。

运行：
  PYTHONIOENCODING=utf-8 python l3_tieban.py --datetime "1990-05-01 10:00"                 # 单点查表
  PYTHONIOENCODING=utf-8 python l3_tieban.py --datetime "1990-05-01 10:00" --examine \
      --facts '{"父母.生肖":"马"}' --verdicts '{"1031":"hit"}'
"""
import argparse, csv, json, os, sys
from datetime import datetime, timedelta
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import m1
import l3_heluolishu as HLYL
import l3_bazi_liuri as LR

PILLAR_KEYS = ("year", "month", "day", "hour")
POS = ("y", "m", "d", "h")
SHICHEN = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
MODES = {
    "8": {"count": 8, "per": 15.0, "anchor": "shichen",
          "source": "铁板一时八刻（96 刻制，每刻 15 分钟，刻位自时辰起点计 1..8）"},
    "100": {"count": 100, "per": 14.4, "anchor": "midnight",
            "source": "古百刻制（每刻 14.4 分钟，自当日 00:00 子正起计 1..100）"},
}
LIB_PATH = os.path.join(BASE, "data", "tieban_tiaowen.csv")
LIB_FIELDS = ("id", "category", "text", "claim", "ke") + \
             tuple(f"{p}_{k}" for p in POS for k in ("gan", "zhi"))
TAIXUAN_ALT = "各传本自定数系互异；本表为 hlyl-01 同源网传太玄数派"
POSITIONING = ("铁板神数为条文+考刻系统；考刻=用已知事实反推刻数（以已知数据拟合参数，拟合≠预测验证）。"
               "本模块只做结构键与键匹配，不自造任何传本编号或条文；条文 id/正文一律来自外部库。")


def _check_tables():
    # 太玄数固定值锁：与 l3_heluolishu（hlyl-01）双向一致，防上游表漂移
    assert HLYL.GAN_SHU == {"甲": 9, "己": 9, "乙": 8, "庚": 8, "丙": 7, "辛": 7,
                            "丁": 6, "壬": 6, "戊": 5, "癸": 5}
    assert HLYL.ZHI_SHU == {"子": 9, "午": 9, "丑": 8, "未": 8, "寅": 7, "申": 7,
                            "卯": 6, "酉": 6, "辰": 5, "戌": 5, "巳": 4, "亥": 4}


def tai_xuan_key(pillars):
    """tb-01：四柱 → 八太玄数结构键（年/月/日/时各 干数+支数；仅结构键，非条文编号）。"""
    _check_tables()
    vals, detail = [], {}
    for k in PILLAR_KEYS:
        g, z = pillars[k][0], pillars[k][1]
        vals += [HLYL.GAN_SHU[g], HLYL.ZHI_SHU[z]]
        detail[k] = {"ganzhi": pillars[k], "gan_shu": HLYL.GAN_SHU[g], "zhi_shu": HLYL.ZHI_SHU[z]}
    return {"rule_id": "tb-01", "source": "太玄数表（hlyl-01 同源，import 自 l3_heluolishu）",
            "alt": TAIXUAN_ALT, "pillars": dict(pillars), "detail": detail,
            "values": vals, "total": sum(vals)}


def _shichen_start(ts):
    s = m1.shichen(ts.hour)
    st = ts.replace(hour=(23 + 2 * s) % 24, minute=0, second=0, microsecond=0)
    if st > ts:
        st -= timedelta(days=1)
    return s, st


def _pillars_of(bj, lon):
    r = m1.compute(bj, lon)
    if "error" in r:
        return None, r["error"]
    return {k: r["pillars"][k]["ganzhi"] for k in PILLAR_KEYS}, None


def ke_candidates(ref_dt, lon, mode="8"):
    """tb-02：刻候选枚举（ref_dt=北京时近似出生时刻）。每刻窗起点+1 分钟取样防舍入越界。"""
    if mode not in MODES:
        return {"error": f"错误: mode 须为 {'/'.join(sorted(MODES))}"}
    spec = MODES[mode]
    ts0 = m1.true_solar(ref_dt, lon)
    s, st = _shichen_start(ts0)
    anchor = st if spec["anchor"] == "shichen" else ts0.replace(hour=0, minute=0, second=0, microsecond=0)
    cands = []
    for i in range(spec["count"]):
        start = anchor + timedelta(minutes=spec["per"] * i)
        end = start + timedelta(minutes=spec["per"])
        sample_ts = start + timedelta(minutes=1)
        bj = LR.bj_at_true_solar(sample_ts, lon)
        p, err = _pillars_of(bj, lon)
        c = {"ke": i + 1,
             "start_true": start.strftime("%Y-%m-%d %H:%M"),
             "end_true": end.strftime("%Y-%m-%d %H:%M"),
             "sample_true": sample_ts.strftime("%Y-%m-%d %H:%M"),
             "sample_bj": bj.strftime("%Y-%m-%d %H:%M")}
        if err:
            c["error"] = err
        else:
            c["pillars"] = p
        cands.append(c)
    return {"rule_id": "tb-02", "mode": mode, "source": spec["source"],
            "alt": "刻位为本文约定口径（时辰内第 N 刻）；传本另有从子时起计全日子刻等惯例",
            "ref_true": ts0.strftime("%Y-%m-%d %H:%M"),
            "shichen": s, "shichen_name": SHICHEN[s], "candidates": cands}


def ke_of(ts, mode="8"):
    """真太阳时刻 → 刻位（mode 8：时辰内第 N 刻 1..8；mode 100：全日子刻 1..100）。"""
    if mode not in MODES:
        return None
    spec = MODES[mode]
    s, st = _shichen_start(ts)
    anchor = st if spec["anchor"] == "shichen" else ts.replace(hour=0, minute=0, second=0, microsecond=0)
    k = int((ts - anchor).total_seconds() // (spec["per"] * 60)) + 1
    return max(1, min(spec["count"], k))


def load_library(path=None):
    path = path or LIB_PATH
    if not os.path.exists(path):
        return {"rows": [], "path": path, "exists": False}
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({k: (r.get(k) or "").strip() for k in LIB_FIELDS})
    return {"rows": rows, "path": path, "exists": True}


def _row_match(row, pillars, ke, warnings=None):
    if row["ke"]:
        try:
            if int(row["ke"]) != ke:
                return False
        except ValueError:
            if warnings is not None:
                warnings.append(f"行 id={row.get('id') or '(无 id)'}: ke='{row['ke']}' 非法（须整数），该行永不匹配")
            return False
    for p, k in zip(POS, PILLAR_KEYS):
        if row[f"{p}_gan"] and row[f"{p}_gan"] != pillars[k][0]:
            return False
        if row[f"{p}_zhi"] and row[f"{p}_zhi"] != pillars[k][1]:
            return False
    return True


def retrieve(pillars, ke, lib=None):
    """tb-03：(刻位+八位干支) 键匹配；库行字段空=通配；id 直引库列，引擎不自造编号。
    异常行入 warnings（数据错误外显不静默）：ke 非整数行永不匹配。"""
    lib = lib if lib is not None else load_library()
    warnings = []
    rows = [r for r in lib["rows"] if _row_match(r, pillars, ke, warnings)]
    return {"rule_id": "tb-03", "source": "外部条文库 id 列（引擎不自造传本编号）",
            "library": lib["path"], "exists": lib["exists"], "ke": ke,
            "pillars": dict(pillars), "matched": rows, "count": len(rows),
            "warnings": warnings}


def evaluate_rows(rows, facts=None, verdicts=None):
    """逐条判定：verdicts（人工）优先；否则 claim:"属性=值" 对 facts 自动判定；缺者为 unknown。
    异常入 warnings（外显不静默）：verdict 值非法、claim 含多个 '='。"""
    facts = {str(k).strip(): str(v).strip() for k, v in (facts or {}).items()}
    verdicts = {str(k).strip(): str(v).strip().lower() for k, v in (verdicts or {}).items()}
    warnings, details = [], []
    for row in rows:
        rid = row.get("id", "")
        raw_v = verdicts.get(rid)
        if raw_v in ("hit", "miss", "unknown"):
            v, how = raw_v, "人工"
        else:
            if raw_v is not None:
                warnings.append(f"行 id={rid or '(无 id)'}: verdict='{raw_v}' 非法（须 hit/miss/unknown），已按自动判定处理")
            claim = row.get("claim") or ""
            attr, _, want = claim.partition("=")
            if want and "=" in want:
                warnings.append(f"行 id={rid or '(无 id)'}: claim='{claim}' 含多个 '='，按首个 '=' 分割")
            if not want:
                v, how = "unknown", "无断言"
            elif attr.strip() in facts:
                v, how = ("hit" if facts[attr.strip()] == want.strip() else "miss"), "自动"
            else:
                v, how = "unknown", "facts 缺失"
        details.append({"id": rid, "category": row.get("category", ""), "text": row.get("text", ""),
                        "claim": row.get("claim", ""), "verdict": v, "how": how})
    counts = {k: sum(1 for d in details if d["verdict"] == k) for k in ("hit", "miss", "unknown")}
    return {"details": details, "counts": counts, "score": counts["hit"] - counts["miss"],
            "warnings": warnings}


def examine(ref_dt, lon, facts=None, verdicts=None, mode="8", library_path=None):
    """tb-04：考刻-验证交互回路。候选枚举 → 键检索 → 判定 → 计分排序（hit+1/miss-1/unknown 0）。"""
    cc = ke_candidates(ref_dt, lon, mode)
    if "error" in cc:
        return cc
    lib = load_library(library_path)
    cands, warnings, seen_ids = [], [], set()
    for c in cc["candidates"]:
        item = dict(c)
        if "pillars" in c:
            item["key"] = tai_xuan_key(c["pillars"])
            item["retrieval"] = retrieve(c["pillars"], c["ke"], lib)
            item["evaluation"] = evaluate_rows(item["retrieval"]["matched"], facts, verdicts)
            warnings += item["retrieval"]["warnings"] + item["evaluation"]["warnings"]
            seen_ids |= {m.get("id") for m in item["retrieval"]["matched"]}
        cands.append(item)
    if verdicts:
        orphan = sorted(set(verdicts) - seen_ids)
        if orphan:
            warnings.append(f"verdicts 含 id={orphan}：未在任何候选刻检索命中中出现（库缺失或 id 不符）")
    warnings = list(dict.fromkeys(warnings))
    ranked = sorted((c for c in cands if "evaluation" in c),
                    key=lambda x: (-x["evaluation"]["score"], x["ke"]))
    notes = ["考刻=以已知事实拟合刻数：拟合≠预测验证；得分仅反映与所给 facts/verdicts 的一致度",
             "无 claim 或 facts 缺失的行判 unknown，不参与计分；并列得分需继续以人工条文核对收敛"]
    if not lib["exists"]:
        notes.insert(0, f"条文库未提供（{lib['path']}）；引擎不自造传本条文，检索为空属预期")
    return {"rule": "tb-04", "mode": cc["mode"], "positioning": POSITIONING,
            "ref_true": cc["ref_true"], "shichen": cc["shichen_name"], "library": lib["path"],
            "candidates": cands,
            "ranking": [{"ke": c["ke"], "score": c["evaluation"]["score"],
                         "counts": c["evaluation"]["counts"]} for c in ranked],
            "warnings": warnings,
            "notes": notes}


def lookup(birth_dt, lon, ke=None, mode="8", library_path=None):
    """单点查表：已知精确时刻 → 四柱键（tb-01）+ 条文检索（tb-03）；ke 缺省由真太阳时刻反推。"""
    p, err = _pillars_of(birth_dt, lon)
    if err:
        return {"error": err}
    ts = m1.true_solar(birth_dt, lon)
    if ke is None:
        ke = ke_of(ts, mode)
    return {"rule": "tb-01/tb-03", "pillars": p, "true_solar": ts.strftime("%Y-%m-%d %H:%M"),
            "ke": ke, "mode": mode, "positioning": POSITIONING, "key": tai_xuan_key(p),
            "retrieval": retrieve(p, ke, load_library(library_path))}


def _print_result(r):
    if "rule" in r and r["rule"] == "tb-04":
        print(f"考刻-验证回路（mode {r['mode']}，{r['shichen']}时，真太阳时基准 {r['ref_true']}）")
        print(r["positioning"])
        for c in r["candidates"]:
            if "evaluation" not in c:
                print(f"  刻{c.get('ke')}: 无四柱（{c.get('error')}）")
                continue
            ev = c["evaluation"]
            print(f"  刻{c['ke']}: {c['sample_bj']}候（真{c['sample_true']}） "
                  f"{''.join(c['pillars'][k] for k in PILLAR_KEYS)} "
                  f"键{c['key']['values']} 条文{c['retrieval']['count']}条 "
                  f"hit{ev['counts']['hit']}/miss{ev['counts']['miss']}/un{ev['counts']['unknown']} 得分{ev['score']}")
        print("排序：" + "，".join(f"刻{r['ke']}={r['score']}" for r in r["ranking"]))
        for n in r["notes"]:
            print(f"  注：{n}")
        for w in r.get("warnings") or []:
            print(f"  警告：{w}")
    else:
        print(f"四柱: {r['pillars']['year']} {r['pillars']['month']} {r['pillars']['day']} {r['pillars']['hour']}"
              f"（真太阳时 {r['true_solar']}）")
        print(f"太玄数键（tb-01）: {r['key']['values']} 合计 {r['key']['total']}（{r['key']['alt']}）")
        ret = r["retrieval"]
        print(f"刻位: {r['ke']}（mode {r['mode']}；tb-02 口径） 条文库: {ret['library']}"
              f"{'（未提供）' if not ret['exists'] else ''}")
        print(f"命中条文（tb-03）: {ret['count']} 条")
        for m in ret["matched"]:
            print(f"  [{m['id']}] {m['category']} {m['text']}（claim: {m['claim'] or '无'}）")


def main():
    ap = argparse.ArgumentParser(description="铁板条文层：tb-01 结构键 / tb-02 刻框架 / tb-03 键匹配 / tb-04 考刻回路")
    ap.add_argument("--datetime", required=True, help="出生（近似/精确）北京时 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--mode", default="8", choices=sorted(MODES))
    ap.add_argument("--ke", type=int, default=None, help="单点查表指定刻位（缺省由真太阳时反推）")
    ap.add_argument("--examine", action="store_true", help="考刻-验证回路（候选刻全枚举+计分排序）")
    ap.add_argument("--facts", default=None, help='已知事实 JSON，如 {"父母.生肖":"马"}')
    ap.add_argument("--verdicts", default=None, help='人工判定 JSON，如 {"1031":"hit"}')
    ap.add_argument("--library", default=None, help="条文库 CSV 路径（缺省 data/tieban_tiaowen.csv）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
        facts = json.loads(a.facts) if a.facts else None
        verdicts = json.loads(a.verdicts) if a.verdicts else None
    except ValueError as e:
        print(f"错误: 参数非法（{e}）；--datetime 须为 YYYY-MM-DD HH:MM，--facts/--verdicts 须为 JSON")
        sys.exit(2)
    r = examine(dt, a.lon, facts, verdicts, a.mode, a.library) if a.examine \
        else lookup(dt, a.lon, a.ke, a.mode, a.library)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        _print_result(r)
    sys.exit(1 if "error" in r else 0)


if __name__ == "__main__":
    main()
