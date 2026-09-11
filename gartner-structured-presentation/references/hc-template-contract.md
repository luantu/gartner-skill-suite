# 标准 HC 双曲线模板与验收

用于两份可比 HC 的标准双年度总览。用户指定的 SVG 和 HTML 是视觉真值源；不能仅借用编辑器外壳再自行重画。内置 `assets/hc-two-track-template/standard.svg` 和 `editor.html` 来自经实际浏览器验收的模板，移除了业务数据；保留 1152×576 画布、两条不同轨道、两份图例及原标记路径。年份占位值在构建时更新。

## 输入与生成

`build_hc_template.py` 依赖 Python 3 与 lxml，不解析 PDF。输入为 `chart.points` 数组，每点具有 `technology_id`（稳定 slug）、`year`、英文 `name`、`stage`、`years`、`source_pixel.x/y`、`normalized_plot.x/y`。每项每年恰好一个点；已确认改名须共用稳定 ID。拆分、合并、不同系列或仅有阶段数据，不可直接输入此坐标投影器。

`--source-edges` 是经原图核验的曲线左端点、四条阶段边界、曲线右端点，严格递增，使用与 source_pixel.x 相同的坐标系；不是页面边界。两年源图须先归一化到相同坐标系。不能从另一个项目复制边界值。纵坐标投影到模板对应轨道；这种视觉投影不保留原图绝对高度，也不表示 Gartner 定量分数。

```bash
python3 scripts/build_hc_template.py \
  --data /path/to/hc-comparison-data.json --output-dir /path/to/chart-candidate \
  --subject 'Report Series' --years 2026 2027 \
  --source-edges 0 1 2 3 4 5 --shift-policy stage-relative-v1
```

示例边界仅说明参数个数，必须替换为原图核验值。输出 SVG、HTML 和 `hc-template-mapping.json`；拒绝覆盖已有输出。自定义同款模板可使用 `--svg-template`／`--html-template`；它必须保留 line2d_1..8、legend_1/2、text_42 及标记定义 ID。其他模板先建立显式角色映射，不静默退回自绘样式。

`stage-relative-v1` 是明确选择的显示政策：来源归一化位置不变则无迁移；跨阶段或横向位移 ≥0.12 为红色，≥0.035 为黄色，其余非零变化为蓝色。它不是 Gartner 的迁移评级、速度或定量评分，输出必须披露。其他政策先扩展并验证，不能沿用这个图例却改变颜色含义。

## 不变的视觉与语义

- 总览恰好两条年度轨道；2025／前一年为 #aebbcb 虚线，2026／后一年为 #263238 实线。保留模板曲线、轴线、阶段界线与两份图例的原有几何和样式。分面只作为补充。
- 迁移使用模板红 #e43d30、黄 #f2a900、蓝 #2176c7；稳定／新增 #475467；移出 #667085。不能换成收益或优先级配色。
- 年限沿用圆（不足 2 年）、方（2–5 年）、菱（5–10 年）、三角（超过 10 年）；前一年空心，后一年实心，按各年自己的采用年限取形状。
- 移出是年度集合变化，沿用灰叉及标签删除线。Obsolete before plateau 是采用状态，使用 † 和明确脚注，不映射灰叉或年限形状；未知采用状态拒绝生成，要求有依据的模板扩展。
- 技术点不能因排版而移动；同源位置不能因两轨道有间距而生成迁移线。标签可避让，标签引导线与年度迁移线分别检查。引导线不得通过放宽阈值获得“通过”。

## 排版、编辑与验收

在浏览器打开候选 HTML，用 `scripts/arrange_hc_template_labels.js` 的 `async(page)` 函数执行真实字体测量及标签避让，生成调整后 SVG／PNG／布局 JSON。该排版器只适用于内置同款画布，调整其他模板前复核可用区域。它不移动数据点。导出版本取代初始版本用于发布；将导出 SVG 嵌回交付 HTML，使打开、重置和再次导出均对应验收布局。

```bash
python3 scripts/validate_hc_template.py \
  --svg /path/to/hc-comparison.svg --mapping /path/to/hc-template-mapping.json
```

验收器重新依据输入与模板构建基准，逐项比对两轨／图例／符号／颜色／点位／迁移线，并验证来源哈希与覆盖，允许标签改变位置。它不替代浏览器视觉验收：检查文字重叠、长引导线、裁切，真实测试拖动、多选、框选、文字编辑、输入框方向键、撤销／恢复、保存／载入及 SVG／PNG 导出。固定数据几何默认锁定，但图例仍可操作；导出不能含选框或命中辅助层。

`build_hc_editor.py` 是通用 DOM／安全打包器；允许自包含本地样式以重新打开浏览器导出，拒绝外部资源、脚本和危险 CSS。它的通过不能替代本模板验收器。`validate_hc_delivery.py` 只验飞书文档结构，不能把 token 存在当作画板质量通过。

## 飞书同步

发布当前验收 SVG，记录上传输入哈希；更新已有画板前 fetch 定位并备份 raw，按现有授权复用同一画板。发布后实际导出 raw 与 preview，与验收图比对曲线、颜色、两份图例、全部标签及裁切，并清点原生节点与降级图像。飞书可能将曲线或符号转为嵌入 SVG 图像，视觉正确不等于全部可原生编辑。完整编辑能力由 HTML／SVG 提供。

线上附件若仍包含旧图，同步图表包并回读下载哈希，避免正文画板和下载编辑器不一致。只读样例和其他文档不得成为写入目标。
