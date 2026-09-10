---
name: gartner-hc-mq-insight
description: Use when completed Gartner Hype Cycle and Magic Quadrant analyses need combined cross-report insight, external validation, or an optional vendor comparison.
---

# Gartner HC×MQ 交叉洞察

仅在 HC 与 MQ 的结构化分析均已完成且可追溯时使用。不要在此重新读取或翻译 PDF，也不要替代单侧分析；缺少一侧时只能输出观察项并说明缺口。

每条核心趋势必须同时具备：HC 信号、MQ 信号、外部证据、变化机制和行业影响。单侧 Gartner 信号只能进入观察项。`target_vendor` 只有用户明确指定时才出现；`domain_profile` 默认留空，使用领域专属建议时才显式传入。

当 `domain_profile=networking` 时，加载 [Networking 领域配置](references/domain-networking.md)；其他领域不套用网络设备或 SME 假设。

按需读取：

- [HC×MQ 交叉洞察协议](../gartner-analysis/references/analysis-cross-insight-protocol.md)
- [分析证据与质量](../gartner-analysis/references/analysis-evidence-and-quality.md)
- [分析输出契约](../gartner-analysis/references/analysis-output-contract.md)
- [飞书输出协议](../gartner-analysis/references/analysis-feishu-output.md)

使用 `agent-reach` 检索外部一手或权威证据。完成后运行 [分析输出验证器](../gartner-analysis/scripts/validate_outputs.py) 的 `--mode full --years Y1 Y2`，按需附加 `--target-vendor`。默认交付 Markdown；用户明确要求飞书时，发布经验证的副本并回读确认。
