# gartner-structured-presentation — 总体规划 (PLAN)

## 1. 目标

保留 HC/MQ 章节呈现，增加依据两份 HC 的可调整双曲线 HTML 和可选飞书画板输出。

## 2. 输入（依赖上游）

已验证的提炼底表、年度技术映射和证据；Gartner-HC-Editor 通用交互实现；用户指定的可写画板目标。

## 3. 产出（固定文件和结构）

- `references/hc-comparison-editor.md`：双年度数据、SVG DOM、HTML、画板发布与验证方法。
- `assets/hc-editor-shell.html`：不含原报告数据的单文件编辑器外壳。
- `scripts/build_hc_editor.py`：SVG 校验与 HTML 打包。
- `tests/`：合成 SVG 和打包回归测试。

## 4. 证据规则与约束

年度比较与呈现职责分离。坐标不当作定量分数；源报告和企业业务数据不进入 Skill 包；只读文档不可发布。原编辑器项目只读保留。

## 5. 完成条件（可验证）

合法双年度 SVG 可生成独立 HTML；错误输入拒绝；浏览器拖动、文本、布局保存载入、SVG/PNG 导出检查通过；路由与相对引用有效；画板写入按实时 CLI 与授权目标执行后回读。

## 6. 状态

2026-09-10：已纳入原编辑器通用外壳和可执行打包流程。画板命令依据 lark-cli 1.0.94 help 核对；本次未执行在线写入。具体报告仍需由 Agent 完成提炼、年度核对和 SVG 绘制，打包脚本不是 PDF 自动分析器。
