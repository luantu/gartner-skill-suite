---
name: gartner-structured-presentation
description: Use when Gartner HC or MQ analysis needs structured chapters, tables, editable HC charts, or a complete Feishu HC technology-insight report with native document and whiteboard verification.
---

# Gartner HC/MQ 结构化呈现

这是呈现层 Skill，不重新解析 PDF、不补造字段，也不做 HC×MQ 交叉推理。输入必须是已验证的提炼底表、HC/MQ 分析或交叉洞察。

- `report_type=HC`：使用 HC 章节模板，保留阶段、Priority Matrix、技术线索和单年比较边界。
- `presentation_format=hc-feishu-insight`：两份 HC 到完整飞书技术线索报告，按[专用交付契约](references/hc-feishu-insight.md)组织洞察总结、两类画板、双年原图、全技术总览与逐技术详情；此配置优先于通用 HC 章节模板，发布后使用 [XML 验收器](scripts/validate_hc_delivery.py)。
- `presentation_format=hc-editor`：用户要求两份 HC 的双曲线、技术迁移图或可调整 HTML 时，使用[双曲线编辑器流程](references/hc-comparison-editor.md)，交付自包含 HTML、布局 JSON 与 SVG；数据不足先交还提炼／年度分析。
- `report_type=MQ`：使用 MQ 章节模板，保留关键变化、位置变化表和能力分析表。
- 只有存在两年同市场输入时，才生成年度变化、趋势或象限移动；否则明确写“暂无年度比较数据”。
- MQ 模板直接使用 `1.1 关键变化`，去除“关键变化洞察”标题，避免重复层级。

呈现稿只改变章节、表格、洞察块和标题层级，不改写原有证据、结论和限制。嵌入已有文档时先读取父级 heading；用户要求飞书时先遵循 `feishu-doc-optimizer` 完成格式优化，再局部写入并回读验证。

按需读取：

- [章节呈现契约](references/presentation-contract.md)
- [分析输出契约](../gartner-analysis/references/analysis-output-contract.md)
- [飞书输出协议](../gartner-analysis/references/analysis-feishu-output.md)

章节呈现默认交付 Markdown；双曲线编辑器模式交付可调整 HTML 与 SVG。完整飞书技术线索配置先保留阅读源稿，再使用 `lark-doc` 创建工作流生成原生 XML，以保留合并单元格、分栏、图片、画板和样式。其他简单飞书呈现可使用 `lark-doc-convert`。完成后检查标题层级、表格、引用和洞察块是否完整。
