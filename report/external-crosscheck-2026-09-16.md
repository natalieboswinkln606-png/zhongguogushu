# shushu 外部独立交叉验证报告

- 日期：2026-09-16
- 验证对象：`D:\shushu`（v1.0 冻结 + v1.1 增补；L0 数据 → L1 `m1.py` → L2 `rules.py` → L3 术种 → L4/L5 审计门禁）
- 验证方法：外部开源同类项目代码级/文档级交叉印证
- 验证者立场：外部独立代理，不与 shushu 团队同源；结论不预设 shushu 正确

---

## 一、检索方法与覆盖范围

### 1.1 检索手段

- 工具：`WebSearch`、`WebFetch`（含 GitHub raw 源码直读）、`gh api`（取 star 数/语言/许可证/最近推送）。
- 语种：中英双语关键词并检。
- 关键词族：
  - 八字：`八字 排盘 python github`、`bazi calculator open source`
  - 紫微：`紫微斗数 python github`、`ziwei doushu library`、`iztro 安星 五行局`
  - 奇门/六壬：`奇门遁甲 python github 拆补 置闰`、`qimen dunjia`、`大六壬 python`
  - 历法/节气：`农历 节气 算法 开源`、`sxtwl 寿星天文历`、`python solar terms VSOP87`
  - 六爻：`六爻 纳甲 python github`

### 1.2 覆盖范围

- 共定位并采信 **12 个开源仓库**（详见第二节），覆盖：历法/节气基座、八字四柱、紫微斗数、奇门遁甲、大六壬、太乙、六爻。
- 深度验证（读过源码）的仓库：`6tail/lunar-python`（`EightChar.py`、`Lunar.py`、`ShouXingUtil.py`）、`kentang2017/kinqimen`（`kinqimen.py`）、`morongs/iztro`（`src/astro/palace.ts`、`src/star/location.ts`）、`skydancep/sxtwl`、`ebraminio/astronomy`。
- 仅文档级验证：`whitefssw/bazi-calculator`、`hqzxsc/bazi`、`xiongdun8/liuyao`、`kentang2017/kinliuren`、`kentang2017/kintaiyi`、`x-haose/x-iztro`。
- 同时核对了 shushu 自身实现证据：`m1.py`（真太阳时/EOT/判界）、`l3_ziwei.py`（五行局/身宫/四化）、`l3_qimen.py`（定局/中宫寄宫）、以及 `report/m1_compare_report.txt`、`data/arbitration_log.csv`、`report/boundary_cases.csv`。

### 1.3 采样偏差声明（重要）

- 选择偏向"有 star、有文档、近期活跃"的仓库，**不等于**覆盖了术数开源生态的全部主流实现；大量高价值实现存在于私有软件（如"元亨利贞""问真"等闭源 App）与 Academia Sinica 两千年中西历转换等历表项目中，本次未覆盖。
- 奇门/六壬/紫微的"权威口径"本身在术数界**无统一标准**，凡涉及流派差异，本报告只判定"是否与某一主流做法一致"，不判定"谁绝对正确"。
- 本次**未能运行**任何外部项目做数值对拍（仅静态代码/文档比对），故所有"一致/不一致"判断均基于算法口径的文字/源码描述，非实测数值。

---

## 二、仓库清单表

> star 数、语言、许可证、最近推送时间经 `gh api` 于 2026-09-16 实时读取。

| # | 仓库 | URL | ★ | 语言 | 许可 | 覆盖术种 | 算法口径要点（挖到的最深处） |
|---|---|---|---|---|---|---|---|
| 1 | 6tail/lunar-python | https://github.com/6tail/lunar-python | 655 | Python | MIT | 历法/节气/八字/十神/纳音/黄历/方位/建除 | 节气=**寿星天文历混合算法**（1645 前后分段：古代用均值表 `__QI_KB`+插值、1645+ 用低精度公式 `qiLow`+字符串修正表 `__QB`、范围外用 `qiHigh`/VSOP 级数）；八字年柱用 `getYearInGanZhiExact`（立春族）、月柱 `getMonthInGanZhiExact`（节气）、日柱 `getDayInGanZhiExact2`（默认，**0:00 子正**）；`Yun` 两种流派：sect1=**3天1年/1天4月/1时辰10天**、sect2=按分钟；**无真太阳时** |
| 2 | kentang2017/kinqimen | https://github.com/kentang2017/kinqimen | 146 | Python | 无 | 时家奇门/刻家奇门/金函玉镜日家奇门 | **转盘法**（星门神按八宫旋转，非飞宫步进）；**中宫寄坤二宫**（源码多处 `earth.get("坤")`/`new_list(rotate,"坤")`，**无寄艮代码**）；`pan(1)`=**拆补**、`pan(2)`=**置闰**两法并存，定局后盘体逻辑共用；节气依赖 `sxtwl`；**无真太阳时** |
| 3 | kentang2017/kinliuren | https://github.com/kentang2017/kinliuren | 105 | Python | MIT | 大六壬（三传/四课/天地盘/神煞） | 入口 `Liuren(节气, 农历月, 日干支, 时干支)`；格局示例"贼尅/重审"；**月将/日干寄宫/九宗门广度未在文档展开**；自述"不包含年月日时干支演化" |
| 4 | kentang2017/kintaiyi | https://github.com/kentang2017/kintaiyi | 58 | Python | MIT | 太乙神数（年月日时→分 全谱 + 命法） | shushu 未覆盖太乙，仅列作三式生态参照 |
| 5 | x-haose/x-iztro | https://github.com/x-haose/x-iztro | 4 | Rust（含 Py/Go 绑定） | MIT | 紫微斗数（12宫/约100星/六层运限/64格局） | iztro v2.5.8/v2.6.1 的 **field-for-field 移植**；声称 716,314 golden cases 零差异；`algorithm` 开关 `default`/`zhongzhou`（**中州派安星**可选）；亮度 −3…+3；另有八字反查 |
| 6 | morongs/iztro（JS 镜像） | https://github.com/morongs/iztro | 0 | JS | MIT | 紫微斗数 | **五行局=干支数法**（干对号 1–5 + 支组号 1–3，和>5 减 5）；**命宫=月支−时支、身宫=月支+时支**；四化/亮度表可自定义；安星受中州派选项影响 |
| 7 | skydancep/sxtwl | https://github.com/skydancep/sxtwl | 13 | C++（SWIG 多语言） | 无 | 农历/节气/干支（**纯天文历**） | **寿星天文历 C++ 实现**（许剑伟原始算法），"免除附带表数据"；BC722 后与实历相符；自述**未支持真太阳时** |
| 8 | ebraminio/astronomy | https://github.com/ebraminio/astronomy | 2 | C/多语言 | MIT | 星历（日月行星/朔望/升落/节气相关） | **VSOP87 + NOVAS C 3.1**，±1 角分；可反解"某黄经对应的时刻"（即节气求根工具） |
| 9 | shangdawei/lunar-calendar | https://github.com/shangdawei/lunar-calendar | 2 | Python | BSD-2 | 农历/节气（iCal） | VSOP87 天文法算节气（`aa.py`/`vsop.c`） |
| 10 | whitefssw/bazi-calculator | https://github.com/whitefssw/bazi-calculator | 0 | 未标注 | 无 | 八字+五行/格局/用神/神煞/大运/流年 | 自述"**支持真太阳时修正**（lunarcalendar 库）"；大运"**起运年龄校正**"、阳男阴女顺/阴男阳女逆；无边界口径说明 |
| 11 | hqzxsc/bazi | https://github.com/hqzxsc/bazi | 0 | Python | 无 | 八字/十神/旺衰/格局/神煞/大运/生肖合婚 | 依赖 `lunar_python`；有"上运时间"/大运序列；**真太阳时未提及**；无测试 |
| 12 | xiongdun8/liuyao | https://github.com/xiongdun8/liuyao | 13 | Python | MIT | 六爻（本卦/变卦/纳甲/六神/世应/旬空） | 输入爻码 1–4；含**旺衰分析**（季节旺相休囚死、长生墓绝、冲合）——**超出 shushu"六爻止于排卦"的范围**；卦辞/爻辞存于 `data.py` |

---

## 三、逐口径对比表

> 说明：判定列取 **①佐证（与主流一致）／②流派分歧（各有依据）／③批判-己方错／④批判-对方错／⑤未决**。
> shushu 口径证据来自 `preregister.md`、`README.md`、`m1.py`、`l3_*.py` 源码实测。

### 3.1 历法与四柱内核（L0/L1）

| 口径项 | shushu 口径（含源码证据） | 外部项目口径（含证据） | 判定 |
|---|---|---|---|
| **真太阳时公式** | 北京时 + (经度−120)×4 分 + EOT（`m1.py:21`）；EOT 用 NOAA 简化式 `9.87·sin2B−7.53·cosB−1.5·sinB, B=2π/365·(N−81)`（`m1.py:14-15`） | `lunar-python` 与 `sxtwl` **均无真太阳时**（sxtwl 明确列为"未支持"）；仅 `whitefssw` 声称支持但未给公式 | **①佐证**（shushu 比主流开源库做得更完整）；EOT 用 NOAA 简化式为通行做法 |
| **EOT 来源与精度** | NOAA 公式；自述"无锚点互校前不生成冗余 EOT 表"（preregister L59） | 开源库普遍**不做** EOT；es 无外部 EOT 实现可比 | **⑤未决**（无第二实现可对拍；shushu 亦自认待《中国天文年历》互校） |
| **年柱判界** | **立春**（`m1.py:67` `year_pillar`），且判界时域=**北京时域**（`m1.py:95`；2026-09-15 裁决） | `lunar-python` 用 `getYearInGanZhiExact`（立春族）；术数界通行=立春 | **①佐证**（立春换年=主流） |
| **月柱判界** | **12 节**（节气时刻过宫），不用农历月（`m1.py` `month_pillar`） | `lunar-python` `getMonthInGanZhiExact`=节气时刻过宫；八字无闰月概念=通行 | **①佐证** |
| **判界时域** | 年/月柱=**北京时域(UTC+8)**；真太阳时仅用于日柱/时柱（preregister L28；2026-09-15 裁决统一） | 开源库用钟表时（北京时间）判界，与 shushu 修复后一致 | **①佐证**（修复后与主流一致；修复前的单边真太阳时口径确为隐患，见 `report/errata/2026-09-15-qiyun-fix.md`） |
| **换日界（子初 vs 子正）** | **真太阳时子正（0:00）**（preregister L27；`m1.py` 换日界=真太阳时子正） | `lunar-python`：`getDayInGanZhi()`（默认）=**0:00 子正**、`getDayInGanZhiExact()`（非默认）=23:00 子初；`EightChar.getDay()` 默认 `sect=2` → `getDayInGanZhiExact2()`=**0:00 子正** | **①佐证（子正轴）+ ③批判（描述错误）**：shushu 的"子正"与 lunar-python **默认**同族；但 preregister 把 oracle 说成"默认 23:00 子初"**不准确**（详见四-2） |
| **早子时/晚子时** | 晚子时（23:00–23:59）**算当日**（子正换日）；日柱时柱同轨真太阳时 | `lunar-python` `Exact2`=晚子时算当日、`Exact`=算次日；shushu 选择与 `Exact2`（默认）一致 | **①佐证** |
| **起运间隔** | 出生到顺/逆最近节的**绝对时长**（两侧同域北京时相减），折算 **4320 分/岁、360 分/月、12 分/天、余×2=时**（preregister L29；`l3_bazi_daliu.py` `qiyun()`） | `lunar-python` `Yun` sect1 定义：**"3天1年，1天4个月，1时辰10天"** → 换算即 4320 分/岁、360 分/月、12 分/天，**逐项完全吻合** | **①佐证（强）**：shushu 与 lunar-python sect1 数值口径完全一致（且 shushu 对拍 25/25 岁/月/天全同） |
| **节气表来源** | **预置 CSV**（`data/solar_terms.csv`，1948–2101），运行期只读表、**拒绝回退 lunar-python 计算值**（preregister L53） | `lunar-python`=寿星天文历**混合**（古代均值表+插值、现代低精度公式+修正表）；`sxtwl`=**纯天文算法**"免除附表数据"；`astronomy`=VSOP87/NOVAS；`lunar-calendar`=VSOP87 | **②流派分歧（各有依据）**：表化 vs 天文算法是两条合法路线；shushu 用官方源(HKO/紫台)锚定+第三方对拍，方法论上更利于"可溯源、可仲裁"，但牺牲了超范围外推能力 |
| **月将宫界** | 黄经 30° 整数倍过宫 ≡ 中气（preregister L31） | `kinliuren` **未暴露**月将/黄经规则 | **⑤未决**（无外部对照） |
| **干支编号基准** | 甲=0…癸=9、子=0…亥=11、甲子=0（preregister L32） | 主流实现内部不一致（有的甲=1）；属实现细节，非术理口径 | **①佐证**（不影响结果，仅内部约定） |

### 3.2 紫微斗数（L3）

| 口径项 | shushu 口径 | 外部项目口径 | 判定 |
|---|---|---|---|
| **命宫** | 寅起正月顺数生月、**逆数生时**（`l3_ziwei.py:99`） | `iztro`：`soulIndex = fixIndex(monthIndex − branchIndexOfTime)`（`src/astro/palace.ts`）——**同一公式** | **①佐证** |
| **身宫** | 顺数生月、**顺数生时**（`l3_ziwei.py:99`） | `iztro`：`bodyIndex = fixIndex(monthIndex + branchIndexOfTime)`——**同一公式** | **①佐证** |
| **五行局定法** | 命宫宫干（五虎遁：寅起丙）＋命宫支 → **纳音** → 局（`l3_ziwei.py:105`，zw-03） | `iztro` `getFiveElementsClass`：干对号(甲乙1…壬癸5)＋支组号(子丑午未1/寅卯申酉2/辰巳戌亥3)，和>5 减 5 → 木三/金四/水二/火六/土五 | **①佐证（等价）**：iztro 该公式即**纳音局数表**的代数写法。实测校验：甲子→金四局✓（海中金）、丙寅→火六局✓（炉中火），与纳音法同结果 |
| **生年四化表** | `SIHUA` 表，**易安居图例对拍一致**（`l3_ziwei.py:41`，zw-07） | `iztro` 内建表 + `zhongzhou` 中州派可选；四化表存在**多流派异文** | **②流派分歧**：四化表明显存在流派版本差异（通行表/中州派/全书派），shushu 取易安居通行表并已声明；属合法选择，但对拍 oracle 单一 |
| **紫微年干取年** | 年干项（四化/魁钺/禄存）按**民俗农历年（正月初一换年）**，与八字的立春换年**并存双标准**（`l3_ziwei.py:96,155`） | `iztro` 由公历推农历年取干（同正月初一系） | **②流派分歧**：紫微"年"取正月初一 vs 立春是已知两派；shushu 明确申报了与八字的双标准，逻辑自洽（`l3_ziwei.py:155` 外显声明） |
| **安紫微（局数日进）** | 局数日进一宫（`l3_ziwei.py:4`，zw-04，易安居口径） | `iztro` 系列同法（紫微定位为通行"局数起法"） | **①佐证** |
| **闰月起宫** | 闰月按**次月顺延起宫**（`l3_ziwei.py:4`，oracle 实测） | `iztro` 有 `fixLeap` 开关处理闰月 | **②流派分歧**：闰月起宫存在"归本月/归次月/月中分算"多派，shushu 取其一并声明 |

### 3.3 奇门遁甲（L3）

| 口径项 | shushu 口径 | 外部项目口径 | 判定 |
|---|---|---|---|
| **盘法（转/飞）** | **转盘法**（`l3_qimen.py:2,9`；星随干转/门随时转/神随符转） | `kinqimen`=**转盘**（`pan_sky` 按八宫序旋转、`pan_door`/`pan_god` 亦旋转，无飞宫步进逻辑） | **①佐证（强）** |
| **中宫寄宫** | **寄坤二宫**（`l3_qimen.py:104,161`；时干落中宫值符寄坤、天禽寄芮） | `kinqimen`=**寄坤二宫**（源码 `earth.get("坤")`、`new_list(rotate,"坤")`，忠实无寄艮分支）；文献：转盘奇门"**问事局用寄坤宫法**"为最常见，另有寄二八/寄四维/寄八节共 4 法 | **①佐证（强）**：shushu 与 kinqimen 及主流文献一致 |
| **定局法（拆补/置闰）** | **拆补法**：真太阳时所属节气时刻后首个甲己符头日定元，残日取符头元前一元（`l3_qimen.py:11,65`） | `kinqimen` **两法并存**：`pan(1)`=拆补、`pan(2)`=置闰；`year_yuen` 用 60 甲子循环定元 | **①佐证（方向）+ ⑤未决（细节）**：shushu 用拆补=kinqimen 支持的合法一法；但"符头=甲己日、残日取前一元"的**细节算法**需读 kinqimen `config.py` 才能确认是否逐字等价（本次未取到） |
| **节气驱动** | solar_terms.csv 权威，24 节（含中气）皆定局（`l3_qimen.py:55`） | `kinqimen` 依赖 `sxtwl` 算节气 | **②实现分歧**（同 3.1 节气来源项） |

### 3.4 六壬 / 六爻（L3）

| 口径项 | shushu 口径 | 外部项目口径 | 判定 |
|---|---|---|---|
| **九宗门完整性** | 贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/返吟**九宗门齐全**（README；`l3_liuren.py`） | `kinliuren` 文档仅示例"贼尅/重审"，**未声明九宗门覆盖广度** | **⑤未决**（无法确认 kinliuren 是否实现九宗门；但 shushu 的宗门列表=《六壬大全》卷一通行体系，属经典口径） |
| **六壬起课输入** | 日干寄宫/月将/天地盘由引擎全算（含年月日时干支演化） | `kinliuren` 输入=节气+农历月+日干支+时干支（**干支演化由外部提供**） | **②范围分歧**：shushu 端到端自算，kinliuren 只做起课，非对错 |
| **六爻范围** | **止于排卦**：纳甲/六神/世应；**不做旺衰/神煞**（preregister I-7、L110） | `xiongdun8/liuyao` **含旺衰分析**（旺相休囚死、长生墓绝、冲合） | **②范围分歧**：shushu 明确声明"旺衰判定不在本库范围"（依据 I-7 对《增删卜易》只对拍规则层），是有据的自我设限；对方做了 shushu 故意不做的层 |
| **六爻纳甲/八宫** | najia.csv 纳甲、bagong.csv 八宫（京房六亲）（README） | `xiongdun8/liuyao` `data.py` 存卦辞，输出含六亲/六神/世应/旬空 | **①佐证**（京房纳甲六亲为通行体系；细节未逐值比对） |

---

## 四、结论

### 4.1 佐证清单（shushu 口径与外部主流一致）

| 编号 | 口径项 | 佐证来源 | 强度 |
|---|---|---|---|
| Z-1 | 起运 3 天=1 岁（4320 分/岁、360 分/月、12 分/天） | `lunar-python` `Yun` sect1 定义逐项吻合 | **强**（数值级，且 shushu 已对拍 25/25） |
| Z-2 | 年柱=立春换年 | lunar-python + 术数通行 | 强 |
| Z-3 | 月柱=节气（12 节）换月，八字无闰月 | lunar-python `getMonthInGanZhiExact` | 强 |
| Z-4 | 换日界=子正（0:00），晚子时算当日 | `lunar-python` **默认** `getDayInGanZhi()`/`Exact2`/`EightChar sect=2` 均为 0:00 | 强（但描述有误，见 C-1） |
| Z-5 | 判界时域统一为北京时域 | 开源库普遍用钟表时判界 | 强（2026-09-15 修复后） |
| Z-6 | 奇门=转盘法 | `kinqimen` 源码=转盘 | 强 |
| Z-7 | 奇门中宫=寄坤二宫 | `kinqimen` 源码=寄坤；文献"问事局寄坤"最常见 | 强 |
| Z-8 | 奇门定局=拆补（之一） | `kinqimen` `pan(1)`=拆补 | 中 |
| Z-9 | 紫微命宫=逆数生时、身宫=顺数生时 | `iztro` `getSoulAndBody` 同公式 | 强 |
| Z-10 | 紫微五行局=命宫干支纳音 | `iztro` `getFiveElementsClass` 该公式即纳音局数代数式（实测两点校验通过） | 强 |
| Z-11 | 真太阳时=经度差 + EOT | 概念为通行天文学做法（开源库多不做，shushu 更完整） | 中 |
| Z-12 | 六爻=京房纳甲/八宫/六亲体系 | `xiongdun8/liuyao` 同体系 | 中（未逐值比） |

### 4.2 批判清单（含判定与依据）

> 严格执行"禁止包庇"：凡 shushu 与主流/权威不同且站不住脚，直说。

**C-1【判定 ③批判-己方描述错误（中危·文档级）】——preregister 对 oracle 换日界默认值的描述不准确，且与 shushu 自身报告自相矛盾。**

- 事实：`preregister.md:27` 写"换日界 = 真太阳时子正（0:00 子正换日；**lunar-python 默认 23:00 子初换日**，两者差异归'算法分歧'类单列）"。
- 源码核验（本次 `gh`/raw 直读）：
  - `lunar_python/EightChar.py`：`__init__` 设 `self.__sect = 2`；`getDay()` 实现为 `return self.__lunar.getDayInGanZhiExact2() if 2 == self.__sect else self.__lunar.getDayInGanZhiExact()` → **默认走 `Exact2`**。
  - `lunar_python/Lunar.py` `__computeDay`：基准日索引取自当日**正午**，**仅** `23:00–23:59` 时对 `Exact` 变体 `+1`；`Exact2` **不**移。故 `Exact2`=**0:00 子正**、`Exact`=23:00 子初。
  - 结论：**lunar-python 的默认日柱换日=0:00 子正，与 shushu 同口径**；23:00 子初仅存在于**非默认**的 `getDayInGanZhiExact()`。
- shushu 自身也已知情：`report/m1_compare_report.txt:5` 明确写"`getDayInGanZhi()`: 0:00 换日（子正，**与自研同口径**）；`getDayInGanZhiExact()`: 23:00 换日（oracle 对拍用此）"。
- 判定：**preregister 的"默认 23:00"表述错误**——shushu 拿**非默认** API 的 23:00 行为当成 lunar-python 的"默认"，从而把"子初/子正"定性为与 oracle 的"算法分歧"。真实情况是：**换日界的子初/子正轴上二者默认一致**；真正的差异是 shushu 用**真太阳时**、lunar-python 用**钟表时**（这一点 `arbitration_log.csv` F1-006/007 等条目其实写对了："真太阳时口径差异：EOT 修正致真太阳时跨子正"）。
- 修法建议：① 订正 `preregister.md:27`，区分"默认 `getDayInGanZhi`(子正) vs 对拍所用非默认 `getDayInGanZhiExact`(子初)"；② `arbitration_log.csv` 中 F1-001/002/003 的 reason 写"oracle 23:00 子初"处宜补注"（非默认 API `getDayInGanZhiExact`）"，避免读者误以为 oracle 默认如此。
- 影响面：口径本身（真太阳时子正）**站得住**，且比 oracle 更精细；此项仅为**描述/归因错误**，不产生错误盘面。但按 shushu 自己的"差异无处藏身"标准，这条措辞必须订正。

**C-2【判定 ③批判-己方文档陈旧（低危·待自查）】——boundary_cases 旧条目注释疑与 2026-09-15 判界时域裁决冲突。**

- 事实：`report/boundary_cases.csv` 中 `stb-001..stb-005`（年柱/月柱）注释仍写"**自研按真太阳时时刻 ≥ 立春时刻**（EOT±16 分内）……年柱月柱按契约用真太阳时判界"。
- 冲突点：`README.md`（2026-09-15 修复段①）与 `preregister.md:28` 已裁决 **判界时域=北京时域**，真太阳时仅用于日/时柱。旧注释的"真太阳时判界"语义已被推翻。
- 判定：**③己方文档陈旧**（低置信度，可能已被 errata 覆盖但行注释未同步）。建议 shushu 自查 `stb-001..005` 的 expected/actual 是否随修复而失配，必要时按"不删旧行、新增结案行"的先例补注。
- 注：`report/boundary_cases.csv:2` 现为**空表头**（仅列名行），而 README/CLAUDE.md 声称"边界用例 170 条"。两地计数不一致，属文件状态问题，一并提交 shushu 自查。

**C-3【判定 ②流派分歧（非错误）】——下列 shushu 选择与部分实现不同，但均有依据，**不判错**：**

- 节气表用预置 CSV 而非天文算法（与 sxtwl/astronomy 路线不同）——属可复现性优先的合理取舍。
- 紫微生年四化/闰月起宫/年干取年表——存在明确流派异文，shushu 已声明并挂 oracle。
- 六爻不做旺衰——shushu 明确的自设范围（I-7）。

**C-4【判定 ④批判-对方（提示性，非 shushu 问题）】：**

- 本次**未发现**任何外部仓库在可核验口径上"明确错误"到值得单独立案的程度。少数项目（`whitefssw/bazi-calculator` 0★ 无许可、`hqzxsc/bazi` 无测试、`iztro` 阅读器存在版本引用自相矛盾：tagline 称 v2.5.8、accuracy 段称 v2.6.1）存在**工程规范瑕疵**，但均非术理错误，仅作提示。

### 4.3 未决清单（本次未能判定）

| 编号 | 未决项 | 原因 |
|---|---|---|
| U-1 | **奇门拆补定元的细节等价性** | shushu"节气后首个甲己符头、残日取前一元" vs `kinqimen` `config.py` 的真元算法（本次未取到该文件）；两法同名"拆补"未必逐字等价 |
| U-2 | **六壬月将/日干寄宫/九宗门** | `kinliuren` 文档未展开这些规则，无法对拍 |
| U-3 | **EOT 数值正确性** | 无外部开源 EOT 实现可比；shushu 自认待《中国天文年历》锚点 |
| U-4 | **紫微四化表逐星比对** | 仅确认"取表+已声明流派"，未逐星对照 iztro/中州派表 |
| U-5 | **六爻纳甲/八宫逐值比对** | 仅确认同体系，未逐支逐卦比 |
| U-6 | **节气表数值精度** | 本次为**静态比对**，未运行 sxtwl/astronomy 与 `solar_terms.csv` 实测对拍；shushu 已有 skyfield DE440s 对拍（≤2 分）为其自身证据，非本次独立复现 |

---

## 五、本次验证的局限

1. **未做数值实跑**：所有判定基于源码/文档的**口径层**比对，未安装运行任何外部项目做逐例数值对拍。若需"实跑级"佐证，应补：用 `sxtwl`/`astronomy` 独立重算 shushu 对拍语料的节气/四柱/起运，与 `data/*.csv` 逐例比。
2. **采样偏差**：术数开源生态**高度分散、质量参差**，高 star 者集中于"历法/黄历"（lunar-python 655★），真正的奇门/六壬/紫微专业实现多在**闭源商业软件**（元亨利贞、问真八字、各派排盘 App）与散落博客，本次未及。故"主流做法"的判断置信度**低于**一般软件工程领域。
3. **"权威"不可得**：术数多数术种**无统一权威口径**（四化表、闰月起宫、中宫寄宫、拆补/置闰之争古已有之），本报告只能判定"是否与某一主流做法一致"，**不能**判定"该法绝对正确"。凡标注"流派分歧"处，shushu 的选择只要自洽+申报，即视为通过。
4. **oracle 单一性风险（对 shushu 的独立观察）**：shushu 紫微/奇门/合盘的 oracle 高度依赖**易安居**单一时源（README 多处"易安居实测校准"）。本次外部验证确认 shushu 的奇门/紫微口径与 kinqimen/iztro **独立实现**一致（Z-6/Z-7/Z-9/Z-10），这在一定程度上**降低了单一 oracle 风险**——这是本次外部交叉验证对 shushu 的正面价值。
5. **本次未覆盖 shushu 的 L0 数值**（节气/朔望/干支表）的独立复算，仅覆盖其**口径声明**；L0 精度的独立验证需第 1 条的实跑补齐。
6. **未验证 shushu 的审计/门禁层**（l4_audit / l5_defense_check）——该层是"工程防错"，非"术理口径"，不在本次外部交叉验证范围，本次未审。

---

## 附：核心分歧速览

| 分歧 | 定性 | shushu 是否站得住 |
|---|---|---|
| 真太阳时子正 vs lunar-python 默认 | **伪分歧**——默认同为子正；真实差异是"真太阳时 vs 钟表时" | shushu 站得住（更精细）；但 preregister 措辞须订正 |
| 年/月柱判界时域 | 曾为真分歧，2026-09-15 已修复为单位北京时域 | 修复后与主流一致 |
| 紫微四化/闰月/年干取年 | 真流派分歧 | 站得住（已申报+oracle） |
| 奇门拆补 vs 置闰 | 真流派分歧 | 站得住（kinqimen 亦并存两法） |
| 六爻做不做旺衰 | 真范围分歧 | 站得住（自设范围，I-7） |

**最严重的分歧 = C-1**：preregister 把 oracle（lunar-python）的**非默认** 23:00 子初行为误记为"默认"，导致把与 oracle 同族的"子正"口径定性为"算法分歧"。此为**描述/归因错误**，不影响盘面数值，但直接违反 shushu 自己"差异无处藏身、逐条申报"的立项承诺，须订正。
