# QA 清单

自动检查：

1. `pdfinfo` 或 PyMuPDF：源/译物理页数相等；逐页 `rect`、rotation 相等。
2. PyMuPDF：图片数量和链接数量逐页可核对；关键 URI 不缺失。
3. `get_page_fonts()`：每个含中文的页能找到嵌入 CJK TrueType 字体。
4. 审计稿：页锚点从 1 到物理页数连续且唯一，文本非空；无 `ZZP`、`ZZEND`、`ZZTERM` 残留。
5. 数字、年份、Gartner ID、Figure/Table 编号和保护术语按页抽样比对。
6. 逐页统计源 PDF 与中文 PDF 的 `Analysis By:` 数量；任何“分析师：”“分析者：”“分析人员：”“分析人：”“分析作者：”均直接判失败。
7. 以源 PDF 中每个 `Analysis By:` 前一项作为 profile 技术项名称，与中文 PDF 对应页逐项精确比对；英文名称缺失或被中文化均直接判失败。

人工抽查：首页、报告元数据页、曲线图页、Priority Matrix、至少一页 profile、横向附录和末页。检查重复、残句、断词、溢出、遮挡、tofu、页脚对齐和链接可点击性。任何失败都记录页码和原因，不得以“整体可读”代替修复。
