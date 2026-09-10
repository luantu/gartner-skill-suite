# HC 双曲线对比：可调整 HTML 与飞书画板

## 适用与交接

用户提供两份可比 HC，并要求双曲线、技术迁移图、可调整 HTML 或将对比图写入画板时，必须交付可调整 HTML。沿用 `annual-hc → presentation`，呈现参数为 `presentation_format=hc-editor`；不新建分析入口。只有两份 PDF 时，先由 `gartner-report-extraction` 建立底表，再由 `gartner-hype-cycle-analysis` 完成技术映射与比较。

两份报告须为同一 HC 系列、年份递增且范围可比。若是同年不同系列或范围改变，明确不可比项，不画未经证实的年度迁移箭头。单年任务不进入双曲线流程。

方法来自 Gartner-HC-Editor 的交付编辑器：原生 SVG + 单文件 HTML；复用标签、多选、拖动、动态引导线、撤销／恢复、布局保存／载入与 SVG／PNG 导出。仓库模板只保留通用交互外壳，不带原报告数据、企业判断、人员或文档地址。

## 1. 从两份 HC 建立图表数据

在任务工作区保存 `hc-comparison-data.json`，逐项记录：

- 报告：标题、年份、报告 ID、来源文件、曲线图物理页码及 profile 页码。
- 技术：稳定 `technology_id`、各年英文原名、各年阶段、Benefit Rating、Years to Mainstream Adoption、Market Penetration、Maturity（源文档有则保留）。
- 映射：持续、新增、移出、改名、拆分、合并或不可比；非同名匹配记录证据，不能仅按字符串相似度连接。
- 图形定位：各年原图归一化位置、定位依据（原图点位读取／阶段示意）、标签初始位置。图形坐标是排版数据，不能当作 Gartner 定量评分或迁移速度。

必须同时核对两年的技术全集。新增仅有后年点位，移出仅有前年点位；移出不等于失败或淘汰。改名可连接已确认同一实体，拆分／合并不得伪装为一对一迁移。

## 2. 生成双曲线 SVG

依据已验证底表生成 `hc-comparison.svg`，必要时使用 PDF 工具查看两份原图并核对点位。曲线保持同一坐标系，前一年浅色虚线、后一年深色实线，图例写实际年份；技术名保持英文原名。

- 两条曲线各自保留峰值、谷底、平台及阶段边界。能读取原图时按原图归一化，不把两张不同尺寸原图直接叠加。
- 只有阶段信息时，可以绘制阶段示意曲线，但图内必须写“阶段示意；位置不代表精确时间或量化分数”。不从阶段等级编造连续坐标变化证据。
- 同一技术前后年点位用迁移连线关联，方向是前年到后年；无精确点位证据时只表达阶段变化。新增、移出使用独立符号和明确图例。
- 符号形状映射各年自身的主流采用年限，不能把后年符号强加给前年；收益、关注优先级和迁移幅度也不可混用。
- 标签先自动避让，再允许用户拖动；技术点、曲线和标签分组，图例符号也可选中。较密集图可分领域／分面，并保留覆盖清单。
- SVG 使用真实 `<text>`，不能把全部文字转路径或整图栅格化。使用自包含的 path、line、circle、polygon、g、text/tspan 和内联样式；不带脚本、外链图片、外部字体、foreignObject 或外部 CSS。

### 编辑器 DOM 契约

完整 SVG 根节点有有限正尺寸 `viewBox`，包含 `id="axes_1"` 分组。以下是结构示意；真实交付需补全两年全部曲线、点位、技术和图例，不能把示意当作真实报告：

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600">
  <g id="axes_1">
    <g id="curve-before" data-hc-year="2024"><path d="M 80 470 Q 240 80 360 180 T 650 400 T 1080 300" fill="none" stroke="#98a2b3" stroke-dasharray="8 6"/></g>
    <g id="curve-after" data-hc-year="2025"><path d="M 80 460 Q 240 70 360 170 T 650 390 T 1080 290" fill="none" stroke="#2176c7"/></g>
    <circle cx="360" cy="170" r="5" fill="#2176c7"/>
    <path class="dynamic-leader" data-for="tech-a:2025" d="M 360 170 L 390 150" fill="none" stroke="#98a2b3"/>
    <text class="tech-label" data-name="tech-a:2025" data-point-x="360" data-point-y="170" x="390" y="150" font-size="14">Example Technology</text>
  </g>
</svg>
```

每个标签（包括 `.aux-label`）使用稳定、唯一的 `data-name`，例如 `technology_id:year`；不能用会改动的显示名称作为关联键。每个 `.tech-label` 有对应 `.dynamic-leader[data-for]`，锚点 `data-point-x/y` 与点位使用同一坐标系。所有可编辑几何组有稳定 ID、`data-geometry-editable="true"`；图例组另加 `data-editor-role="legend-symbol"`。避免在标签及其父组上叠加独立可拖动变换。

默认锁定数据几何，仅调整标签。编辑器解锁后可移动标记过的几何组；原实现不会自动更新所有迁移连线及数据锚点，若移动数据点或曲线，必须重新计算受影响锚点／迁移线并核对来源后才能导出。普通排版无需解锁数据几何。

## 3. 打包并调整 HTML

使用本 Skill 中的脚本（路径相对 Skill 根目录；产物放任务输出目录）：

```bash
python3 scripts/build_hc_editor.py \
  --svg /path/to/task/hc-comparison.svg \
  --output /path/to/task/hc-comparison-editor.html
```

脚本检查 SVG 结构并嵌入 `assets/hc-editor-shell.html`，拒绝覆盖已有 HTML。它不负责解析 PDF，也不能替代数据正确性检查。HTML 无 CDN／服务端依赖，可在浏览器直接打开。

操作顺序：拖动标签或空白区域框选 → 批量拖动／方向键微调（Shift 为 5 单位）→ 双击标签编辑文字 → 撤销／恢复或恢复初始布局 → 保存位置 JSON。继续编辑时打开同一 HTML 并载入位置 JSON。JSON 与原图成对保存，不能载入另一组报告。

完成排版后导出 SVG 和 PNG。画板发布必须使用浏览器导出的 `hc-comparison-edited.svg`，不能重新取初始 SVG 丢失调整。布局 JSON 保存的是位置和文本，不是源报告事实；技术名称编辑必须回核原名。SVG 导出保留真实文字、动态引导线样式和 viewBox，移除选区及命中辅助节点；PNG 为预览，不替代可调整 HTML 或画板矢量输入。

## 4. 使用 lark-cli 写入画板

调用时读取 `lark-doc` 的画板参考与 `lark-whiteboard` 的 SVG 更新参考，并以当前 `--help` 为准。HTML 留在本地；飞书接收 SVG 并转换画板内容，不执行 HTML 中的 JavaScript，也不继承本地编辑器的撤销或布局 JSON 功能。

用户只要求生成 HTML 时，到本地验收为止。用户要求写入飞书时使用明确指定的文档／画板；只读终稿不可写入。不得把示例 token 或上一个任务的文档作为发布目标。

### 新增到指定位置

先 fetch 定位最新插入块，将以下 XML 保存为任务目录中的 `insert-hc-board.xml`（SVG 与 XML 位于该目录，CLI 从该目录运行）：

```xml
<whiteboard type="svg" path="@./hc-comparison-edited.svg"></whiteboard>
```

```bash
lark-cli docs +fetch --doc "$TARGET_DOC" --scope outline --detail with-ids --as user
lark-cli docs +update --doc "$TARGET_DOC" --command block_insert_after \
  --block-id "$ANCHOR_BLOCK" --doc-format xml --content @./insert-hc-board.xml --as user
```

插入后重新 fetch 取得真实画板 token，不能把文档 token／block ID 当画板 token。

### 更新指定画板

先 fetch 文档确认目标画板，导出原节点备份；仅当用户已授权替换该画板全部内容时使用 `--overwrite`，因为它会清空整板再导入。无覆盖授权不自动重建；追加也须确认放置范围，避免双图叠加。

```bash
lark-cli whiteboard +export --whiteboard-token "$BOARD_TOKEN" \
  --output-type raw --output ./board-before.json --as user
lark-cli whiteboard +update --whiteboard-token "$BOARD_TOKEN" \
  --input_format svg --source @./hc-comparison-edited.svg \
  --idempotent-token "$UPDATE_KEY" --overwrite --as user
```

`UPDATE_KEY` 在同一次逻辑更新中固定且至少 10 字符；超时后先回读，确认是否已经成功，重试复用同一个 key。SVG 转画板可能重排文本或将部分元素转成图片；不能未经回读承诺所有元素可编辑。

### 发布回读

```bash
lark-cli docs +fetch --doc "$TARGET_DOC" --detail full --as user
lark-cli whiteboard +export --whiteboard-token "$BOARD_TOKEN" \
  --output-type raw --output ./board-after.json --as user
lark-cli whiteboard +export --whiteboard-token "$BOARD_TOKEN" \
  --output-type preview --output ./board-preview.png --as user
```

检查画板位置、两条曲线、年份、所有技术标签、符号、迁移方向、引导线和裁切；预览肉眼检查与原节点检查结合。若只导入一张整图图片，明确其可编辑性降级，保留 HTML + SVG 继续调整，不宣称画板原生元素全部可编辑。

## 5. 交付与验证

交付：`hc-comparison-data.json`、初始 SVG、可调整 HTML、用户调整后的布局 JSON 与 SVG、PNG 预览和 QA 记录；仅当执行飞书发布后增加文档链接、画板 token、回读及备份。实际报告数据、布局和画板回读留在用户任务目录，不提交到 Skill 仓库。

至少验证：

- 前后年报告可比性，技术集合覆盖及匹配证据；新增／移出不带虚构另一年度点位。
- 浏览器真实拖动标签、框选批量移动、文字编辑、撤销／恢复、保存／载入位置。
- 所有坐标有限；缩放后拖动不消失；载入位置后引导线立即更新；编辑文本时方向键不移动标签。
- 调整后的 SVG／PNG 导出成功，年份、标签、颜色、箭头与引导线一致，SVG 没有选框／透明命中层。
- 飞书发布则检查返回结果并回读预览及节点；未执行在线写入时单独注明，不用 CLI help 通过代替发布验证。
