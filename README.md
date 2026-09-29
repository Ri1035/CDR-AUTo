# CDR AUTo — CorelDRAW 吊牌自动化插件

![version](https://img.shields.io/badge/version-v1.4.0-blue) ![stage](https://img.shields.io/badge/stage-训练完成%20R1--R11%20%7C%20P2%20MCP化待启动-orange) ![platform](https://img.shields.io/badge/platform-Windows%20%2B%20CorelDRAW%20X4%2F2020-lightgrey) ![license](https://img.shields.io/badge/data-private-yellow)

> **当前阶段记号**：训练阶段 R1-R11 **全部完成** ✅（v1.4.0）→ 下一阶段 P2 MCP 化 ⬜

用 Python + pywin32 通过 COM 驱动本机 CorelDRAW，实现吊牌/售后卡/服饰卡的**自动化生产**：一份配置（或模板+替换表）自动产出 **双份 .cdr 源文件（原样+转曲）+ 印刷级 PDF + PNG 预览**，全程 CMYK、X4/2020 双版本兼容。

## ✨ 核心能力（全部经真实模板验证）

| 能力 | 说明 |
|---|---|
| 🏭 纯生成 | JSON 配置 → 卡片绘制（文字/线/矩形/圆/字段线/复选框/打孔），越界自动防护 |
| 📋 模板填充 | 语义字段填充（`product_name=田园土鸡蛋`），内容/规范化/#序号三模式匹配，越界自动缩放 |
| 🗂️ 模板登记 | 一条命令"摸清"模板构成 → 卡组聚类 + 字段清单 + 资产档案 + 孔位策略 |
| 🔀 多模板融合 | 跨模板摘取元素组装新吊牌（卡型+照片窗+洗涤结构融合，见 R11 检验件） |
| 💾 双源文件 | 原样可编辑 .cdr + 全文转曲 .cdr（`SaveAs(Version:1400)` X4 格式） |
| 🖨️ 印刷输出 | CMYK、文字转曲 PDF + PNG 预览 |
| 📝 注释层 | NOTES 图层自动跳过（枚举/替换/导出全忽略） |
| 🔤 字体核验 | 设备字体枚举（430+），缺失即告警 |

## 🚀 快速开始

```bash
# 0. 环境：Windows + CorelDRAW X4/2020 + 64位 Python 3.11+
python -m pip install pywin32

# 1. 环境自检
python scripts/cdr_env_check.py

# 2a. 纯生成（配置见 scripts/example_card.json）
python scripts/hangtag_generator.py --config configs/demo_mapping.json --out 输出目录

# 2b. 模板填充（语义字段）
python scripts/hangtag_fill.py --template 模板.cdr --meta templates/<id>/meta.json --values 字段值.json --out 输出目录 --name 吊牌名

# 3. 模板入库（自动分析生成结构档案）
python scripts/template_register.py --template 新模板.cdr --id 新模板id
```

## 📚 文档导航

| 文档 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | **AI 接入入口（优先读取）** |
| [docs/TODO.md](docs/TODO.md) | 任务与进度（切换会话直接读这个继续） |
| [PLAN.md](PLAN.md) | 计划书 v1.4（需求/阶段/工程规则/状态） |
| [docs/DESIGN.md](docs/DESIGN.md) | 视觉与印刷规范（CMYK/字体/孔位/注释层） |
| [docs/user-guide.md](docs/user-guide.md) | 使用手册（无需读代码） |
| [docs/development.md](docs/development.md) | 开发方式与回归测试清单 |
| [docs/architecture.md](docs/architecture.md) | 架构与数据流 |
| [docs/component-api.md](docs/component-api.md) | 脚本 API 参考 |
| [references/api_gotchas.md](references/api_gotchas.md) | CorelDRAW COM 实测陷阱 21+ 条 |
| [TRAINER_GUIDE.md](TRAINER_GUIDE.md) | 训练者规范（合作者必读） |
| [HANDOVER.md](HANDOVER.md) | 换电脑/换会话交接 |

## 🧪 训练记录（R1-R11）

| 轮次 | 成果 |
|---|---|
| R1-R2 | 基线验证 + 越界防护（7/7 告警） |
| R3 ★ | **SaveAs 版本参数突破**：`SaveAs(path, StructSaveAsOptions{Version:1400})` 打通 .cdr 程序化保存；本机版本真相（实装 X4） |
| R4-R5 | 真实模板全结构解析（6 套 12 张）+ 孔位规则定论 + **PositionX/Y 参考点陷阱**（改用 LeftX/BottomY） |
| R6-R7 | 模板填充引擎 + 规范化匹配 + 越界自动缩放（10/10 命中） |
| R8-R9 | 读取修复（字体/字号/位图模式）+ NOTES 注释层跳过 |
| R10 | 语义正式批次（6 套 12 张读图验收通过） |
| R11 ★ | **三模板融合批次**：三套模板元素融合一套吊牌（用户检验件） |

## ⚠️ 已知约束

- 需 Windows + 交互式桌面会话（无头服务器不可用）
- COM 单实例 → 任务串行
- 模板素材（.cdr）不入 git，另行走网盘同步
