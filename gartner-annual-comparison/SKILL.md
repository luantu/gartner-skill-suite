---
name: gartner-annual-comparison
description: Use when the user explicitly requests a comparison of two editions of the same Gartner Hype Cycle or a technology profile within it.
---

# Gartner Hype Cycle 年度对比（兼容入口）

年度 HC 对比的唯一实现位于 `gartner-hype-cycle-analysis` 的 `mode=annual-hc`。本 Skill 只为已有显式调用保留入口：收到请求后直接转到该模式，不在此维护第二套字段、证据规则或输出模板。

适用范围、条目映射、证据链、分析师小结和飞书回读要求，统一读取：

- [HC/MQ 分析协议](../gartner-analysis/references/analysis-hc-mq-protocol.md)
- [分析师小结指南](../gartner-hype-cycle-analysis/references/analyst-summary-guide.md)
