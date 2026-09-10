---
name: gartner-magic-quadrant-analysis
description: Use when interpreting a single Gartner Magic Quadrant or comparing same-market MQ editions with vendor, criteria, strengths, cautions, and evidence-backed conclusions.
---

# Gartner Magic Quadrant 分析

本 Skill 只处理 MQ。先使用可回读的 MQ 提炼底表或原始 PDF，再选择一个模式：

- `mode=single-mq`：总结市场定义、评价标准、战略假设、厂商档案、Strengths、Cautions、方法限制和引用；不写年度变化。
- `mode=annual-mq`：比较同一市场的多个年度版本，匹配厂商实体和评价维度，识别象限类别、纳入/移除、评价标准、Strengths/Cautions 和战略假设变化。

象限是类别，不是可直接相减的四级排名。并购、品牌合并、市场定义或评价权重变化必须说明可比性；不要凭图上细小位移估算坐标。

每项重要变化使用“变化事实 → Gartner 页码证据 → Gartner 结论 →（如需要）外部证据 → 支持程度 → 限制”。厂商材料只能证明厂商公开主张或动作，不能单独证明行业趋势。

HC、HC×MQ 交叉推理和章节呈现分别转交对应 Skill。需要完整研究套件时由总路由编排，不在本 Skill 内自动扩展范围。

按需读取：

- [HC/MQ 分析协议](../gartner-analysis/references/analysis-hc-mq-protocol.md)
- [分析输出契约](../gartner-analysis/references/analysis-output-contract.md)
- [分析证据与质量](../gartner-analysis/references/analysis-evidence-and-quality.md)
- [飞书输出协议](../gartner-analysis/references/analysis-feishu-output.md)

完成后运行 [分析输出验证器](../gartner-analysis/scripts/validate_outputs.py) 的 `--mode mq` 或 `--mode single-mq`。默认交付 Markdown；用户明确要求飞书时，发布经验证的副本并回读确认。
