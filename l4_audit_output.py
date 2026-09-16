# -*- coding: utf-8 -*-
"""l4_audit_output.py — L4 输出审计层：快照 / 不变量 / 文本对账（只读引擎直出，不改任何既有模块）。

使命：让 AI 输出测算结论时的"手推数据"无处遁形。背景是 4 个真实事故——最严重者：
A 命造（2006-06-25 00:30 女 120E）大运被凭记忆错写为"甲午(2012-2021)→癸巳(2022-2031)…"，
引擎实证正确为"癸巳(2012-2021)→壬辰(2022-2031)→…"（阳年女逆排，首步=月柱甲午上一位癸巳）。

三大功能（全部数据引擎直出，禁止任何手算补充）：
① snapshot(dt_str, gender, lon, ...) → 全量快照 dict：四柱+十神(m1)、大运完整序列+l3_bazi_daliu、
   流年干支(默认 2020-2040)、紫微十二宫×十二时辰全谱(l3_ziwei)、奇门盘(l3_qimen)、称骨(l3_chenggu)；
   附 meta.provenance 记录所用引擎文件 sha256（快照与冻结版本绑定）。dump(obj, path) 落盘 UTF-8。
② check_invariants(snap) → [{id, ok, detail}]：五条机械化不变量 aud-inv-01..05，
   其中 aud-inv-01 即"大运首步=月柱±1"防线（本次重大错误的机械化复现检测点）。
③ reconcile(text, snap) → {"matched","unverified","conflicts"}：抽取文中干支/年份区间/术数词表，
   凡无法在快照中机械溯源的一律标出（宁多报不漏报）；干支紧邻十年区间但与大运步骤对不上 → conflicts。

CLI：python l4_audit_output.py snapshot|check|reconcile（argparse；结果一律写 --out UTF-8 JSON，
控制台只打 ASCII 状态行，规避 GBK 乱码）。
注册表说明：rule_id 采用 aud-inv-* 形态，registry_check 的扫描正则与范围（l3_*.py+m1.py）
抓不到该形态（详见报告），故不变量 id 以本模块 INVARIANTS 常量 + 断言脚本双向锁定，不动 data/rule_registry.csv。
"""
import argparse, copy, hashlib, json, os, re, sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import m1
import rules
from rules import GAN, ZHI
import l3_bazi_daliu as BD
import l3_ziwei as ZW
import l3_qimen as QM
import l3_chenggu as CG
import l3_wuyunliuqi as WYLQ
import l3_liuyao as LY
import l3_liuren as LR
import l3_meihua as MH
import l3_xiaoliuren as XLR
import l3_heluolishu as HLY
import l3_huangli as HL
import l3_hepan as HP
import l3_qimen_duanju as QMDJ
import l3_shensha as SS
import l3_ziwei_liunian as ZL

# ---------------------------------------------------------------- 基础工具
ENGINE_FILES = [
    "m1.py", "rules.py",
    "l3_bazi_daliu.py", "l3_ziwei.py", "l3_qimen.py", "l3_chenggu.py",
    "l3_wuyunliuqi.py", "l3_liuyao.py", "l3_liuren.py",
    "l3_meihua.py", "l3_xiaoliuren.py", "l3_heluolishu.py",
    "l3_huangli.py", "l3_hepan.py", "l3_qimen_duanju.py",
    "l3_shensha.py", "l3_ziwei_liunian.py",
]

TEN_GODS_ALL = ["比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"]
MAIN14_ALL = list(ZW.MAIN14)
AUX_ALL = ["左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "擎羊", "陀罗", "火星", "铃星", "天马"]
DOORS_ALL = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
STARS_ALL = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]
GODS_ALL = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

GZ_RE = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")       # 六十甲子干支对
RANGE_RE = re.compile(r"(19\d\d|20\d\d)\s*[-–~至]\s*(19\d\d|20\d\d)")        # 年份区间 2012-2021 / 2012~2021 / 2012至2021
YEAR_RE = re.compile(r"(19\d\d|20\d\d)")                                      # 单年份


def _sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def gz_seq(gz):
    """六十甲子序（甲子=0…癸亥=59）：本地独立实现（rules 干支序号），不借用被审模块的算术。"""
    return (6 * rules.gan_idx(gz[0]) - 5 * rules.zhi_idx(gz[1])) % 60


def seq_gz(n):
    """六十甲子序 → 干支：本地独立实现。"""
    return GAN[n % 10] + ZHI[n % 12]


def year_gz_formula(year):
    """流年干支公式 (y-4)%60：本地独立实现（aud-inv-03 的期望值来源，不调用引擎函数）。"""
    return seq_gz((year - 4) % 60)


def dump(obj, path):
    """落盘工具：UTF-8、ensure_ascii=False、indent=2。"""
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


# ---------------------------------------------------------------- ① 快照
def snapshot(dt_str, gender, lon=120.0, hours=None, years=(2020, 2040),
             dayun_steps=8, with_qimen=True, with_chenggu=True,
             partner_dt=None, partner_gender=None, partner_lon=None,
             ziwei_target_year=None):
    """给定出生时间生成全量快照 dict（全部引擎直出）。

    dt_str      北京时间 "YYYY-MM-DD HH:MM"
    gender      "男"/"女"（大运顺逆、称骨歌诀用）
    hours       紫微采样时辰列表，默认 [0,2,...,22] 十二时辰全谱（每时辰整点采样，分钟归零）
    years       流年干支年份区间 (起, 止) 含端点，默认 2020-2040
    dayun_steps 大运步数（默认 8 步，同 l3_bazi_daliu 默认）
    with_qimen/with_chenggu  可选模块开关（默认纳入）
    partner_dt/partner_gender  合盘对方（可选），用于 l3_hepan
    partner_lon 合盘对方经度（默认=主体 lon；对方四柱精度受其影响）
    ziwei_target_year  紫微大限/流年目标年（默认 None → 当前年）
    """
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    r = m1.compute(dt, lon)
    if "error" in r:
        return {"error": r["error"], "input": {"datetime": dt_str, "gender": gender, "lon": lon}}
    dm = r["ten_gods"]["day_master"]

    # 大运完整序列（含顺逆 fwd 与起运信息）：l3_bazi_daliu.dayun 直出
    dl, qy, jie, jiao, fwd = _dayun_pack(dt, lon, gender, dayun_steps)

    # 流年干支（默认 2020-2040）：引擎 year_gz + r5 十神
    y0, y1 = (years if isinstance(years, (tuple, list)) else (years, years))[:2]
    liunian = [{"year": y, "ganzhi": BD.year_gz(y), "god": m1.ten_god(dm, BD.year_gz(y)[0])}
               for y in range(int(y0), int(y1) + 1)]

    # 紫微十二时辰全谱：每时辰整点各排一盘
    if hours is None:
        hours = list(range(0, 24, 2))
    ziwei_hours = []
    for h in hours:
        zr = ZW.compute(dt.replace(hour=int(h), minute=0), lon)
        if "error" in zr:
            ziwei_hours.append({"hour": int(h), "error": zr["error"]})
            continue
        ziwei_hours.append({
            "hour": int(h),
            "lunar": {"month": zr["lunar"]["month"], "day": zr["lunar"]["day"],
                      "is_ruen": zr["lunar"].get("is_ruen")},
            "minggong": {"zhi": zr["minggong"]["zhi"], "gan": zr["minggong"]["gan"]},
            "shengong": zr["shengong"],
            "wuxing_ju": zr["wuxing_ju"],
            "sihua": zr["sihua"],
            "palaces": [{"name": p["name"], "zhi": p["zhi"], "gan": p["gan"],
                         "stars": p["stars"], "aux": p["aux"], "sihua": p["sihua"], "shen": p["shen"]}
                        for p in zr["palaces"]],
        })

    snap = {
        "meta": {
            "tool": "l4_audit_output.py",
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "note": "全部数据由冻结引擎直出（m1/l3_bazi_daliu/l3_ziwei/l3_qimen/l3_chenggu/l3_wuyunliuqi/l3_liuyao/l3_liuren/l3_meihua/l3_xiaoliuren/l3_heluolishu/l3_huangli/l3_hepan/l3_qimen_duanju/l3_shensha/l3_ziwei_liunian），无任何手算补充",
            "provenance": {f: _sha256_of(os.path.join(BASE, f)) for f in ENGINE_FILES},
        },
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "gender": gender, "lon": lon},
        "true_solar_time": r["true_solar_time"],
        "pillars": {k: r["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "hour")},
        "ten_gods": r["ten_gods"],
        "dayun": {"direction": fwd, "qiyun": qy, "jie_time": jie,
                  "jiao_time": jiao.strftime("%Y-%m-%d %H:%M"), "steps": dl},
        "liunian": liunian,
        "ziwei_hours": ziwei_hours,
    }
    if with_qimen:
        q = QM.compute(dt, lon)
        snap["qimen"] = None if "error" in q else {
            "dingju": {k: q["dingju"][k] for k in ("term", "dun", "yuan", "ju")},
            "zhifu_zhishi": {k: q["zhifu_zhishi"][k]
                             for k in ("xunshou", "yiyi", "zhifu_star", "zhifu_palace",
                                       "zhishi_door", "zhishi_palace")},
            "sanqi_liuyi_layout": {str(k): v for k, v in q["sanqi_liuyi"]["layout"].items()},
            "nine_stars": q["nine_stars"], "eight_doors": q["eight_doors"], "eight_gods": q["eight_gods"],
            "pan": q["pan"],
        }
    if with_chenggu:
        c = CG.compute(dt, lon, gender)
        snap["chenggu"] = None if "error" in c else {
            "lunar": c["lunar"],
            "bones_total_weight": c["total"]["weight"],
            "grade": c["poem"]["level"],
            "bones": {k: {"key": v["key"], "weight": v["weight"]} for k, v in c["bones"].items()},
            "poem": {"level": c["poem"]["level"], "text": c["poem"]["text"]},
        }
    # ---- 神煞（l3_shensha）：dt+lon ----
    try:
        ssr = SS.compute(dt, lon)
        snap["shensha"] = None if "error" in ssr else ssr["shensha"]
    except Exception as e:
        snap["shensha"] = {"error": f"shensha_exc: {e}"}
    # ---- 紫微大限流年（l3_ziwei_liunian）：dt+lon+性别+目标年 ----
    try:
        zt = ziwei_target_year if ziwei_target_year is not None else datetime.now().year
        zl = ZL.compute(dt, lon, gender, target_year=zt)
        snap["ziwei_liunian"] = None if "error" in zl else zl
    except Exception as e:
        snap["ziwei_liunian"] = {"error": f"ziwei_liunian_exc: {e}"}
    # 注入 reconcile 规则五/六 所需的字段（盲点 A/B 防线）
    snap["day_master"] = dm
    try:
        from l3_wangshuai import compute as _ws_compute
        ws = _ws_compute(dt, lon)
        snap["wangshuai"] = {
            "zonghe": ws.get("zonghe", {}),
            "de_ling": ws.get("de_ling"),
            "de_di": ws.get("de_di"),
            "de_shi": ws.get("de_shi"),
        }
    except Exception:
        snap["wangshuai"] = {}

    # ---- 五运六气（l3_wuyunliuqi）：仅需 dt ----
    try:
        w = WYLQ.compute(dt)
        snap["wuyunliuqi"] = None if "error" in w else w
    except Exception as e:
        snap["wuyunliuqi"] = {"error": f"wuyunliuqi_exc: {e}"}

    # ---- 六爻（l3_liuyao）：dt+lon（时间起卦 / lunar 模式） ----
    try:
        ly = LY.compute(dt, lon, mode="lunar")
        snap["liuyao"] = None if "error" in ly else ly
    except Exception as e:
        snap["liuyao"] = {"error": f"liuyao_exc: {e}"}

    # ---- 六壬（l3_liuren）：dt+lon+sex ----
    try:
        lr = LR.compute(dt, lon, sex=gender)
        snap["liuren"] = None if "error" in lr else lr
    except Exception as e:
        snap["liuren"] = {"error": f"liuren_exc: {e}"}

    # ---- 梅花（l3_meihua）：时间起卦 compute_time(dt, lon) ----
    try:
        mh = MH.compute_time(dt, lon, category="通用")
        snap["meihua"] = None if "error" in mh else mh
    except Exception as e:
        snap["meihua"] = {"error": f"meihua_exc: {e}"}

    # ---- 小六壬（l3_xiaoliuren）：dt+lon ----
    try:
        xlr = XLR.compute(dt, lon, category="通用")
        snap["xiaoliuren"] = None if "error" in xlr else xlr
    except Exception as e:
        snap["xiaoliuren"] = {"error": f"xiaoliuren_exc: {e}"}

    # ---- 河洛理数（l3_heluolishu）：dt+gender+lon ----
    try:
        hly = HLY.compute(dt, gender, lon=lon)
        snap["heluolishu"] = None if "error" in hly else hly
    except Exception as e:
        snap["heluolishu"] = {"error": f"heluolishu_exc: {e}"}

    # ---- 黄历（l3_huangli）：日盘 daily(d) ----
    try:
        snap["huangli"] = HL.daily(dt.date())
    except Exception as e:
        snap["huangli"] = {"error": f"huangli_exc: {e}"}

    # ---- 奇门断局（l3_qimen_duanju）：duanju(dt, lon) ----
    try:
        qdj = QMDJ.duanju(dt, lon=lon)
        snap["qimen_duanju"] = None if "error" in qdj else qdj
    except Exception as e:
        snap["qimen_duanju"] = {"error": f"qimen_duanju_exc: {e}"}

    # ---- 人际合盘（l3_hepan）：单人时合 self；如有 partner 则双人合盘 ----
    try:
        if partner_dt:
            pdt = datetime.strptime(partner_dt, "%Y-%m-%d %H:%M")
            hp = HP.compute(dt_str, pdt.strftime("%Y-%m-%d %H:%M"),
                            lon_a=lon, lon_b=(partner_lon if partner_lon is not None else lon),
                            scene="婚姻", year=dt.year)
            snap["hepan"] = None if isinstance(hp, dict) and "error" in hp else hp
        else:
            # 单人自合（仅 a，无 b），按合盘契约"差异无处藏身"标注
            hp = HP.compute(dt_str, None, lon_a=lon, scene="朋友", year=dt.year)
            snap["hepan"] = None if isinstance(hp, dict) and "error" in hp else hp
    except Exception as e:
        snap["hepan"] = {"error": f"hepan_exc: {e}"}

    return snap


def _dayun_pack(dt, lon, gender, steps):
    """兼容 dayun 不同返回宽度：取 (steps, qiyun_dict, jie, jiao, fwd)。"""
    out = BD.dayun(dt, lon, gender, steps=steps)
    dl = out[0]
    fwd = out[-1]
    if len(out) >= 8:  # (dl, 岁,月,天,时, jie, jiao, fwd)
        y, mo, d, h, jie, jiao = out[1], out[2], out[3], out[4], out[5], out[6]
        qy = {"age": y, "month": mo, "day": d, "hour": h}
    else:  # 防御：未来签名收窄为 (dl, qiyun, jie, jiao, fwd)
        qy, jie, jiao = out[1], out[2], out[3]
    return dl, qy, jie, jiao, fwd


# ---------------------------------------------------------------- ② 不变量
INVARIANTS = ["aud-inv-01", "aud-inv-02", "aud-inv-03", "aud-inv-04", "aud-inv-05"]


def _res(rid, ok, detail):
    return {"id": rid, "ok": bool(ok), "detail": detail}


def check_invariants(snap):
    """五条机械化不变量，返回 [{id, ok, detail}]；失败时 detail 给出实测值与期望值。

    aud-inv-01 排向与首步：fwd=="逆" → 首步干支序==月柱序-1；=="顺" → ==月柱序+1（重大错位事故防线）
    aud-inv-02 大运链连续：相邻步干支序按排向恒 ±1（顺+1/逆-1），start_year 相邻差恰 10
    aud-inv-03 流年公式：(y-4)%60 本地独立复算 == 引擎直出值，快照范围内每年全查
    aud-inv-04 紫微：每时辰 12 宫齐全且宫名唯一；十二时辰命宫地支两两不重且逐时辰恒进一位（方向一致）
    aud-inv-05 奇门：中五宫 star/door/shen 全 None；值符星/值使门所在宫与申报宫一致（中宫寄坤2 豁免）；
               值符宫天盘干含旬首六仪（寄宫豁免同上）
    """
    out = []
    if "error" in snap:
        return [_res(rid, False, f"快照本身带 error: {snap['error']}") for rid in INVARIANTS]

    # ---- aud-inv-01 排向与首步 ----
    fwd = snap["dayun"]["direction"]
    steps = snap["dayun"]["steps"]
    mseq = gz_seq(snap["pillars"]["month"])
    fseq = gz_seq(steps[0]["ganzhi"])
    want = (mseq - 1) % 60 if fwd == "逆" else (mseq + 1) % 60
    out.append(_res(
        "aud-inv-01", fseq == want,
        f"direction={fwd} 月柱={snap['pillars']['month']}(序{mseq}) 首步={steps[0]['ganzhi']}(序{fseq}) "
        f"期望序{want}({'月柱-1' if fwd == '逆' else '月柱+1'})"
        + ("" if fseq == want else " ← 疑似凭记忆错位（历史事故形态）")))

    # ---- aud-inv-02 大运链连续 ----
    step_dir = 1 if fwd == "顺" else -1
    bad_chain, bad_year = [], []
    for i in range(1, len(steps)):
        d = (gz_seq(steps[i]["ganzhi"]) - gz_seq(steps[i - 1]["ganzhi"])) % 60
        if d != step_dir % 60:
            bad_chain.append(f"{steps[i - 1]['ganzhi']}→{steps[i]['ganzhi']} 序差{(d - 0) % 60}≠{step_dir}")
        if steps[i]["start_year"] - steps[i - 1]["start_year"] != 10:
            bad_year.append(f"{steps[i - 1]['ganzhi']}({steps[i - 1]['start_year']})→"
                            f"{steps[i]['ganzhi']}({steps[i]['start_year']}) 起年差≠10")
    chain = [x["ganzhi"] for x in steps]
    years = [x["start_year"] for x in steps]
    out.append(_res(
        "aud-inv-02", not bad_chain and not bad_year,
        f"链={'→'.join(chain)} 起年={years[0]}..{years[-1]} 期望每步干支序{'+' if step_dir > 0 else '-'}1、起年差+10"
        + (f"；违例 {bad_chain + bad_year}" if (bad_chain or bad_year) else "")))

    # ---- aud-inv-03 流年公式 ----
    bad_ln = []
    for e in snap["liunian"]:
        want_gz = year_gz_formula(e["year"])
        if e["ganzhi"] != want_gz:
            bad_ln.append(f"{e['year']}:{e['ganzhi']}≠公式{want_gz}")
    out.append(_res(
        "aud-inv-03", not bad_ln,
        f"流年 {snap['liunian'][0]['year']}-{snap['liunian'][-1]['year']} 共 {len(snap['liunian'])} 年，"
        f"(y-4)%60 独立复算全查" + (f"；违例 {bad_ln[:5]}" if bad_ln else "全部一致")))

    # ---- aud-inv-04 紫微十二宫 + 命宫随时辰进位 ----
    zs = [z for z in snap["ziwei_hours"] if "error" not in z]
    errs = []
    names_ref = None
    for z in zs:
        names = [p["name"] for p in z["palaces"]]
        if len(names) != 12 or len(set(names)) != 12:
            errs.append(f"{z['hour']}时宫数/宫名异常: {len(names)}宫 重名{sorted({n for n in names if names.count(n) > 1})}")
        if names_ref is None:
            names_ref = names
        elif names != names_ref:
            errs.append(f"{z['hour']}时宫名序列漂移")
    ming = [rules.zhi_idx(z["minggong"]["zhi"]) for z in zs]
    diffs = [(ming[i] - ming[i - 1]) % 12 for i in range(1, len(ming))] if len(ming) > 1 else []
    distinct = len(set(ming)) == len(ming)
    uniform = len(set(diffs)) == 1 and diffs and diffs[0] in (1, 11)
    if len(zs) < len(snap["ziwei_hours"]):
        errs.append("存在时辰盘 error 未纳入")
    if not distinct:
        errs.append(f"命宫地支有重复: {[ZHI[x] for x in ming]}")
    if not uniform:
        errs.append(f"命宫逐时辰进位不一致: 差集{sorted(set(diffs))}")
    seq_txt = "→".join(z["minggong"]["zhi"] for z in zs)
    out.append(_res(
        "aud-inv-04", not errs,
        f"{len(zs)} 时辰命宫地支 {seq_txt}（每时辰 {(11 if (diffs and diffs[0] == 11) else 1)} 位即逆/顺一位，方向一致）"
        + ("；十二宫名齐全唯一" if not errs else f"；问题 {'; '.join(errs[:3])}")))

    # ---- aud-inv-05 奇门寄宫与值符值使自洽 ----
    q = snap.get("qimen")
    if not q:
        out.append(_res("aud-inv-05", True, "SKIP 快照未纳入奇门（with_qimen=False）"))
    else:
        p5 = q["pan"]["5"]
        none5 = p5["star"] is None and p5["door"] is None and p5["shen"] is None
        zzs = q["zhifu_zhishi"]
        zf_loc = next((int(p) for p, s in q["nine_stars"].items() if s == zzs["zhifu_star"]), None)
        zs_loc = next((int(p) for p, s in q["eight_doors"].items() if s == zzs["zhishi_door"]), None)

        def _loc_ok(loc, rep):  # 中宫寄坤二宫惯例：申报 5 宫时实际落 2 宫亦算自洽
            return loc is not None and (loc == rep or (rep == 5 and loc == 2))
        zf_ok = _loc_ok(zf_loc, zzs["zhifu_palace"])
        zs_ok = _loc_ok(zs_loc, zzs["zhishi_palace"])
        tian = q["pan"][str(zf_loc)]["tianpan_gan"] if zf_loc is not None else ""
        yiyi_ok = zzs["yiyi"] in tian
        ok = none5 and zf_ok and zs_ok and yiyi_ok
        out.append(_res(
            "aud-inv-05", ok,
            f"中五宫star/door/shen={[p5['star'], p5['door'], p5['shen']]}"
            f" 值符{zzs['zhifu_star']}实落{zf_loc}宫/申报{zzs['zhifu_palace']}宫"
            f" 值使{zzs['zhishi_door']}实落{zs_loc}宫/申报{zzs['zhishi_palace']}宫"
            f" 值符宫天盘「{tian}」含旬首仪「{zzs['yiyi']}」={yiyi_ok}"))

    order = {rid: i for i, rid in enumerate(INVARIANTS)}
    return sorted(out, key=lambda x: order[x["id"]])


# ---------------------------------------------------------------- ③ 文本对账
def _collect_gods(ten_gods):
    """m1 ten_gods 结构防御式抽取十神名集合。"""
    out = set()
    for v in (ten_gods or {}).values():
        if isinstance(v, str):
            out.add(v)
        elif isinstance(v, dict):
            out |= _collect_gods(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    out.add(x)
                elif isinstance(x, dict) and "god" in x:
                    out.add(x["god"])
    return {g for g in out if g in TEN_GODS_ALL}


def _snap_universe(snap):
    """快照可溯源全集：(干支对集合+出处映射, 单字干集合, 词表 dict)。全部引擎直出。"""
    gz, where, chars = set(), {}, set()

    def add(v, src):
        if v and v not in gz:
            gz.add(v)
            where[v] = src

    for k, v in snap["pillars"].items():
        add(v, f"四柱·{k}柱")
        chars |= set(v)
    for s in snap["dayun"]["steps"]:
        add(s["ganzhi"], "大运步骤")
    for e in snap["liunian"]:
        add(e["ganzhi"], "流年")
    for z in snap.get("ziwei_hours", []):
        for p in z.get("palaces", []):
            add(p["gan"] + p["zhi"], "紫微宫干支")
            chars.add(p["gan"])
    q = snap.get("qimen") or {}
    if q:
        add(q["zhifu_zhishi"]["xunshou"], "奇门旬首")
        for d in q["pan"].values():
            chars.add(d["dipan_gan"])
            chars |= set(d["tianpan_gan"])
            chars.add(q["zhifu_zhishi"]["yiyi"])

    vocab = {
        "十神": (_collect_gods(snap.get("ten_gods"))
                 | {s["god"] for s in snap["dayun"]["steps"]}
                 | {e["god"] for e in snap["liunian"]}),
        "紫微星": set(),
        "八门": set(), "九星": set(), "八神": set(),
    }
    for z in snap.get("ziwei_hours", []):
        for p in z.get("palaces", []):
            vocab["紫微星"] |= set(p["stars"]) | set(p["aux"])
    if q:
        for d in q["pan"].values():
            if d["star"]:
                vocab["九星"].add(d["star"])
            if d["door"]:
                vocab["八门"].add(d["door"])
            if d["shen"]:
                vocab["八神"].add(d["shen"])
    return gz, where, chars, vocab


def _ctx(text, i, ln):
    return text[max(0, i - 30): i + ln + 30].replace("\n", "⏎")


def reconcile(text, snap):
    """文本 ↔ 快照对账：{"matched","unverified","conflicts"}。

    规则一 干支溯源：文中每个干支对必须能在快照全集（四柱/大运/流年/紫微宫干支/奇门旬首等）找到，
            找不到 → unverified（附前后 30 字上下文）。
    规则二 大运配年：干支紧邻十年区间时，必须与大运某步 (ganzhi,start_year,end_year) 完全匹配；
            匹配不上且该干支在大运序列 → conflicts(错位)；不在大运序列但在别处（如四柱）→
            conflicts(冒名)，同样按冲突处理——配了十年区间即主张大运身份（宁多报不漏报）。
    规则三 词表比对（尽力而为）：十神/紫微星/八门/九星/八神出现而本盘词表没有 → unverified。
    单年份（不在任何区间内）：能对应快照任一年份字段则 matched，否则 unverified。
    """
    uni, where, chars, vocab = _snap_universe(snap)
    matched, unverified, conflicts = [], [], []
    seen_m, seen_u, seen_c = set(), set(), set()
    ranges = [(m.start(), m.end(), int(m.group(1)), int(m.group(2))) for m in RANGE_RE.finditer(text)]
    span_used = [(rs, re_) for rs, re_, _, _ in ranges]

    def in_range_span(i):
        return any(rs <= i < re_ for rs, re_ in span_used)

    # ---- 规则一 + 规则二：干支对 ----
    gz_hits = [(m.start(), m.end(), m.group()) for m in GZ_RE.finditer(text)]
    for gs, ge, gzv in gz_hits:
        # 找紧邻年份区间：优先前方 8 字内最近的，其次后方 8 字内
        cand = [(rs - ge, rs, re_, sy, ey) for rs, re_, sy, ey in ranges if 0 <= rs - ge <= 8]
        cand += [(gs - re_, rs, re_, sy, ey) for rs, re_, sy, ey in ranges if 0 <= gs - re_ <= 8]
        near = min(cand)[1:] if cand else None
        if near:
            rs, re_, sy, ey = near
            exact = next((s for s in snap["dayun"]["steps"]
                          if s["ganzhi"] == gzv and s["start_year"] == sy and s["end_year"] == ey), None)
            if exact:
                k = ("dayun_range", gzv, sy, ey)
                if k not in seen_m:
                    seen_m.add(k)
                    matched.append({"kind": "dayun_range", "value": f"{gzv}({sy}-{ey})",
                                    "step": {"index": exact["index"], "ganzhi": exact["ganzhi"],
                                             "start_year": exact["start_year"], "end_year": exact["end_year"],
                                             "god": exact["god"]}})
                continue
            in_dayun = [s for s in snap["dayun"]["steps"] if s["ganzhi"] == gzv]
            kc = (gzv, sy, ey)
            if kc in seen_c:
                continue
            seen_c.add(kc)
            if in_dayun:
                conflicts.append({
                    "kind": "shifted", "ganzhi": gzv, "claimed": [sy, ey], "context": _ctx(text, gs, ge - gs),
                    "actual": [{"index": s["index"], "start_year": s["start_year"], "end_year": s["end_year"]}
                               for s in in_dayun],
                    "detail": f"{gzv} 实为大运第{in_dayun[0]['index']}步"
                              f"({in_dayun[0]['start_year']}-{in_dayun[0]['end_year']})，"
                              f"文中写作 ({sy}-{ey}) —— 疑似序列错位/张冠李戴"})
            else:
                src = where.get(gzv)
                conflicts.append({
                    "kind": "not_in_dayun", "ganzhi": gzv, "claimed": [sy, ey],
                    "context": _ctx(text, gs, ge - gs), "appears_in": src,
                    "detail": f"{gzv} 不在本命大运序列（" +
                              (f"仅见于{src}）" if src else "且不在快照任何可溯源集合）") +
                              f"，文中却配十年区间 ({sy}-{ey}) 冒充大运步骤"})
            continue
        # 无区间相伴 → 规则一纯溯源
        if gzv in uni:
            if ("ganzhi", gzv) not in seen_m:
                seen_m.add(("ganzhi", gzv))
                matched.append({"kind": "ganzhi", "value": gzv, "found_in": where.get(gzv)})
        else:
            if ("ganzhi", gzv) not in seen_u:
                seen_u.add(("ganzhi", gzv))
                unverified.append({"kind": "ganzhi", "value": gzv,
                                   "context": _ctx(text, gs, ge - gs),
                                   "reason": "快照全集（四柱/大运/流年/紫微宫干支/奇门旬首）中不存在"})

    # ---- 单年份（区间外）----
    verifiable_years = ({e["year"] for e in snap["liunian"]}
                        | {s["start_year"] for s in snap["dayun"]["steps"]}
                        | {s["end_year"] for s in snap["dayun"]["steps"]}
                        | {int(snap["input"]["datetime"][:4])})
    for m in YEAR_RE.finditer(text):
        if in_range_span(m.start()):
            continue
        y = int(m.group())
        if ("year", y) in seen_m or ("year", y) in seen_u:
            continue
        if y in verifiable_years:
            seen_m.add(("year", y))
            matched.append({"kind": "year", "value": str(y)})
        else:
            seen_u.add(("year", y))
            unverified.append({"kind": "year", "value": str(y), "context": _ctx(text, m.start(), 4),
                               "reason": "快照流年范围/大运起止年/出生年之外，无法机械溯源"})

    # ---- 规则三：词表比对（尽力而为）----
    CANON = [("十神", TEN_GODS_ALL), ("紫微星", MAIN14_ALL + AUX_ALL),
             ("八门", DOORS_ALL), ("九星", STARS_ALL), ("八神", GODS_ALL)]
    for cat, names in CANON:
        if cat == "八门" and not (snap.get("qimen") or {}).get("eight_doors"):
            continue  # 快照未含奇门则跳过该类
        for w in names:
            i = text.find(w)
            if i < 0:
                continue
            if w in vocab[cat]:
                if (cat, w) not in seen_m:
                    seen_m.add((cat, w))
                    matched.append({"kind": f"word:{cat}", "value": w})
            else:
                if (cat, w) not in seen_u:
                    seen_u.add((cat, w))
                    unverified.append({"kind": f"word:{cat}", "value": w,
                                       "context": _ctx(text, i, len(w)),
                                       "reason": f"{cat}「{w}」不在本盘快照词表"})

    # ---- 规则四：双源同引一致性 ----
    # 同一大运步骤 ganzhi 在文中 ≥2 位置出现时，start_year/end_year/god 必须全等
    dayun_occurrences = {}  # gz -> list of (start_year, end_year, god)
    for m in matched:
        if m.get("kind") == "dayun_range":
            gz = m["value"][:2]  # 截断 (sy-ey) 前缀
            d = m["step"]
            dayun_occurrences.setdefault(gz, []).append(
                (d["start_year"], d["end_year"], d.get("god", "?")))
    # 扫描冲突中也收集
    for c in conflicts:
        if c.get("kind") in ("shifted", "not_in_dayun"):
            gz = c.get("ganzhi", "")
            claimed = c.get("claimed", [])
            if len(claimed) == 2:
                dayun_occurrences.setdefault(gz, []).append((claimed[0], claimed[1], "?"))
    # 检测双源不一致
    for gz, occs in dayun_occurrences.items():
        if len(occs) < 2:
            continue
        # 标准化
        canon = occs[0]
        diffs = [o for o in occs if o != canon]
        if diffs:
            conflicts.append({
                "kind": "double_source_mismatch",
                "ganzhi": gz,
                "canonical": {"start_year": canon[0], "end_year": canon[1], "god": canon[2]},
                "all_occurrences": [{"start_year": o[0], "end_year": o[1], "god": o[2]} for o in occs],
                "detail": f"大运{gz}在文中出现 {len(occs)} 次，年份/十神不完全一致："
                          f"canon=({canon[0]}-{canon[1]},{canon[2]})，diffs={diffs}。"
                          f"违反铁律4『双源同引』——必须以快照 step 为准，"
                          f"其他位置要么改成与快照一致、要么删去、要么改用「见大运表」式引用。"
            })

    # ---- 规则五：旺衰 ws-04 score 跨段一致性（盲点 A 防线）----
    # 文中若出现 "XX分偏弱/中和/偏旺" 等档位分值，分值必须等于 snap.wangshuai.zonghe.score
    # 仅匹配 [0,100] 区间且明确带档位形容词的"X分"，避免误中"得地5分"等无关用法
    ws_level = (snap.get("wangshuai", {}) or {}).get("zonghe", {}).get("level", "")
    ws_score = (snap.get("wangshuai", {}) or {}).get("zonghe", {}).get("score", None)
    if ws_level and ws_score is not None:
        # 匹配"X分"（双向：X 分在档位词前/后均可），档位词取窗口内 10 字内
        LEVELS = "(中和|偏弱|偏旺|极旺|极弱|旺|弱|强|太旺|太弱)"
        # 形式 A：X分...档位词（顺序）
        score_lvl_pat = re.compile(
            r"(?<![0-9.])(\d{1,3}(?:\.\d+)?)\s*分"
            r"[\s，,、）)]*"
            r"(中和|偏弱|偏旺|极旺|极弱|旺|弱|强|太旺|太弱)")
        # 形式 B：档位词...（X分）
        lvl_score_pat = re.compile(
            r"(中和|偏弱|偏旺|极旺|极弱|旺|弱|强|太旺|太弱)"
            r"[\s（(]*"
            r"(?<![0-9.])(\d{1,3}(?:\.\d+)?)\s*分")
        for m in score_lvl_pat.finditer(text):
            claimed = float(m.group(1))
            if not (0 <= claimed <= 100):
                continue
            claimed_level = m.group(2)
            if abs(claimed - ws_score) > 0.5:
                conflicts.append({
                    "kind": "ws_score_drift",
                    "claimed_score": claimed,
                    "snap_score": ws_score,
                    "snap_level": ws_level,
                    "context": _ctx(text, m.start(), m.end() - m.start()),
                    "detail": f"文中出现 {claimed} 分{claimed_level}，"
                              f"快照 ws-04 实际为 {ws_score} 分（{ws_level}）——"
                              f"违反'禁止凭印象手填分值'硬约束（盲点 A 防线），疑为旧值残留。"
                })
        for m in lvl_score_pat.finditer(text):
            claimed = float(m.group(2))
            if not (0 <= claimed <= 100):
                continue
            claimed_level = m.group(1)
            if abs(claimed - ws_score) > 0.5:
                conflicts.append({
                    "kind": "ws_score_drift",
                    "claimed_score": claimed,
                    "snap_score": ws_score,
                    "snap_level": ws_level,
                    "context": _ctx(text, m.start(), m.end() - m.start()),
                    "detail": f"文中出现{claimed_level}{claimed} 分，"
                              f"快照 ws-04 实际为 {ws_score} 分（{ws_level}）——"
                              f"违反'禁止凭印象手填分值'硬约束（盲点 A 防线），疑为旧值残留。"
                })

    # ---- 规则六：藏干十神日主映射（盲点 B 防线）----
    # 文中若形如 "X 偏财" 或 "X 正印" 列举藏干 X 的十神，
    # 必须等于 DM_GOD[日主][X]，否则冲突。
    day_master = snap.get("day_master", "") or snap.get("input", {}).get("day_master", "")
    DM_GOD = {  # 与 l4_data_harvest.py 同步
        "甲": {"甲":"比肩","乙":"劫财","丙":"食神","丁":"伤官","戊":"偏财","己":"正财","庚":"七杀","辛":"正官","壬":"偏印","癸":"正印"},
        "乙": {"甲":"劫财","乙":"比肩","丙":"伤官","丁":"食神","戊":"正财","己":"偏财","庚":"正官","辛":"七杀","壬":"正印","癸":"偏印"},
        "丙": {"甲":"偏印","乙":"正印","丙":"比肩","丁":"劫财","戊":"食神","己":"伤官","庚":"偏财","辛":"正财","壬":"七杀","癸":"正官"},
        "丁": {"甲":"正印","乙":"偏印","丙":"劫财","丁":"比肩","戊":"伤官","己":"食神","庚":"正财","辛":"偏财","壬":"正官","癸":"七杀"},
        "戊": {"甲":"七杀","乙":"正官","丙":"偏印","丁":"正印","戊":"比肩","己":"劫财","庚":"食神","辛":"伤官","壬":"偏财","癸":"正财"},
        "己": {"甲":"正官","乙":"七杀","丙":"正印","丁":"偏印","戊":"劫财","己":"比肩","庚":"伤官","辛":"食神","壬":"正财","癸":"偏财"},
        "庚": {"甲":"偏财","乙":"正财","丙":"七杀","丁":"正官","戊":"偏印","己":"正印","庚":"比肩","辛":"劫财","壬":"食神","癸":"伤官"},
        "辛": {"甲":"正财","乙":"偏财","丙":"正官","丁":"七杀","戊":"正印","己":"偏印","庚":"劫财","辛":"比肩","壬":"伤官","癸":"食神"},
        "壬": {"甲":"食神","乙":"伤官","丙":"偏财","丁":"正财","戊":"七杀","己":"正官","庚":"偏印","辛":"正印","壬":"比肩","癸":"劫财"},
        "癸": {"甲":"伤官","乙":"食神","丙":"正财","丁":"偏财","戊":"正官","己":"七杀","庚":"正印","辛":"偏印","壬":"劫财","癸":"比肩"},
    }
    god_map = DM_GOD.get(day_master, {})
    if god_map:
        # 抓 "X偏财/比肩/正印/..."，X ∈ 十天干
        cg_pat = re.compile(r"([甲乙丙丁戊己庚辛壬癸])(偏财|正财|比肩|劫财|食神|伤官|七杀|正官|偏印|正印)")
        for m in cg_pat.finditer(text):
            cgan = m.group(1)
            cgod = m.group(2)
            expected = god_map.get(cgan)
            if expected and expected != cgod:
                # 排除"日主辛金"之类（日主自身不用映射）
                if f"{cgan}{cgod}" == "辛比肩" and cgan == day_master:
                    continue
                conflicts.append({
                    "kind": "ten_god_mismatch",
                    "canggan": cgan, "claimed_god": cgod,
                    "day_master": day_master, "expected_god": expected,
                    "context": _ctx(text, m.start(), m.end() - m.start()),
                    "detail": f"日主{day_master}对应{cgan}应为{expected}，文中写{cgod}——"
                              f"违反'藏干十神日主映射'硬约束（盲点 B 防线）"
                })

    # ---- 规则七：流年→年龄硬约束（盲点 C 防线）----
    # 抓"X 岁 YYYY"形式：岁数+年份应满足 year-birth_year == age（容差 ±1，跨生日）
    birth_year = None
    try:
        dt_str = snap.get("input", {}).get("datetime", "")
        if dt_str:
            birth_year = int(dt_str[:4])
    except (ValueError, TypeError):
        pass
    if birth_year:
        # 严格匹配"X 岁"独立单元（前面非数字/连字符/中文数字），后接 YYYY 年
        age_year_pat = re.compile(
            r"(?<![0-9\-—])(\d{1,2})\s*[岁歳]\s*[（(]?\s*(\d{4})")
        for m in age_year_pat.finditer(text):
            try:
                age = int(m.group(1))
                year = int(m.group(2))
            except ValueError:
                continue
            expected = year - birth_year
            if abs(age - expected) > 1:
                conflicts.append({
                    "kind": "age_year_mismatch",
                    "claimed": {"age": age, "year": year},
                    "expected_age": expected,
                    "birth_year": birth_year,
                    "context": _ctx(text, m.start(), m.end() - m.start()),
                    "detail": f"文中写{age}岁{year}年，但 {year}-{birth_year}={expected}岁——"
                              f"违反'流年→年龄'硬约束（盲点 C 防线），"
                              f"疑为凭印象手填年龄"
                })

    return {"matched": matched, "unverified": unverified, "conflicts": conflicts}


# ---------------------------------------------------------------- CLI
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="L4 输出审计层：snapshot / check / reconcile（结果一律落 --out JSON）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("snapshot", help="生成全量快照（四柱/大运/流年/紫微十二时辰/奇门/称骨）")
    ps.add_argument("--datetime", required=True, help="北京时间 YYYY-MM-DD HH:MM")
    ps.add_argument("--gender", default="男", choices=("男", "女"))
    ps.add_argument("--lon", type=float, default=120.0)
    ps.add_argument("--hours", help="紫微采样小时逗号串，默认 0,2,...,22")
    ps.add_argument("--years-from", type=int, default=2020)
    ps.add_argument("--years-to", type=int, default=2040)
    ps.add_argument("--no-qimen", action="store_true")
    ps.add_argument("--no-chenggu", action="store_true")
    ps.add_argument("--ziwei-year", type=int, default=None,
                    help="紫微大限/流年目标年（默认=当前年）")
    ps.add_argument("--partner-datetime", help="合盘对方北京时间 YYYY-MM-DD HH:MM（可选）")
    ps.add_argument("--partner-gender", choices=("男", "女"), help="合盘对方性别（可选）")
    ps.add_argument("--partner-lon", type=float, help="合盘对方经度（默认=主体经度）")
    ps.add_argument("--out", required=True, help="输出 JSON 路径")

    pc = sub.add_parser("check", help="对已有快照跑五条不变量 aud-inv-01..05")
    pc.add_argument("--snap", required=True, help="快照 JSON 路径")
    pc.add_argument("--out", required=True, help="输出 JSON 路径")

    pr = sub.add_parser("reconcile", help="文本对账（抓无法溯源/错位数据）")
    pr.add_argument("--text", required=True, help="待对账文本文件路径（UTF-8）")
    pr.add_argument("--snap", required=True, help="快照 JSON 路径")
    pr.add_argument("--out", required=True, help="输出 JSON 路径")

    a = ap.parse_args()
    if a.cmd == "snapshot":
        hours = [int(x) for x in a.hours.split(",")] if a.hours else None
        snap = snapshot(a.datetime, a.gender, a.lon, hours=hours,
                        years=(a.years_from, a.years_to),
                        with_qimen=not a.no_qimen, with_chenggu=not a.no_chenggu,
                        ziwei_target_year=a.ziwei_year,
                        partner_dt=a.partner_datetime,
                        partner_gender=a.partner_gender,
                        partner_lon=a.partner_lon)
        dump(snap, a.out)
        if "error" in snap:
            print(f"ERROR snapshot: {snap['error']}")
            sys.exit(2)
        print(f"OK snapshot -> {a.out} "
              f"(pillars={'/'.join(snap['pillars'][k] for k in ('year', 'month', 'day', 'hour'))} "
              f"dayun={snap['dayun']['direction']}:{snap['dayun']['steps'][0]['ganzhi']} "
              f"liunian={len(snap['liunian'])} ziwei_hours={len(snap['ziwei_hours'])} "
              f"qimen={'Y' if snap.get('qimen') else 'N'} "
              f"ziwei_liunian={'Y' if snap.get('ziwei_liunian') else 'N'})")
    elif a.cmd == "check":
        with open(a.snap, encoding="utf-8") as f:
            snap = json.load(f)
        res = check_invariants(snap)
        dump(res, a.out)
        nok = sum(1 for x in res if x["ok"])
        for x in res:
            print(f"{'PASS' if x['ok'] else 'FAIL'} {x['id']}")
        print(f"{'OK' if nok == len(res) else 'FAIL'} {nok}/{len(res)} -> {a.out}")
        sys.exit(0 if nok == len(res) else 1)
    else:
        with open(a.text, encoding="utf-8") as f:
            text = f.read()
        with open(a.snap, encoding="utf-8") as f:
            snap = json.load(f)
        rep = reconcile(text, snap)
        dump(rep, a.out)
        print(f"OK reconcile matched={len(rep['matched'])} "
              f"unverified={len(rep['unverified'])} conflicts={len(rep['conflicts'])} -> {a.out}")


if __name__ == "__main__":
    main()
