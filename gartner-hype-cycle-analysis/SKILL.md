---
name: gartner-hype-cycle-analysis
description: Use when interpreting a single Gartner Hype Cycle or comparing two editions of the same Hype Cycle with stage, benefit, adoption, and evidence-backed conclusions.
---

# Gartner Hype Cycle 分析

本 Skill 只处理 HC。先使用可回读的 HC 提炼底表或原始 PDF，再选择一个模式：

- `mode=single-hc`：总结单年 Gartner 结论、完整字段、重点技术、方法限制和引用；不写年度变化。
- `mode=annual-hc`：比较同一 HC 的两个年度版本，先建立条目映射，再逐字段解释阶段、Benefit、Years、Drivers、Obstacles、User Recommendations 和 Innovation Profile 的变化。

两年报告必须属于同一 HC 系列，且市场范围、技术分类和指标口径可比。改名、拆分、合并或移除条目要单独标明可比性，不把条目数量变化直接写成市场规模变化。

每项重要变化使用“变化事实 → Gartner 页码证据 → Gartner 结论 →（如需要）外部证据 → 支持程度 → 限制”。单年不得构造趋势箭头；推理与 Gartner 原话分开。

MQ、HC×MQ 交叉推理和章节呈现分别转交对应 Skill。需要完整研究套件时由总路由编排，不在本 Skill 内自动扩展范围。

按需读取：

- [HC/MQ 分析协议](../gartner-analysis/references/analysis-hc-mq-protocol.md)
- [分析输出契约](../gartner-analysis/references/analysis-output-contract.md)
- [分析证据与质量](../gartner-analysis/references/analysis-evidence-and-quality.md)
- [飞书输出协议](../gartner-analysis/references/analysis-feishu-output.md)
- [分析师小结指南](references/analyst-summary-guide.md)

完成后运行 [分析输出验证器](../gartner-analysis/scripts/validate_outputs.py) 的 `--mode hc` 或 `--mode single-hc`。默认交付 Markdown；用户明确要求飞书时，发布经验证的副本并回读确认。
