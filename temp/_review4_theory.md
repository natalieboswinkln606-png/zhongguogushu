# shushu 第三方对抗审查（术理/口径方向）— 第 4 轮独立复审

- 审查员立场：第三方独立，不与修复方同源；结论不预设修复方自述正确
- 复审对象：本轮 4 项修改（C-1 换日界描述订正、C-2a 结案行、③ arbitration 订正行、④ 头计数）
- 方法：只读文件 + 实跑 `python`（含 `lunar_python` 实测、`m1.compute` 全量抽验）；**未修改任何项目文件**
- 结论：放行（无高危 findings；2 条低危文档残留 + 1 条中危列语义隐患，均非本轮数值错误）

---

## ① C-1：`docs/preregister.md` 换日界描述订正 — 核验通过

### 实测命令
```python
from lunar_python import Solar
s = Solar.fromYmdHms(2000,1,1,23,30,0)
s.getLunar().getEightChar().getDay()      # 默认日柱
s.getLunar().getDayInGanZhiExact()        # 非默认 API
s.getLunar().getDayInGanZhiExact2()
```
### 实测输出（覆盖 22:30/23:00/23:30/23:59/00:00/00:30）
| 北京时 | `getDay()`默认 | `getDayInGanZhiExact()` | `getDayInGanZhiExact2()` | `getDayInGanZhi()` |
|---|---|---|---|---|
| 22:30 | 戊午 | 戊午 | 戊午 | 戊午 |
| 23:00 | **戊午** | **己未** | 戊午 | 戊午 |
| 23:30 | **戊午** | **己未** | 戊午 | 戊午 |
| 23:59 | 戊午 | 己未 | 戊午 | 戊午 |
| 00:00 | 戊午 | 戊午 | 戊午 | 戊午 |
| 00:30 | 戊午 | 戊午 | 戊午 | 戊午 |

- **默认 `getDay()` @23:30 = 戊午 = 当日干支 = 0:00 子正**，证实新文「默认同为 0:00 子正」正确。
- **`getDayInGanZhiExact()` @23:30 = 己未 = 次日 = 23:00 子初**，证实「23:00 子初仅存在于非默认 API」。
- **`getDayInGanZhiExact2` 方法存在**（`hasattr` = True），且 = 0:00 子正。
- 源码佐证（`inspect.getsource(EightChar)`）：`def getDay(self): return self.__lunar.getDayInGanZhiExact2() if 2 == self.__sect else self.__lunar.getDayInGanZhiExact()`，且 `__init__` 设 `self.__sect = 2` → **默认路由到 Exact2**。新文「`getDay()` → `getDayInGanZhiExact2()`」逐字属实。

### 报告口径一致性
- `report/m1_compare_report.txt:5`：「`getDayInGanZhi()`: 0:00 换日（子正，与自研同口径）；`getDayInGanZhiExact()`: 23:00 换日（oracle 对拍用此，与 M0 compare.py 一致）」——与新文**实质一致**。
- 「M0 对拍所用」核验：`compare.py:day()` = `(l.getDayGanIndexExact(), l.getDayZhiIndexExact())`，确用 **Exact** 变体 → 表述属实。
- 原文（错误）已不存在；新文（preregister.md:27）与 `report/external-crosscheck-2026-09-16.md` C-1 结论吻合。

**结论：C-1 订正正确，无 findngs。**

---

## ② C-2a：`report/boundary_cases.csv` 新增 2 行结案 — 数值核验通过

### 两条新增行本值核验
```python
import m1; from datetime import datetime
m1.compute(datetime(2024,2,4,16,30), 120.0)   # stb-006
m1.compute(datetime(2024,8,7,8,12), 120.0)    # stb-016
```
- **stb-006**（立春 16:27 +3 分 = 输入 16:30）→ 自研 = **甲辰/丙寅**，与新行 `actual` 一致；新行 note 称「自研由 癸卯/乙丑 → 甲辰/丙寅」，旧行（第 31 行）actual 正是 癸卯/乙丑 ✓
- **stb-016**（立秋 08:09 +3 分 = 输入 08:12）→ 自研 = **甲辰/壬申**，与新行一致；旧行（第 41 行）actual = 甲辰/辛未 ✓

### 全量抽验（stb-* 全部 22 行 + F1-* 全部 23 行，对照「自研」列）
判据：`stb` 系列自研在 **`actual`(第 5 列)**；`F1` 系列自研在 **`expected`(第 4 列)**（含「真太阳时」标注者为自研）。stb 的「±N分」已加到基准时刻后再跑。
- **stb 全 22 行**：除**故意保留的旧行** stb-006（claim 癸卯/乙丑）与 stb-016（claim 甲辰/辛未）外，**其余 20 行全部与当前 `m1.compute` 逐字一致**（pass/arbitrated 与实测无关，值全对）。
- 两条不一致的旧行，正是本轮新增结案行所覆盖的两条；新行 `actual` 与实测一致 → **无漏改、无多改**。
- 修复影响面核查：stb-001..005、007..020 的 ±偏移足够大，北京时/真太阳时未跨节，故未受影响（值仍匹配）；**修复仅翻转 stb-006、stb-016 两条，且两条均有结案行**。
- **F1 全 23 行**：F1-004..021 `expected` 自研列与 `m1.compute` 日/时**逐条一致**；F1-022/023 经 CLI 范围闸门拒绝（1900/2100 越 M1 输入界），按报告 L44 声明走内核层：`true_solar` + `ganzhi_days` + `hour_pillar` 复算 = **甲戌/丙寅、丁未/庚戌**，与自研列一致；F1-001..003「归当日（戊午）」格式亦与内核日柱实测一致。

### 项目惯例核查
- 旧行保留（第 31、41 行仍在，未删）✓；`case_id` 复用（stb-006/016 各出现两次）✓ 与先例一致（bd-a05、bd-q01 结案行同法）；note 说明充分（含触发来源、旧→新值、留痕路径）✓。
- 列数一致性：全表 172 数据行**全部 7 列**，无错列。

**结论：C-2a 两行结案在数值层与惯例层均正确。**

### ⚠ FINDING（中危）：`expected`/`actual` 两列语义在 F1 与 stb 系列间**反转**
- **F1 系列**：`expected` = 自研（含「真太阳时」标注），`actual` = oracle。例 F1-006 `expected`=「日=戊午 时=癸亥（真太阳时…）」、`actual`=「日=己未 时=甲子」（oracle）。
- **stb 系列**：`expected` = oracle，`actual` = 自研。例 stb-001 `expected`=「年=己丑 月=乙丑」（oracle）、`actual`=「年=戊子…（真太阳时…）」（自研）。
- 即**同一张申报表的「expected/actual」在同一文件内互换含义**，读者/审计者极易把 oracle 与自研读反（本轮 stb-006 新行两列同值尚不暴露，一旦分歧即误读）。
- 该语义不一致**非本轮引入**（历史遗留），但本轮新增行继续沿用 stb 惯例，使其在表内固化。建议后续（可非阻塞）统一列语义或加列头注记「F1=自研在 expected / stb=自研在 actual」。

---

## ③ `data/arbitration_log.csv` 新增 F1-001 订正行 — 核验通过
- 新行 = 文件末行（第 126 行），`case_id=F1-001`、`category=换日界(描述订正)`、10 列完整 ✓。
- 表述与 C-1 **一致**：「lunar-python 默认日柱（`getDay()` → `getDayInGanZhiExact2()`）同为 0:00 子正…23:00 子初仅存在于其非默认 API `getDayInGanZhiExact()`（M0 对拍所用）…两侧真实差异为『真太阳时 vs 钟表时』之时标分歧」✓
- **未篡改原有行**：原 F1-001 行（第 3 行）仍在，`value_a` 仍为「oracle 23:00 子初」，未被改写 ✓（新行明示「原行保留为历史」）。`grep F1-001` 命中 2 行（原 + 订正），符合预期。
- 列数一致性：全表 124 数据行 + 表头/注释，**全部 10 列**，无错列。

**结论：③ 正确，无 findings。**

---

## ④ `report/boundary_cases.csv` 头计数「170 例」— 不属实（现为 172）

- 实测：文件总 174 行；第 1 行 = 列名；第 2 行 = 注释头（内容 `本表实载 170 例，非空`）；**数据行 = 172**（末 2 行即本轮新增 stb-006/stb-016 结案行）。
- 「剔除本轮 2 行 = 170」→ **该 170 是本轮追加 2 行之前的旧计数**，头文本未随追加同步。
- **⚠ FINDING（低危）**：头声明「实载 170 例」与当前实际 172 数据行**差 2**（= 新增行数），数字陈旧。按项目自身「差异无处藏身」标准，应为 **172**。不阻塞（不影响任何测算值），但建议同步。

---

## 其他发现（残留口径，低危）

- **`docs/sampling.md:5`** 仍写「自研 0:00 子正 vs **oracle 23:00 子初**差异单列」，未加「（非默认 API `getDayInGanZhiExact`）」限定；`report/boundary_cases.csv` 的 F1-001/002/003 行 note 亦仍写「oracle 23:00 子初 vs 自研 0:00 子正」未限定。C-1 的清扫范围只覆盖 `preregister.md` 与新增 arbitration 行，上述 2 处**同族表述未同步**（**低危**，纯文档、不改任何值；与 C-1 属同一「措辞须订正」家族）。
- **非残留**：`l3_hepan.py:95`、`report/l3_hepan_report.txt:70`、`l2_compare_report.txt:16` 中的「易安居 23:00 子初」指的是**另一个 oracle（易安居）**，与 lunar-python 无关，不算 C-1 残留。
- 正向核查：`m1_compare.py`（第 5/143/192 行）与新文表述一致，未见矛盾。

---

## findings 汇总

| 级别 | 项 | 说明 | 是否阻塞 |
|---|---|---|---|
| 高 | 无 | — | — |
| 中 | ② 列语义反转 | `expected`/`actual` 在 F1 与 stb 系列间互换含义（自研 vs oracle），历史遗留、本轮固化 | 否（建议后续修） |
| 低 | ④ 头计数陈旧 | 「实载 170 例」应为 172（差 2 = 新增行） | 否 |
| 低 | 残留未限定表述 | `docs/sampling.md:5` 与 F1-001..003 note 仍写「oracle 23:00 子初」未加「非默认 API」限定 | 否 |

---

## verdict：**放行**

四项修改经独立实跑核验**全部成立**：C-1 的 lunar-python 换日界事实（默认子正 / 非默认 23:00 子初 / `getDayInGanZhiExact2` 存在且默认路由）逐条证实；C-2a 两条结案行的自研值（甲辰/丙寅、甲辰/壬申）与 `m1.compute` 一致，且 stb/F1 全 45 行抽验无漏改；③ 订正行表述与 C-1 一致且未篡改原行。无高危 findings；1 条中危（列语义，历史遗留）+ 2 条低危（计数陈旧、残留表述）均为文档层，不影响任何盘面/数值，建议但不阻塞后续修订。
