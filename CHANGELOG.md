# Changelog — coreldraw-hangtag（CDR AUTo）

格式参考 Keep a Changelog；版本号 semver。所有变更记录于 TRAINING_LOG.md，重要节点同步于此。

## [1.4.0] - 2026-09-29

### Added
- **R8 读取修复**：字号=Story.Size（10/10）；字体名=Text.FontProperties.Name / Story.Font；位图模式=Bitmap.Mode（CMYK 基线=5）；Bitmap.ConvertTo 确认（图片 CMYK 化可直用）
- **R9 NOTES 注释层**：walk 增 skip_layers，枚举/替换/导出跳过 NOTES 图层
- **R10 语义正式批次**：fill 引擎 `--meta --values` 模式（语义字段名→替换），6 套 12 张读图验收通过
- **R11 融合批次**：三模板元素融合一套吊牌（2 张）读图验收通过（用户检验件）；就地融合路线（弃跨页剪贴板）
- 文档全集：AGENTS.md 入口 + docs/{TODO,DESIGN,overview,architecture,user-guide,development,component-api}
- GitHub 推送：Ri1035/CDR-AUTo（private）

### Fixed
- **R12 回归修复**：PublishToPDF/COM 文件参数**相对路径陷阱**（按 CorelDRAW 进程 cwd 解析）→ 全引擎入口 abspath 防御；相对路径回归测试自愈验证
- R4 遗留读取根因：Story 无 FontProperties（字体在 Text 层）

### 训练记录
- R1-R11 全过程见 TRAINING_LOG.md；总体完成度 70%，下一步 P2 MCP 化

## [1.3.0] - 2026-09-29

### Added
- 模板登记器 `template_register.py`：模板入库自动分析（卡组聚类/文字字段/资产/孔策略）→ meta.json 草稿 + index.json 索引
- 模板填充引擎 `hangtag_fill.py`：内容/规范化/#序号三模式匹配、中心恢复、越界自动缩放（R6/R7 验证 10/10）
- 模板库架构：templates/<id>/template.cdr + meta.json；语义字段预填（product_name/series_en 等 10 字段）
- R3：`SaveAs(path, StructSaveAsOptions{Version:1400})` 程序化保存 .cdr（X4）打通
- R5：坐标陷阱修复（PositionX/Y 参考点不固定 → LeftX/BottomY/RightX/TopY）+ 视觉裁决法

### Changed
- **素材与代码分离**：templates/*.cdr 不入 git（历史已重建清除），分享包纯规范+代码
- 本机版本认知修正：实装 CorelDRAW X4（build 14.0.0.701；目录名"2020"为历史命名）

## [1.1.0] - 2026-09-29

### Added
- 生成器新增**元素越界检测**：text/rect/ellipse/checkbox_row 等元素渲染前校验坐标与尺寸是否超出卡片范围，越界元素跳过并写入结果日志 `[越界]` 警告（训练轮 R2）。
- `hangtag_result.json` 新增 `warnings[]` 字段，供自动化上层系统采集。

### Fixed
- 示例配置 checkbox_row gap 28→12（原值导致第二项超出 50mm 卡宽）。

## [1.0.0] - 2026-09-29

### Added
- SKILL.md：触发词、前置条件、三步流程（自检→配置→生成）、配置字段参考、陷阱浓缩、自动化接入约定、分享方法。
- `scripts/hangtag_generator.py`：参数化吊牌生成器（JSON 配置驱动，2up/single 布局，CMYK，PDF+PNG+结果 JSON，退出码 0/2/3/4）。
- `scripts/cdr_env_check.py`：环境自检（Python 位数 / pywin32 / COM 连接 / gen_py 缓存自修复）。
- `scripts/example_card.json`：示例配置（50×90mm 吊牌，正/背面）。
- `references/api_gotchas.md`：CorelDRAW 2020 COM 实测陷阱 20 条。
- 基线验证通过：环境自检 ok → 示例生成 → 预览读图核对（训练轮 R1）。
