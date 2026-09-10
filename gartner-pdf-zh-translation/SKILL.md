---
name: gartner-pdf-zh-translation
description: Use when a Gartner Hype Cycle or similar report PDF must be translated into Simplified Chinese while preserving technical terminology, page geometry, charts, links, and an auditable page-by-page record.
---

# Gartner PDF 中文保真翻译

## 核心不变量

- 原始 Gartner PDF 是唯一真值源；源文件只读，不用摘要或外部材料替代原文。
- 正式输出固定为 `{source-stem}-pdf-zh.pdf` 和 `{source-stem}-translation.md`，另有 `{slug}-translation-qa.md`。
- 技术名、产品名、厂商名、标准、协议、缩写、URL、邮箱、ID 和业界统一术语先做 token 保护；普通描述忠实翻译。统一术语首次可中英并列，后续保持一致。
- Hype Cycle profile 的技术项名称按源 PDF 原样保留英文；固定字段 `Analysis By:` 全文保留英文并统一拼写。
- 保留原页面数量、页框尺寸、方向、图表、颜色、矢量元素、脚注和链接。不能安全编辑的图内标签或彩色矩阵保留英文并记录原因。
- PDF 生成后校正 CJK 字体 ToUnicode 的 ASCII 连字符映射，避免可复制技术名出现软连字符。
- CJK TrueType 字体必须嵌入；正文中文尽量维持约 9pt 或以上，不能以缩小到不可读为代价追求塞入原框。

## 工作流

1. 读取报告的 source manifest、提取稿和本 Skill 相关参考，确认物理页数与正文页脚页数。
2. 用 `scripts/translate_gartner_pdf.py` 按页合并视觉换行、隔离项目符号、批量翻译并缓存；使用 `--font` 指定报告资产中的 CJK 字体。
   默认优先使用可用的 Gartner 技术翻译模型；当 OpenRouter 额度不足时，可使用 `minimax/minimax-m3:free`（脚本会按输入长度显式设置 `max_tokens`，避免免费额度因隐式预留 4096 tokens 而被拒绝）。`google-gtx` 仅用于诊断性回退，不作为严谨交付路径；其术语 token 若发生改写会被严格校验拒绝。
3. 生成 PDF 和逐页审计 Markdown；缓存仅放 `pdf-zh/assets/translation-cache/` 或显式 `--cache-dir`。
   刷新既有报告时先运行 `scripts/refresh_gartner_hc_terms.py`，再使用缓存重建，确保技术项名称和 `Analysis By:` 不受模型自由翻译影响。
4. 按 `references/qa-checklist.md` 运行 `scripts/qa_gartner_pdf_translation.py`，再人工抽查首页、图表页、表格密集页、横向附录和末页。
5. 运行 `scripts/qa_gartner_workspace_hygiene.py` 检查活动树；若发现 `.DS_Store`、报告根目录 `work/`、`pdf-zh` 根目录中间文件或旧缓存，先归档再交付。
6. 只有页数、页框、图片、链接、字体、marker、数字、术语、可复制文本和目录卫生均通过，才将报告 PLAN 标记完成。

按需读取：

- 翻译细节：[`references/pdf-translation-protocol.md`](references/pdf-translation-protocol.md)
- 目录和文件契约：[`references/pdf-translation-output-contract.md`](references/pdf-translation-output-contract.md)
- 报告术语策略：[`references/term-policy.md`](references/term-policy.md)
- 失败重试与恢复：[`references/failure-recovery.md`](references/failure-recovery.md)
- 最终 QA：[`references/qa-checklist.md`](references/qa-checklist.md)
