# -*- coding: utf-8 -*-
"""l3_bazi_liuri.py — L3-2b 八字流日模块（lr-01..lr-03）。v1.1 新增文件（不改任何冻结模块）。

定位（审计定稿口径）：流日为**非经典层级**——古典主干止于流年（命局→大运→小运→流年），
流月为实务辅助层（bd-04）；流日/流时颗粒度更细，断语一致性与可复核性越差、事后附会空间越大。
本模块只出"数据层+关系层"，不作吉凶断语；notes 随件声明。

口径：
- lr-01 流日序列：流年/流月/流日干支 = 目标日"真太阳时正午"经 m1.compute 直出（立春换年 r3、
  节换月 r4、真太阳时子正换日 r1 全继承）。取真太阳时正午使任意经度下的日界修正不跨日
  （bj_at_true_solar 反解北京时，极端经度亦稳）；节交接日附 jie_note（当日有节交接时注明）。
  注：负经度区真太阳时正午对应北京时在当日夜间至次日凌晨，若目标日北京时取样越出 m1 支持区间
  （1949-01-01 03:30 ~ 2100-12-31 20:30）则报错——可用日期窗相应收缩。
- lr-02 关系层：十神（流日干对日主，r5）+ 合冲刑害关系（天干五合/相克，地支六合/六冲/六害/半合/自刑/三刑），
  表复用 l3_hepan（《三命通会》《渊海子平》底本，hp-01 同源）；三刑口径同 hp-01"三字俱全方成刑"，
  池=原局四支∪流日支（流日盘=原局+流日两体）；逐对全列、不套用 hp-01 单值优先级链
  （合冲刑害可并存，取舍由使用方，模块不作裁决）。
- lr-03 黄历层：l3_huangli.daily 直出引用（hl-01 建除 / hl-02 黄黑道 / hl-03 神煞），双源同引。
- 大运定位：l3_bazi_daliu.compute 的 bd-01 步序列按年份区间粗定位（交运月份/日期见 qiyun 明细，
  跨交运年内的边界日以年份为粗界，输出注明）。

差异无处藏身：每输出项带 rule_id（lr-xx）+ source + alt；对拍（--compare）= 日柱用 lunar-python
独立 oracle（60 随机 + 8 边界样本），节交接日的年/月柱因 oracle 按日期粒度、m1 按时刻粒度，
不作对比（如实注明）。
"""
import argparse, json, os, random, sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import m1
import l3_hepan as H
import l3_huangli
import l3_bazi_daliu

PILLAR_KEYS = ("year", "month", "day", "hour")
PILLAR_NAMES = {"year": "年", "month": "月", "day": "日", "hour": "时"}


def bj_at_true_solar(ts, lon):
    """求北京时（分钟精度）使 m1.true_solar(bj, lon) ≈ ts：bj = ts − 经度修正 − EOT(bj)，迭代 3 次收敛
    （EOT 对输入日缓变）；四舍五入到分（m1 拒秒级输入）。调用方须复核往返差（本模块内部恒 ≤1 分钟）。"""
    off = (lon - 120) * 4
    bj = ts - timedelta(minutes=off)
    for _ in range(3):
        bj = ts - timedelta(minutes=off + m1.eot_minutes(bj))
    return (bj + timedelta(seconds=30)).replace(second=0, microsecond=0)


def pair_relations(a_gz, b_gz, zhi_pool):
    """流日柱 a_gz 对目标柱 b_gz 的因对关系（逐对全列）：{"gan": [...], "zhi": [...]}。
    干：五合/相克（有序标注方向）；支：六合/六冲/六害/半合（同三合局，含同支归局）/自刑/三刑（三字俱全）。"""
    out = {"gan": [], "zhi": []}
    ag, az, bg, bz = a_gz[0], a_gz[1], b_gz[0], b_gz[1]
    if (ag, bg) in H.WU_HE:
        out["gan"].append(f"五合（{ag}{bg}合{H.WU_HE[(ag, bg)]}）")
    elif (bg, ag) in H.WU_HE:
        out["gan"].append(f"五合（{bg}{ag}合{H.WU_HE[(bg, ag)]}）")
    if (ag, bg) in H.GAN_KE:
        out["gan"].append(f"相克（{ag}克{bg}）")
    if (bg, ag) in H.GAN_KE:
        out["gan"].append(f"受克（{bg}克{ag}）")
    if H._pair_rel(az, bz, H.LIU_HE, "六合"):
        out["zhi"].append(f"六合（{az}{bz}）")
    if H._pair_rel(az, bz, H.LIU_CHONG, "六冲"):
        out["zhi"].append(f"六冲（{az}{bz}）")
    if H._pair_rel(az, bz, H.LIU_HAI, "六害"):
        out["zhi"].append(f"六害（{az}{bz}）")
    # 半合含同支归局（hp-01 口径，局名分歧见 arbitration_log hp-x02）；同支自刑优先不入半合（hp-01 同链）
    if not (az == bz and (az, az) in H.SAN_XING) and H._sanhe_rel(az, bz):
        out["zhi"].append(f"半合（{az}{bz}半合{H._sanhe_rel(az, bz)}局）")
    if az == bz and (az, az) in H.SAN_XING:
        out["zhi"].append(f"自刑（{az}{az}）")
    elif az != bz and H._xing_ok(az, bz, zhi_pool):
        name = H.SAN_XING.get((az, bz)) or H.SAN_XING.get((bz, az))
        out["zhi"].append(f"三刑（{az}{bz}·{name}）")
    return out


def dayun_at(rbd, d):
    """目标日期 → 当值大运步（bd-01 步序列按年份区间定位；8 步外/交运前返回 None+注明）。"""
    for it in rbd["dayun"]["list"]:
        if it["start_year"] <= d.year <= it["end_year"]:
            return {"index": it["index"], "ganzhi": it["ganzhi"], "god": it["god"],
                    "start_year": it["start_year"], "end_year": it["end_year"],
                    "rule_id": "bd-01", "source": "l3_bazi_daliu bd-01 大运步（年份区间粗定位；交运月日内精度见 qiyun 明细）"}
    return {"ganzhi": None, "note": f"{d.year} 年落 bd-01 输出 8 步区间外（交运前或第 8 步后）", "rule_id": "bd-01"}


def jie_note(d):
    """目标日是否有节交接（solar_terms.csv 12 节；时刻级，供流月/流年柱交接日标注）。"""
    return [{"term": t["term"], "datetime": t["datetime"], "rule_id": "r4", "source": "solar_terms.csv"}
            for t in m1.load_terms() if t["datetime"][:10] == d.isoformat()]


def load_chart(birth_dt, lon, sex):
    """出生信息 → 流日计算上下文 {pillars(原局四柱), day_master, dayun_r(bd-01 全量)}；非法输入返回 {"error"}。"""
    rb = m1.compute(birth_dt, lon)
    if "error" in rb:
        return {"error": "出生: " + rb["error"]}
    rbd = l3_bazi_daliu.compute(birth_dt, lon, sex)
    if "error" in rbd:
        return {"error": "出生: " + rbd["error"]}
    return {"pillars": {k: rb["pillars"][k]["ganzhi"] for k in PILLAR_KEYS},
            "day_master": rb["ten_gods"]["day_master"], "dayun_r": rbd}


def day_entry(d, lon, chart, with_huangli=True):
    """目标日全量：流年/流月/流日柱（lr-01）+ 十神 + 关系（lr-02）+ 黄历引用（lr-03）+ 节交接注。"""
    r = m1.compute(bj_at_true_solar(datetime(d.year, d.month, d.day, 12, 0), lon), lon)
    if "error" in r:
        return {"date": d.isoformat(), "error": r["error"]}
    P = {k: r["pillars"][k]["ganzhi"] for k in PILLAR_KEYS}
    dm = chart["day_master"]
    day_gz = P["day"]
    # 三刑池=原局四支∪流日支（不含流年/流月/大运支，声明见 notes）；hp-01 三字俱全口径
    zhi_pool = {p[1] for p in chart["pillars"].values()} | {day_gz[1]}
    du = dayun_at(chart["dayun_r"], d)
    pool_src = "池=原局四支∪流日支，不含流年/流月/大运支（hp-01 同口径：三刑三字俱全）"
    rel = {}
    for k in PILLAR_KEYS:
        rel[PILLAR_NAMES[k] + "柱"] = pair_relations(day_gz, chart["pillars"][k], zhi_pool)
    rel["流年"] = pair_relations(day_gz, P["year"], zhi_pool)
    rel["流月"] = pair_relations(day_gz, P["month"], zhi_pool)
    rel["大运"] = pair_relations(day_gz, du["ganzhi"], zhi_pool) if du["ganzhi"] else None
    out = {
        "date": d.isoformat(),
        "shape": {
            "year": P["year"], "month": P["month"], "day": day_gz,
            "rule_id": "lr-01",
            "source": "m1.compute 直出（真太阳时正午取样；r3 立春换年/r4 节换月/r1 真太阳时子正换日）",
            "alt": "流月交接日：节在当日某时刻，正午取样落在交接前后一侧；精确到时辰需流时层（非经典层级，本模块不提供）",
        },
        "day_master_god": {"day_master": dm, "gan": day_gz[0], "god": m1.ten_god(dm, day_gz[0]),
                           "rule_id": "r5", "source": "m1.ten_god（rules.py 五行关系）"},
        "day_zhi_gods": m1.branch_gods(dm, day_gz[1], m1.load_canggan()),
        "relations": dict(rel, rule_id="lr-02",
                          source="十神 r5；合冲刑害表复用 l3_hepan（《三命通会》六合/三合/冲/害 + 《渊海子平》十干合/三刑）",
                          alt="逐对全列不套 hp-01 优先级链；同支口径（自刑优先/半合归局）与 hp-01 一致；" + pool_src),
        "dayun_at": du,
        "jie_note": jie_note(d),
    }
    if with_huangli:
        hl = l3_huangli.daily(d)
        if "error" not in hl:
            out["huangli"] = {
                "ganzhi": hl["ganzhi"], "lunar": hl["lunar"],
                "jianchu": {"name": hl["jianchu"]["name"], "ji": hl["jianchu"]["ji"]},
                "huanghei": {"name": hl["huanghei"]["name"], "dao": hl["huanghei"]["dao"]},
                "shensha": [h["name"] for h in hl["shensha"]["hits"]],
                "yi": hl["yi_ji"]["yi"], "ji": hl["yi_ji"]["ji"],
                "rule_id": "lr-03",
                "source": "l3_huangli.daily 直出引用（hl-01 建除 / hl-02 黄黑道 / hl-03 神煞 / hl-03b 宜忌）",
            }
    return out


def compute(birth_dt, lon, sex, start_date, days=1, with_huangli=True):
    """出生信息 + 目标起始日 → 流日序列 JSON。
    birth_dt=北京时 datetime（出生记录，四柱口径全继承 m1）；start_date=datetime.date；days 1..62。"""
    if not 1 <= days <= 62:
        return {"error": f"错误: days={days} 超出 1..62（流日层为逐日明细，限制输出规模）"}
    chart = load_chart(birth_dt, lon, sex)
    if "error" in chart:
        return chart
    rbd = chart["dayun_r"]
    days_out = []
    for i in range(days):
        days_out.append(day_entry(start_date + timedelta(days=i), lon, chart, with_huangli))
    return {
        "rule": "lr-01",
        "positioning": ("流日=非经典层级（审计定稿）：古典主干止于流年，流月为实务辅助；颗粒度越细断语一致性"
                        "与可复核性越差、事后附会空间越大。本模块只出数据层+关系层，不作吉凶断语。"),
        "input": {"birth": birth_dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "sex": sex,
                  "start_date": start_date.isoformat(), "days": days, "tz": "UTC+8 北京时间",
                  "sample": "目标日=真太阳时正午取样（bj_at_true_solar 反解，任意经度日界稳定）"},
        "chart": {"pillars": chart["pillars"], "day_master": chart["day_master"],
                  "dayun": [{"index": it["index"], "ganzhi": it["ganzhi"], "god": it["god"],
                             "start_year": it["start_year"], "end_year": it["end_year"]} for it in rbd["dayun"]["list"]],
                  "qiyun": rbd["dayun"].get("qiyun"), "rule_id": "bd-01",
                  "source": "l3_bazi_daliu.compute（bd-01 大运步；起运口径 r3/r4 同源）"},
        "days": days_out,
        "notes": [
            "定位声明：非经典层级（古典主干止于流年），只提供数据与关系层，慎用、不作吉凶断语（指本模块不推断；黄历层 yi/ji 等标记为 l3_huangli 引用数据，属其体系自有口径）",
            "三刑池=原局四支∪流日支（不含流年/流月/大运支）：三刑三字俱全判定仅就原局+流日两体，跨运年组合三刑不标注",
            "流年/流月/流日干支=m1 直出；关系层表复用 l3_hepan（底本见 lr-02 source）；黄历层引用 l3_huangli.daily",
            "流月交接日 jie_note 标注节时刻；正午取样对当日节交接后/前一侧取值，详见 shape.alt",
        ],
    }


# ---------------------------------------------------------------- 对拍（lunar-python oracle）
def _rand_dates(seed, n, lo="1950-01-01", hi="2099-12-28"):
    rng = random.Random(seed)
    lo_d, hi_d = datetime.fromisoformat(lo).date(), datetime.fromisoformat(hi).date()
    span = (hi_d - lo_d).days
    return sorted({lo_d + timedelta(days=rng.randint(0, span)) for _ in range(n)})


def compare(seed=20260915, n=60):
    """日柱 oracle 对拍：60 随机 + 8 边界样本，逐日 vs lunar-python（独立实现源）。
    节交接日的年/月柱 oracle 按日期粒度、m1 按时刻粒度，不作对比（如实注明）；
    其余样本年柱（立春口径）+ 月柱（节换月口径）同对。结果落 report/l3_bazi_liuri_report.txt。"""
    from lunar_python import Solar
    birth = datetime(1990, 5, 1, 10, 0)
    chart = load_chart(birth, 120.0, "男")
    assert "error" not in chart
    jie_days = {t["datetime"][:10] for t in m1.load_terms()}
    BOUND = ["2024-02-03", "2024-02-04", "2024-03-05", "2000-02-29", "2024-01-31", "2024-03-01",
             "1949-01-02", "2100-12-30"]
    dates = [datetime.fromisoformat(s).date() for s in BOUND] + _rand_dates(seed, n)
    mism, checked, skipped = [], 0, 0
    for d in sorted(set(dates)):
        e = day_entry(d, 120.0, chart, False)
        lu = Solar.fromYmd(d.year, d.month, d.day).getLunar()
        got, want = e["shape"]["day"], lu.getDayInGanZhi()
        if got != want:
            mism.append((d.isoformat(), "day", got, want))
        checked += 1
        if d.isoformat() in jie_days:
            skipped += 1  # 节交接日：年/月柱粒度分歧不对比
        else:
            for k, fn in (("year", lu.getYearInGanZhiByLiChun), ("month", lu.getMonthInGanZhiExact)):
                got, want = e["shape"][k], fn()
                if got != want:
                    mism.append((d.isoformat(), k, got, want))
                checked += 1
    lines = [f"l3_bazi_liuri 对拍（lunar-python oracle，seed={seed}）",
             f"样本 {len(set(dates))} 日（含 8 边界），检查项 {checked}，差异 {len(mism)}，节交接日年/月柱跳过 {skipped} 日",
             "口径：day=日柱（全样本）；year=立春换年、month=节换月（节交接日 oracle 按日期粒度、不对比）"]
    for m in mism:
        lines.append("  差异: " + str(m))
    out = "\n".join(lines) + "\n"
    print(out)
    with open(os.path.join(BASE, "report", "l3_bazi_liuri_report.txt"), "w", encoding="utf-8") as f:
        f.write(out)
    return {"checked": checked, "mism": len(mism), "skipped": skipped}


def main():
    ap = argparse.ArgumentParser(description="L3-2b 八字流日（lr-01..03；非经典层级，数据+关系层）")
    ap.add_argument("--datetime", help="出生北京时 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--sex", default="男", choices=("男", "女"))
    ap.add_argument("--start-date", help="目标起始日 YYYY-MM-DD")
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--no-huangli", action="store_true")
    ap.add_argument("--compare", action="store_true", help="lunar-python oracle 对拍（独立实现源）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.compare:
        sys.exit(0 if compare()["mism"] == 0 else 1)
    if not a.datetime or not a.start_date:
        sys.exit("错误: 需 --datetime 与 --start-date（或 --compare）")
    dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    sd = datetime.strptime(a.start_date, "%Y-%m-%d").date()
    r = compute(dt, a.lon, a.sex, sd, a.days, not a.no_huangli)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        c = r["chart"]
        print(f"原局: {c['pillars']}  日主 {c['day_master']}  [ {r['positioning'][:28]}… ]")
        for e in r["days"]:
            if "error" in e:
                print(f"{e['date']}  {e['error']}")
                continue
            s = e["shape"]
            rel = e["relations"]
            hits = [f"{k}:{','.join(v['gan'] + v['zhi'])}" for k, v in rel.items()
                    if isinstance(v, dict) and (v["gan"] or v["zhi"])]
            hl = e.get("huangli")
            hlt = f"  黄历:{hl['jianchu']['name']}/{hl['huanghei']['name']}" if hl else ""
            print(f"{e['date']} 流年{s['year']} 流月{s['month']} 流日{s['day']}"
                  f"（{e['day_master_god']['god']}）大运{(e['dayun_at']['ganzhi'] or '—')}{hlt}")
            for h in hits:
                print(f"    {h}")


if __name__ == "__main__":
    main()
