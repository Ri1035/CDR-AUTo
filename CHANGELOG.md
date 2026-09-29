# Changelog — coreldraw-hangtag（CDR AUTo）

格式参考 Keep a Changelog；版本号 semver。所有变更记录于 TRAINING_LOG.md，重要节点同步于此。

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
