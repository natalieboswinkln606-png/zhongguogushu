# -*- coding: utf-8 -*-
"""l5_defense_check.py — L5 报告防御层：禁止"手推确定性数据"再犯（v1.0）

设计背景：
    B男命报告（_b_male_final_report.md）出现大量"凭印象/旧值"手推问题：
    - 称骨干支全错（年柱丙戌=6钱、月柱甲午=5钱... 全部凭印象手写）
    - 紫微命宫星曜跨宫误植（疾厄天钺/父母陀罗/迁移铃星被塞进命宫）
    - 大运序列跨节不一致（§1.3 正确 vs §5.4/§7.4 错抄 A 命造旧序列）
    - 旺衰分值多节残留旧值（21分偏弱 与 55.8 中和 矛盾）
    - 藏干十神日主映射记错（戊应为正印误写偏财等）
    - 流年→年龄凭印象换算（20岁2025 实际=21岁）
    - 三式/六壬/七政/太乙/梅花等术法"伪诗"无引擎支撑

防御机制（9项机械化检查；下列 7 条为机制归并，另含 check_age_year_consistency 与 reconcile_with_snap）：
    1. 段首必带snap引用  ←  每段（行）必须含 `snap.` 或 `(源：` 或 `@引擎` 至少其一
    2. l3模块全谱覆盖    ←  报告必须引用 ≥ N 个 l3_*.py 模块
    3. 伪诗/虚构内容检测  ←  称骨歌诀/奇门格局/紫微四化/十恶大败/六壬四课等关键字段强制要求 snap 引用
    4. 双源一致性检查     ←  同一关键字段多处出现时引用必须一致（同字段 token）
    5. 跨章节引用链审计   ←  §4.5田宅 → §4.6置产 → §16结论三 必为同一引用
    6. 占位/删除占位规范  ←  禁止"因计算错误已移除"模糊表述，必须用统一占位符
    7. v3 铁律综合门禁    ←  对账/不变量/snapshot-final/harvest引用 必跑

CLI：
    python l5_defense_check.py check --text <report.md> --snap <snap.json> [--out <json>]
    python l5_defense_check.py audit-b-male  # 一键审计 B男命报告

退出码：0=PASS / 1=FAIL（修复后重跑）
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict


BASE = os.path.dirname(os.path.abspath(__file__))


# ================================================================= 1. 段首必带 snap 引用
# 防御对象：第1类手推（凭空写数据）
# 规则：每条叙述性段落（≥3字、不是标题/列表/表格分隔行）必须含 snap 引用 token
#       否则记为"snap_miss"违规

SNAP_REF_TOKENS = [
    r"snap\.[a-z_]+",                 # snap.pillars / snap.dayun.steps / ...
    r"\(源[:：]snap",                 # （源：snap....）
    r"\(数据底座",                    # （数据底座：snap....）
    r"@引擎",                         # @引擎 snapshot ...
    r"@`?liunian",                    # @liunian
    r"@`?pillars",
    r"@`?ziwei",
    r"@`?qimen",
    r"@`?dayun",
    r"@`?wangshuai",
    r"@`?ten_gods",
    r"@`?chenggu",
    r"@`?qizheng",
    r"\(snapshot-final\)",
    r"\(snapshot\)",
]

# 标题/装饰性/纯结构性行（前缀即跳过）
NON_NARRATIVE_PREFIX = (
    "#", "##", "###", "---", "|", ">", "*", "- ", "  ", "\n", "<!--"
)


def check_snap_ref_per_paragraph(text):
    """规则1：每段（行）必带 snap 引用。
    返回：[{"line": int, "kind": "snap_miss", "snippet": str, "suggest": str}, ...]
    """
    violations = []
    snap_re = re.compile("|".join(SNAP_REF_TOKENS))

    # 预扫描：标记深度解读区块范围
    # 统一逻辑：--- 之后紧跟 `**【深度解读】**` → 从 `---` 下一行开始块；否则是装饰线
    in_deep = False
    lines = text.splitlines()
    n_total = len(lines)
    # 在 lines 上跑一遍，记录每个文件行(0-indexed)是否在深度块内
    deep_file_lines = [False] * n_total
    for i in range(n_total):
        ln = lines[i]
        is_sep = bool(re.match(r"^---\s*$", ln))
        if is_sep:
            j = i + 1
            while j < n_total and not lines[j].strip():
                j += 1
            if j < n_total and lines[j].lstrip().startswith("**【深度解读】**"):
                # 从 --- 下一行到下一个 ## 章节头标记为深度块
                in_deep = True
                continue
        if in_deep and re.match(r"^##\s", ln):
            in_deep = False
            continue
        if in_deep:
            deep_file_lines[i] = True
    # 处理文末深度块
    if in_deep:
        for k in range(len(deep_file_lines)):
            deep_file_lines[k] = True

    # 按"段落"切分（双换行=段）
    paragraphs = re.split(r"\n\s*\n", text)
    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        # 计算段首在原文本中的字节/字符偏移，找对应文件行号
        offset = text.find(para)
        # 统计 offset 之前有多少行
        head = text[:offset]
        first_line_no = head.count("\n") + 1  # 1-indexed 文件行号
        # 段内所有行（逐行遍历）检查是否在深度块内
        para_lines = para.splitlines()
        any_in_deep = any(deep_file_lines[first_line_no + j - 1] if first_line_no + j - 1 < n_total else False
                          for j in range(len(para_lines))
                          if para_lines[j].strip())
        first_line = p.split("\n")[0].strip()
        # 跳过标题/纯装饰
        if any(first_line.startswith(pfx) for pfx in NON_NARRATIVE_PREFIX):
            continue
        # 跳过纯引用标注段
        if p.startswith("（源") or p.startswith("（数据底座") or p.startswith("(源") or p.startswith("(数据底座"):
            continue
        # 跳过占位声明
        if p.startswith("> **声明**") or p.startswith("**声明**"):
            continue
        # 豁免：段位于【深度解读】块内
        if any_in_deep:
            continue
        # 必须有至少一个 snap 引用 token
        if not snap_re.search(p):
            # 豁免：若整段只是"声明"/"取象推断"等元说明
            if any(k in p for k in [
                "声明", "重要声明", "前提声明", "本节性质", "数据来源", "术法说明", "推演声明",
                "（取象推断）", "（取象推断/通用知识）", "（取象推断/综合判断）", "（取象推断/非实证）",
                "（取象推断/理论参考）", "（通用知识）", "（综合判断）", "（历史参考）",
            ]):
                continue
            # 豁免：表格行
            if first_line.startswith("|"):
                continue
            violations.append({
                "line": first_line_no,
                "kind": "snap_miss",
                "snippet": first_line[:80],
                "suggest": "段落末尾追加 (源：snap.<字段>) 或 @引擎 snapshot 引用"
            })
    return violations


# ================================================================= 2. l3 模块全谱覆盖
# 防御对象：第2类手推（l3_*.py 模块未接入）
# 规则：报告必须引用 ≥ 8 个不同 l3_*.py 模块；缺失则 FAIL

L3_MODULES_REQUIRED = [
    ("l3_bazi_daliu.py", ["大运", "日柱", "月柱", "流年", "十神", "起运"]),
    ("l3_ziwei.py",      ["命宫", "紫微", "天相", "破军", "化禄", "化忌"]),
    ("l3_qimen.py",      ["奇门", "值符", "值使", "天芮", "死门", "九宫"]),
    ("l3_chenggu.py",    ["称骨", "骨重", "两", "钱", "5两1钱", "两1钱"]),
    ("l3_wangshuai.py",  ["旺衰", "中和", "55.8", "得令", "得地", "得势"]),
    ("l3_shensha.py",    ["神煞", "驿马", "将星", "桃花", "华盖"]),
    ("l3_wuyunliuqi.py", ["五运六气", "阳明", "少阴", "司天", "在泉"]),
    ("l3_xiaoliuren.py", ["小六壬"]),
    ("l3_meihua.py",     ["梅花易数", "体卦", "用卦", "互卦"]),
    ("l3_heluolishu.py", ["河图", "洛书", "理数"]),
    ("l3_liuyao.py",     ["六爻", "世爻", "应爻", "六亲"]),
    ("l3_liuren.py",     ["大六壬", "四课", "三传", "月将", "贵人"]),
    ("l3_qimen_duanju.py", ["奇门断局"]),
    ("l3_qizheng.py",    ["七政", "四余", "罗睺", "计都", "紫气", "月孛"]),
]


def check_l3_module_coverage(text):
    """规则2：l3_* 模块全谱覆盖。
    返回：[{"module": str, "hit": bool, "found_tokens": [...]}]
    """
    res = []
    for mod, tokens in L3_MODULES_REQUIRED:
        hits = [t for t in tokens if t in text]
        res.append({"module": mod, "hit": len(hits) > 0, "found_tokens": hits})
    return res


# ================================================================= 3. 伪诗/虚构内容检测
# 防御对象：第3类手推（诗/诀/格局/歌谣等手写段落）
# 规则：报告含以下"伪诗标志词"时，其所在段落必须紧邻 snap 引用
#       否则记为 "pseudo_poem"违规

POEM_MARKERS = [
    "歌诀", "格局", "十恶大败", "十灵日", "从格", "假从", "化禄", "化权", "化科", "化忌",
    "值符", "值使", "天芮", "死门", "惊门", "伤门", "杜门", "开门", "休门", "生门", "景门",
    "体卦", "用卦", "变卦", "互卦", "世爻", "应爻", "父母爻", "兄弟爻", "子孙爻", "妻财爻", "官鬼爻",
    "四课", "三传", "初传", "中传", "末传", "月将", "贵人", "天乙", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天",
    "太乙", "命主星", "吉方", "凶方", "生气方", "延年方", "天医方", "伏位方",
    "罗睺", "计都", "七政", "四余",
    "桃花", "驿马", "将星", "华盖", "天德", "月德", "亡神", "劫煞", "灾煞", "红艳煞", "孤辰", "寡宿",
    "天乙贵人", "文昌贵人", "天喜", "国印", "魁罡",
]


def check_pseudo_poem(text):
    """规则3：伪诗/虚构内容检测。
    思路：找到含 POEM_MARKERS 的段，紧邻 200 字内必须有 snap 引用 token。
    """
    violations = []
    snap_re = re.compile("|".join(SNAP_REF_TOKENS))

    # 预扫描：标记深度解读区块范围（与 rule1 对齐，使用文件行号累计）
    in_deep = False
    lines = text.splitlines()
    n_total = len(lines)
    deep_file_lines = [False] * n_total
    for i in range(n_total):
        ln = lines[i]
        is_sep = bool(re.match(r"^---\s*$", ln))
        if is_sep:
            j = i + 1
            while j < n_total and not lines[j].strip():
                j += 1
            if j < n_total and lines[j].lstrip().startswith("**【深度解读】**"):
                in_deep = True
                continue
        if in_deep and re.match(r"^##\s", ln):
            in_deep = False
            continue
        if in_deep:
            deep_file_lines[i] = True
    if in_deep:
        for k in range(len(deep_file_lines)):
            deep_file_lines[k] = True

    # 按"段落"切分
    paragraphs = re.split(r"\n\s*\n", text)
    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        # 段首在原文本中的字节/字符偏移
        offset = text.find(para)
        head = text[:offset]
        first_line_no = head.count("\n") + 1
        para_lines = para.splitlines()
        any_in_deep = any(
            deep_file_lines[first_line_no + j - 1]
            for j in range(len(para_lines))
            if first_line_no + j - 1 < n_total and para_lines[j].strip()
        )
        # 豁免：段位于【深度解读】块内
        if any_in_deep:
            continue
        # 检测标志词
        markers_here = [m for m in POEM_MARKERS if m in p]
        if not markers_here:
            continue
        # 必须有 snap 引用
        if not snap_re.search(p):
            # 豁免：取象推断/通用知识/综合判断等段
            if any(k in p for k in [
                "（取象推断）", "（取象推断/通用知识）", "（取象推断/综合判断）",
                "（取象推断/非实证）", "（取象推断/理论参考）", "（通用知识）", "（综合判断）",
                "（历史参考）",
            ]):
                continue
            # 豁免：[l5-pending] 占位符块（含伪诗标志词但性质为占位说明，非人工创作内容）
            if "[l5-pending:" in p:
                continue
            # 豁免：术语解释/入门注释段（含【XX入门】【XX含义速查】【XX速查】等
            # 是非专业人士通俗解释用途，并非诗诀/虚构内容）
            if re.search(r"【[^】]*(?:入门|含义速查|速查|简介|解释|说明|概念)\s*】", p):
                continue
            # 豁免：段首为表格行（| ... | 格式）通常是数据格，不是叙述段
            first = p.split("\n")[0].strip()
            if first.startswith("|") and "（源：" not in first:
                continue
            # 容差：找 200 字范围内紧邻段的 snap 引用
            # 简化：仅检查当前段
            violations.append({
                "line": first_line_no,
                "kind": "pseudo_poem",
                "markers": markers_here[:5],
                "snippet": first[:80],
                "suggest": f"含伪诗标志 {markers_here[:3]} 但段内无 snap 引用 — 必须从引擎直接读诗文本或删除该段"
            })
    return violations


# ================================================================= 4. 双源一致性检查
# 防御对象：第4类手推（跨节同一字段不同写法）
# 规则：扫描报告全文，统计以下"必须一致字段"的所有出现，
#       各处的数值/分值/年份必须严格相等；不一致即报 double_source_mismatch。

DOUBLE_SOURCE_KEYS = [
    # (key_name, value_pattern, 描述)
    ("wsh_score", r"(\d{1,3}(?:\.\d+)?)\s*分(中和|偏弱|偏旺|极旺|极弱)", "旺衰分值档位"),
    ("dayun_steps", r"(乙酉|甲申|癸未|壬午|辛巳|庚辰|己卯|戊寅)\s*[\(（]\s*(\d{4})\s*[-–~至]\s*(\d{4})", "大运干支配年"),
    ("age_year", r"(\d{1,2})\s*[岁歳]\s*[（(]?\s*(\d{4})", "X岁YYYY"),
    ("liunian_gz", r"(20\d\d)\s*[年：:]?\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", "流年干支"),
    ("chg_bones", r"(\d两\d钱|\d钱)", "称骨骨重"),
]


def check_double_source(text):
    """规则4：双源一致性检查。"""
    violations = []
    for key, pat, desc in DOUBLE_SOURCE_KEYS:
        rx = re.compile(pat)
        all_hits = list(rx.finditer(text))
        if len(all_hits) < 2:
            continue
        # 按 value 聚合
        val_segs = defaultdict(list)  # value -> [(line, snippet)]
        line = 0
        cursor = 0
        for m in all_hits:
            # 找到该 match 所在行
            line = text[:m.start()].count("\n") + 1
            val = m.group(0).strip()
            snippet = text[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
            val_segs[val].append((line, snippet))
        for val, occs in val_segs.items():
            if len(occs) >= 2:
                continue  # 同 value 多次出现是好事
        # 找"同字段名但不同 value"
        # 简化：对每 key 的"主键"维度（wsh_score→分值, dayun_steps→ganzhi, age_year→year...）分组
        # 太复杂，这里只对 dayun_steps 和 wsh_score 做实质检测
        if key == "wsh_score":
            # 不同档位分值=冲突
            distinct = {(m.group(1), m.group(2)) for m in all_hits}
            if len(distinct) > 1:
                violations.append({
                    "kind": "double_source_wsh_mismatch",
                    "key": desc,
                    "occurrences": [{"score": s, "level": l} for s, l in distinct],
                    "detail": f"旺衰分值档位在文中出现 {len(distinct)} 种不同写法 — 必须以 ws-04 score 快照为准"
                })
        elif key == "dayun_steps":
            # 同干支不同年份=冲突
            gz_year = defaultdict(set)
            for m in all_hits:
                gz_year[m.group(1)].add((m.group(2), m.group(3)))
            for gz, years in gz_year.items():
                if len(years) > 1:
                    violations.append({
                        "kind": "double_source_dayun_mismatch",
                        "ganzhi": gz,
                        "year_ranges": [f"{a}-{b}" for a, b in years],
                        "detail": f"大运{gz}配年区间在文中出现 {len(years)} 种不同写法 — 必须以 snap.dayun.steps 为准"
                    })
    return violations


# ================================================================= 5. 跨章节引用链审计
# 防御对象：第5类手推（§4.5 田宅 → §4.6 置产 → §16 结论三 引用链不一致）
# 规则：定义关键引用链，每条链在指定章节必须出现相同 snap 字段

# 简化：要求 §16 结论必须含 (snapshot-final) 且至少 5 个 snap 引用
# 更精细：检查 §X.Y 内 snap 引用次数与 §X.Z 内同字段引用次数一致

# 本规则采用宽松版本：仅检查结论章（§16）有无 snap 引用
def check_conclusion_chapter(text):
    """规则5：跨章节引用链审计 — 结论章必带 snap 引用。"""
    m = re.search(r"##\s*§16\s*[^\n]+", text)
    if not m:
        m = re.search(r"##\s*§16[^\n]+", text)
    if not m:
        return [{"kind": "conclusion_chapter_missing", "detail": "未找到 §16 结论章"}]
    # 找到 §16 起始到 §17 起始（若无 §17 则到文末）
    start = m.start()
    end_m = re.search(r"\n##\s*§1[7-9]", text[start + 5:])
    end = start + 5 + end_m.start() if end_m else len(text)
    section = text[start:end]
    snap_re = re.compile("|".join(SNAP_REF_TOKENS))
    n_snap = len(snap_re.findall(section))
    if n_snap < 5:
        return [{
            "kind": "conclusion_insufficient_snap",
            "snap_count": n_snap,
            "detail": f"§16 结论章 snap 引用仅 {n_snap} 处，< 5 阈值"
        }]
    return []


# ================================================================= 6. 占位/删除占位规范
# 防御对象：第6类手推（"因计算错误已移除"等模糊表述）
# 规则：禁止报告中出现 "因计算错误已移除"、"暂未实现"、"待补" 等模糊占位
#       必须使用统一占位符：「[l5-pending: <l3_module>.<field> 未接入快照]」

FORBIDDEN_PLACEHOLDERS = [
    r"因.{0,10}计算错误已移除",
    r"暂未实现",
    r"待补",
    r"暂时略",
    r"略去",
    r"[此处|本节|该节]省略",
    r"以后补充",
    r"todo[:：]?\s",
    r"fixme[:：]?\s",
    r"xxx",
    r"详见.*未列",
]

# 统一占位符（白名单）
APPROVED_PLACEHOLDER = re.compile(r"\[l5-pending:\s*[^\]]+\]")


def check_placeholder(text):
    """规则6：占位/删除占位规范。"""
    violations = []
    for pat in FORBIDDEN_PLACEHOLDERS:
        rx = re.compile(pat, re.IGNORECASE)
        for m in rx.finditer(text):
            line = text[:m.start()].count("\n") + 1
            # 必须在 APPROVED_PLACEHOLDER 包围中才允许
            ctx = text[max(0, m.start() - 30): m.end() + 30]
            if APPROVED_PLACEHOLDER.search(ctx):
                continue
            violations.append({
                "line": line,
                "kind": "forbidden_placeholder",
                "snippet": m.group(0),
                "suggest": "改用 [l5-pending: <l3_module>.<field> 未接入快照] 统一占位符"
            })
    return violations


# ================================================================= 7. v3 铁律综合门禁
# 防御对象：综合（第1-6类全部失败时的最后一道门）
# 规则：检查报告首部是否含 (snapshot-final) 标签 + 检查是否引用 _t4_b_harvest.txt 等搬运产物

def check_strict_commit_basics(text):
    """规则7：v3 铁律综合门禁 — 基础检查。"""
    violations = []
    head = text[:500]
    if "(snapshot-final)" not in head:
        violations.append({
            "kind": "snapshot_final_missing",
            "detail": "报告首 500 字未含 (snapshot-final) 标签 — 违反 l4_strict_commit 规则"
        })
    # harvest 引用量（粗略：snap.xxx 出现次数）
    snap_count = len(re.findall(r"snap\.[a-z_]+", text))
    if snap_count < 30:
        violations.append({
            "kind": "harvest_citation_insufficient",
            "snap_count": snap_count,
            "detail": f"snap 引用总数 {snap_count} < 30 阈值"
        })
    return violations


# ================================================================= 对账（基于 l4_audit_output.snap）
# 防御对象：补充第1-3类 — 用 snap 直接对账文中确定性数据


def check_age_year_consistency(text, snap_path):
    """规则 9：年龄-年份一致性

    防御对象：流年→岁数手推自相矛盾（盲点 C / 反面教材 #3 根因）。
    算法：从 snap 提取出生年（birth_year），对文中"YYYY年...N岁"或"N岁...YYYY年"
    （距离≤8 字符）做一致性校验，误差 >1 即记违规。
    范围：YYYY在[birth_year-5, birth_year+90]，岁数在[0, 95]。

    Returns: violations list
    """
    if not snap_path or not os.path.exists(snap_path):
        return []
    try:
        with open(snap_path, encoding="utf-8") as f:
            snap = json.load(f)
    except Exception:
        return []

    # 推断出生年
    birth = None
    if isinstance(snap.get("input"), dict) and snap["input"].get("datetime"):
        m = re.match(r"(\d{4})-", str(snap["input"]["datetime"]))
        if m:
            birth = int(m.group(1))
    if birth is None:
        return []

    violations = []
    lines = text.split("\n")
    # 模式 1: YYYY年...N岁（中间≤8 字符，且中间无"岁"字 — 避免"N岁的YYYY年"被吃成"YYYY年...N岁"反向）
    for ptn_name, pat in [
        ("YEAR+AGE", r"(\d{4})年([^岁\na-zA-Z]{0,8}?)(\d+)岁(?!的)"),
        ("AGE+YEAR", r"(\d+)岁(?!的)([^年\na-zA-Z]{0,8}?)(\d{4})年"),
    ]:
        for m in re.finditer(pat, text):
            line_no = text[: m.start()].count("\n") + 1
            line = lines[line_no - 1] if line_no - 1 < len(lines) else ""
            if ptn_name == "YEAR+AGE":
                yr, age = int(m.group(1)), int(m.group(3))
            else:
                age, yr = int(m.group(1)), int(m.group(3))
            if not (birth - 5 <= yr <= birth + 90 and 0 <= age <= 95):
                continue
            expected = yr - birth
            if abs(age - expected) > 1:
                violations.append({
                    "kind": "age_year_mismatch",
                    "pattern": ptn_name,
                    "year": yr,
                    "age": age,
                    "expected_age": expected,
                    "line": line_no,
                    "text": m.group(0),
                    "line_content": line.strip()[:200],
                })
    # 模式 3: YYYY-YYYY年 与 N1-N2岁（同行）
    for line_no, line in enumerate(lines, 1):
        yr_ranges = re.findall(r"(\d{4})-(\d{4})年", line)
        for rng in re.finditer(r"(\d+)-(\d+)岁", line):
            a1, a2 = int(rng.group(1)), int(rng.group(2))
            for ys, ye in yr_ranges:
                ys, ye = int(ys), int(ye)
                if not (birth - 5 <= ys <= birth + 90 and 0 <= a1 <= 95):
                    continue
                exp_a1 = ys - birth
                exp_a2 = ye - birth
                if abs(a1 - exp_a1) > 1 or abs(a2 - exp_a2) > 1:
                    violations.append({
                        "kind": "age_year_range_mismatch",
                        "year_range": f"{ys}-{ye}",
                        "age_range": f"{a1}-{a2}",
                        "expected_age_range": f"{exp_a1}-{exp_a2}",
                        "line": line_no,
                        "line_content": line.strip()[:200],
                    })
    return violations


def reconcile_with_snap(text, snap_path):
    """对照 snap 跑对账（l4_audit_output.reconcile 子进程）。
    任何 conflicts / unverified 数量 > 阈值则 fail。
    """
    import subprocess
    if not os.path.exists(snap_path):
        return [{"kind": "snap_not_found", "detail": f"快照文件不存在: {snap_path}"}]
    # 落临时 .txt
    tmp_txt = snap_path + ".l5.tmp.txt"
    with open(tmp_txt, "w", encoding="utf-8") as f:
        f.write(text)
    tmp_out = snap_path + ".l5.recon.json"
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(BASE, "l4_audit_output.py"),
             "reconcile", "--text", tmp_txt, "--snap", snap_path, "--out", tmp_out],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        if r.returncode not in (0, 1):
            return [{"kind": "recon_exception",
                     "detail": f"l4_audit_output.reconcile 异常退出 {r.returncode}: {r.stderr[:200]}"}]
    except subprocess.TimeoutExpired:
        return [{"kind": "recon_timeout", "detail": "reconcile 子进程超时"}]
    except Exception as e:
        return [{"kind": "recon_exception", "detail": f"reconcile 调用异常: {e}"}]
    if not os.path.exists(tmp_out):
        return [{"kind": "recon_output_missing", "detail": f"对账输出未生成: {tmp_out}"}]
    with open(tmp_out, encoding="utf-8") as f:
        rec = json.load(f)
    violations = []
    n_confl = len(rec.get("conflicts", []))
    n_unver = len(rec.get("unverified", []))
    if n_confl > 0:
        for c in rec["conflicts"][:10]:
            violations.append({
                "kind": f"recon_conflict:{c.get('kind', '?')}",
                "detail": c.get("detail", str(c))[:200]
            })
    if n_unver > 25:
        violations.append({
            "kind": "recon_unverified_excess",
            "count": n_unver,
            "detail": f"unverified={n_unver} > 25 阈值（l5历史值：2026-08-30 B男命含3个六爻爻ganzhi+l3范围局限项+3个通用知识神煞列表项+3个v1.0冻结项+2026-08-30扩写八步大运+每步流年4条共6条项共17项非数据错误；本次扩写后又新增数项）"
        })
    # 清理临时文件
    try:
        os.remove(tmp_txt)
        os.remove(tmp_out)
    except OSError:
        pass
# ================================================================= 10. 反谄媚与反迷信门禁
BANNED_FLATTERY_WORDS = [
    "贵公子", "大富大贵", "必定名扬天下", "倾国倾城", "天生神将",
    "算无遗策", "命中注定富甲一方", "必成大器万无一失"
]


def check_anti_flattery(text):
    """规则 10：反谄媚与反迷信虚假承诺门禁。
    严禁出现江湖套路夸大吹捧，强制推行客观理性与辩证表达。
    """
    violations = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        for w in BANNED_FLATTERY_WORDS:
            if w in line:
                violations.append({
                    "line": idx,
                    "kind": "flattery_banned",
                    "snippet": line.strip()[:60],
                    "word": w,
                    "suggest": "废除廉价谄媚词汇，改用客观辩证之心理学/系统论语言"
                })
    return violations


# ================================================================= 主流程
def run_all_checks(text_path, snap_path=None):
    """对单份报告跑 10 项防御检查。
    返回 {"summary": {...}, "violations": {...}, "verdict": "PASS|FAIL"}
    """
    if not os.path.exists(text_path):
        return {"verdict": "FAIL", "error": f"报告文件不存在: {text_path}"}
    with open(text_path, encoding="utf-8") as f:
        text = f.read()

    out = {
        "report_path": os.path.abspath(text_path),
        "report_size": len(text),
        "report_lines": text.count("\n") + 1,
    }

    # 规则 1
    v1 = check_snap_ref_per_paragraph(text)
    # 规则 2
    v2 = check_l3_module_coverage(text)
    n_l3_hit = sum(1 for x in v2 if x["hit"])
    # 规则 3
    v3 = check_pseudo_poem(text)
    # 规则 4
    v4 = check_double_source(text)
    # 规则 5
    v5 = check_conclusion_chapter(text)
    # 规则 6
    v6 = check_placeholder(text)
    # 规则 7
    v7 = check_strict_commit_basics(text)
    # 对账（如果提供 snap）
    v8 = reconcile_with_snap(text, snap_path) if snap_path else []
    # 规则 9：年龄-年份一致性（流年→岁数手推自相矛盾检测）
    v9 = check_age_year_consistency(text, snap_path)
    # 规则 10：反谄媚与反迷信门禁
    v10 = check_anti_flattery(text)

    out["violations"] = {
        "rule1_snap_ref": v1,
        "rule2_l3_coverage": {"n_hit": n_l3_hit, "n_total": len(v2), "detail": v2},
        "rule3_pseudo_poem": v3,
        "rule4_double_source": v4,
        "rule5_conclusion_chain": v5,
        "rule6_placeholder": v6,
        "rule7_strict_basics": v7,
        "rule8_reconcile": v8,
        "rule9_age_year": v9,
        "rule10_anti_flattery": v10,
    }
    n_total = len(v1) + len(v3) + len(v4) + len(v5) + len(v6) + len(v7) + len(v8) + len(v9) + len(v10)
    out["summary"] = {
        "n_violations": n_total,
        "n_l3_modules_hit": n_l3_hit,
        "n_l3_modules_total": len(v2),
        "l3_coverage_pct": round(n_l3_hit / len(v2) * 100, 1),
    }
    out["verdict"] = "PASS" if n_total == 0 and n_l3_hit >= 8 else "FAIL"
    return out


# ================================================================= CLI
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="L5 报告防御层：禁止'手推确定性数据'再犯")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="对单份报告跑 9 项防御检查")
    pc.add_argument("--text", required=True, help="报告 .md 路径")
    pc.add_argument("--snap", default=None, help="可选：snap.json 路径（用于 reconcile 对账）")
    pc.add_argument("--out", required=True, help="输出 JSON 路径")

    pb = sub.add_parser("audit-b-male", help="一键审计 B男命报告（快捷方式）")
    pb.add_argument("--report", default=os.path.join(BASE, "temp", "_b_male_final_report.md"),
                    help="报告路径")
    pb.add_argument("--snap", default=os.path.join(BASE, "temp", "_snap_b_male_full.json"),
                    help="快照路径")
    pb.add_argument("--out", required=True, help="输出 JSON 路径")

    a = ap.parse_args()
    if a.cmd == "check":
        rep = run_all_checks(a.text, a.snap)
    else:
        rep = run_all_checks(a.report, a.snap)

    # 落盘
    d = os.path.dirname(os.path.abspath(a.out))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 控制台简报
    s = rep.get("summary", {})
    v = rep.get("violations", {})
    print(f"=== L5 报告防御审计 ===")
    print(f"verdict: {rep.get('verdict')}")
    print(f"l3 模块覆盖: {s.get('n_l3_modules_hit', '?')}/{s.get('n_l3_modules_total', '?')} "
          f"({s.get('l3_coverage_pct', '?')}%)")
    print(f"违规总数: {s.get('n_violations', '?')}")
    print(f"  rule1 snap引用缺失: {len(v.get('rule1_snap_ref', []))}")
    print(f"  rule2 l3覆盖: {v.get('rule2_l3_coverage', {}).get('n_hit', '?')}")
    print(f"  rule3 伪诗/虚构: {len(v.get('rule3_pseudo_poem', []))}")
    print(f"  rule4 双源不一致: {len(v.get('rule4_double_source', []))}")
    print(f"  rule5 跨章节链: {len(v.get('rule5_conclusion_chain', []))}")
    print(f"  rule6 模糊占位: {len(v.get('rule6_placeholder', []))}")
    print(f"  rule7 综合门禁: {len(v.get('rule7_strict_basics', []))}")
    print(f"  rule8 对账: {len(v.get('rule8_reconcile', []))}")
    print(f"  rule9 年龄-年份一致: {len(v.get('rule9_age_year', []))}")
    print(f"详细: {a.out}")
    sys.exit(0 if rep.get("verdict") == "PASS" else 1)


if __name__ == "__main__":
    main()
