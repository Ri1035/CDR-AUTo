# architecture — 项目架构与数据流

## 1. 三层形态

```
┌─────────────────────────────────────────────┐
│ 调用方：AI agent（任意 MCP 客户端）/ 编排系统 / 人工 │
└──────────────┬──────────────────────────────┘
               │ MCP 协议（P2）/ 命令行（已就绪）
┌──────────────▼──────────────────────────────┐
│ 手册层 Skill：SKILL.md + api_gotchas.md      │  ← AI 读手册按流程操作
│ （WorkBuddy skill 机制，分发副本自动同步）      │
└──────────────┬──────────────────────────────┘
┌──────────────▼──────────────────────────────┐
│ 引擎层 CLI（scripts/*.py，稳定 API）           │
│  ├ cdr_env_check.py      环境自检             │
│  ├ hangtag_generator.py  参数化生成            │
│  ├ hangtag_fill.py       模板填充（R6/R7）     │
│  ├ template_register.py  模板登记入库          │
│  └ sync_to_workbuddy_skill.cmd 同步           │
└──────────────┬──────────────────────────────┘
┌──────────────▼──────────────────────────────┐
│ COM 层：pywin32 → CorelDRAW X4 (14.0.0.701)  │
│  gencache 早期绑定 / _oleobj_.Invoke 绕接口参数 │
└─────────────────────────────────────────────┘
```

## 2. 模块职责

| 模块 | 职责 | 关键能力 |
|---|---|---|
| cdr_env_check | 环境自检 | Python 位数/pywin32/COM 连接；gen_py 缓存损坏自修复 |
| hangtag_generator | 纯生成管线 | JSON 配置 → 卡片（text/line/rect/ellipse/underline_field/checkbox_row）；越界防护；CMYK；PDF/PNG |
| hangtag_fill | 模板填充管线 | 模板副本 → 文字枚举（递归+PowerClip）→ 三模式映射替换 → 中心恢复 → 越界自动缩放 → Save() |
| template_register | 模板入库 | 结构分析（卡组聚类/文字字段/资产/孔）→ meta.json 草稿 → index.json 索引 |
| （P2）server.py | MCP 包装 | 4 工具：env_check / list_fonts / fill_template / generate_hangtag；串行锁 |

## 3. 数据流

### 3.1 模板入库（一次性）

```
模板.cdr ──copy──▶ templates/<id>/template.cdr
        ──COM 分析──▶ meta.json 草稿（sets 聚类 / fields 文字清单 / assets / holes）
        ──人工回填──▶ field 语义名 + max_chars（status: draft → ready）
```

### 3.2 模板填充出活（每次）

```
meta(ready) + 字段值
  → copy template.cdr → <name>_原样.cdr
  → OpenDocument → 枚举文字（递归群组+PowerClip）
  → 映射替换（内容精确 / 规范化去空白 / #序号）
  → 中心恢复 + 越界自动缩放（fit_and_center，容器=最小包含大对象）
  → Save()                    ⇒ 原样 .cdr（可编辑，X4 格式）
  → copy → OpenDocument → 全文 ConvertToCurves → Save()  ⇒ 转曲 .cdr
  → PublishToPDF(TextAsCurves, CMYK)                     ⇒ 印刷 PDF
  → Export(802)                                          ⇒ PNG 预览
  → hangtag_result.json（状态/产物/警告/日志）
```

### 3.3 纯生成出活

```
config.json（card/colors/hole/front[]/back[]）
  → CreateDocument → 逐元素绘制（越界防护）→ SaveAs(Version:1400) .cdr → PDF/PNG
```

## 4. 关键技术决策

| 决策 | 理由 |
|---|---|
| 直连 COM 而非 MCP-first | COM 路径已验证；MCP 是包装层，先稳引擎再包 |
| gencache 早期绑定 | 晚期绑定会让属性 setter 静默失效 |
| `_oleobj_.Invoke` 绕接口参数 | Weld/SaveAs 等接口类型参数 pywin32 直传报错 |
| `LeftX/BottomY/RightX/TopY` 取坐标 | `PositionX/Y` 参考点不固定（陷阱 #21） |
| `Save()` 存回副本 + `SaveAs(Version:1400)` | 绕过"只传字符串"的签名不匹配；显式 X4 版本 |
| 转曲另存 = 复制+OpenDocument+ConvertToCurves+Save() | 绕过 SaveAs 限制的两步法 |
| meta.json 与 .cdr 同目录分离 | meta 入 git（小），素材不入 git（大） |

## 5. 已知约束（硬）

1. 交互式桌面会话必需（无头服务器不可用）
2. COM 单实例 → 串行锁（P2）
3. .cdr 无法纯程序"另存新路径+任意版本"→ 两步法已解
4. 文本内 `\n` 不换行 → 多条目拆独立对象
