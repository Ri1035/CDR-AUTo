# AGENTS.md — AI 接入入口（项目说明书）

> **AI 接入本项目时优先读本文件**。读完后按指引继续阅读，即可在不依赖聊天上下文的情况下接手工作。
> 仓库：`C:\Users\Mayn\Desktop\CDR AUTo\`（本地 git 源）｜ 详细文档在 `docs/` 子文件夹。

## 1. 项目是什么

**CDR 吊牌自动化插件**：用 Python + pywin32 通过 COM 驱动本机 CorelDRAW（X4，build 14.0.0.701），实现吊牌/售后卡/服饰卡的自动化生产：

- **纯生成管线**：配置 JSON → 绘制 → 校验 → 双 .cdr（原样 + 转曲）→ 印刷 PDF + PNG 预览
- **模板管线**：已有模板 + 文字替换表 → 同上（推荐，业务主路线）
- 全程 CMYK、X4 版本兼容、自动化无人工干预

## 2. 三层形态（详见 docs/architecture.md）

| 层 | 名称 | 状态 |
|---|---|---|
| 引擎层 | CLI 工具（scripts/*.py） | ✅ |
| 手册层 | Skill（SKILL.md + api_gotchas.md） | ✅ |
| 插件层 | MCP Server（fastmcp 包装） | ⬜ 训练完成后做 |

## 3. AI 接入三步（必读顺序）

1. **`docs/TODO.md`** —— 当前任务与进度（做到哪了、下一步是什么）
2. **`PLAN.md`** —— 计划书 v1.4（需求清单 N1-N10 / 阶段计划 / 工程规则 / 状态与完成度）
3. 按需深入：`docs/TRAINER_GUIDE.md`（训练循环规范+红线）、`references/api_gotchas.md`（21 条 COM 陷阱）、`docs/component-api.md`（脚本 API）

**接手后第一件事**：核对 PLAN.md「八、当前状态」的完成度与 TODO.md 是否一致，然后继续下一个未完成项。

## 4. 红线（违反 = 事故，全文见 docs/TRAINER_GUIDE.md 第 4 节）

- ❌ 不触碰用户原始文件（一律复制副本操作）
- ❌ 不调用 `app.Quit()`；不关用户已打开的命名文档
- ❌ COM 脚本必须关沙箱运行 + Windows 盘符路径
- ❌ 指令存在两种以上解读时，先复述理解请用户确认再执行
- ❌ 不重写/删除 git 历史（迭代数据是研究资料）；`templates/*/template.cdr` 素材不入库

## 5. 工程规则速记（v1.4）

- 单一项目源 = 本仓库；WorkBuddy skill 目录是分发副本（同步：`scripts/sync_to_workbuddy_skill.cmd`）
- 每轮训练 = 定目标 → 写验收 → 执行 → 验证 → TRAINING_LOG 记录 → git 提交
- 训练难题优先网上资源求解（已验证有效：SaveAs 版本参数即由此突破）
- 本机 = CorelDRAW **X4**（14.0.0.701）；2020 为业务另一端，向下兼容待回归
