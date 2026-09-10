---
name: gartner-analysis
description: Use when a Gartner request spans PDF extraction, Chinese PDF translation, HC/MQ analysis, annual comparison, cross-report insight, or structured presentation and needs one authoritative route.
---

# Gartner 分析路由

这是 Gartner 套件的唯一总入口。先判断用户要交付什么，再只进入一个主模式；除非用户明确要求完整研究套件，否则不要自动展开所有阶段。

| 用户目标 | 权威入口 |
|---|---|
| 读取 PDF、提炼元数据、字段、表格和页码证据 | `gartner-report-extraction`，`mode=extract` |
| 将 PDF 做成中文保真 PDF，并保留版式、链接和逐页 QA | `gartner-pdf-zh-translation`，`mode=translate-pdf` |
| 解读单份 Hype Cycle（HC） | `gartner-hype-cycle-analysis`，`mode=single-hc` |
| 比较同一 HC 的两个年度版本 | `gartner-hype-cycle-analysis`，`mode=annual-hc` |
| 解读单份 Magic Quadrant（MQ） | `gartner-magic-quadrant-analysis`，`mode=single-mq` |
| 比较同一市场多个 MQ 年度版本 | `gartner-magic-quadrant-analysis`，`mode=annual-mq` |
| 结合已完成的 HC 与 MQ 做交叉洞察 | `gartner-hc-mq-insight`，`mode=cross-insight` |
| 把已完成结果编排成章节、表格或飞书呈现稿 | `gartner-structured-presentation`，`mode=presentation` |

`gartner-annual-comparison` 是兼容入口：只有用户显式点名它时才使用，并立即转到 HC 的 `annual-hc` 模式，不再维护第二套分析流程。

## 共享不变量

- Gartner 原始 PDF 是事实真值源；原文、Gartner 判断、外部证据和 `<推理>` 分开。
- HC 与 MQ 先分开分析，只有 `gartner-hc-mq-insight` 可以跨报告推理。
- 单年输入不构造年度变化；不可比报告不生成趋势箭头、象限移动或采用结论。
- 未指定 `target_vendor` 或 `domain_profile` 时不自行选择厂商或行业视角。
- 默认先输出并验证 Markdown；只有用户明确要求时才发布飞书，并按局部更新与回读流程执行。

## 共享资源

需要完整套件、证据分级或飞书发布时，按需读取：

- [分析输出契约](references/analysis-output-contract.md)
- [分析证据与质量](references/analysis-evidence-and-quality.md)
- [HC/MQ 分析协议](references/analysis-hc-mq-protocol.md)
- [HC×MQ 交叉洞察协议](references/analysis-cross-insight-protocol.md)
- [分析内容翻译协议](references/analysis-translation-content-protocol.md)
- [飞书输出协议](references/analysis-feishu-output.md)
- [路由、参数与交接契约](references/routing-and-parameters.md)

处理 PDF 使用 `pdf:pdf`；需要外部验证时使用 `agent-reach`。完成交付前运行适用的验证器。
