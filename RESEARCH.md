# 可行性调研 — coreldraw-hangtag 训练为自动化插件

> 调研日期：2026-09-29 ｜ 结论先行：**可行，推荐「CLI 编排 → MCP 化」两阶段路线**，总体风险中低。

## 1. 目标形态定义

"训练为自动化插件"在本项目语境下有三种可落地形态：

| 形态 | 说明 | 调用方 |
|---|---|---|
| A. CLI 编排件 | 纯命令行 + JSON 配置 + 退出码 + 结果 JSON | n8n/PowerShell/定时任务/CI，或 AI agent 按 SKILL.md 调用 |
| B. MCP Server | 把能力包装成 MCP 工具（`generate_hangtag(config_json)`），注册进 MCP 客户端 | WorkBuddy / Claude Desktop / Cursor / Cline 等任意 MCP 客户端 |
| C. HTTP 服务 | fastmcp streamable-http 或 FastAPI 包一层，局域网多客户端共享 | 网页/小程序后端、多机调度 |

## 2. 三条路径可行性评估

### 形态 A：CLI 编排件 —— ✅ 已达成（基线能力）

- 生成器已满足：纯 CLI 无交互（`--config --out`）、退出码 0/2/3/4、`hangtag_result.json` 机读、幂等覆盖、越界防护告警（R2）。
- 调用示例（任何编排系统可直接嵌入）：
  `python hangtag_generator.py --config card.json --out out_dir` → 解析 result JSON。
- 剩余缺口：无批量模式（多配置循环）、无异常注入回归。→ 归入训练计划 Phase 2/3。

### 形态 B：MCP Server —— ✅ 可行（推荐主攻方向）

- 技术栈：`fastmcp`（pypi 可达，最新 4.0.10，未安装需 `pip install fastmcp`）+ 现有 pywin32。
- 参考实现：社区 `wuguirongsg/coreldraw-mcp`（本机留有部署资料 `E:\WK\cdr\mcp\coreldraw-mcp-deploy\references\install.md`），其 stdio 配置模式、客户端信任流程（WorkBuddy 连接器「信任」）、排错表均可直接复用。
- 包装面极小：只需 2-3 个工具——
  1. `env_check()` → 环境自检（包装 cdr_env_check.py）
  2. `generate_hangtag(config_json, out_dir)` → 包装生成器主流程
  3. `list_examples()` → 返回示例配置（可选）
- 传输：stdio（单客户端，最稳）起步；streamable-http 留待形态 C。
- 风险：fastmcp 4.x API 与社区资料（基于 2.x 时代）存在版本差异——实施时以 fastmcp 4.x 官方文档为准，包装层很薄，预计影响可控。

### 形态 C：HTTP 服务 —— ⚠️ 可行但受硬约束，暂缓

- 技术上 fastmcp 支持 streamable-http；但见第 3 节并发与桌面会话约束，单机单 CorelDRAW 实例下收益有限。建议 MCP stdio 跑稳后再评估。

## 3. 关键技术风险与约束（硬约束 = 无法绕过）

| # | 约束/风险 | 等级 | 影响 | 对策 |
|---|---|---|---|---|
| 1 | **交互式桌面会话必需**：COM 驱动 CorelDRAW 需要可视桌面，Windows 服务/Session 0 后台场景会失败 | 硬约束 | 无法部署到无头服务器/纯后台容器 | 部署在带桌面的办公机/工作站；远程桌面会话断开后进程可能受限，需保持登录 |
| 2 | **COM 单实例串行**：同一台机器所有调用共享一个 CorelDRAW 进程，并发请求互相污染 | 硬约束 | 并发=数据竞争 | MCP 工具内加全局锁（threading.Lock）/队列串行；文档注明"单任务独占" |
| 3 | **CorelDRAW 弹窗阻塞**：许可、更新、崩溃恢复对话框会卡住 COM 调用 | 中 | 自动化中途挂起 | 训练阶段加超时（生成器外层 timeout）；首次运行人工确认一次设置 |
| 4 | **版本兼容**：2020=14.0 类型库已验证；更高版本 ProgID 相同但行为未回归 | 中 | 分发到他人机器可能行为差异 | env_check 输出版本号；SKILL 注明"2020 验证，更高版本需回归" |
| 5 | **gen_py 缓存绑定 Python**：换 Python 版本/环境迁移需重建 | 低 | 新机器首跑报 CLSIDToClassMap | 生成器已内置自动清理重试（R1 已验证）；env_check 给出提示 |
| 6 | **字体依赖**：微软雅黑/Arial Windows 自带 | 低 | 几乎无 | 无需处理 |
| 7 | **导出耗时**：5-15 秒/次，批量时线性累加 | 低 | 批量任务时长 | 批量模式汇总报告显示进度；不设单次硬超时太短 |

## 4. 现有资产盘点（调研时点，git bbece90）

- ✅ 生成器（参数化、越界防护、CMYK、PDF/PNG/结果 JSON、退出码）—— R1/R2 验证通过
- ✅ 环境自检（含 gen_py 自修复）
- ✅ SKILL.md + 陷阱清单 20 条 + 示例配置 + 越界测试配置
- ✅ git 版本管理 + CHANGELOG + TRAINING_LOG
- ⬜ fastmcp 依赖未安装（pypi 可达）
- ⬜ MCP server 包装层未写
- ⬜ 批量模式、异常注入回归未做

## 5. 结论与推荐

1. **可行性成立**：形态 A 已是事实标准；形态 B 是"自动化插件"的最优落点，包装成本低（预计一个 ~100 行的 server.py）、复用社区成熟部署模式。
2. **推荐路线**：Phase 1 MCP 化（stdio 单工具入口）→ Phase 2 健壮性（异常注入+串行锁）→ Phase 3 批量 → Phase 4 分发打包（对方机器一键 setup 脚本：装 pywin32/fastmcp + 生成 mcp.json 合并配置）。
3. **不推荐**：跳过 MCP 直接做 HTTP 多客户端服务（受约束 1/2 限制，收益不成比例）。
4. 分发边界提醒：插件依赖对方机器安装有 CorelDRAW 2020+ 与合法许可，这是产品前提而非工程问题。

---

## 6. 二轮补充调研（2026-09-29 下午）：SaveAs 版本参数官方出路 ★★★

### 6.1 突破发现

`Document.SaveAs(FileName, StructSaveAsOptions)` 是**双参数**方法——此前 pywin32 报"类型不匹配"的根因是只传了字符串、缺少第二个 options 参数导致整个签名不匹配，并非 FileName 本身无解。

实测（本机 2020/14.0）：
- ✅ `app.CreateStructSaveAsOptions()` 工厂方法存在（返回 IDrawStructSaveAsOptions）
- ✅ `doc._oleobj_.Invoke(SaveAs_dispid, 0, 1, True, path, opt._oleobj_)` 双参调用**通道打通**（无异常返回）
- ⬜ 待收口：正确设置 `opt.Filter = cdrCDR`、`opt.Version = cdrVersion14` 枚举值（可从 gencache 类型库模块 dump 常量）后验证文件真实落盘（首测枚举值乱设 789，文件未生成——需正枚举值重测）

**意义**：打通后纯生成模式也能直接输出 .cdr 且**指定 X4（version 14）版本**，不必依赖"复制副本+Save()"绕法；模板模式转曲版另存新文件也更直接。这是 N3/N8 两项需求的最优解。

### 6.2 权威依据与在线资源

| 资源 | 用途 |
|---|---|
| lyvba.com（CorelDRAW 对象模型逐条文档，如 `StructSaveAsOptions.Version`） | 官方 API 语义查询：`cdrFileVersion` 枚举可存 5.0+ 各版本 |
| community.coreldraw.com 论坛 | 实战宏示例（含 `.Version = cdrVersion14` 存 X4 的完整代码） |
| CSDN「CorelDRAW VBA 另存为 X4 版本」（zebe1989） | 中文示例：StructSaveAsOptions + CorelScriptTools.GetFileBox |
| cdrvba.com | cdrVersion14 兼容性说明 |

### 6.3 开源项目补充（新增 CubicDev1/corel-mcp 细节）

- 精简 14 工具目录（对比 70+ 大目录提升 AI 工具选择可靠性）→ 本项目 P2 直接采纳
- attach 已开文档（`COREL_ATTACH_POLICY=existing_only`），不偷偷开第二实例
- 原子操作（一次 Undo 组）+ 修订冲突检测 → P2 健壮性参考
- `COREL_OUTPUT_ROOT` 限制输出目录白名单 → 安全设计参考
- 注意：其 save 机制细节未及深挖（源码 404 于猜测路径），但两条自有路线（Save() 存回 / SaveAs+options）已足够支撑
