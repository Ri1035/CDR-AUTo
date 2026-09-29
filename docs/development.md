# development — 开发方式、执行命令、回归测试清单

## 1. 开发方式：训练循环

每个开发轮次（R#）遵循固定循环（详见 TRAINER_GUIDE.md）：

```
① 定目标（从 TODO.md 取最高优先项） → ② 写验收标准 → ③ 执行（编码/实验）
→ ④ 验证（命令+读图） → ⑤ TRAINING_LOG 记录 → ⑥ git 提交 → ⑦ PLAN/TODO 状态更新
```

规则：
- 一轮一目标；失败结论同样记录（防止重复踩坑）
- 指令歧义（两种以上解读）必须先向用户复述确认
- 难题优先网上资源求解（已验证：SaveAs 突破即由此而来）
- **禁止重写/删除 git 历史**（迭代数据是研究资料）

## 2. 环境

```bash
PY="C:/Users/Mayn/.workbuddy/binaries/python/versions/3.13.12/python.exe"
"$PY" -m pip install --no-cache-dir pywin32     # P2 后追加: fastmcp
```

- 必须使用 **64 位 Python**（匹配 CorelDRAW）
- `pywin32` 必须正常 pip 安装（禁止 `--target`）
- **所有 COM 脚本必须关闭沙箱执行**（bash 参数 `dangerouslyDisableSandbox: true`）

## 3. 执行命令速查

```bash
# 环境自检（期望输出 "ok": true）
"$PY" scripts/cdr_env_check.py

# 纯生成出牌
"$PY" scripts/hangtag_generator.py --config configs/example_card.json --out outputs/<dir>

# 模板文字清单（只看不改）
"$PY" scripts/hangtag_fill.py --template <模板.cdr> --mapping <map.json> --out <dir> --name <名> --list-only

# 模板填充出全套
"$PY" scripts/hangtag_fill.py --template <模板.cdr> --mapping <map.json> --out <dir> --name <名>

# 模板登记入库
"$PY" scripts/template_register.py --template <模板.cdr> --id <id>

# 同引擎到 WorkBuddy skill 副本（改引擎后必跑）
scripts/sync_to_workbuddy_skill.cmd
```

## 4. 回归测试清单（每次改引擎后必跑）

| # | 测试 | 命令/文件 | 预期 |
|---|---|---|---|
| T1 | 环境自检 | `cdr_env_check.py` | `"ok": true` |
| T2 | 纯生成基线 | generator + `configs/example_card.json` | 4 产物齐全；warning=0；读图：打孔/字段线/复选框正确 |
| T3 | 越界防护 | generator + `configs/bounds_test.json` | 7 条越界告警命中；status=done |
| T4 | 模板枚举 | fill `--list-only` + `templates/demo_mixed_v1/template.cdr` | 10 个文字对象 |
| T5 | 模板填充 | fill + `configs/demo_mapping.json` | 替换含 #9/#10（规范化匹配）共 10 处；双 .cdr+PDF+PNG |
| T6 | 读图核对 | Read 输出 PNG | 无溢出、无错位、替换文字正确渲染 |
| T7 | 结果 JSON | `scripts/hangtag_fill_result.json` | status=done、warnings 合理 |

## 5. 提交与版本规范

- 提交信息：`<type>: <要点> (R# / Phase P#)`，type ∈ feat/fix/docs/chore
- Phase 完成：打 tag `v1.x.0` + CHANGELOG 条目
- 分支：当前 master 单线；P2 起可开 `feature/mcp` 分支
- **禁止**：重写历史、提交大文件（templates/*.cdr 已 ignore）、提交密钥

## 6. 已知坑索引（动手前必读）

`references/api_gotchas.md`（21 条）——最高频五条：
1. 字号 `Text.Story.Size`（FontProperties.Size 静默无效）
2. `CreateEllipse(L,B,R,T)` 对角两点
3. 文本内 `\n` 不换行
4. 坐标用 `LeftX/BottomY/RightX/TopY`（PositionX/Y 参考点不固定）
5. 接口类型参数用 `_oleobj_.Invoke` 绕过（Weld/SaveAs）
