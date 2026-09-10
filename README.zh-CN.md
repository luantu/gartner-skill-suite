# Gartner Skill Suite

[English](README.md) | 简体中文

这是一个模块化的 Gartner 研究 Skill 套件，覆盖可审计的 PDF 提炼、中文翻译、Hype Cycle 与 Magic Quadrant 分析、年度对比、跨报告洞察和结构化呈现。

## 快速开始

1. 将各 Skill 目录复制到你的 Agent 运行时所使用的 Skill 目录。
2. 从套件权威路由 `gartner-analysis` 开始。
3. 说明任务并选择对应模式。例如：

   > 使用 `$gartner-analysis` 提炼这份 Gartner PDF 的字段和页码锚点，使用 `mode=extract`，输出 Markdown。

   > 使用 `$gartner-analysis` 比较这份 Gartner Hype Cycle 的 2025 和 2026 版本，使用 `mode=annual-hc`，引用页码证据。

4. 仅提供你有权处理的原始材料。生成报告和源 PDF 应保存在本仓库之外。

## 模式与 Skill

| 目标 | 入口 Skill | 模式 |
| --- | --- | --- |
| 提炼元数据、字段、表格和页码证据 | `gartner-report-extraction` | `extract` |
| 将 Gartner PDF 翻译为简体中文 | `gartner-pdf-zh-translation` | `translate-pdf` |
| 分析单份 Hype Cycle | `gartner-hype-cycle-analysis` | `single-hc` |
| 比较两个 Hype Cycle 版本 | `gartner-hype-cycle-analysis` | `annual-hc` |
| 分析单份 Magic Quadrant | `gartner-magic-quadrant-analysis` | `single-mq` |
| 比较多个 Magic Quadrant 版本 | `gartner-magic-quadrant-analysis` | `annual-mq` |
| 合并已完成的 HC 与 MQ 分析 | `gartner-hc-mq-insight` | `cross-insight` |
| 编排已验证结果用于呈现 | `gartner-structured-presentation` | `presentation` |

`gartner-annual-comparison` 作为兼容入口保留，并转到 `gartner-hype-cycle-analysis` 的 `mode=annual-hc`。

## 推荐工作流

1. **提炼**：从源 PDF 建立可审计的输入底表，并记录页码锚点。
2. **分析**：针对所选模式运行 HC 或 MQ 专项 Skill，清楚区分 Gartner 原文、外部证据和分析判断。
3. **比较或合并**：年度比较只用于口径可比的版本；跨报告洞察只在 HC 与 MQ 分析均完成后使用。
4. **呈现**：使用结构化呈现 Skill 编排已验证内容，不改变证据和结论。
5. **验证**：分享结果前运行适用的验证器。

## 仓库结构

- `gartner-analysis/`：路由、共享协议、验证器和测试
- `gartner-report-extraction/`：PDF 提炼契约
- `gartner-pdf-zh-translation/`：翻译脚本和逐页 QA
- `gartner-hype-cycle-analysis/`：Hype Cycle 分析
- `gartner-magic-quadrant-analysis/`：Magic Quadrant 分析
- `gartner-hc-mq-insight/`：跨报告洞察
- `gartner-structured-presentation/`：结构化呈现契约
- `gartner-annual-comparison/`：兼容入口

## 验证

在 `gartner-analysis/` 目录执行：

```bash
python3 -m pytest -q tests
python3 scripts/validate_terminology.py --skills-root ..
```

PDF 翻译 Skill 还提供了位于 `gartner-pdf-zh-translation/scripts/` 中的专项 QA 命令。

## 范围与安全

本仓库只包含可复用的 Skill 说明、参考资料、脚本和测试，不包含 Gartner 源 PDF、客户材料、生成报告、凭证、API 密钥、缓存、字节码或本机元数据。

仅使用你有权处理和再分发的源材料。厂商专属测试数据已替换为通用占位名。

## 许可证与第三方权利

再分发前请审查 Gartner 条款以及源材料的许可证。本仓库提供工作流说明和工具，不授予再分发 Gartner 报告或其他第三方内容的权利。

## 可调整 HC 双曲线对比

调用示例：“使用 `$gartner-analysis` 比较这两份 HC，生成可调整的双曲线 HTML（`presentation_format=hc-editor`）。”Agent 先核对报告与技术映射、生成 SVG，再通过 `gartner-structured-presentation/scripts/build_hc_editor.py` 打包 HTML。浏览器中可拖动、编辑标签，保存／载入布局 JSON，导出调整后的 SVG／PNG。需要发布时指定飞书文档或画板，Agent 使用 `lark-cli` 写入 SVG 并回读预览。详见[完整流程与命令](gartner-structured-presentation/references/hc-comparison-editor.md)。

## 两份 HC 直接生成飞书技术线索报告

调用示例：“使用 `$gartner-analysis`，根据这两份 HC 生成完整飞书技术线索文档，包含洞察总结、双曲线画板、年度总览和逐技术详情。”自动使用 `hc-feishu-insight` 配置，连续完成提炼、年度分析、XML 排版、发布与回读；无需额外提供 MQ 或先生成全文译稿。企业布局资料可选，缺失时明确未知。详见[交付结构和验收](gartner-structured-presentation/references/hc-feishu-insight.md)。
