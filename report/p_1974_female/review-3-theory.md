# 命造 P 报告修复核验轮·术理终审（第三轮复核，轻量）

- 终审对象：`D:\shushu\temp\_p_final_report.md`（snapshot-final 定稿，484 行）
- 数据底座：`D:\shushu\temp\_probe_snap.json`（生成于 2026-09-15T22:32:18）
- 上轮依据：`D:\shushu\temp\_p_review2_theory.md`（verdict=打回重做（轻量），低 findings ×2）
- 终审方式：报告段落逐行读取 + 快照字段级核验 + **独立 python 复算公式** + 引擎哈希抽验 + `l4_audit.py --verify`。全程只读，未修改任何引擎或报告文件。
- 终审日期：2026-09-15

---

## 一、两条低 findings 修复核验

### 修复 1（§12 公式转录瑕疵）——到位
- 落地位置：报告 L224。新注文（摘）：`时支序=((h+1)//2)%12+1，子=1…亥=12；23:00-23:59 属次日的民俗口径；模块 docstring 转录公式省略末位 +1 系文档瑕疵、实现正确，已记入 errata`。
- **独立复算**（python，`((h+1)//2)%12+1`）：
  - h=22 → **12**（亥）＝快照 `snap.xiaoliuren["xlr-01"].hour_ordinal=12`、`shichen="亥时"` ✓
  - h=23 → **1**（子）；h=0 → **1**（子）；另验 h=1→2、h=2→2、h=3→3、h=21→12，全时区映射自洽 ✓
- **文档瑕疵描述准确性**：`D:\shushu\l3_xiaoliuren.py` 模块 docstring L18 与函数 docstring L110 均写作 `(h+1)//2%12`（缺末位 +1），实现 L111 = `(dt.hour + 1) // 2 % 12 + 1`——errata 所述「约 L18 / 约 L110 vs L111」差异描述**准确**。
- **errata 记录属实**：`D:\shushu\report\errata\2026-09-15-p-seg3-fix.md` §五-1 / §六-1 已记录该 finding 与修复，并注明「冻结模块 docstring 不改，瑕疵记入本 errata，留待 v2 解冻窗口修正文档」；§12「已记入 errata」为真。

### 修复 2（§5 / §15 月将引用路径悬空）——到位
- 落地位置：§5 L132「月将同为未（月将数据底座：snap.qimen_duanju.month_jiang）……（定局数据底座：snap.qimen.dingju）」；§15 L257「（定局数据底座：snap.qimen.dingju；月将数据底座：snap.qimen_duanju.month_jiang）」。
- **独立快照核验**：
  - `snap.qimen` 键集 = {dingju, eight_doors, eight_gods, nine_stars, pan, sanqi_liuyi_layout, zhifu_zhishi}，**不含 month_jiang** ✓（与 L172-180 裁剪行为一致）
  - `snap.qimen_duanju.month_jiang == "未"` ✓
  - 全快照 `month_jiang` 仅两处：`/liuren/month_jiang`（六壬，中气换将）、`/qimen_duanju/month_jiang`（奇门，节界 bisect）——新引用路径**精确命中落盘字段** ✓

## 二、本轮 4 处文字修改核验（含另 2 处）

### 修改 3（§15 奇门申报引用拆分）——到位
同修复 2 的 §15 L257 行；定局引 `snap.qimen.dingju`（实测 = {"term":"夏至","dun":"阴遁","yuan":"下元","ju":6} ✓）。

### 修改 4（§15 河洛拆分引用 hlyl01 / hlyl02）——到位、无过度声称
- 新注文（L258）：`取数采用网传太玄数起卦派（干支同数，数据底座：snap.heluolishu.hlyl01）与先天卦序（数据底座：snap.heluolishu.hlyl02）；古籍原书取数（纳甲洛书数+河图支双数）及河图生成数派为异文，模块 alt 已申报、报告按主口径`
- 快照对照：`hlyl01.source` 载「网传太玄数起卦派：太玄数干支同数 甲己子午9…」✓；`hlyl02.source` 载「…先天八卦序 乾1兑2离3震4巽5坎6艮7坤8…」✓；异文「纳甲洛书数+河图支双数」「天干河图生成数」确在 `hlyl01.alt` ✓。拆分引用准确，与上轮数据域 Finding 低-2 的整改要求（「先天」二字实在 hlyl02）完全对应。

### 无夹带检查
- 全文 grep：`h+1` 仅 L224 一处；`月将同为未` 仅 L132/L257 两处；奇门类 `month_jiang` 引用全部指向 qimen_duanju——旧瑕疵无残留。
- `_p_report_draft.md` 与 `_p_final_report.md` 逐字节一致；errata §六 列出的 4 项修复与本轮实际改动一一对应，未见未申报的额外修改。

## 三、全文扫读（无因本轮修改产生的内部矛盾）

- §1–§16 与附录全文读取：§16 十二条结论与本文章节一致（四柱甲寅/庚午/丁未/庚戌、68.6 分偏旺、大运乙丑偏印、奇门阴遁六局天芮死门、六壬月将未、小六壬终宫大安、河洛坎为水·元堂六上）。
- §11 六壬「月将未（中气换将）」与 §5 奇门「月将未（节界 bisect）」机制不同、分别标注，无矛盾（上轮已认定）。
- 门禁产物复核：`_p_rec.json`（22:45）matched=105 / unverified=5 / **conflicts=0**，5 条 unverified 均为已知非数据错误项（六爻爻干支己卯 ×1、河洛大运卦年份 ×4）；`_p_final_report.md.l5.json`（22:45）**verdict=PASS**、违规 0、l3 覆盖 13/13。
- 快照与现行引擎一致性：抽验 `m1.py` / `l3_xiaoliuren.py` / `l3_qimen.py` / `l3_qimen_duanju.py` SHA256 前缀 4/4 与 `snap.meta.provenance` MATCH；`l4_audit.py --verify` = **113/113 一致**——冻结文件未被触碰，仅文字层修改。

## 四、Findings

**无 findings。**

- 上两轮 3 条唯一低 finding（§12 公式、§5/§15 月将路径、§15 河洛卦序引用）全部清零；
- 本轮 4 处修改经独立复算/字段核验无新引入的术理错误或过度声称；
- 全文无新内部矛盾。

### 观察（不计入 findings，不阻断放行）

1. §12「已记入 errata」未附具体文件路径（实为 `report/errata/2026-09-15-p-seg3-fix.md`）。经全库 grep 可唯一解析（该瑕疵仅此一处记录），属可解析引用；建议后续轮次顺手补路径（超轻量）。
2. §5「同落夏至～小暑段、月将同为未」仍为定局段名（24 节气）与月将分段（节界）的机制混述，可读性小瑕（上轮已列为观察，结论不受影响）；本轮未改、不构成阻断项。

## 五、Verdict：放行

- 两条低 findings 修复措辞均已落地且**经独立复算证实正确**；新增的 §15 河洛拆分引用准确；
- 冻结引擎零触碰（哈希抽验 MATCH、SHA256SUMS 113/113）；门禁产物（reconcile / l5）均为修改后时间戳且全过；
- 满足项目「无 findings 才许出口」条件，准予对外输出。

---

### 附：本轮独立核验命令要点（可复现）

```python
# 1) 公式复算
[(h, ((h+1)//2)%12+1) for h in (22, 23, 0)]   # -> [(22,12),(23,1),(0,1)]
# 2) 快照字段
snap['qimen'].keys()                            # 无 month_jiang
snap['qimen_duanju']['month_jiang']             # "未"
snap['xiaoliuren']['xlr-01']['hour_ordinal']    # 12 (亥时)
# 3) 哈希抽验 + SHA256SUMS
# sha256(m1.py|l3_xiaoliuren.py|l3_qimen.py|l3_qimen_duanju.py) vs snap.meta.provenance -> 4/4 MATCH
# python l4_audit.py --verify -> 113/113 一致
```
