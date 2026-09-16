# -*- coding: utf-8 -*-
"""l4_data_harvest.py — 快照确定性数据自动搬运工具（v1.0）

设计目标：把"四柱/大运/流年/神煞/紫微/称骨/河洛/梅花/六爻/小六壬/大六壬/五运六气/奇门/黄历"
全部确定性数据从快照中格式化为可直接复制到草稿的"引用区段"，人工只在引用区下方做
取象推断/综合分析，禁止在引用区段内手写任何确定性数据。

输入：
  --t1-bazi   t1_bazi.json 路径
  --t1-ziwei  t1_ziwei.json 路径
  --t4-all    t4_b_all.json 路径
  --target    命造标识（如 "B 男命"）
  --out       输出 .txt 路径

输出：txt 文件，结构分 4 个引用区段，每个引用区段都标注 (snapshot) 标签。
"""
import argparse
import json
import os
import sys


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def harvest_bazi(t1, target, source_name):
    """搬运八字层确定性数据：四柱/大运/流年/神煞/称骨/旺衰"""
    out = []
    out.append(f"# === [B] 八字层确定性数据搬运（source: {source_name}）— (snapshot) ===")
    out.append(f"## 目标: {target}")
    out.append("")

    # 四柱
    pillars = t1.get("m1_compute", {}).get("pillars", {})
    if not pillars:
        pillars = t1.get("eight_chars_ten_gods", {}).get("pillars", {})
    out.append("### B.1 四柱（m1.py 直出）")
    ten_gods = t1.get("eight_chars_ten_gods", {})
    for p in ("year", "month", "day", "hour"):
        pgz = pillars.get(p, {})
        gz = pgz.get("ganzhi", "?") if isinstance(pgz, dict) else pgz
        out.append(f"- {p}: 干支=`{gz}`")
    out.append("")

    # 十神（pillars 是 list）
    out.append("### B.2 各柱十神（eight_chars_ten_gods.pillars[list]）")
    tg_list = ten_gods.get("pillars", [])
    if isinstance(tg_list, list):
        for tg in tg_list:
            main_qi = tg.get("branch_main_qi") or next((b.get("god") for b in (tg.get("branch_canggan_ten_gods") or [])), None)
            out.append(f"- {tg.get('pillar', '?')}柱 `{tg.get('ganzhi')}`: 干={tg.get('stem')}({tg.get('stem_ten_god')}), 支主气={tg.get('branch')}({main_qi or '?'})")
    out.append("")

    # 旺衰
    ws = t1.get("wangshuai", {})
    out.append("### B.3 旺衰（l3_wangshuai.py）")
    dl = ws.get("de_ling", {})
    dd = ws.get("de_di", {})
    dsh = ws.get("de_shi", {})
    zh = ws.get("zonghe", {})
    out.append(f"- 得令: status={dl.get('status')}, score={dl.get('score')}, 月支={dl.get('month_zhi')}, 本气={dl.get('ben_qi')}({dl.get('ben_qi_wx')}), rule={dl.get('rule_id')}")
    out.append(f"- 得地: rule={dd.get('rule_id')}, items数={len(dd.get('items', []))}")
    out.append(f"- 得势: rule={dsh.get('rule_id')}")
    out.append(f"- 综合: score={zh.get('score')}, level={zh.get('level')}, rule={zh.get('rule_id')}, 权重={zh.get('weights')}")
    out.append("")

    # 大运
    dy = t1.get("dayun_full", {})
    out.append("### B.4 大运序列（l3_bazi_daliu.py，direction={}，{}岁起运）".format(
        dy.get("direction", "?"), dy.get("qiyun", "?")))
    out.append("| 步 | 干支 | 起始年 | 结束年 | 十神 |")
    out.append("|---|---|---|---|---|")
    for step in dy.get("list", []):
        out.append(f"| {step.get('index')} | {step.get('ganzhi')} | {step.get('start_year')} | {step.get('end_year')} | {step.get('god', '?')} |")
    out.append("")

    # 流年 2024-2040
    yg = t1.get("year_gz_2026_2040", {})
    ln = t1.get("liunian", {})
    # 干：用 (y-4)%60 公式独立计算（au-inv-03 用同公式）
    GAN10 = "甲乙丙丁戊己庚辛壬癸"
    ZHI12 = "子丑寅卯辰巳午未申酉戌亥"
    day_master = t1.get("wangshuai", {}).get("day_master", "")
    # 日主对天干的十神映射
    DM_GOD = {  # 日主 -> {天干:十神}
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

    out.append("### B.5 流年 2024-2040（l3_bazi_daliu.py）")
    out.append("| 年 | 干支 | 天干十神 |")
    out.append("|---|---|---|")
    for yr in range(2024, 2041):
        if str(yr) in yg:
            gz = yg[str(yr)]
        else:
            idx = (yr - 4) % 60
            gz = GAN10[idx % 10] + ZHI12[idx % 12]
        god = god_map.get(gz[0], "?")
        out.append(f"| {yr} | {gz} | {god} |")
    out.append("")

    # 神煞
    ss = t1.get("shensha", {}).get("shensha", {})
    out.append(f"### B.6 神煞（l3_shensha.py，hit_total={ss.get('hit_total', '?')}）")
    for grp, items in ss.get("groups", {}).items():
        out.append(f"- **{grp}**: " + " / ".join(f"{it['name']}({it.get('rule_id', '?')})" for it in items))
    out.append("")

    # 称骨
    cg = t1.get("chenggu", {})
    if cg:
        out.append("### B.7 称骨（l3_chenggu.py）")
        bones = cg.get("bones", {})
        for k in ("year", "month", "day", "hour"):
            b = bones.get(k, {})
            out.append(f"- {k} 骨重: key=`{b.get('key')}` weight=`{b.get('weight')}` (qian={b.get('qian')}, {b.get('rule_id')})")
        total = cg.get("total", {})
        out.append(f"- 合计: {total.get('weight')} (rule={total.get('rule_id')})")
        out.append("")

    return "\n".join(out)


def harvest_ziwei(t1z, target, source_name):
    """搬运紫微斗数层确定性数据"""
    out = []
    out.append(f"\n# === [Z] 紫微层确定性数据搬运（source: {source_name}）— (snapshot) ===")
    out.append("")

    pan = t1z.get("pan", {})

    # 命宫身宫
    out.append("### Z.1 命宫身宫与五行局")
    out.append(f"- 命宫: 干支=`{pan.get('minggong', {}).get('gan')}{pan.get('minggong', {}).get('zhi')}`, 规则={pan.get('minggong', {}).get('rule_id')}")
    shen = pan.get("shengong", {})
    out.append(f"- 身宫: 支=`{shen.get('zhi')}`, 规则={shen.get('rule_id')}")
    out.append(f"- 五行局: {pan.get('wuxing_ju', {}).get('name', '?')}")
    out.append("")

    # 十二宫
    out.append("### Z.2 十二宫星曜（pan.palaces）— 严格按主星/辅星/煞星三栏")
    out.append("| 宫位 | 干支 | 主星 | 辅星 | 煞星 | 四化 |")
    out.append("|---|---|---|---|---|---|")
    palaces = pan.get("palaces", [])
    for p in palaces:
        stars = p.get("stars", [])
        aux = p.get("aux", [])
        # 区分辅星（文昌文曲左辅右弼天魁天钺禄存天马）和煞星（火星铃星擎羊陀罗地空地劫）
        SHAS = {"火星", "铃星", "擎羊", "陀罗", "地空", "地劫"}
        FU = {"文昌", "文曲", "左辅", "右弼", "天魁", "天钺", "禄存", "天马"}
        aux_fu = [x for x in aux if x in FU]
        aux_sha = [x for x in aux if x in SHAS]
        sihua = "/".join(str(x) for x in p.get("sihua", []))
        out.append(f"| {p.get('name')} | {p.get('gan')}{p.get('zhi')} | {','.join(stars) or '空'} | {','.join(aux_fu) or '—'} | {','.join(aux_sha) or '—'} | {sihua or '—'} |")
    out.append("")

    # 生年四化落宫
    sn = t1z.get("lists", {}).get("a_shengnian_sihua_luogong", [])
    out.append("### Z.3 生年四化落宫（a_shengnian_sihua_luogong）")
    out.append("| 化星 | 落宫 | 宫干支 | 来源 |")
    out.append("|---|---|---|---|")
    for x in sn:
        out.append(f"| {x.get('star')}{x.get('hua')} | {x.get('palace')} | {x.get('palace_ganzhi')} | {x.get('source', '')[:50]} |")
    out.append("")

    # 大限
    lm = t1z.get("liunian_module", {})
    daxian = lm.get("daxian", {})
    out.append(f"### Z.4 大限（{daxian.get('start_age')}岁起限，{daxian.get('direction')}，局={daxian.get('start_age', '?')}岁）")
    out.append("| 限 | 年龄 | 干支 | 宫位 | 限四化 |")
    out.append("|---|---|---|---|---|")
    for i, d in enumerate(daxian.get("items", []), 1):
        sihua = "/".join(f"{x['star']}{x['hua']}" for x in d.get("sihua", []))
        out.append(f"| {i} | {d.get('ages')} | {d.get('ganzhi')} | {d.get('palace')} | {sihua} |")
    out.append("")

    # 流年
    liunian = lm.get("liunian", {})
    if liunian and "year" in liunian:
        # 单年 dict
        out.append(f"### Z.5 流年（{liunian.get('year')}年）— 紫微流年命宫与四化")
        sihua = "/".join(f"{x['star']}{x['hua']}" for x in liunian.get("sihua", []))
        out.append(f"- {liunian.get('year')}年 干支=`{liunian.get('ganzhi')}` 流年命宫=`{liunian.get('palace_ganzhi')}`({liunian.get('palace')}) 流年四化: {sihua}")
        out.append("")

    return "\n".join(out)


def harvest_all(t4all, target, source_name):
    """搬运全谱层确定性数据（8 个新术种）"""
    out = []
    out.append(f"\n# === [A] 全谱层确定性数据搬运（source: {source_name}）— (snapshot) ===")
    out.append("")

    # 1. 五运六气
    wylq = t4all.get("wuyunliuqi", {})
    if wylq:
        out.append("### A.1 五运六气（l3_wuyunliuqi.py）")
        if "sui_yun" in wylq or "suiyun" in wylq:
            sy = wylq.get("sui_yun") or wylq.get("suiyun")
            out.append(f"- 岁运: {sy}")
        if "si_tian" in wylq or "sitian" in wylq:
            st = wylq.get("si_tian") or wylq.get("sitian")
            out.append(f"- 司天: {st}")
        if "zai_quan" in wylq or "zaiquan" in wylq:
            zq = wylq.get("zai_quan") or wylq.get("zaiquan")
            out.append(f"- 在泉: {zq}")
        # 任意 key 全部输出
        for k, v in wylq.items():
            if k in ("meta", "input", "error"):
                continue
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
        out.append("")

    # 2. 小六壬
    xlr = t4all.get("xiaoliuren", {})
    if xlr:
        out.append("### A.2 小六壬（l3_xiaoliuren.py）")
        for k, v in xlr.items():
            if k in ("meta", "input", "error"):
                continue
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
        out.append("")

    # 3. 梅花
    mh = t4all.get("meihua", {})
    if mh:
        out.append("### A.3 梅花易数（l3_meihua.py）")
        for k, v in mh.items():
            if k in ("meta", "input", "error"):
                continue
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
            elif isinstance(v, list):
                out.append(f"- {k}: list len={len(v)} sample={json.dumps(v[0], ensure_ascii=False)[:200] if v else 'empty'}")
        out.append("")

    # 4. 黄历
    hl = t4all.get("huangli_day", {})
    if hl:
        out.append("### A.4 黄历（l3_huangli.py）— 出生日")
        for k, v in hl.items():
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, (list, dict)):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
        out.append("")

    # 5. 河洛理数
    hlyl = t4all.get("heluolishu", {})
    if hlyl:
        out.append("### A.5 河洛理数（l3_heluolishu.py）")
        for k, v in hlyl.items():
            if k in ("meta", "input", "error"):
                continue
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
        out.append("")

    # 6. 六爻
    ly = t4all.get("liuyao", {})
    if ly:
        out.append("### A.6 六爻（l3_liuyao.py）")
        for k, v in ly.items():
            if k in ("meta", "input", "error"):
                continue
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
            elif isinstance(v, list):
                out.append(f"- {k}: list len={len(v)} sample={json.dumps(v[0], ensure_ascii=False)[:200] if v else 'empty'}")
        out.append("")

    # 7. 大六壬
    lr = t4all.get("liuren", {})
    if lr:
        out.append("### A.7 大六壬（l3_liuren.py）")
        for k, v in lr.items():
            if k in ("meta", "input", "error"):
                continue
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
            elif isinstance(v, list):
                out.append(f"- {k}: list len={len(v)} sample={json.dumps(v[0], ensure_ascii=False)[:200] if v else 'empty'}")
        out.append("")

    # 8. 奇门
    qm = t4all.get("qimen_pan_summary", {}) or t4all.get("qimen_duanju", {})
    if qm:
        out.append("### A.8 奇门断局（l3_qimen_duanju.py / l3_qimen.py）")
        for k, v in qm.items():
            if isinstance(v, (str, int, float, bool)):
                out.append(f"- {k}: {v}")
            elif isinstance(v, dict):
                out.append(f"- {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
        out.append("")

    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="快照确定性数据自动搬运工具")
    ap.add_argument("--t1-bazi", required=True, help="t1_bazi.json 路径")
    ap.add_argument("--t1-ziwei", required=True, help="t1_ziwei.json 路径")
    ap.add_argument("--t4-all", required=True, help="t4_b_all.json 路径")
    ap.add_argument("--target", required=True, help="命造标识，如 'B 男命'")
    ap.add_argument("--out", required=True, help="输出 .txt 路径")
    a = ap.parse_args()

    t1 = _load(a.t1_bazi)
    t1z = _load(a.t1_ziwei)
    t4 = _load(a.t4_all)

    src_bazi = os.path.basename(a.t1_bazi)
    src_ziwei = os.path.basename(a.t1_ziwei)
    src_all = os.path.basename(a.t4_all)
    sections = [
        harvest_bazi(t1, a.target, src_bazi),
        harvest_ziwei(t1z, a.target, src_ziwei),
        harvest_all(t4, a.target, src_all),
    ]

    # 顶部声明
    head = f"""# 确定性数据搬运产物（v1.0，l4_data_harvest.py 自动生成）
# 目标: {a.target}
# 来源: {src_bazi} / {src_ziwei} / {src_all}
# 规则: 本文件内所有内容均带 (snapshot) 标签，可直接复制到草稿引用区段
# 禁止修改本文件（修改意味着重新跑搬运）；本文件外的手写确定性数据视同未审计

"""

    full = head + "\n".join(sections) + "\n\n# === END ===\n"
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(full)
    print(f"OK harvest -> {a.out} ({len(full)} chars)")


if __name__ == "__main__":
    main()
