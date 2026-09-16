# 第四轮对抗复审（工程/数据方向）— D:\shushu 清理整理轮

- 复审员：第三方对抗审查（工程/数据）
- 日期：2026-09-16
- 手段：只读 + 跑 python/git，未修改任何被审文件（除本报告）
- 结论口径：不采信修复方自述，全部结论来自本人实跑

---

## 1. 回归独立性验证（本人亲自实跑）

| 命令 | 期望 | 实得 | 判定 |
|------|------|------|------|
| `PYTHONIOENCODING=utf-8 python l4_audit.py` | PASS 198 / FAIL 0 | 合计：PASS 198 / FAIL 0（rc=0） | ✅ |
| `PYTHONIOENCODING=utf-8 python assert_tables.py` | 94/94 | 合计 94 项 PASS 94 FAIL 0（rc=0） | ✅ |
| 全部 `assert_*.py` | 22 个全 rc=0 | 22 个全部 rc=0 | ✅ |
| `PYTHONIOENCODING=utf-8 python l4_audit.py --verify` | 全一致 | 155 个文件哈希全部一致（rc=0） | ✅ |

关键旁证（l4_audit 内嵌第七项独立抽查）：
```
退出码 0
庚辰申子辰组 (2000,2,5,12,0): 紫微 oracle=丑 火星=申 铃星=辰 天魁=丑 禄存=申 差异=无
丙申申子辰组 (2016,1,23,14,0): 紫微 oracle=巳 火星=辰 铃星=巳 天魁=子 禄存=卯 差异=无
独立解析抽查: PASS
```
22 个 assert 明细（均 rc=0）：
assert_l3_bazi_daliu / bazi_liuri / chenggu / heluolishu / hepan / huangli / liuren / liuyao / meihua / qimen / qimen_duanju / shensha / tieban / wangshuai / wuyunliuqi / xiaoliuren / ziwei / ziwei_liunian、assert_l4_audit_output、assert_l4_audit_output_v3_rules、assert_l5_rule9_age_year、assert_tables。

**判定：回归独立复现，与修复方自述一致，无造假迹象。**

---

## 2. 归档安全性（是否误归档被引用文件）

方法：对 `D:\shushu-archive-20260916\` 全量文件名（排除 3 个整库拷贝 `_v11_lfcheck/_v11_repocopy/_v11_v10copy`，617 个）逐一比对项目内是否同名；
再对项目全部 `*.py` 源码提取文件名字面量（86 个），反查「项目内无、归档内有」的引用。

结果：
- 617 个归档文件 → 612 个不在项目内，但**其文件名在项目 py 源码中命中数 = 0**。
- 源码文件名字面量中「项目内不存在」的仅 7 个，且均为**动态拼接后缀**（`.check.json`/`.rec.json`/`.l5.tmp.txt`）或测试临时产物（`_test_v3_clean.txt` 等）或紫微网络缓存 key（运行时抓取），**无一是「被引用却已归档」**。
  - 归档内命中「危险」清单：**空**。

- `data/l3_ziwei_oracle_cache/` 恢复确认：磁盘有 **127 个** html 夹具（另归档 `temp/_zw_oracle_cache` 的 22 个为另一批 `-s0/-s1` 旧探针，非同一批）；`l4_audit_ziwei.py` 独立解析抽查 PASS，`assert_l3_ziwei.py` rc=0 → 夹具确已恢复且可用。

**判定：归档未误摘任何被代码引用的文件。归档安全。**

---

## 3. 交付目录完整性 `report/p_1974_female/`

- 文件数：**11 个**，与预期完全一致：report.md / snapshot.json / harvest.txt / gates-reconcile.json / gates-l5.json / review-1-data.md / review-1-theory.md / review-2-data.md / review-2-theory.md / review-3-data.md / review-3-theory.md。
- report.md 首行「数据底座」指向 `report/p_1974_female/snapshot.json` → **存在**（146 065 B，JSON 可解析，23 个顶层键）。
- report.md 自述引擎版本哈希与快照 meta.provenance 一致（抽查可解析）。
- `gates-l5.json`：`verdict = PASS`，`summary.n_violations = 0`（`violations` 字段是 9 条 rule 名清单，非违规实例），`n_l3_modules_hit/total = 13/13`，覆盖率 100%，`report_size=23173`（= report.md 字符数，非字节数，与磁盘 38 378 B 自洽）。
- `gates-reconcile.json`：`conflicts = []`（0 冲突）；`matched/unverified` 字段齐备。

**判定：交付目录完整、内部自洽。**

---

## 4. git 一致性

- `git ls-files | wc -l` = **156**（符合预期）。
- 已跟踪文件在磁盘缺失数：**0**（逐文件存在性校验通过）。
- 未跟踪项（`git status --porcelain` 中 `??`）：7 项
  - `_ly_oracle_cache.json`（613 663 B，根目录，六爻 oracle 网络缓存；被已跟踪的 `assert_l3_liuyao.py:184` 读取）
  - `data/l3_ziwei_oracle_cache/`（127 html，**注释明确「未入库」**，见 `l4_audit_ziwei.py:4`，设计如此）
  - `temp/_assert_cli_snap.json` / `_assert_rec_old.json` / `_assert_snap_a.json` / `_text_old.txt`（经核实由 `assert_l4_audit_output.py:135-150` 生成，跑测试即重建，属预期产物）
  - `temp/_review4_theory.md`（并行理论审查员产物）
- **★ 中等问题（index 滞后）**：工作树有 **24 个已跟踪文件**内容未 `git add`，index 仍停在最后一次提交（HEAD=9042771，2026-08-16 08:15）：
  ```
  README.md SHA256SUMS.txt
  assert_l3_bazi_daliu.py assert_l3_bazi_liuri.py assert_l3_hepan.py assert_l3_tieban.py
  data/arbitration_log.csv data/rule_registry.csv docs/preregister.md docs/sampling.md
  l3_bazi_daliu.py l3_bazi_liuri.py l3_hepan.py l3_tieban.py l4_audit.py m1.py m1_compare.py
  report/boundary_cases.csv report/final_assert_report.txt report/l3_bazi_daliu_report.txt
  report/l3_hepan_report.txt report/l3_liuyao_report.txt report/l4_audit_report.txt report/m1_compare_report.txt
  ```
  证据（非行尾噪声，为实质内容改动）：
  ```
  $ git diff --stat -- . ':!report'   → 17 files changed, 361 insertions(+), 145 deletions(-)
  $ git show HEAD:docs/sampling.md | sed -n 5p
    ...（自研 0:00 子正 vs oracle 23:00 子初差异单列）。
  $ sed -n 5p docs/sampling.md
    ...（自研 0:00 子正 vs oracle 非默认 API `getDayInGanZhiExact` 的 23:00 子初，差异单列；oracle 默认 API 同为 0:00 子正，见 docs/preregister.md「约定语义」）。
  ```
  即：本轮 `git add` **只覆盖了新增文件（49 个 `A`）**，对**已跟踪文件的改动未 add**。
  - SHA256SUMS 侧：本人核对 `--verify` 通过、并逐文件确认 `SHA256SUMS.txt` 条目哈希 == **工作树**内容（LF 归一），即 **签名快照 = 工作树**，内部自洽。
  - 但 index ≠ 工作树 ⇒ 若日后按当前 index 提交，提交出的树将与 SHA256SUMS（工作树版）不一致，且**本轮的返工改动不会被提交捕获**。用户要求的「只 git add + 重签」中的 git add 未完成。

---

## 5. 结构隐患检查

- `temp/` 现存 **17 个**文件：12 个已入库（`_b_female_dump.txt`/`_rec_old.json`/`_snap_a.json`/`_snap_b_clean.json`/`_snap_b_female_full.json`/`_snap_b_male_full.json`/`_t4_b_harvest.txt`/`_t4_b_snap_v3.json`/`audit_ziwei.py`/`cg_oracle_samples.json`/`l3_qimen_duanju_oracle_dump.json`/`qm_audit.py`）+ 5 个未跟踪（见 §4）。未见孤儿目录、无嵌套 `.git`、无符号链接/联接。
- `_zw_oracle_probe.py`（`assert_l3_ziwei.py:249` 的 `from _zw_oracle_probe import cmp_self` 依赖，且被 `l4_audit_ziwei.py` 设计性旁路）**已入库**：在 `git ls-files`（跟踪）且出现在 `SHA256SUMS.txt` 中。**✅**
- `.gitignore` 已补外部星历：`de440_l4.bsp`、`de440s.bsp` 均在册，`git check-ignore` 双双命中。**✅**
- `SHA256SUMS.txt` 头部注释 3 行 + 156 行，共 160 行；`_zw_oracle_probe.py` 出现 1 次（已签）。生成脚本 `l4_audit.py:385` 为唯一写点（仅 `--resign` 触发），报告 `report/l4_audit_report.txt` 为「重跑覆盖」设计产物（`l4_audit.py:475`），与工作树中的 ` M` 状态吻合，非异常。

---

## Findings

### 高
- 无。

### 中
1. **git index 滞后于工作树（`git add` 未完成）**：24 个已跟踪文件（含 `SHA256SUMS.txt` 自身与 `l3_hepan.py`/`m1.py`/`l3_tieban.py`/`l4_audit.py` 等源码）工作树已改但未 staged，index 仍为 2026-08-16 HEAD。SHA256SUMS 已按工作树重签并校验通过，故「快照自洽」；但 index 与签名快照不一致，日后提交会漏掉本轮改动并产出与签名不符的树。**提交前应 `git add` 这 24 个文件（并确认无需二次重签，因签名已对工作树）。**

### 低
2. `_ly_oracle_cache.json`（613 KB）未跟踪但仍被已跟踪的 `assert_l3_liuyao.py` 读取；文件在盘则离线可跑，若缺失将转入真实网络请求（`oracle_post` 有 3s 限流）。建议明确「入库 / 明确 gitignore」二选一，避免半入库态。
3. `temp/` 残留 4 个跑测试即重建的未跟踪产物（`_assert_cli_snap.json` 等）+ 1 个审查员产物（`_review4_theory.md`）；非本次清理遗留，但建议纳入 `.gitignore` 或清理。
4. `data/l3_ziwei_oracle_cache/` 未跟踪属**设计性**（`l4_audit_ziwei.py:4` 注释「未入库」），本次不计问题，仅记录以免误判。

---

## Verdict

**放行（有条件）**

- 5 项复审维度中，回归、归档安全、交付目录、结构隐患 **4 项通过**；git 一致性功能面无缺失（156/156、0 丢失）。
- 唯一实质问题是 **中等问题 1（index 滞后 / `git add` 未覆盖已跟踪文件的改动）**——因当前工作树 + SHA256SUMS 自洽且 `--verify` 通过，功能与冻结快照未受损，故不构成打回；但**在任何提交动作之前必须先补齐该 24 个文件的 `git add`**，否则冻结语义被破坏。
- 另需澄清低 2（`_ly_oracle_cache.json` 的入库口径）。
