# 交接文档（HANDOVER）— coreldraw-hangtag / CDR AUTo

> 用途：换电脑、换会话、换人时，凭本文件 + 仓库即可完整接手，不依赖任何聊天上下文。
> 维护规则：每个 Phase 完成、重大决策变更、或仓库位置变动时，更新「当前状态快照」并 git 提交。

---

## 1. 一句话项目简介

把"AI 按 SKILL.md 现场操作 CorelDRAW 制作吊牌/卡片"训练成**标准化自动化插件**：任何 agent 或编排系统提供一份配置（或模板+替换表），自动产出 双份 .cdr 源文件（原样+转曲）+ 印刷 PDF + PNG 预览，全程 CMYK、X4/2020 双版本兼容。

## 2. 换电脑恢复工作（四步）

1. **拷贝整个仓库文件夹**（含 `.git`，U盘/网盘均可）到新机任意路径，例如 `C:\Users\<你>\Desktop\CDR AUTo\`；
2. **装环境**：64 位 Python 3.11+ → `pip install pywin32`（P1 后追加 `pip install fastmcp`）；
3. **确认 CorelDRAW**：本机装有 CorelDRAW 2020（或 X4，见版本说明）且能正常打开；
4. **素材迁移**：`templates/*/template.cdr` 等素材 .cdr 不在 git 里——从旧电脑网盘/U盘单独拷贝到同路径；
5. **验证**：运行
   `"C:\Users\Mayn\.workbuddy\binaries\python\versions\3.13.12\python.exe" "scripts\cdr_env_check.py"`
   输出 `"ok": true` 即接手完成；然后读 `PLAN.md` 末尾状态表继续训练。

## 3. 新会话接手指令（给 AI 的一句话）

> 读 `C:\Users\Mayn\Desktop\CDR AUTo\` 下的 PLAN.md 和 TRAINING_LOG.md，按当前状态继续训练。

AI 应先读 PLAN.md（计划+状态）→ TRAINING_LOG.md（历史轮次）→ 再行动，避免重复工作。

## 4. 目录结构

```
CDR AUTo/
├── PLAN.md              # 计划书（单一事实源：需求/计划/进度/验收标准）
├── RESEARCH.md          # 可行性调研（三形态评估、7 条约束、开源项目）
├── TRAINING_LOG.md      # 训练日志（每轮记录：目标/结果/问题/修复/提交号）
├── CHANGELOG.md         # 版本变更记录（semver）
├── SKILL.md             # AI 技能手册（WorkBuddy skill 机制用）
├── references/
│   └── api_gotchas.md   # CorelDRAW COM 实测陷阱 20 条
├── scripts/
│   ├── hangtag_generator.py   # 核心：参数化生成器（CLI）
│   ├── cdr_env_check.py       # 环境自检
│   ├── example_card.json      # 示例配置
│   └── hangtag_result.json    # 最近一次运行结果（自动生成）
├── configs/             # 测试/训练用配置
├── AGENTS.md            # AI 接入入口（根目录，AI 优先读取）
├── docs/                # 项目文档：TODO/DESIGN/overview/architecture/user-guide/development/component-api
├── templates/           # 模板库：index.json+meta.json 入 git；template.cdr 素材不入 git（换电脑单独拷贝）
├── groups/              # （P1）可复用群组元素库（水洗标/花纹）
└── outputs/             # 生成产物（git 忽略）
```

## 5. 当前状态快照

- **日期**：2026-09-29 ｜ **最新提交**：见 `git log`（PLAN.md v1.1 已入库）
- **Phase 进度**：P0 ✅ → P1（模板体系与核心闭环）⬜ 待模板素材 → P2 MCP 化 → P3 健壮+批量 → P4 分发
- **已验证能力**：COM 连接、字体枚举（430 个）、文字转曲、群组递归遍历、参数化生成、越界防护（7/7）
- **待收口**：`OpenDocument → 修改 → Save()` 存回副本的 .cdr 保存链路（高置信，实验被中断）；图片 CMYK/灰度转换 API 实测
- **待用户提供**：1-2 个真实模板（含异形/群组/图片最佳）+ 替换文字表；模板规范三项拍板（占位命名/刀线识别/安全字体清单）

## 6. 环境依赖（新机器核对清单）

- Windows 10/11，**保持登录的桌面会话**（无头服务器不可用）
- CorelDRAW Graphics Suite 2020（本机验证 14.0 COM）或 X4；业务双版本目标 X4 + 2020
- 64 位 Python 3.11+（WorkBuddy 受管 Python 即可）；pywin32（P1 后加 fastmcp）
- 字体：模板所用字体在生成机上必须存在（用 `FontList` 核对）

## 6b. 双目录同步（防分叉）

- **源（git）**：`C://Users//Mayn//Desktop//CDR AUTo\`——一切改动在此进行
- **分发副本**：`C://Users//Mayn//.workbuddy//skills//coreldraw-hangtag//`（WorkBuddy skill 触发机制用）
- 同步：改完 CDR AUTo 后运行 `scripts\sync_to_workbuddy_skill.cmd`

## 7. 关键技术结论索引（避免重新踩坑）

- 字号必须 `Text.Story.Size`；`FontProperties.Size` 静默无效 → 全表见 `references/api_gotchas.md`
- `.cdr` 的 SaveAs(路径) 是类型库死路；**突破口 = 复制副本 → OpenDocument → 修改 → Save()**（继承模板格式 → X4 兼容）
- 文本内 `\n` 不换行 → 多条目拆独立文本对象
- CorelDRAW 进程必须关沙箱访问；`app.Quit()` 禁止调用
- Weld 等接口类型参数用 `_oleobj_.Invoke` 绕过

## 8. 术语与形态（详见 PLAN.md 第二节）

CLI 工具（引擎，已有）→ Skill（AI 手册+脚本，已有）→ **MCP 插件/连接器**（P2 目标形态）。对外统称：**CDR 吊牌自动化插件**。
