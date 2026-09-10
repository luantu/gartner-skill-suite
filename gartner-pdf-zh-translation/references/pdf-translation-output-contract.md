# 输出契约

对每个 `{slug}`：

```text
01-extract/{slug}/
├── {slug}-PLAN-extract.md
├── {slug}-extraction.md
├── {slug}-source-manifest.md
├── {slug}-translation-qa.md
├── pdf-zh/
│   ├── {source-stem}-pdf-zh.pdf
│   ├── {source-stem}-translation.md
│   └── assets/
│       ├── HiraginoSansGB-W3.ttf
│       └── translation-cache/translations-grouped.json
└── assets/                         # 原始提取、图和 OCR 中间件
```

`00-source/` 不放翻译或脚本。正式 `pdf-zh/` 根目录只放 PDF 和审计稿；JSON、字体、渲染图和临时脚本放 `assets/`、`work/` 或 `_archive/`。源 stem 保留 Gartner `ndx` 编号，不重命名。

唯一的 `HiraginoSansGB-W3.ttf` 必须使用已修正 ToUnicode 映射的字体版本；旧字体、旧缓存和历史渲染件归档，不与当前版本并列。
