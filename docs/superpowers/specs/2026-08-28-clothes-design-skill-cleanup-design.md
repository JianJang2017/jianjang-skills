# Clothes Design Skill 脚本清理与优化设计

## 目标

将 `clothes-design-skill` 收敛为服装设计交接与确定性制版技能，删除已经被平台能力替代或用户明确不再需要的脚本，保留裁片、拼装、规格、图片逆向分析和验证能力，并恢复完整测试闭环。

## 删除范围

1. 删除 PDF 链路：
   - `scripts/pattern_pdf.py`
   - `tests/test_pattern_pdf.py`
   - `draw_pattern.py` 的 `--pdf` 参数、动态导入和输出逻辑
   - `validate_skill.py` 的 `pattern-pdf` 门禁
   - SKILL、README、合同和工程参考中的 PDF 交付说明
2. 删除本地生图链路：
   - `scripts/generate-image.js`
   - `scripts/qwen-image-generator.js`
   - `scripts/bl-image-generator.js`
   - `models.json`
   - 与这些入口有关的说明和过期引用
3. 删除 Python 缓存目录 `scripts/__pycache__/`，并确保 `.gitignore` 忽略 `__pycache__/` 与 `*.pyc`。
4. 删除已失效的旧示例逐字节比对测试 `tests/test_examples_current.py`，改为验证当前 `examples/crossover-blouse-a` 的结构、SVG 可解析性、同源裁片数量和必需文档。

## 保留范围

- `calculate_garment.py`：尺码、用量与成本估算。
- `pattern_drafting.py`：确定性裁片几何事实源。
- `pattern_geometry.py`：毛样、刀口、拓扑和缝合关系校验。
- `draw_pattern.py`：完整单画布 SVG 技术示意。
- `pattern_assembly.py`：同源裁片拼装示意。
- `reverse-prompt.js`：服装图片外观分析；输出不再声称可直接交给已删除的生图脚本。
- `styles.js`：供逆向分析使用的风格词表；删除对不存在脚本的注释。
- `svg2png.sh`：SVG 人工验收用的可选预览转换。
- `validate_skill.py`：调整后的技能门禁入口。

## 平台生图策略

效果图继续属于技能交付能力，但不再由技能目录维护多供应商 API/CLI 路由。执行环境有图像生成工具时调用平台内置能力；不可用时明确降级为 `CONDITIONAL`，不伪造效果图，也不要求本地 Node 生图脚本。

## 文档优化

- SKILL 入口只保留高风险边界和核心工作流，删除 PDF 与本地供应商细节。
- `package.json` 更新为当前版本和职责描述；若逆向分析仍需要 ESM，则保留最小 `type: module` 与 Node 版本约束。
- 工业交付合同统一使用“单画布 SVG 技术示意，可无损放大但不可直接裁剪”。
- `prompt-framework.md` 只承担效果图提示词指导，不再引用已删除的生成脚本。

## 验收条件

- 仓库内不存在被删除脚本及其有效引用。
- `draw_pattern.py` 只接受 SVG 输出，缺少 `--output` 时清晰报错。
- 当前古风样例仍包含样衣图、裁片 SVG、拼装 SVG、制衣流程、规格和 README。
- 裁片 SVG 与拼装 SVG 可解析，包含 6 种/7 片交领上衣裁片关系。
- `validate_skill.py` 全部门禁通过。
- `python3 -m unittest discover -s clothes-design-skill/tests -p 'test_*.py'` 无失败。
- 不恢复用户主动删除的历史示例文件。

## 非目标

- 不改变交领上衣裁片几何、尺寸公式或制衣流程。
- 不新增 DXF/PLT、工业放码、真实排料或生产纸样能力。
- 不合并、推送或清理其他技能及用户未提交的工作。
