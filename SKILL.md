---
name: coreldraw-hangtag
description: |
  通过 COM 自动化驱动本机 CorelDRAW（2020+）批量制作吊牌/卡片类印刷品。
  触发词：制作吊牌、hang tag、连cdr、连通CorelDRAW、CDR出图、吊牌生成、
  售后卡/服饰卡/标签制作、CorelDRAW 自动化、自动化插件吊牌。
  用途：环境自检 → 连接 CorelDRAW → 按 JSON 配置参数化生成吊牌正/背面
  （打孔位、下划线字段、复选框、色块、图标行均可配置）→ PNG/PDF 交付。
  面向分享与自动化插件训练：纯 CLI + JSON 输入 + 结果 JSON + 规范退出码。
---

# CorelDRAW 吊牌自动化（coreldraw-hangtag）

用 Python + pywin32 通过 COM 接口驱动本机正在运行的 CorelDRAW，按 **JSON 配置**生成吊牌（也适用于售后卡、服饰卡、标签等竖版卡片类印刷品）。全程 CMYK，产出印刷级 PDF 与 PNG 预览。

## 0. 前置条件

| 项 | 要求 |
|---|---|
| 系统 | Windows（CorelDRAW 与 Python 必须同位数，64 位） |
| 软件 | CorelDRAW Graphics Suite 2020 或更高（COM 安装时自动注册） |
| Python | 64 位 Python 3.11+，已装 `pywin32` |
| 运行方式 | **必须关闭沙箱执行**（脚本要访问真实 CorelDRAW 进程与磁盘） |

pywin32 安装（装进 Python 自己的 site-packages，**严禁** `--target`，会丢 `.pyd` 导致 `No module named 'pywintypes'`）：

```bash
"<PYTHON>" -m pip install --no-cache-dir pywin32
```

## 1. 环境自检（每次开工先跑）

```bash
"<PYTHON>" "<本目录>/scripts/cdr_env_check.py"
```

输出 JSON：`{"ok": true/false, "python_bits": 64, "pywin32": true, "coreldraw": {"connected": true, "version": "14.0...", "documents": 0}}`。`ok=false` 时按 `hints` 处理（常见：缺 pywin32 → 重装；gen_py 缓存坏 → 见 references/api_gotchas.md 第 2 条）。

## 2. 快速开始（三步出牌）

### 第 1 步：写配置 JSON

```json
{
  "name": "我的吊牌",
  "layout": "2up",
  "card": {"width": 50, "height": 90},
  "colors": {
    "background": [0, 0, 0, 0],
    "primary": [85, 60, 15, 5],
    "text": [0, 0, 0, 85],
    "hole": [0, 0, 0, 28]
  },
  "hole": {"enabled": true, "cx": 25, "cy_from_top": 7, "d": 4},
  "front": [
    {"type": "text", "text": "品牌名", "align": "center", "y_from_top": 20, "size": 10, "bold": true},
    {"type": "line", "x1": 8, "x2": 42, "y_from_top": 26, "width_mm": 0.25},
    {"type": "underline_field", "label": "价格：", "x": 6, "line_to": 44, "y_from_top": 40},
    {"type": "checkbox_row", "items": ["合格证", "检验员 03"], "x": 6, "y_from_top": 78}
  ],
  "back": [
    {"type": "text", "text": "洗涤说明", "align": "center", "y_from_top": 15, "size": 9, "bold": true},
    {"type": "text", "text": "40°C 水温，不可漂白，悬挂晾干", "align": "center", "y_from_top": 24, "size": 6, "color": [0,0,0,60]}
  ]
}
```

### 第 2 步：运行生成器（关沙箱）

```bash
"<PYTHON>" "<本目录>/scripts/hangtag_generator.py" --config card.json --out "E:/输出目录"
```

### 第 3 步：核对与交付

- 生成器导出 `<name>.pdf`（印刷级，文字转曲 CMYK）+ `<name>_preview.png`（整页预览，含正/背面）+ `hangtag_result.json`（结果与逐条日志）。
- **Agent 必须用读图核对该 PNG**：文字溢出、错位、字号失真按日志坐标修正配置后重跑（通常 1-2 轮收敛）。
- 交付时给用户可点击的绝对路径；`.cdr` 源文件需用户在 CorelDRAW 里手动 Save As（COM 无法自动存，见陷阱 9）。

## 3. 配置字段参考

### 全局

| 字段 | 说明 |
|---|---|
| `name` | 输出文件名（不含扩展名） |
| `layout` | `2up`（A4 画布，正/背横排间距 3mm，默认）或 `single`（画布=卡片尺寸，仅正面） |
| `card` | `width` / `height`（mm）；直角，无圆角 |
| `colors` | CMYK 数组 `[C,M,Y,K]`：`background` 卡底 / `primary` 主色 / `text` 正文 / `hole` 打孔圆填充 |
| `hole` | 打孔位：`enabled`、`cx`（mm 距左）、`cy_from_top`（mm 距顶）、`d`（直径） |

### 元素（front / back 数组；y 全部"距卡顶 mm"，脚本内部换算 CorelDRAW 的 y-up 坐标）

| type | 专有字段 | 说明 |
|---|---|---|
| `text` | `text` `x`(mm，align≠center 时) `align`(center/left) `y_from_top` `size`(磅) `bold` `font`(`cn`/`en`/字体名) `color` | 文字 |
| `line` | `x1` `x2` `y_from_top` `width_mm` `color` | 水平线（细矩形实现） |
| `rect` | `x` `y_from_top` `w` `h` `fill` `outline` `outline_mm` | 矩形（直角） |
| `ellipse` | `cx` `cy_from_top` `r` `fill` `outline` | 正圆 |
| `underline_field` | `label` `x` `line_to` `y_from_top` `label_size` | 标签+横线（登记类字段） |
| `checkbox_row` | `items` `x` `y_from_top` `box_size` `gap` | 复选框行 |

公共可选字段（所有元素）：`color` 覆盖默认文字色。多行文本/多条目**拆成多个元素**，不要依赖文本内换行（陷阱 6）。

## 4. 必读陷阱（浓缩版，全文见 references/api_gotchas.md）

1. **字号必须 `Text.Story.Size`**；`FontProperties.Size` 静默无效（不报错，停留默认 24pt，版式全炸）。
2. `CreateEllipse(L,B,R,T)` 收**对角两点**，不是 L,B,W,H。
3. 文本内 `\n` **不产生换行**——多条目拆独立文本对象。
4. 连接用 `gencache.EnsureDispatch("CorelDRAW.Application")`；`GetActiveObject` 在多数机器报"操作无法使用"。
5. gen_py 缓存报 `CLSIDToClassMap` → 删 `%LOCALAPPDATA%\Temp\gen_py\<ver>\FBF4300F-*` 目录重生成。
6. **不要调用 `app.Quit()`**；文档保持打开，用户手动 Save As。
7. 脚本路径一律 Windows 盘符（`E:/x/y`），POSIX 风格 `/e/x` 在子进程解析不到。
8. Weld 等接口类型参数用 `_oleobj_.Invoke` 绕过（详见 gotchas 第 10 条）。

## 5. 自动化插件接入约定

为便于训练为自动化插件 / 被编排系统调用，生成器遵循：

- **纯 CLI**：`--config <json> --out <dir>`，无交互、无确认。
- **结果可机读**：`hangtag_result.json`（`status` / `outputs{}` / `log[]`），stdout 同时打印日志。
- **退出码**：`0` 成功；`2` 配置错误；`3` CorelDRAW 连接失败；`4` 导出失败。
- **幂等**：同名输出直接覆盖，重跑安全；每次运行新建文档，不触碰用户已打开文件。
- **限制说明**：CorelDRAW 无真无头模式（`Visible=True` 可视化运行），宿主机需有桌面会话；导出约 5-15 秒/次。

## 6. 分享方法

把本 Skill 整个文件夹（`SKILL.md + references/ + scripts/`）拷贝给对方，放入其 `~/.workbuddy/skills/coreldraw-hangtag/`（或项目 `.workbuddy/skills/`）即可。对方只需满足前置条件第 0 节（装一次 pywin32）。
