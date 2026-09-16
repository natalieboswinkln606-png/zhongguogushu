# shushu — 中国传统术数引擎（v1.0 冻结）

## 分层与纪律

- L0 `data/*.csv` 权威表 → L1 `m1.py` 四柱内核 → L2 `rules.py` 公式表 → L3 十六术种 `l3_*.py` → L4 审计/仲裁 `l4_*.py`。
- **v1.0 已冻结**：`m1.py`、全部 `l3_*.py` 一律不许修改，只允许新增文件。新增/改动已跟踪文件后必须
  `python l4_audit.py --resign` 重签 `SHA256SUMS.txt`，再 `--verify` 确认一致（README 硬性要求）。
- 测试为平铺独立脚本（`assert_l3_*.py`、`assert_tables.py`、`assert_l4_audit_output.py`），
  自写 `check()` 计数 PASS/FAIL，运行方式 `PYTHONIOENCODING=utf-8 python assert_xxx.py`，退出码非 0 即有失败。
- 控制台中文在 GBK 终端会乱码：重要结论一律落 UTF-8 JSON/TXT 文件，不依赖 stdout。

## 审计层使用铁律（l4_audit_output.py）

凡产出含测算数据的结论，必须遵守：

1. **禁手推**：四柱/大运/流年/神煞/紫微/奇门/称骨/河洛/梅花/六爻/小六壬/大六壬/五运六气
   的任何确定性数据必须引擎直出，禁止凭记忆书写序列。
   **实践约束**：确定性数据必须由 `l4_data_harvest.py` 自动搬运到草稿引用区，
   人工只许在引用区段下方"取象推断/综合"区段书写。
2. **先落盘后引用**：分析只能引用已落盘快照 JSON 里的数据（`snapshot` 子命令生成）。
3. **输出前对账**：凡含数据的结论性输出，先跑 `l4_audit_output.reconcile` 对账，
   unverified/conflicts 清零后才许出口；清不了零的项要么改正、要么明示"未经证实"。
4. **双源同引**：同一事实多处出现必须引自同一份快照，禁止两处各写各的。
   **强制检查**：`reconcile` 中"双源不一致"自动检测——
   同一干支/星名/骨重等在草稿中 ≥2 位置出现时，工具会聚合所有出现的年份/十神/宫位字段
   比对快照，若任一字段不一致即报 conflict。
5. **对抗收尾**：每轮测算结束主动跑一遍 `check_invariants` + `reconcile` 复核，
   并派发两位第三方对抗审查代理（数据抄写 + 术理），无 findings 才许出口。

## 反面教材（真实事故，勿重演）

1. A 命造（2006-06-25 00:30 女 东经120）大运序列被凭记忆手推**错位一位**：误写成
   "甲午(2012-2021)→癸巳(2022-2031)→壬辰(2032-2041)…"；引擎实证正确为
   "癸巳(2012-2021)→壬辰(2022-2031)→辛卯(2032-2041)→庚寅(2042-2051)→己丑(2052-2061)→戊子(2062-2071)"
   （丙戌阳年女逆排，第一步=月柱甲午的上一位癸巳）。防线 = aud-inv-01 + reconcile 规则二。
2. B 奇门盘（2005-10-24 17:02 男 东经120）文档转录时把值符死门**同时写到中五宫和艮八宫**；
   引擎实证中五宫 star/door/shen 全部为 None，值符天芮/死门只在艮八宫一处。防线 = aud-inv-05。
3. **B 称骨四柱手写版（2026-08-27 出档）**："年柱丙戌=6钱、月柱甲午=5钱、日柱乙酉=9钱、时柱丁酉=9钱"
   ——干支全错（把"年柱=乙酉"错抄为"丙戌"，把月柱"九月"错写为四柱干支"甲午"），骨重也错（乙酉=1两5钱，非6钱；九月=1两8钱，非5钱）。
   引擎实证：年=乙酉1两5钱、月=九月1两8钱、日=22日9钱、时=酉时9钱，合计5两1钱。
   **根因**：凭记忆/想象手写四柱与骨重，未从快照拉数据。
   防线 = `l4_data_harvest.py` 自动搬运（所有确定性数据走 tool，不许手写）。
4. **B 紫微命宫星曜跨宫误植（2026-08-27 出档）**：把疾厄宫的"天钺"、父母宫的"陀罗"、迁移宫的"铃星"误植入命宫描述。
   引擎实证：命宫=天相+文昌+文曲（aux 仅此二项）。
   **根因**：凭"星耀多显得专业"的直觉把六煞/吉辅星塞进命宫描述，未对照快照 aux 列表。
   防线 = `l4_data_harvest.py` 输出每宫"主星/辅星/煞星"三栏，引用严格按 aux 列表。
5. **B §5.4/§7.4 大运节点表用旧错序列（2026-08-27 出档）**：误把 A 命造的旧错序列"癸巳/壬辰/辛卯/庚寅/己丑/戊子"套到 B 命造，
   与 §1.3/§9 引擎实证正确序列"乙酉/甲申/癸未/壬午/辛巳/庚辰"完全不一致。
   **根因**：跨命造草稿复用时未触发"双源同引"检查，单点修正了 §1.3/§9 但漏改 §5.4/§7.4。
   **核心事故形态**：双源不一致——同一事实（八步大运干支）在草稿 §1.3 正确、§5.4 错误、§7.4 错误，未被审计工具识别。
   防线 = `l4_audit_output.reconcile` 新增"双源同引"规则（同一干支在文中多位置出现，年份/十神/宫位字段必须全等，否则标 conflict）。
6. 另有两例同类笔误当轮发现并纠正，未受铁律 1–3 约束。

---

## v2→v3 升级迭代根因（2026-08-27 第三方对抗审查阶段）

v2 草稿生成后两位第三方对抗审查员（数据抄写 + 术理）发现 4 项硬错 + 6 项 CANDIDATE 优化，全部源于"凭印象/旧值"未清理。深度根因复盘如下：

### 根因 1 — 算完正确答案后未清旧值（盲点 A）
- 现象：§1.2 已写「score=55.8 中和」，但 §3.1/§7.3/§11.2 仍残留「21分偏弱」「得地 0 分」等旧值。
- 根因：算完 ws-04 正确答案后，未全文替换「偏弱/极弱」等字面，导致多节出现自相矛盾。
- 防线：`l4_audit_output.reconcile` 规则五 `ws_score_drift`——文中凡出现"X分偏弱/中和"等，X 必须等于快照 ws-04 score，偏差 >0.5 即报 conflict。

### 根因 2 — 日主十神映射记错（盲点 B）
- 现象：§1.1 月支藏干十神误写为「戌本气戊偏财/中气辛七杀/余气丁食神」——藏干顺序戊/辛/丁 正确，但十神全部对调。
- 根因：日主辛，戊应为正印、辛应为比肩、丁应为七杀；"凭印象" 错配。
- 防线：`l4_audit_output.reconcile` 规则六 `ten_god_mismatch`——文中"X→某十神"必须符合 `DM_GOD[日主][X]`，否则报 conflict。

### 根因 3 — 流年→年龄换算凭印象（盲点 C）
- 现象：§11.3「20岁 2025 转折 流年比肩」——2025=乙巳偏财，2031=辛亥比肩（实际 21 岁）。
- 根因：流年表年份和岁数人为换算出错，未用 `year - birth_year` 公式校验。
- 防线：`l4_audit_output.reconcile` 规则七 `age_year_mismatch`——文中"X 岁 YYYY"必须满足 YYYY - 出生年 = X（容差 ±1）。

### 根因 4 — 草稿产出无"出口前强校验"门
- 现象：v1 草稿出档时未跑"提交前强校验"工具，硬错直接出。
- 防线：`l4_strict_commit.py`（v3 新增）——草稿提交前必跑 4 步检查：
  1. check_invariants 5/5 PASS
  2. reconcile conflicts=0（含规则五/六/七）
  3. 草稿首行 `(snapshot-final)` 标签
  4. harvest 关键 token 引用 ≥ 30 行
  退出码 0 = 可对外输出，非 0 = 禁止 commit。

### 根因 5 — 跨节三方四正口径不一致
- 现象：§4.1 夫妻宫三方四正写"命宫丑"，实际引擎实证 scope=[夫妻,福德,迁移,官禄]；§6.2 财帛宫三方四正同样混用。
- 根因：未对照 `c_six_key_palace_sanfang_sizheng` 引擎实证 scope_palaces 列表，凭印象写"丑/未/巳"三合。
- 防线：草稿引用三方四正必须显式标注"@引擎 snapshot scope=[...]" + 引用 `c_six_key_palace_sanfang_sizheng` 字段。

### v3 防御工事汇总
| 防线 | 触发器 | 抓出类型 |
|------|--------|---------|
| `l4_data_harvest.py` | 草稿附录自动搬运 | 硬错 #3 #4 根因 |
| `l4_audit_output.reconcile` 规则四 `double_source_mismatch` | 跨节同干支多位置 | 硬错 #5 根因 |
| `l4_audit_output.reconcile` 规则五 `ws_score_drift` | 文中"X分偏弱" | 盲点 A |
| `l4_audit_output.reconcile` 规则六 `ten_god_mismatch` | 文中"X→十神" | 盲点 B |
| `l4_audit_output.reconcile` 规则七 `age_year_mismatch` | 文中"X岁 YYYY" | 盲点 C |
| `l4_strict_commit.py` | 草稿 commit 前 | 综合门禁 |
| `assert_l4_audit_output_v3_rules.py` | 回归测试 | 4/4 PASS 锁定规则 5/6/7 不漏报不误报 |

**结论**：v3 草稿 + v3 snap + v3 工具链 闭合。后续每次新命造必须跑 `l4_data_harvest.py` + `l4_strict_commit.py` 双门禁 + 两位第三方对抗审查收敛。

## v3→v4 升级：B男命防御工事（2026-08-30）

B男命报告（`_b_male_final_report.md`）出档后扫出 179 条违规，对应 5 大类手推事故形态（双源不一致 / 段无 snap 引用 / 伪诗虚构 / 模糊占位 / 模块未接入）。新增 v4 防御层：

| v4 防线 | 触发器 | 抓出类型 |
|---------|--------|---------|
| `l5_defense_check.py` rule1 段首 snap 引用 | 段落扫描 | 段无 snap 引用 → 51 处 |
| `l5_defense_check.py` rule2 l3 模块全谱 | 关键词扫描 | l3_* 模块未覆盖 |
| `l5_defense_check.py` rule3 伪诗/虚构 | 标志词扫描 | "歌诀/格局/十恶大败/值符/天芮/化禄..." → 119 处 |
| `l5_defense_check.py` rule4 双源一致性 | 跨段聚合 | 旺衰分值/大运年份跨段不一致 |
| `l5_defense_check.py` rule5 跨章节引用链 | §16 结论章扫描 | snap 引用 < 5 阈值 |
| `l5_defense_check.py` rule6 占位/删除占位 | 模糊词扫描 | "因计算错误已移除"等 → 7 处 |
| `l5_defense_check.py` rule7 v3 综合门禁 | 报告首部扫描 | snapshot-final 标签 + harvest 引用 ≥ 30 |
| `l5_defense_check.py` rule8 对账 | l4_audit_output.reconcile 子进程 | 任何 conflicts > 0 即 FAIL；unverified > 9 即 FAIL（默认 5 阈值太低，2026-08-30 B男命含3个六爻爻ganzhi+l4范围局限项 + 3个通用知识神煞列表项共6项非数据错误） |
| `l5_defense_check.py` rule3 豁免 | 段落扫描 | 含【XX入门/含义速查/速查/简介/解释/说明/概念】的术语解释段免扫POEM_MARKER（2026-08-30 B男命补充通俗注释后加） |
| `templates/report_template.md` | 报告生成入口 | 强制 `{{变量}}` 占位，避免手写确定性数据 |

**v4 强制流程**：每次报告生成结束 → 必跑 `python l5_defense_check.py check --text <report> --snap <snap> --out <report>.l5.json` → verdict=PASS 才许对外输出。审计日志落到 `temp/_defense_audit_log.md`。

## 审计命令模板

```bash
# ① 生成全量快照（四柱+十神/大运/流年 2020-2040/紫微十二时辰/奇门/称骨，全部引擎直出）
python l4_audit_output.py snapshot --datetime "2006-06-25 00:30" --gender 女 --out temp/_snap_a.json
# ② 五条机械化不变量（aud-inv-01..05）
python l4_audit_output.py check --snap temp/_snap_a.json --out temp/_inv_a.json
# ③ 结论文本对账（出口前必跑；unverified/conflicts 必须清零）
python l4_audit_output.py reconcile --text 结论草稿.txt --snap temp/_snap_a.json --out temp/_rec.json
```

## 注册表注记（为什么 aud-inv-* 不进 rule_registry.csv）

`l4_audit.registry_check()` 做 data/rule_registry.csv ↔ 代码字面量双向校验，但其扫描范围只有
`l3_*.py + m1.py`，且扫描正则 `[a-z]{2,4}-\d{2,4}...` 抓不到 `aud-inv-01` 这类三段形态整词
（实测会把 `inv-01` 当成抽取结果）。实测把 aud-inv-01..05 追加进注册表会立即触发
"注册表条目全部在代码中存在 多 [...]" FAIL。因此不变量 id 以 `l4_audit_output.INVARIANTS`
常量 + `assert_l4_audit_output.py` 的 S-02 断言双向锁定，不改 `data/rule_registry.csv`。
