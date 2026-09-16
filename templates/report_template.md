# (snapshot-final) {{SUBJECT_NAME}} 报告

> **数据底座**：`{{SNAP_PATH}}`（引擎版本哈希：{{ENGINE_HASHES}}）
> **生辰**：{{BIRTH_DATETIME}}（北京时间），{{GENDER}}，东经{{LON}}度
> **真太阳时**：{{TRUE_SOLAR_TIME}}（+{{CORRECTION}}）
> **核心纪律**：所有确定性数据必须从snapshot搬运，人工只许在"取象推断/综合"区段书写。
> **snap引用规范**：每段叙述性内容末尾必须标注 `(数据底座：snap.{{FIELD}})` 或 `@引擎 snapshot`，
> 禁止凭空书写任何确定性数据（干支/星名/骨重/分值/宫位等）。

---

## §1 基础信息

### 1.1 四柱骨架
（数据底座：snap.pillars）

| 柱位 | 天干 | 地支 | 五行 | 阴阳 |
|------|------|------|------|------|
| 年柱 | {{YEAR_STEM}} | {{YEAR_BRANCH}} | {{YEAR_ELEMENT}} | {{YEAR_YINYANG}} |
| 月柱 | {{MONTH_STEM}} | {{MONTH_BRANCH}} | {{MONTH_ELEMENT}} | {{MONTH_YINYANG}} |
| 日柱 | **{{DAY_STEM}}** | {{DAY_BRANCH}} | {{DAY_ELEMENT}} | {{DAY_YINYANG}} |
| 时柱 | {{HOUR_STEM}} | {{HOUR_BRANCH}} | {{HOUR_ELEMENT}} | {{HOUR_YINYANG}} |

### 1.2 十神配置
（数据底座：snap.ten_gods.stems / snap.ten_gods.branches）

- **年干{{YEAR_STEM}}** → {{YEAR_STEM_GOD}}（snap.ten_gods.stems.year）
- **月干{{MONTH_STEM}}** → {{MONTH_STEM_GOD}}（snap.ten_gods.stems.month）
- **时干{{HOUR_STEM}}** → {{HOUR_STEM_GOD}}（snap.ten_gods.stems.hour）
- **日支{{DAY_BRANCH}}藏干**：{{DAY_BRANCH_CANGGAN}}（snap.ten_gods.branches.day）
- **月支{{MONTH_BRANCH}}藏干**：{{MONTH_BRANCH_CANGGAN}}（snap.ten_gods.branches.month）

### 1.3 旺弱评定
（数据底座：snap.wangshuai.zonghe）

**综合旺衰得分：{{WS_SCORE}}分（中和）**（源：snap.wangshuai.zonghe.score）

### 1.4 大运序列
（数据底座：snap.dayun.steps，起运年龄{{QIYUN_AGE}}岁）

| 步数 | 干支 | 十神 | 起年 | 止年 | 年龄 |
|------|------|------|------|------|------|
{{DAYUN_TABLE_ROWS}}

### 1.5 称骨
（数据底座：snap.chenggu）

- 年柱{{YEAR_GZ}}：{{YEAR_CG_WEIGHT}}
- 月柱{{MONTH_GZ}}：{{MONTH_CG_WEIGHT}}
- 日柱{{DAY_GZ}}：{{DAY_CG_WEIGHT}}
- 时柱{{HOUR_GZ}}：{{HOUR_CG_WEIGHT}}
- **合计：{{TOTAL_BONES_WEIGHT}}**

---

## §2-§N 命理分论

> **段落引用规范**：每段确定性数据必须以 `(数据底座：snap.字段)` 结尾，
> 取象推断段以 `（取象推断）` 结尾，理论参考段以 `（{{MODULE}}理论参考）` 结尾。

### §2 性格深层结构
（数据底座：snap.ten_gods.branches）

### §3 紫微十二宫
（数据底座：snap.ziwei_hours[hour={{HOUR}}].palaces）

### §4 奇门遁甲
（数据底座：snap.qimen）

---

## §N 核心结论

> **结论规范**：每条结论必须标注 `（数据底座：snap.xxx）`，
> 禁止凭空书写任何分值/干支/星名。

---

## 附录：确定性数据搬运产物引用

> 以下数据全部来自 l4_data_harvest.py 自动搬运（带 (snapshot) 标签），
> 禁止在引用区外手写任何确定性数据。

{{HARVEST_CITATION_BLOCK}}

---

**报告结束**

<!--
  模板版本：v1.0
  L5 防御检查：python l5_defense_check.py check --text <OUTPUT> --snap <SNAP> --out <OUTPUT>.l5.json
-->
