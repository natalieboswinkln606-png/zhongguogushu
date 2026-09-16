# 全球玄学与命理开源生态深度调研与 D:\shushu 架构印证比对报告

> **调研范围**：GitHub 开源社区、MCP Server 生态、AI Agent 命理 Skills、各类平台型应用（Coze / Claude Code / Cursor / Antigravity）
> **比对基准**：`D:\shushu`（L0-L5 工业级传统术数引擎与审计防御防御体系）
> **报告日期**：2026-09-16
> **调研编写**：Antigravity 命理工程与智能体架构研究组

---

## 目录
1. [执行摘要与生态全景图谱](#一执行摘要与生态全景图谱)
2. [重点开源项目深度技术解构](#二重点开源项目深度技术解构)
   - 2.1 [Brhiza/mingyu (命语：TS全能工具箱 + 跨界生态)](#21-brhizamingyu-命语)
   - 2.2 [Sudo-Biao/Chinese-Metaphysics-Platform (Python全栈 + 8600行古籍BM25 RAG)](#22-sudo-biaochinese-metaphysics-platform)
   - 2.3 [0xfnzero/YiSphere (易圈：5D时空世界线与贝叶斯应用)](#23-0xfnzeroyisphere-易圈)
   - 2.4 [专用 MCP 矩阵：cantian-ai、shunshi-ai 与 ChesterRa/mingpan](#24-专用-mcp-矩阵)
   - 2.5 [平台级 Agent Skills 与 Bots (Claude Code / Coze / Cursor)](#25-平台级-agent-skills-与-bots)
3. [多维度横评与技术指标矩阵](#三多维度横评与技术指标矩阵)
4. [与 D:\shushu 逐项印证与对比分析](#四与-dshushu-逐项印证与对比分析)
   - 4.1 [shushu 的降维打击优势（绝对壁垒）](#41-shushu-的降维打击优势绝对壁垒)
   - 4.2 [冲突与分歧点（架构与规范路线）](#42-冲突与分歧点架构与规范路线)
   - 4.3 [遗漏点与短板剖析（外部优秀特性）](#43-遗漏点与短板剖析外部优秀特性)
5. [D:\shushu 演进路线图与升级落地建议](#五dshushu-演进路线图与升级落地建议)
6. [附录：精选开源项目清单与参考索引](#六附录精选开源项目清单与参考索引)

---

## 一、执行摘要与生态全景图谱

在过去的 12 至 18 个月内，AI 与传统命理术数（Chinese Metaphysics & Western Divination）的结合迎来了爆炸式增长。开发者们已经从最初简单的“Prompt 扮演玄学大师”，全面过渡到了**“确定性算法排盘 + 大模型解读”**的新阶段。

然而，经过对全网数十个主流开源项目、MCP Server 和 Agent Skill 的代码与实现逻辑进行逐行剖析后，我们发现了整个行业当前面临的**核心分水岭**：

1. **行业常态（开环脆弱架构）**：
   几乎所有开源项目（包括获得广泛关注的 `cantian-ai/bazi-mcp`、`shunshi-ai/bazi-reader-mcp`、`ChesterRa/mingpan`、`Brhiza/mingyu` 等）均停留在**“前置排盘注入即结束（Open-Loop Pre-computation）”**模式。它们成功解决了“LLM 算不准天干地支”的问题，但对于**“LLM 在拿到正确排盘后，生成长篇解读时依然会张冠李戴、伪造歌诀、错乱大运年龄、漂移旺衰数值”**这一“最后一公里硬伤”，**全网几乎没有任何项目提供事后的工程化防御审查，普遍依赖 Prompt 祈求大模型不要犯错**。
2. **`D:\shushu` 的突破（闭环对抗与机械门禁体系）**：
   `shushu` 走了一条截然不同的工业级系统工程路线：不仅拥有基于 NASA/JPL DE440 高精星历与十六大自研术种的坚固数学底座，更独创了 **L4 输出审计层（快照指纹 + 5项机械不变量 + 正反向文本对账器）** 与 **L5 报告防御门禁（段首强制溯源 + 伪诗扫描 + 双源一致性审查）**，将 AI 命理的准确性判定从“概率玄学”提升为“软件工程编译级别的自动化阻断”。

```
                    ┌─────────────────────────────────────────────────────────┐
                    │               全球 AI 命理生态技术成熟度阶梯              │
                    └─────────────────────────────────────────────────────────┘
  Level 5 (机械闭环门禁) │  [D:\shushu] (L4对账审查 + L5报告门禁 + JPL星历 + 16术种自研)
  Level 4 (原典证据增强) │  [Sudo-Biao/Chinese-Metaphysics-Platform] (8600行古籍 + BM25 RAG)
  Level 3 (多术种/跨界MCP)│  [Brhiza/mingyu], [ChesterRa/mingpan] (八字/紫微/六爻/塔罗/占星)
  Level 2 (专用单术种工具)│  [cantian-ai], [shunshi-ai], [bazi-skill] (八字排盘Facts + 真太阳时)
  Level 1 (纯自然语言提示)│  各类基础 Coze Bot / GPTs 伪大师 (无排盘引擎，幻觉重灾区)
```

---

## 二、重点开源项目深度技术解构

### 2.1 Brhiza/mingyu (命语)
- **代码仓库**: [Brhiza/mingyu](https://github.com/Brhiza/mingyu)
- **技术栈**: TypeScript / React / Node.js / pnpm workspace
- **模块组成**: 核心算法包 `mingyu-core` + MCP Server (`pnpm mcp`) + Agent Skill (`npx skills add Brhiza/mingyu`)

#### 架构与实现逻辑
1. **连接模式**：
   - 采用“算法直出 Facts + 预制解读 Prompt 模版”的组合交付机制。
   - 底层计算并非 100% 自研，而是采取**聚合集成策略**：紫微斗数采用 `iztro` 作为 peer dependency，天体运行与星历排盘引入 `celestine`，农历换算采用标准化算法，并在其上统一封装出一套对外的 TypeScript 函数。
2. **MCP 与 Tool 规范**：
   - 暴露工具覆盖度极宽，涵盖：`bazi`（八字）、`ziwei`（紫微斗数）、`astrology`（西洋现代星盘）、`qimen`（奇门遁甲）、`liuyao`（六爻）、`meihua`（梅花易数）、`daliuren`（大六壬）、`xiaoliuren`（小六壬）、`tarot`（塔罗牌）、`lenormand`（雷诺曼）、`lingqian`（灵签抽签）、`zeri`（择日）。
   - 参数要求标准化日期时间，提供 `resolveTrueSolarBirthTime` 方法进行经纬度真太阳时补偿。
   - 返回结构不仅包含排盘原始数据，还会附带专为 LLM 定制的结构化提示语引导大模型按步分析。
3. **防幻觉机制**：
   - **典型的开环前置防御**。工具负责提供准确的 JSON Facts 和 System Prompt。
   - **缺陷**：生成后没有任何审计对账、没有任何不变量验证（如大运首步是否合法、星曜是否跨宫等）。大模型完全可能在解读时无中生有。
4. **交互与生态广度**：
   - **广度第一**：全网唯一深度整合东方三式、四柱、六爻与西方占星（Astrology）、韦特塔罗（Tarot 78张）、雷诺曼的现代化 TypeScript 工具库。
   - 前端支持基础排盘页面展示与 Markdown 渲染，但未形成完备的印刷级多页 PDF 输出引擎。

---

### 2.2 Sudo-Biao/Chinese-Metaphysics-Platform
- **代码仓库**: [Sudo-Biao/Chinese-Metaphysics-Platform](https://github.com/Sudo-Biao/Chinese-Metaphysics-Platform)
- **技术栈**: Python (FastAPI + Pydantic v2) + React (Vite + PWA) + SSE 流式响应

#### 架构与实现逻辑
1. **连接模式**：
   - 遵循现代化前后端分离与微服务分层设计，严格划分 **Calculation Layer（计算层）** 与 **API / Interpretation Layer（解读层）**。
   - 计算层为纯 Python 算法，强调“遵从古法”（以立春为岁首、节令定月建、真太阳时折算子正换日）。
   - 解读层支持接入 13+ 家大模型服务商（Anthropic、OpenAI、DeepSeek、Gemini、Moonshot 等），通过 Server-Sent Events (SSE) 向前端实时打字机推流。
2. **古籍 RAG 知识底座（核心特色）**：
   - 内置精心整理的 **8,600+ 行经典古籍数据库**，涵盖：
     - 八字：《滴天髓》、《穷通宝鉴》、《子平真诠》、《三命通会》
     - 卜筮：《增删卜易》、《卜筮正宗》
     - 奇门：《奇门遁甲统宗》
   - 引入 **BM25（Best Matching 25）检索算法**。鉴于文言文和传统玄学名词（如“伤官见官”、“青龙返首”、“得令通根”）具有高度特定的字符形态，传统 Dense Vector Embedding（如 OpenAI text-embedding-3）极易在文言语境下发生语义漂移，而 BM25 词法精确匹配反而在玄学术语检索中表现出极高召回率与准确度。
3. **防幻觉机制**：
   - **双重前置锚定（Dual-Anchored Prompting）**：同时向模型 Context 注入“排盘确定性数据”和“BM25 检索到的古籍原典片段”，要求模型紧扣原典字句解读，从源头上遏制了口嗨编造断语的倾向。
   - **局限**：同样属于开环设计，无后置文本校验机制，模型在长篇多轮对话中依然可能发生上下文遗忘与事实错位。
4. **交互与呈现**：
   - 前端体验极为优秀：React + Vite，支持移动端自适应与 PWA 离线安装，支持繁简体与英文切换，盘面 UI 规整清晰。

---

### 2.3 0xfnzero/YiSphere (易圈)
- **代码仓库**: [0xfnzero/YiSphere](https://github.com/0xfnzero/YiSphere)
- **技术栈**: Python / FastAPI / SSE / 前端单页 Web 聊天应用

#### 架构与实现逻辑
1. **连接模式与理论创新**：
   - 试图用现代数学与系统论重塑传统术数。提出了 **“5D 投影世界线引擎”（5D Projection Worldline Engine）**。
   - 将《周易》六十四卦的错综复杂、阴阳消长，结合**贝叶斯后验概率更新（Bayesian Updating）**与**时空结晶世界线投影**，将周易推演视为一种探索未来因果关系的动态推断工具。
   - 后端划分为模块化微服务：`bazi_service`、`iching_service`、`huangli_service`、`calendar_service`。
2. **防幻觉机制**：
   - 依赖本地服务进行起卦（如三铜钱法概率模拟）和排盘计算，保证物理卦象与干支输入的准确。解读层面依赖 LLM 的系统提示词与对话上下文约束，未见独立的事后审计对账门禁。

---

### 2.4 专用 MCP 矩阵：cantian-ai、shunshi-ai 与 ChesterRa/mingpan

| 项目 | 核心特色与工具定义 | 优缺点分析 |
| :--- | :--- | :--- |
| **`cantian-ai/bazi-mcp`** | 工具：`getBaziDetail`, `getSolarTimes`, `buildBaziFromSolarDatetime`。<br>专注于高质量八字核心数据（四柱干支、十神、藏干、大运年份等）。 | **优点**：颗粒度精细、极简无赘肉，被大量消费级应用和文化 Agent 采用。<br>**缺点**：仅限八字，无紫微/奇门/六爻等横向扩展，无后置审计。 |
| **`shunshi-ai/bazi-reader-mcp`** | 工具聚焦于专业实战八字。默认强制经纬度真太阳时校正；深度支持**中/英/日/韩四国语言**本地化输出。 | **优点**：国际化能力出众，真太阳时与跨时区处理严谨。<br>**缺点**：同样属于单向排盘工具，无报告对账防线。 |
| **`ChesterRa/mingpan`** | 纯粹的中国传统术数排盘 MCP：涵盖八字、紫微斗数、六爻纳甲、梅花易数、大六壬、奇门遁甲。坚持“Facts Only”，输出纯排盘字典。 | **优点**：东方主流术数全覆盖，接口统一，无多余主观诱导。<br>**缺点**：算法依赖外部通用包，未见深层天文星历校验与机械不变量断言。 |

---

### 2.5 平台级 Agent Skills 与 Bots (Claude Code / Coze / Cursor)

1. **纯 Prompt 包装型（Prompt-only Bots，以早期的 Coze/GPTs 命理大师为主）**：
   - **运行机制**：完全依靠 System Prompt 指引（如“你是一位精通渊海子平的八字宗师，请根据用户的生日推算八字...”）。
   - **致命缺陷**：大模型本质是自回归文本预测模型，缺乏确定性历法计算器。遇节气交接必算错、大运顺逆常倒置、地支藏干十神混乱，甚至出现“甲子年丙寅月丁卯日”等不存在的干支组合，是严重的**幻觉灾难区**。
2. **Deterministic Agent Skill（如 `xuemian168/bazi-skill`、`gaoxin492/bazi-skill`）**：
   - **运行机制**：将 Python 计算脚本装载至 Claude Code 或 Cursor 的本地 Skill 环境（通过 `SKILL.md` 规范）。在 Prompt 中强制定义工作流：Agent 必须先执行本地 Python 脚本计算真太阳时与排盘，拿到 JSON 后方可开始解读。
   - **档案系统管理**：如 `gaoxin492/bazi-skill` 实现了本地命造档案管理（Destiny Archive），方便跨会话多轮追踪。
   - **核心瓶颈——“最后一公里断裂”**：
     这些项目已经意识到并做到了“禁手算排盘”。但真实实战中，**大模型在依据 JSON 生成 3000 字以上深度分析长文时，脑中依然会“凭直觉篡改数据”**！
     - 典型事故：把日支戌中“戊正印”顺口说成“偏财”；把 2025 年当成 20 岁（实际 21 岁）；跨段复用旧模版遗留了上一个命造的大运；编造“天德合入命必当大官”等虚假神煞歌诀。
     - **全网除 `shushu` 外，无任何 Skill 在 Agent 写作完毕后挂载自动化校验器进行“出口前拦截”**。

---

## 三、多维度横评与技术指标矩阵

| 评估维度 / 技术指标 | `D:\shushu` | `Brhiza/mingyu` | `Sudo-Biao Platform` | `0xfnzero/YiSphere` | `shunshi / cantian MCP` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **底层实现语言** | **Python (纯自研冻结内核)** | TypeScript (TS) | Python | Python | TypeScript |
| **天文学高精底座** | **NASA/JPL DE440 BSP + Skyfield 仲裁** | `celestine` 基础计算 | 纯算法标准节气公式 | 标准天文历法 | 基础真太阳时经纬度表 |
| **术数生态覆盖** | **传统正统 16 大术种全谱** (四柱/紫微/奇门/六爻/大六壬/小六壬/河洛/梅花/铁板/称骨/五运六气/黄历/合盘等) | **传统术数 + 西方占星 + 78张塔罗 + 雷诺曼 + 灵签** | **正统 7 大术数** (四柱/紫微/六爻/奇门/玄空风水/择日/周易) | 易经/六爻/八字/黄历/起名 | 专注八字或基础多术种 |
| **MCP 规范与服务** | **标准 JSON-RPC 2.0 stdio (7大核心工具，含审计工具)** | 标准 stdio MCP + Agent Skill (`skills add`) | FastAPI RESTful API (可封装 MCP) | FastAPI 微服务 | 标准 stdio MCP Server |
| **Facts 颗粒度** | **极高且严谨** (Pydantic Schema，分柱、藏干、长生得地、三方四正合宫、格局断局) | 较高 (附带生成 AI 引导 Prompt) | 极高 (Pydantic v2 标准模型) | 中等 (面向会话组织) | 高 (八字专属字段完备) |
| **古籍文献集成** | 暂未内置全文 RAG (依赖内部 rules 逻辑) | 暂无大篇幅古籍检索 | **内置 8,600+ 行古籍 + BM25 检索** | 概念型哲学世界模型 | 暂无 |
| **防幻觉：前置排盘** | **全自研锁定，禁手推** | 算法计算 | 算法计算 | 算法计算 | 算法计算 |
| **防幻觉：快照与不变量**| **全量 JSON 快照 + 5项机械不变量 (`aud-inv-01..05`)** | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 |
| **防幻觉：文本正反向对账**| **L4 `reconcile` (大运错位/十神错配/分数漂移/双源冲突)** | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 |
| **防幻觉：报告防御门禁** | **L5 九重铁律 (`l5_defense_check.py` 伪诗/双源/段引用)** | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 |
| **前端交互与渲染** | **零外部依赖现代离线 HTML (`visualizer.py` 内联CSS+原生JS)** | React 组件 + Markdown 渲染 | **现代化 React + Vite + PWA + 移动端自适应** | 单页 Web 对话 UI | 纯数据接口，依赖客户端客户端宿主 |
| **报告导出能力** | Markdown + 独立离线交互式 HTML | Markdown 输出 | 页面预览与复制 | 对话流文本输出 | 纯 JSON / 文本输出 |
| **多模型集成** | 兼容所有标准 MCP 宿主 (Claude/Cursor/AGY) | 兼容 Claude/GPT 等 | **内置 13+ 家 LLM 网关 (SSE 流式输出)** | OpenAI 兼容接口 | 兼容 Claude/Cursor |

---

## 四、与 D:\shushu 逐项印证与对比分析

### 4.1 shushu 的降维打击优势（绝对壁垒）

#### 1. 唯一建立“生成后机械闭环防御”体系（终结最后一公里幻觉）
全网所有开源项目在此刻均停留在**“前置输入保护”**阶段。而 `shushu` 的核心竞争力，正是经历过数十次真实命理研判事故打磨而成的 **L4/L5 纵深防御工事**：
- **快照指纹与版本锚定 (`snapshot` + `meta.provenance`)**：任何排盘结论必须先生成确定性快照，快照绑定引擎全量文件的 SHA-256 签名，杜绝算推混杂。
- **机械不变量审查 (`check_invariants`)**：
  - `aud-inv-01`：起运首步绝对等于月柱 $\pm 1$（彻底阻断阳年女/阴年男逆排首步错位的经典事故）；
  - `aud-inv-02`：大运链条每步必须严密递增/递减，起运年份精确递增 10 岁；
  - `aud-inv-03`：流年干支公式 $(year - 4) \pmod{60}$ 独立全量验算；
  - `aud-inv-04`：紫微十二宫不重不漏，命宫地支随生时进位方向必须全盘均匀；
  - `aud-inv-05`：奇门九宫中五宫必须寄坤二宫（星门神仪置空），值符天盘必含旬首仪。
- **正反向文本对账器 (`l4_audit_output.reconcile`)**：
  大模型产出 Markdown 草稿后，工具使用严格正则与词表进行全文抓取并与快照 cross-check：
  - `double_source_mismatch`：排查跨段落同干支多位置出现时的属性冲突（防跨命造草稿拼凑）；
  - `ws_score_drift`：旺衰分值若与快照偏差 $> 0.5$ 立即报警（防旧数值残留）；
  - `ten_god_mismatch`：文中所有日主十神必须严格匹配 `DM_GOD[日主][干支]`（防凭印象配十神）；
  - `age_year_mismatch`：文中“X岁 YYYY”必须严格满足 $YYYY - 出生年 = X$（防凭直觉换算年龄）。
- **L5 报告防御门禁 (`l5_defense_check.py`)**：
  - 每段叙述强制包含 `snap.`、`@引擎` 溯源标签；
  - 自动扫描“歌诀/格局/十恶大败/天芮”等高频伪造词，严禁大模型私自伪造古籍诗歌（伪诗拦截）；
  - 门禁一票否决制：`conflicts > 0` 或门禁未过，系统直接退出码 1，硬性拒绝出档。

#### 2. 航天级 JPL DE440 高精星历与双源仲裁底座
- 大多数外部项目（包括 TS/JS 社区）使用简化的日月黄经平动拟合算法，在定气（节气交接时刻精确到分秒）和晦朔弦望（日月合朔定农历初一）上存在数分钟乃至数十分钟的理论误差。在遇上“交节日当天、子夜交接、月末三十与初一分界”的极限边缘命盘时，极易排出错位的月柱或日柱。
- `shushu` 集成了 **NASA/JPL DE440 真实星历二进制文件 (`de440_l4.bsp`, 32MB/119MB) + Skyfield**，通过 `skyfield_arbitrate.py` 和 `shuowang_compare.py` 实现了天文台级别的双源交叉仲裁，奠定了无法撼动的数学与天文真理底座。

#### 3. 真正冻结的十六大术种纯算法实现
- 外部工具大多采取“外包”策略：八字调一个包，紫微引一个 `iztro`，奇门调另一个。包与包之间接口混乱、口径不一（例如紫微的农历日与八字的太阳时节气日定义互相冲突）。
- `shushu` 实现了从 L0 权威查表（CSV）到 L1 四柱内核 (`m1.py`)、L2 规则公式 (`rules.py`)、L3 十六大术种全谱（含称骨、五运六气、河洛理数、铁板神数等冷门绝学）的代码全自研闭环，并通过 `SHA256SUMS.txt` 实行版本冻结与测试锁定。

#### 4. 极致轻量、零依赖的现代离线可视化 (`visualizer.py`)
- 相比外部项目繁重的 React/Vite/Webpack 打包与 node_modules 依赖，`shushu` 的 `visualizer.py` 采用内联 CSS 与纯原生 Vanilla JS，一键生成完全离线可用的现代美学 HTML。
- 支持紫微 4x4 回字形网格（点击宫位动态高亮三方四正合宫）、奇门 3x3 洛书九宫、八字四柱五行卡片与六爻本变双向对照，做到了“零网络依赖、单文件分发、开箱即阅”。

---

### 4.2 冲突与分歧点（架构与规范路线）

1. **MCP Server 的角色认知分歧：数据通道 vs 审计网关**
   - **行业主流模式**：MCP 仅仅被作为大模型的输入工具（Tool）。大模型调用工具获得 JSON 数据，后续工作完全脱离 MCP 管控。
   - **`shushu` 的创新矛盾**：`shushu` 在 `mcp_server.py` 中不仅提供了数据生成（`shushu_snapshot`），还提供了 **`shushu_reconcile`（对账审计工具）**。这在行业内属于先锋设计——将“防守自查”作为一项能力暴露给 Agent。然而，在主流 Agent（如 Claude Desktop 或通用 Cursor 规则）中，若无强制 System Prompt 约定，大模型并不会在撰写完成后“主动再次调用 reconcile 工具对账”，这需要配合特殊的 Agent 执行流或 Hook 才能发挥最大威力。
2. **数据输出颗粒度与职责边界**
   - `Brhiza/mingyu` 倾向于“把菜做好端上来”：排盘结果中内嵌了大量预先设定的 Prompt 模版与引导话术。
   - `shushu` 坚持“高内聚低耦合”的 UNIX 哲学：Facts 必须是纯净、结构化、无偏见的数据对象（`shushu_schema.py`），解读策略留给 Agent 自行决断，但后续对其输出行使最严苛的法律审查。
3. **交付形态分歧：现代 Web 全栈 vs 本地工程化 CLI/离线报告**
   - 外部项目（如 Sudo-Biao）追求给最终普通用户提供漂亮的 Web App 和移动端体验；
   - `shushu` 架构是专业工程师、严谨命理学者与超级 Agent 的“军工级作业平台”，以 CLI、JSON 快照、离线 HTML 和 Markdown 报告为核心交付物，技术受众定位更为专业。

---

### 4.3 遗漏点与短板剖析（外部优秀特性）

对比全网优秀开源项目，`shushu` 目前在以下维度存在明显的升级空间：

#### 1. 古籍文献 RAG 检索体系与原典底座缺失（强烈建议吸纳 Sudo-Biao）
- **痛点**：目前 `shushu` 的 L5 防御规则三（`rule3`）对“歌诀/诗词/格局名”采取了极其严苛的标志词扫描。如果 Agent 在行文中引用了真实的《滴天髓》古赋名句，因为快照中未包含古籍全文，极易被 L5 误杀判定为“伪诗虚构”；反之，Agent 也无法方便地自动索引匹配古典依据。
- **借鉴方案**：借鉴 `Sudo-Biao/Chinese-Metaphysics-Platform` 的工程实践，引入其整理的 **8,600+ 行古籍文言文本库**，并在 `shushu` 中构建一个轻量级 BM25 古籍检索模块。当排盘完成后，根据日主格局（如“甲木生于寅月建禄”、“天干壬丙相映”）自动检索古籍原典，作为合规权威语料供给 Agent 引用，彻底解决“引经据典”与“防伪诗”之间的张力。

#### 2. 术数生态广度的空白：西方占星 (Astrology) 与 78 张塔罗牌 (Tarot)
- **痛点**：`shushu` 在中国传统术数上已经登峰造极（16 术种），但在当代年轻化、全球化场景中，西洋占星（Natal Chart、本命盘、相位天顶）与韦特塔罗牌（Tarot 大小阿卡纳 78 张）拥有巨大的受众基础。
- **借鉴方案**：借鉴 `Brhiza/mingyu`，可在东方术数体系之外，增设 Western Metaphysics 扩展模块（例如接入开源成熟的 Swiss Ephemeris `pyswisseph` 或天体计算库，实现西方 12 星座、12 宫位、主要相位角计算，以及 78 张塔罗牌阵与牌意标准 Schema）。

#### 3. 专业多页印刷级 PDF 自动化编译链路
- **痛点**：目前 `shushu` 生成离线 HTML 盘面和 Markdown 深度报告，但交付给最终委托人时，缺乏类似 `mingli_engine` 或商业命理软件那种多页排版精致、带中式古典封面、矢量回字形盘面、防伪水印的专业 PDF 报告。
- **借鉴方案**：引入基于 Playwright Headless 或 Python `weasyprint` 的自动化装配管线，将 `visualizer.py` 的 HTML 盘面与经过 L5 审查通过的 Markdown 报告无缝编译成 A4 印刷级 PDF 交付文档。

#### 4. 交互形态的平台化：流式 SSE API 与多模型支持
- **痛点**：`api_server.py` 目前以同步 JSON 接口为主，缺乏类似 Sudo-Biao 那样支持 OpenAI/Claude 多服务商切换的 SSE 流式输出能力与 Web 实时聊天交互前端。

---

## 五、D:\shushu 演进路线图与升级落地建议

结合本次调研成果，建议 `shushu` 在保持“纯自研内核、L4/L5 闭环防御、JPL 物理星历”绝对壁垒的前提下，启动 **v2.0 平台化与知识工程升级**：

```
                                 D:\shushu v2.0 演进规划
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                                展现与交互层                                  │
    │  [离线 HTML visualizer]  +  [Headless PDF 出档编译]  +  [React/PWA Web UI]   │
    └──────────────────────────────────────┬──────────────────────────────────────┘
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    │                              L5 报告防御门禁层                               │
    │  [段首必引 snap] + [L3模块全谱] + [伪诗拦截 & 原典放行] + [双源一致性 & 门禁] │
    └──────────────────────────────────────┬──────────────────────────────────────┘
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    │                         L4 闭环审计与 RAG 知识检索层                         │
    │  [l4_audit_output 快照/不变量/对账]  +  ★[古籍 RAG: 8600行文言语料 + BM25]    │
    └──────────────────────────────────────┬──────────────────────────────────────┘
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    │                         L3 术数计算引擎层 (完全冻结)                         │
    │  [东方十六正统术数 l3_*.py]  +  ★[扩展: 西洋占星 swisseph / 韦特塔罗牌 78 张]  │
    └──────────────────────────────────────┬──────────────────────────────────────┘
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    │                       L1-L2 内核与 L0 物理天文底座                           │
    │      [m1.py 四柱内核]  +  [rules.py 规则]  +  [NASA/JPL DE440 BSP 星历]       │
    └─────────────────────────────────────────────────────────────────────────────┘
```

### 具体落地四步走：

1. **第一阶段：构建“古籍文献 RAG 底座”（吸收 Sudo-Biao 经验）**
   - 在 `data/` 下建立规范的古籍文言语料库 `classics_corpus/`（引入《滴天髓》、《穷通宝鉴》、《子平真诠》、《增删卜易》等标准化分段语料）。
   - 实现轻量纯 Python BM25 检索模块 `l3_classics_rag.py`。
   - 升级 `l5_defense_check.py` 规则三：当命中原典库真实引句时予以合法放行，既防凭空捏造伪诗，又支持博古通今的文献实证。
2. **第二阶段：跨界术数生态扩展（吸收 mingyu 经验）**
   - 增设 `l3_astrology.py`（西洋星盘本命盘、行星黄道度数、宫位制 Placidus/Koch、相位列表）。
   - 增设 `l3_tarot.py`（78 张韦特牌库数据、正逆位、常用牌阵如凯尔特十字、时间之流等）。
   - 在 `shushu_schema.py` 和 `mcp_server.py` 中补充对应的 Schema 与 MCP Tools。
3. **第三阶段：企业级专业报告装配器（PDF 出档）**
   - 编写 `report_assembler.py`，串联 `visualizer.py` 渲染的矢量盘面与 L5 PASS 报告正文，一键输出中式装帧排版的 PDF 文件。
4. **第四阶段：Agent 双向协议规范化与 MCP 对账 Hook**
   - 完善 MCP Server 的 Prompt 规范，在 `mcp_server.py` 中注入 Client 端的推荐工作流契约（Contract）：强制 AI Agent 在完成撰写后必须主动调用 `shushu_reconcile` 并确认 `conflicts == 0`，形成端到端的自治智能体防幻觉闭环。

---

## 六、附录：精选开源项目清单与参考索引

1. **[Brhiza/mingyu](https://github.com/Brhiza/mingyu)**
   - 全功能命理工具箱，涵盖东方传统三式/四柱/紫微与西方占星、塔罗、雷诺曼，支持 stdio MCP Server 与 Agent Skill。
2. **[Sudo-Biao/Chinese-Metaphysics-Platform](https://github.com/Sudo-Biao/Chinese-Metaphysics-Platform)**
   - Python + FastAPI + React 全栈命理平台，内置 8,600+ 行古籍文言文语料库与 BM25 检索系统，支持 13+ 种主流 LLM 流式解读。
3. **[0xfnzero/YiSphere](https://github.com/0xfnzero/YiSphere)**
   - 易圈：将周易六十四卦与贝叶斯更新、5D 时空世界线投影结合的 AI 传统术数全栈应用。
4. **[cantian-ai/bazi-mcp](https://github.com/cantian-ai/bazi-mcp)**
   - 专注高品质八字排盘与干支事实输出的标准 Model Context Protocol 规范实现。
5. **[shunshi-ai/bazi-reader-mcp](https://github.com/shunshi-ai/bazi-reader-mcp)**
   - 专业真太阳时校正、支持中/英/日/韩四语输出的八字排盘 MCP Server。
6. **[ChesterRa/mingpan](https://github.com/ChesterRa/mingpan)**
   - 聚合八字、紫微、六爻、梅花、奇门、六壬的确定性 Facts-Only 排盘服务。
7. **[xuemian168/bazi-skill](https://github.com/xuemian168/bazi-skill) & [gaoxin492/bazi-skill](https://github.com/gaoxin492/bazi-skill)**
   - 面向 Claude Code / Cursor / Codex 框架的确定性 Agent 本地执行命理技能与命造档案管理系统。
8. **[ydsgangge-ux/mingli_engine](https://github.com/ydsgangge-ux/mingli_engine)**
   - 内置 `assembler/` 模块与 `/api/generate-report` 异步任务架构的命理出档引擎参考。
