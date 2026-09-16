# P 女命报告修复轮 · 数据抄写维度增量复审（第三方对抗审查）

- 审查员立场：独立核验，不采信修复方自述；只读引擎与报告，未修改任何引擎代码/报告文件
- 审查对象：`temp/_p_final_report.md`（与 `_p_report_draft.md` 字节一致，sha256 前 16 位 `845bccab54fb9bb6`，484 行）
- 数据底座：`temp/_probe_snap.json`（meta.generated_at = 2026-09-15T22:32:18，provenance 17 文件）
- 对照物：`temp/_probe_snap.prev.json`（22:16:16）、`temp/_p_harvest.txt` / `_p_harvest.prev.txt`、`temp/_p_rec.json`、`temp/_p_report_draft.md.l5.json`
- 复审新增只读产物（未触及引擎/报告）：`temp/_review2_rec.json`、`_review2_l5.json`、`_review2_inv.json`、`_review2_snap.json`（独立重生成快照）
- 环境：`PYTHONIOENCODING=utf-8 python`（工作目录 D:\shushu）

## 复审结论速览

- 高 findings：**无**
- 中 findings：**无**
- 低 findings：**2**（§5 L132 / §15 L257 一处引用范围精度；§15 L258 一处引用范围精度）——均为「引用路径承载范围」问题，数据值本身核实无误
- 跨域：并行术理复审（`temp/_p_review2_theory.md`）另报 2 条低 finding（其 Finding-2 与本域低-1 为同一问题；其 Finding-1 §12 公式注差「+1」经本复审独立核验属实）——两域合计 **3 条唯一低 finding，全部文字层**
- 最终 verdict：**打回重做（轻量）**——全部申报修复经独立核验达成、零数值错；但 3 条低 finding 未清零，未满足项目「无 findings 才许出口」条件；修正仅涉引用路径扩注与 1 处补注，不触碰引擎/数据/快照，复核即放行

---

## 一、引用承载逐条核验（任务重点）

### 1.1 全量解析

脚本抽取报告中全部 `snap.<路径>` 引用：共 107 处、69 条唯一路径（唯一「未解析」为 `snap.json`，系 `_probe_snap.json` 文件名字符串截取，伪阳性）。**68 条真实引用路径 100% 在快照中可解析、无空挂引用。**

### 1.2 修复项（新增/修改引用）逐值对照

| 报告位置 | 报告文字 | 快照路径与实测值 | 判定 |
|---|---|---|---|
| §1.3 L38 | 得令：月支午、本气丁火、status=旺、score=100、rule=ws-01 | `wangshuai.de_ling` = {month_zhi:午, ben_qi:丁, status:旺, score:100, rule_id:ws-01} | ✓ |
| §1.3 L39 | 得地 rule=ws-02；得势 rule=ws-03 | `wangshuai.de_di.rule_id`=ws-02；`de_shi.rule_id`=ws-03 | ✓ |
| §1.3 L40 | 68.6 分偏旺；权重 0.4/0.35/0.25；rule=ws-04 | `wangshuai.zonghe` = {score:68.6, level:偏旺, weights:{0.4,0.35,0.25}, rule_id:ws-04} | ✓ |
| §3 L78 | 命宫壬申；身宫辰宫；金四局 | `ziwei_hours[hour=22]`：minggong={gan:壬,zhi:申}；shengong.zhi=辰；wuxing_ju.name=金四局 | ✓ |
| §3 L95 | 廉贞禄→父母(癸酉)；破军权→父母；武曲科→仆役(丁丑)；太阳忌→迁移(丙寅) | h22：sihua=廉贞禄/破军权/武曲科/太阳忌；palaces 星位与 sihua 数组交叉吻合（父母[禄,权]、仆役[科]、迁移[忌]） | ✓ |
| §3 L97/L82-93 | 十二宫三栏表 12 行 | h22.palaces 逐格程序化比对（干支/主星/辅+煞并集/四化）：12/12 严格相等 | ✓ |
| §4 L103 | 起限 4 岁、逆行、共 12 限 | `ziwei_liunian.daxian` = {start_age:4, direction:逆行, items:12} | ✓ |
| §4 L107-118 | 大限 12 限表（壬申 4-13 … 癸酉 114-123，限四化全列） | `ziwei_liunian.daxian.items` 逐格程序化比对：12/12 严格相等（含每限 4 个四化） | ✓ |
| §4 L120 | 2026 干支丙午；流年命宫落庚午(夫妻)；四化 天同禄/天机权/文昌科/廉贞忌 | `ziwei_liunian.liunian` = {year:2026, ganzhi:丙午, palace:夫妻, palace_ganzhi:庚午, sihua:[天同禄,天机权,文昌科,廉贞忌]} | ✓ |
| §5 L128 | 夏至·下元·阴遁 6 局 | `qimen.dingju` = {term:夏至, yuan:下元, dun:阴遁, ju:6} | ✓ |
| §5 L129/L130 | 值符天芮（旬首甲辰、隐仪壬）落巽四宫；值使死门 zhishi_palace=5 | `qimen.zhifu_zhishi` = {xunshou:甲辰, yiyi:壬, zhifu_star:天芮, zhifu_palace:4, zhishi_door:死门, zhishi_palace:5}；pan[4].gua=巽宫 | ✓ |
| §5 L131 | 坤二宫之门为死门 | `qimen.eight_doors["2"]`=死门 | ✓ |
| §12 L223 | 月5→小吉、日16→留连、时支序12→大安（吉） | `xiaoliuren.xlr-03` = {month_gong:小吉, day_gong:留连, final_gong:大安}；xlr-02 大安=吉 | ✓ |
| §12 L225 | 断辞「身未动时，问事主安宁」 | `xiaoliuren.xlr-04.duan` 首句逐字一致 | ✓ |
| §13 L231-236 | 1974-07-05/丁未/五月十六；除日吉；勾陈黑道；建除黄道；红艳(hl-03-07)；宜忌表 | `huangli` 各字段逐值一致；shensha.hits 仅 1 项=红艳，与报告「命中：红艳」一致 | ✓ |
| §15 L255 | 六壬北京时钟表时口径 | `liuren.notes[0]` 同文 | ✓ |
| §15 L256 | 小六壬 23 点归次日民俗口径 | `xiaoliuren.notes[1]` + xlr-01.alt 同文 | ✓ |
| §15 L257 | 奇门口径（见 Findings 低-1） | `snap.qimen` 承载定局/盘面，但「月将同为未」不在其子树（实测 `'月将' in snap.qimen`=False） | ⚠ 低-1 |
| §15 L258 | 河洛取数太玄数派+先天卦序、异文已申报（见 Findings 低-2） | `hlyl01.source/alt` 载太玄数与两派异文；「先天」二字不在 hlyl01 子树（实测 False），在 hlyl02.source | ⚠ 低-2 |
| §15 L259 | 岁运换年大寒/立春两派（wylq-01 alt 已申报） | `wuyunliuqi.sui_yun.alt` 原文含两派 | ✓ |
| §15 L260/L261 | 紫微取值来源；快照生成时间 | `ziwei_hours`、`ziwei_liunian` 存在；`meta.generated_at`=2026-09-15T22:32:18 与报告头部一致 | ✓ |
| §16 L267-278 | 12 条核心结论 | 逐条对照快照：四柱/旺衰/大运/紫微/流年/神煞7项/称骨/五运六气/奇门/梅花/六壬/小六壬+黄历/河洛 全部 ✓（含 L270「行限戊辰(44-53)财帛宫」= daxian.items[4]，其 liunian_years 含 2026(午)） | ✓ |

### 1.3 其余正文引用（上一轮已验，本轮抽样复核无回归）

§1.1/1.2/1.4/1.5、§2、§6-§11、§14 的全部 snap 引用（true_solar_time、pillars、day_master、ten_gods、dayun.*、chenggu.*、liunian、shensha、wuyunliuqi.*、meihua.*、liuyao.*、liuren.*、heluolishu.hlyl01-05 等）本轮再度对照，均存在且逐值一致。

## 二、数值独立复算（≥5 项，共 12 项）

1. **起运岁数**：出生 1974-07-05 22:13 − 芒种 1974-06-06 09:52（=snap.dayun.jie_time）= 29天12时21分 = 42501 分钟；按 preregister 折算率（4320/360/12 分）→ 9岁10月1天18时，与 `dayun.qiyun` **精确相等**。
2. **交运时刻**：1974-07-05 22:13 + 9岁10月1天18时 = 1984-05-07 16:13，与 `dayun.jiao_time` 精确相等。
3. **大限限四化**：按「大限宫干 × 标准四化表」（中州派口径）逐限重推 12 条——壬→天梁禄/紫微权/左辅科/武曲忌……癸→破军禄/巨门权/太阴科/贪狼忌，**12/12** 与快照及报告表一致。
4. **命宫/身宫**：农历五月→生月宫=午；真太阳时 19:59→戌时。命宫=自午起子逆数至戌→申宫，申宫五虎遁甲年得壬→**壬申**；身宫=自午起子顺数至戌→辰宫→**辰**。五行局=壬申纳音剑锋金→**金四局**；金四局→起限 4 岁；甲寅阳年女→逆行。全部与快照一致（也解释了 hour=22 采样实取真太阳时辰的模块口径）。
5. **小六壬**：月5 从大安顺数→小吉；日16 自小吉（16≡4 mod6）→留连；时序12 自留连（12≡0）→大安。与 `xlr-03` 一致。
6. **流年干支**：(2026−4) mod 60 = 42 → 丙午。与 §4/§6 一致。
7. **建除**：午月（芒种后）未日→「除」；与 `huangli.jianchu` 一致。
8. **称骨算术**：12+5+8+6 = 31 钱 = 3两1钱；与 `chenggu.bones_total_weight` 一致。
9. **日柱**：直接查 L0 权威表 `data/ganzhi_days.csv` 1974-07-05 = 丁未（独立于引擎路径）。
10. **奇门定局**：丁未日属甲辰旬（符头甲辰，辰∈辰戌丑未→下元）；夏至阴遁下元=6 局（「夏至九三六」）。与 `qimen.dingju` 一致。
11. **奇门值符**：时柱庚戌属甲辰旬→旬首甲辰、隐仪壬（甲辰壬）；壬地盘落 2 宫、天芮为本宫星→值符天芮，加成时干庚之 4 宫。与 `zhifu_zhishi` 一致。
12. **空亡口径校验**：`check_invariants` aud-inv-05：「值符天芮实落4宫/申报4宫；值使死门实落2宫/申报5宫；值符宫天盘壬己含旬首仪壬=True」——与报告 §5 L130「值为中宫申报；寄坤二宫」披露完全一致。

## 三、diff 复核（自行重跑，不采信自述）

### 3.1 快照新旧 diff（`_probe_snap.prev.json` vs `_probe_snap.json`）

深 diff 共 **49 处变更**，与申报逐项吻合、**零删除、零范围外变更**：

| 变更 | 数量 | 明细 |
|---|---|---|
| `ziwei_liunian` 新增 | 1 段 | 整段 ADD（l3_ziwei_liunian 直出） |
| `ziwei_hours` ×12 条目各 +3 键 | 36 | 每时辰新增键恰为 `shengong/sihua/wuxing_ju`，零删除 |
| `wangshuai` 扩展 | 9 | 顶层 +de_ling/de_di/de_shi（3）；zonghe 内 +rule_id/source/alt/weights/advice/thresholds（6）；score=68.6/level=偏旺 无 CHG |
| `meta` | 3 | generated_at CHG（22:16:16→22:32:18）、note CHG（+l3_ziwei_liunian）、provenance +l3_ziwei_liunian.py（16→17） |

### 3.2 harvest 新旧 diff

`difflib` 逐行 diff：**仅 4 行变化**，与申报完全一致——顶部来源行 + [B]/[Z]/[A] 三个标题行，均为 `t1_bazi.json→_p_t1_bazi.json` 等 basename 修正。实测 `temp/_p_t1_bazi.json / _p_t1_ziwei.json / _p_t4_all.json` 存在，旧名（t1_bazi.json、t4_b_all.json）在盘上不存在——修复方向正确。生成器 `l4_data_harvest.py` L339-341 已改为 `os.path.basename(输入)` 动态取源名。

### 3.3 报告附录 vs harvest 文件（补充复核，解释性）

附录段与 `_p_harvest.txt` 逐行 diff：**8 行差异全部为子标题行追加「 (snapshot)」注解**（B.6/Z.2/Z.4/A.3/A.4/A.5/A.7/A.8），数据行零差异。该注解可由管道脚本 `temp/_p_make_draft.py` L12-37（对含 POEM_MARKERS 且无 snap 引用的段首行程序化追加标注）完整复现；且**用「body + 标注后 harvest」在内存中重新合成，与现 draft 全文逐字节一致（True）**——确认 draft 由文档化管道生成，无人工篡改（与上一轮「观察 1」同结论，本轮升级为机制级确证）。

## 四、新引入检查

- §1.3 L38-40 三行（新扩展引用）：值全部落盘、无新错抄（见 §1.2 表）
- §1.5 L62-64：骨重与合计 ✓；「称骨歌（女命版…以引擎收录版本为准）」——文本与 `l3_chenggu.py` FEMALE 表 key=31 条目**逐字相等**（POEM_SRC[女]=astrologybazi 主流版），「女命版」表述有源码依据，无新错抄
- §3/§4 大表：程序化逐格（12+12 行）零不一致，含限四化顺序（禄→权→科→忌）
- §15 各注：6/8 条承载无懈，2 条见 Findings
- §16 12 条结论：全部有承载，无新裸数据
- 报告头部哈希：`fe75470af92b982`（m1.py）、`e5f9889c643aebf`（l3_ziwei.py）、`33d93982c511492`（l3_qimen.py）均为对应 `meta.provenance` 哈希的**正确前 15 字符**；且与磁盘引擎文件实际 sha256 **全等**（m1.py 实测 sha256=fe75470af92b9821f4e62…）

## 五、门禁与回归（独立重跑）

| 项目 | 修复方申报 | 我方实测 | 结果 |
|---|---|---|---|
| reconcile | matched=105 / unverified=5 / conflicts=0 | 重跑 `l4_audit_output.py reconcile`：**105/5/0**（exit 0） | ✓ |
| l5 防御门禁 | PASS | 重跑 `l5_defense_check.py`：**PASS**、违规 0、13/13 模块覆盖（exit 0） | ✓ |
| assert_l4_audit_output | 40/40 | **40/40 PASS**（exit 0） | ✓ |
| v3_rules | ALL PASS | **ALL PASS**（exit 0） | ✓ |
| assert_tables | 94/94 | **94/94**（exit 0） | ✓ |
| l4_audit 主流程 | 198/0 | **PASS 198 / FAIL 0**（exit 0） | ✓ |
| SHA256SUMS --verify | 113/113 | **113 文件全一致**（exit 0，修改过的 L4 工具已重签） | ✓ |
| check_invariants（P 快照） | —（本轮加做） | aud-inv-01..05 **5/5 PASS** | ✓ |
| 快照可复现性 | —（本轮加做） | 以相同参数独立重生成 `_review2_snap.json`，与 `_probe_snap.json` 深比对：**唯一差异为 meta.generated_at 与未传合盘参数（hepan 段）**；新增全部字段字节级复现 | ✓ |
| reconcile 5 项 unverified | 己卯/1979/1980/1988/1989 | 逐项定位：己卯∈`snap.liuyao.lines[0]`；4 个年份∈`snap.heluolishu.hlyl04.dayun.items`——均为工具检索覆盖面限制，非数据错误 | ✓ |

## Findings

### 低-1（引用范围精度）§5 L132 与 §15 L257 同一句：引用 `snap.qimen`，其中「月将同为未」不在该路径子树

- 报告 L132：「本盘真太阳时 19:59 与北京时 22:13 同落夏至～小暑段、月将同为未，两口径无数值差异，提请 v2 重裁（数据底座：snap.qimen）」（§15 L257 同句）
- 实测：`'月将' in json.dumps(snap.qimen)` = False；「月将=未」实际承载于 `snap.qimen_duanju.month_jiang = "未"`（另 `snap.liuren.month_jiang` 同值）；「小暑」边界值在 `data/solar_terms.csv`（1974-07-07 20:11），快照内不含
- 数据值本身核实**正确**（两时戳同日、同落夏至段、定局拆补法按日走元、月将按中气——两口径确无差异），仅引用路径标注不完整
- 建议：引用扩为 `snap.qimen、snap.qimen_duanju.month_jiang`（或改述）

### 低-2（引用范围精度）§15 L258：引用 `snap.heluolishu.hlyl01`，其中「先天卦序」元素不在该子树

- 报告 L258：「河洛理数取数采用网传太玄数起卦派（干支同数）与先天卦序；…（数据底座：snap.heluolishu.hlyl01）」
- 实测：`'先天' in json.dumps(hlyl01)` = False；「先天八卦序 乾1兑2离3震4巽5坎6艮7坤8」位于 `hlyl02.source`
- hlyl01 本身正确承载「太玄数取数派 + 河图生成数/古籍原书取数两派异文」；「先天卦序」为引用范围外溢
- 建议：引用扩为 `snap.heluolishu.hlyl01、hlyl02`（或改述）

（以上两条与上一轮 F3 为同类「引用范围」问题，数据值无错、工具门禁不捕获；按项目纪律「无 findings 才许出口」构成轻量打回条件。）

## 六、跨域汇总参考（供主控）

并行术理复审已落盘 `temp/_p_review2_theory.md`（本会话派发、独立完成、无交叉读取）：verdict=**打回重做（轻量）**，findings 2 条低，其中：

1. 其 Finding-2（§5/§15「月将」引用路径不含该字段，建议改注 `snap.qimen_duanju.month_jiang`）与本复审低-1 为**同一问题**——两评审独立得出、相互印证。
2. 其 Finding-1（§12 口径注公式差「+1」）经本复审独立核验**属实**：`l3_xiaoliuren.py` docstring L18/L110 写 `(h+1)//2%12`，而 L111 实现为 `(dt.hour + 1) // 2 % 12 + 1`；报告 L224 系逐字转述 docstring（非错抄），但读者按所载公式复算 h=22 得 11（戌）≠ 实际 12（亥）。修正方向：报告该句补注实现式「+1 归一 1..12」（引擎 docstring 修正留待解冻后）。

两域合计 3 条唯一低 finding（1 条重叠），均为报告文字层引用/标注精度问题，零数值影响、零引擎数据面影响。

## 最终 Verdict

**打回重做（轻量）。** 理由：

1. 全部申报修复经独立核验达成——F1 高（ziwei_hours +3 键 / ziwei_liunian 新增 / §4 引用改指）、F2 中（wangshuai 全量落盘）、F3 低（harvest basename / 规范出处改注），实测 diff 与申报逐项吻合；全量复核（68 条引用、12 项复算、双 diff、哈希、门禁 6+2 项）**零数值错抄、零双源不一致、零新引入数据错**——数据面本身干净。
2. 但本域 2 条低 finding（叠加术理域 1 条，合计 3 条唯一）未清零，按项目纪律「无 findings 才许出口」，现状未达放行条件；两域评审对「月将引用」问题独立收敛，置信度高。
3. 修正均为**纯文字层**：低-1 → 引用改注 `snap.qimen、snap.qimen_duanju.month_jiang`；低-2 → 引用改注 `snap.heluolishu.hlyl01、hlyl02`（或等价改述）；§12 L224 → 补注实现式。不触碰冻结引擎、不重生成快照；修正后重跑 l5/reconcile + 3 处引用点查即可放行。
