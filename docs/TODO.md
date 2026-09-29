# TODO — 任务、优先级与进度

> 切换 AI / 重启会话：读本文件即可继续开发，无需重读全部项目。
> 状态：✅ 完成 ｜ 🔬 进行中 ｜ ⬜ 待办 ｜ ⏸ 暂缓
> 最后更新：2026-09-29（R7 完成后）

## 当前进度总览

- P0 基础 ✅ ｜ **训练 R1-R7 ✅** ｜ R8-R11（训练收尾）⬜ ｜ P2 MCP 化 ⬜ ｜ P3 批量 ⬜ ｜ P4 分发 ⬜
- 完成度：**总体约 40%**（引擎核心链路已完备并经真实模板验证）

## 🔬 进行中

- （无——等用户确认语义命名后进入 R8）

## ⬜ 待办：训练收尾（R8-R11，当前优先级最高）

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| R8 | 读取修复：文字字体/字号 | 高 | `FontProperties` 在真实模板文字上异常 → 换 `Story.FontProperties` / `Text.Font` 逐对象探测；位图颜色模式换 `Bitmap` 属性重探 |
| R9 | NOTES 注释层识别与跳过 | 高 | 在现有模板加 NOTES 图层模拟验证：枚举/替换/导出时跳过该图层 |
| R10 | 语义正式批次 | 高 | 按 meta.json 已预填的 10 字段语义名（product_name/brand_title_f 等）出真实批次：双 .cdr + PDF/PNG + 读图验收 |
| R11 | 缺孔卡确认 | 低 | 8 张卡实测 7 个 4mm 圆孔——用户对照模板确认哪张缺孔/是否故意 |

## ⬜ 待办：P2 MCP 化（训练完成后）

- fastmcp 安装与 server.py（4 工具：env_check / list_fonts / fill_template / generate_hangtag）
- mcp.json 合并配置 + WorkBuddy 连接器信任
- 串行锁（COM 单实例）+ 三类故障注入测试 + 超时保护
- 参考架构：CubicDev1/corel-mcp（14 工具精简目录）、wuguirongsg/coreldraw-mcp

## ⬜ 待办：P3 / P4

- P3 批量：`--batch` 多配置循环 + 汇总报告；`ShapeRange.StepAndRepeat` 阵列拼版能力
- P4 分发：setup.py 一键装依赖 + mcp.json 自动合并；GitHub 公开/私有策略确认

## ⏸ 暂缓 / 待用户输入

- 真实替换文字表（用户随时给，随时出真实批次）
- 语义字段命名核对（已预填 10 字段，见 `templates/demo_mixed_v1/meta.json`）
- GitHub 仓库公开性（当前 private）

## ✅ 已完成里程碑（摘录，全文见 CHANGELOG.md / TRAINING_LOG.md）

- R1 基线验证 ｜ R2 越界防护（7/7） ｜ **R3 SaveAs 版本参数打通（.cdr 程序化保存 + 本机=X4 真相）** ｜ R4 模板分析（6 套 12 张） ｜ R5 孔位规则 + PositionX/Y 陷阱 ｜ R6 替换引擎 ｜ R7 引擎强化（10/10）
- 模板库：登记器 + demo_mixed_v1 入库（meta.json 语义预填）
- 文档体系：PLAN/RESEARCH/TRAINER_GUIDE/HANDOVER/CHANGELOG/TRAINING_LOG/AGENTS/DESIGN/user-guide/development/component-api
