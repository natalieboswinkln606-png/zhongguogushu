# P 女命报告终审轮 · 数据抄写维度轻量终审（第三方对抗审查）

- 审查员立场：独立核验，不采信修复方自述；只读引擎与报告，**未修改任何引擎代码/报告文件**。本轮仅新增只读核验产物：`temp/_review3_verify.py`、`_review3_repro.md`、`_review3_rec.json`、`_review3_l5.json`、`_review3_inv.json`、`_review3_hash.py`
- 审查对象：`temp/_p_final_report.md`（raw sha256 前 16 位 `582e93fd41e6e4a2`；484 行 / 23160 字符 / CRLF；与 `_p_report_draft.md` 逐字节一致）
- 基线：review2 记录旧定稿 sha256 前 16 位 `845bccab54fb9bb6`（旧字节未在盘上留存；替代实证见 §四方法注记）
- 数据底座：`temp/_probe_snap.json`（sha256 前 16 位 `0d7ad0444cb9ea81`；meta.generated_at = 2026-09-15T22:32:18，与 review2 基线一致——快照未重生成，本轮为纯文字层修复，符合 review2 建议）
- 环境：`PYTHONIOENCODING=utf-8 python`，cwd=D:\shushu

## 一、三处申报修复逐条核验（引用承载验证）

| # | 上轮 finding | 定稿现状（摘录） | 承载核验 | 判定 |
|---|---|---|---|---|
| 1 | 低-1 §5/§15「月将同为未」引 `snap.qimen` 路径悬空 | §5 L132「……月将同为未（**月将数据底座：snap.qimen_duanju.month_jiang**），两口径无数值差异，提请 v2 重裁（**定局数据底座：snap.qimen.dingju**）」；§15 L257「（**定局数据底座：snap.qimen.dingju；月将数据底座：snap.qimen_duanju.month_jiang**），提请 v2 重裁」 | 实测 `snap.qimen_duanju.month_jiang == "未"` ✓；`snap.qimen.dingju` = {term:夏至, yuan:下元, dun:阴遁, ju:6} ✓；两条新路径均可解析、语义各自归属（月将↔qimen_duanju，定局↔qimen.dingju） | 达成 |
| 2 | 低-2 §15「先天卦序」引 hlyl01，实载于 hlyl02.source | §15 L258「河洛理数取数采用网传太玄数起卦派（干支同数，**数据底座：snap.heluolishu.hlyl01**）与先天卦序（**数据底座：snap.heluolishu.hlyl02**）；古籍原书取数（纳甲洛书数+河图支双数）及河图生成数派为异文，模块 alt 已申报、报告按主口径」 | hlyl01.source 原文：「**网传太玄数起卦派：太玄数干支同数** 甲己子午9 乙庚丑未8 丙辛寅申7 丁壬卯酉6 戊癸辰戌5 巳亥4（古籍原书此数仅用于五行纳音，非起卦取数）」→ 与报告「网传太玄数起卦派（干支同数）」逐义一致 ✓；hlyl02.source 原文：「天数÷8 余数=上卦、地数÷8 余数=下卦（**先天八卦序 乾1兑2离3震4巽5坎6艮7坤8**，余 0 取坤）」→ 与报告「先天卦序」语义一致 ✓；续句与 hlyl01.alt（河图生成数派、古籍原书取数=纳甲洛书数+河图支双数）逐义一致 ✓ | 达成 |
| 3 | §12 公式注转录 docstring 缺实现式 +1 | §12 L224「时支序=**((h+1)//2)%12+1**，子=1…亥=12；……**模块 docstring 转录公式省略末位 +1 系文档瑕疵、实现正确，已记入 errata**」 | 独立核验源码：`l3_xiaoliuren.py` L19 docstring / L110 函数注释均写 `(h+1)//2%12`（确缺末位 +1）；L111 实现 `return (dt.hour + 1) // 2 % 12 + 1`（实为 +1）→ 报告「文档瑕疵、实现正确」**属实**；字面代入新式：h=0→1 子、h=12→7 午、h=22→**12 亥**、h=23→1（归次日），与 `snap.xiaoliuren.xlr-03` steps「时支序12→大安」一致 ✓；「已记入 errata」→ `report/errata/2026-09-15-p-seg3-fix.md` §六 实载（「docstring（约 L18）与函数注释（约 L110）……实现 shichen_ordinal……以实现为准；留待 v2 解冻窗口修正文档」），且报告正文旧式 `(h+1)//2%12`（缺 +1 断言式）残留 0 处 ✓ | 达成 |

## 二、引用承载全量核验

- 程序化抽取定稿全部 `snap.<路径>` 引用：**69 条唯一路径，除 `snap.json`（`_probe_snap.json` 文件名截取伪阳性，与 review2 判定一致）外 100% 可解析，零真实悬空引用**。
- 三处修复点新路径实测全部落盘：`snap.qimen_duanju.month_jiang`、`snap.qimen.dingju`、`snap.heluolishu.hlyl01`、`snap.heluolishu.hlyl02` ✓。

## 三、值抽查（30 项程序化比对，全部 PASS）

wangshuai de_ling（午/丁/旺/100/ws-01）与 de_di/de_shi/zonghe（68.6 偏旺 ws-04，权重 0.4/0.35/0.25）；紫微 h22 命宫壬申/身宫辰/金四局；大限 4 岁/逆行/12 限；2026 流年丙午/夫妻/庚午/四化天同禄·天机权·文昌科·廉贞忌（与快照结构逐项比对）；奇门定局夏至下元阴遁 6 局、值符天芮/甲辰/壬/落巽四宫、值使死门 zhishi_palace=5、eight_doors["2"]=死门；qimen_duanju.month_jiang=未；小六壬月小吉/日留连/终大安（含 steps 原文）、xlr-02 大安=吉、notes 23 点归次日口径；黄历 1974-07-05/丁未/五月十六、建除除日吉、勾陈黑道、建除配黄道、神煞命中仅红艳 hl-03-07；八字神煞 7 命中（亡神/国印/将星/禄神/天喜/华盖/天罗，与 groups 项名全等）；称骨 3 两 1 钱；大运起运 9 岁 10 月 1 天 18 时 / 交运 1984-05-07 16:13 / 当前步乙丑 2024-2033 偏印；六壬月将未、元首课三传卯(父母)/亥(官鬼)/未(子孙)；五运六气甲寅土运太过、司天少阳相火、在泉厥阴风木、sui_yun.alt 含大寒/立春两派；梅花本卦地火明夷、变卦水火既济、nums 年支序 3/时支序 11 与正文一致；河洛 hlyl02 命卦坎为水、hlyl03 元堂 pos=6、ming_gua 坎为水；meta.generated_at=2026-09-15T22:32:18 与报告头部一致。**零错抄、零双源不一致。**

## 四、生成链防篡改复现与方法注记

- 用 `temp/_p_make_draft.py` 同一管道（`_p_report_body.md` + `_p_harvest.txt` 标注版）在内存重组并按原样文本模式写出（`temp/_review3_repro.md`），与定稿**原始字节全等**（两者 raw sha256 前 16 位均为 `582e93fd41e6e4a2`）→ 定稿可由文档化管道完整复现，附录搬运区无人工注入痕迹。
- 方法注记（诚实披露）：旧定稿字节（`845bccab…`）未留存、无法新旧直接 diff。替代实证：① 上述管道字节级复现；② reconcile matched 105 项与 review2 基线**逐项全等**（token 清单无增删）；③ l5 违规 0；④ 69 条引用全解析——四处证据共同表明本轮仅引用/标注文字改动、未触碰任何数据。

## 五、门禁独立重跑（不采信修复方产物）

| 项目 | 申报 | 独立实测 | 结果 |
|---|---|---|---|
| reconcile（对定稿+快照重跑） | 105/5/0 | **matched=105 / unverified=5 / conflicts=0**（exit 0）；matched 与 unverified 五项（己卯 + 1979/1980/1988/1989，均为此前已定位的检索覆盖局限项）与申报 `_p_rec.json` **逐项全等** | ✓ |
| l5_defense_check | PASS | **verdict PASS，违规 0，13/13 模块**（rule1..9 全 0，exit 0） | ✓ |
| check_invariants | 5/5 | **aud-inv-01..05 全 PASS**（exit 0） | ✓ |
| 头部哈希声明 | m1 `fe75470af92b982` / l3_ziwei `e5f9889c643aebf` / l3_qimen `33d93982c511492`、22:32:18、17 文件 | 三前缀与 `meta.provenance` 及**磁盘实测全哈希前 15 位全等**；provenance 恰 17 文件；时间戳一致 | ✓ |

## Findings

**无 findings。** 三处申报修复经独立核验全部达成；零数值错抄、零悬空引用、零新增未证实 token；l5/reconcile/invariants 门禁全过。说明性观察（不构成 finding）：§15 L258「先天卦序」为 source 原文「先天八卦序」的缩短表述，语义一致；§12 唯一遗留的旧式写法出现在「省略末位 +1」的说明性文字中，非公式主张。

## Verdict

**放行。** 上轮唯一未清零的 3 条低 finding 已全部修复且经独立验证达成，未发现任何新问题，满足项目「无 findings 才许出口」条件。
