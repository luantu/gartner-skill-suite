# Gartner 路由、参数与交接契约

## 入口判定

| 用户目标 | `mode` | 主 Skill |
|---|---|---|
| PDF 字段提炼与页码锚点 | `extract` | `gartner-report-extraction` |
| 中文保真 PDF 与逐页 QA | `translate-pdf` | `gartner-pdf-zh-translation` |
| 单份 HC 解读 | `single-hc` | `gartner-hype-cycle-analysis` |
| 同一 HC 两年度比较 | `annual-hc` | `gartner-hype-cycle-analysis` |
| 单份 MQ 解读 | `single-mq` | `gartner-magic-quadrant-analysis` |
| 同一 MQ 多年度比较 | `annual-mq` | `gartner-magic-quadrant-analysis` |
| HC 与 MQ 交叉洞察 | `cross-insight` | `gartner-hc-mq-insight` |
| 章节和表格呈现 | `presentation` | `gartner-structured-presentation` |

一次请求选择一个主模式。完整研究套件可以串联多个模式，但每个阶段仍分别验收。

## 交接参数

```yaml
report_type: HC | MQ | MIXED
mode: extract | translate-pdf | single-hc | annual-hc | single-mq | annual-mq | cross-insight | presentation
source_reports:
  - path: /absolute/path/report.pdf
    year: 2026
    gartner_id: G00000000
    pages: 100
output_root: /absolute/path/to/deliverable
target_vendor: null
domain_profile: null
external_evidence: false
feishu_output: false
evidence_status: complete | partial | blocked
```

## 阶段交接

- `extract` 输出：输入清单、报告元数据、完整字段底表、页码锚点和证据缺口。
- `translate-pdf` 输出：中文 PDF、逐页审计 Markdown、翻译 QA；不输出分析结论。
- `single-*` / `annual-*` 输入：可回读的原始 PDF 或已验证提炼底表；输出独立分析和证据映射。
- `cross-insight` 输入：已通过检查的 HC 与 MQ 分析；缺少一侧时只输出观察项。
- `presentation` 输入：已验证的分析或交叉洞察；只改变呈现结构，不改写证据和结论。

`evidence_status=blocked` 时停止生成依赖该证据的结论；`partial` 时明确标出缺口和不可比范围。

## 资源归属

| 资源 | 归属 |
|---|---|
| 分析输出、证据、HC/MQ、交叉洞察、文本翻译和飞书协议 | `gartner-analysis/references/analysis-*.md` |
| PDF 翻译版式、术语、失败恢复、QA | `gartner-pdf-zh-translation/references/` |
| 章节呈现模板 | `gartner-structured-presentation/references/presentation-contract.md` |
| HC 年度映射与分析师小结 | `gartner-hype-cycle-analysis/references/analyst-summary-guide.md` |

共享规则只保留一份；专项 Skill 通过明确路径读取，不复制协议。
