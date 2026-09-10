---
name: gartner-report-extraction
description: Use when reading one or more Gartner Hype Cycle or Magic Quadrant PDFs to extract auditable metadata, structured fields, tables, page anchors, and evidence gaps.
---

# Gartner 报告读取与结构化提炼

目标是把 Gartner PDF 变成可审计的输入清单、结构化底表和证据缺口记录。默认只做 `extract`，不要自动生成年度比较、外部研究或战略建议。

## 执行边界

- 使用 `pdf:pdf` 逐页读取正文、表格、图片和脚注；记录无法可靠读取的页码。
- 识别报告类型、标题、Gartner ID、年份、发布日期、市场范围、页数和可读性。
- HC 底表覆盖技术/Innovation Profile 全集、Hype Cycle Stage、Maturity、Benefit Rating、Years to Mainstream Adoption、Market Penetration、Definition、Why Important、Business Impact、Drivers、Obstacles、User Recommendations、Sample Vendors；Stage 与 Maturity 分开。MQ 底表至少覆盖市场定义、评价标准、战略假设、Vendor Profile、Strengths、Cautions。
- 结构化提炼不得把推测写成 Gartner 原文；所有字段保留页码锚点和原始英文术语。
- 不改变原始 PDF，不把摘要、搜索片段或厂商材料当作字段事实。

## 输出选择

`extract` 只输出输入清单、结构化底表、页码锚点和证据缺口。需要 HC 或 MQ 解读时转交对应分析 Skill；需要其他交付形态时回到总路由重新选择模式。

作为完整飞书 HC 报告的上游时，按[数据交接契约](../gartner-structured-presentation/references/hc-feishu-insight.md#1-输入与证据交接)记录 PDF 哈希、逐字段页码、两年独立技术全集和四张 HC／Priority Matrix 原图；写入 `hc-comparison-data.json`，完成后直接交接年度分析，不把提炼产物当作最终交付。

按需读取 [分析输出契约](../gartner-analysis/references/analysis-output-contract.md)、[分析证据与质量](../gartner-analysis/references/analysis-evidence-and-quality.md) 和 [飞书输出协议](../gartner-analysis/references/analysis-feishu-output.md)。默认交付 Markdown；用户明确要求飞书文档时，使用 `lark-doc-convert` 转换并回读验证。
