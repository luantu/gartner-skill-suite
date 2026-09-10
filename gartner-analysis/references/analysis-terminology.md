# Gartner 共享术语真值表

本文件是 Gartner Skill 套件的唯一共享方法术语表。机器可读值维护在同目录的 `analysis-terminology.json`；翻译、提炼、HC/MQ 分析和结构化呈现必须引用这两份文件；报告专属技术名另建任务级词表。

## 方法与字段

| Key | English | 规范中文 | 禁止作为生成结果的变体 |
|---|---|---|---|
| `hype_cycle` | Hype Cycle | 技术成熟度曲线（Hype Cycle） | 技术成熟度曲线图、HypeCycle |
| `magic_quadrant` | Magic Quadrant | 魔力象限（Magic Quadrant） | 魔法象限 |
| `priority_matrix` | Priority Matrix | 优先级矩阵（Priority Matrix） | PriorityMatrix、PM（首次定义前） |
| `hc_stage.innovation_trigger` | Innovation Trigger | 技术萌芽期 | 创新触发、创新触发期、创新萌芽期 |
| `hc_stage.peak` | Peak of Inflated Expectations | 期望膨胀期 | 期望膨胀顶峰、期望膨胀高峰、期望值高峰期 |
| `hc_stage.trough` | Trough of Disillusionment | 泡沫破裂谷底期 | 失望低谷、失望低谷期、幻灭低谷期 |
| `hc_stage.slope` | Slope of Enlightenment | 稳步爬升复苏期 | 启蒙斜坡、启蒙阶段、启蒙爬坡期、复苏爬升期 |
| `hc_stage.plateau` | Plateau of Productivity | 生产成熟期 | 生产力平台、生产力平台期 |
| `benefit_rating` | Benefit Rating | 收益：{值}（{英文值}） | 收益评级：、变革性、高收益、中收益、低收益 |
| `adoption_years` | Years to Mainstream Adoption | 主流采用年限 | 主流采用时间、主流采用窗口、主流化窗口、主流化年限、主流时间 |
| `market_penetration` | Market Penetration | 市场渗透率 | 市场渗入率 |
| `maturity` | Maturity | 成熟度 | 与 Hype Cycle 阶段混写 |
| `analysis_by` | Analysis By: | `Analysis By:` | 分析师：、分析者：、分析人员：、分析人：、分析作者： |

## Maturity 枚举

`Embryonic=萌芽`、`Emerging=新兴`、`Adolescent=发展`、`Early Mainstream=早期主流化`、`Mature Mainstream=成熟主流化`、`Legacy=遗留`、`Obsolete=淘汰`。

`Innovation Trigger` 的“技术萌芽期”和 `Maturity=Embryonic` 的“萌芽”是不同字段，不能使用全局字符串替换互相转换。

## 使用规则

- 首次出现方法名时中英并列，后续使用规范中文或英文键。
- `Benefit Rating` 的字段键、字段标签和枚举值分开：键为 `benefit_rating`，显示为“收益：高（High）”。
- `Years to Mainstream Adoption` 的字段键为 `adoption_years`，显示为“主流采用年限”。
- 技术、产品、厂商、标准、协议、缩写、Gartner ID 和 `Analysis By:` 按源文档保留英文。
- `Market Penetration` 的区间使用 en dash `–`；边界值统一为“ 不足 1%”和“50% 以上”（中文字段内部不得缺少必要空格）。
