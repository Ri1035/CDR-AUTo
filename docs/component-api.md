# component-api — 组件 API 文档

> 版本：v1.2 ｜ 各脚本均为独立 CLI，退出码 0=成功 / 2=配置错误 / 3=连接失败 / 4=执行失败。

---

## 1. cdr_env_check.py — 环境自检

```
python cdr_env_check.py
```

输出 JSON：
```json
{"ok": true, "python_bits": 64, "pywin32": true,
 "coreldraw": {"connected": true, "version": "14.0.0.701", "documents": 0},
 "hints": []}
```

行为：gen_py 缓存损坏时自动清理并重试；`ok=false` 时 `hints[]` 给修复建议。退出码 0/1。

---

## 2. hangtag_generator.py — 纯生成引擎

```
python hangtag_generator.py --config <card.json> --out <输出目录>
```

### 配置 schema（JSON）

| 键 | 说明 |
|---|---|
| `name` | 输出文件名（不含扩展名） |
| `layout` | `"2up"`（A4 双卡横排间距 3mm，默认）或 `"single"`（画布=卡片） |
| `card` | `{"width": mm, "height": mm}` |
| `colors` | CMYK 数组：`background/primary/text/hole` |
| `hole` | `{"enabled", "cx", "cy_from_top", "d"}`（mm，距顶距左） |
| `front` / `back` | 元素数组（见下） |

### 元素类型

| type | 字段 |
|---|---|
| `text` | `text` `x`(mm) `align`(center/left) `y_from_top` `size`(pt) `bold` `font`(cn/en/名) `color` |
| `line` | `x1` `x2` `y_from_top` `width_mm` `color` |
| `rect` | `x` `y_from_top` `w` `h` `fill` `outline` `outline_mm` |
| `ellipse` | `cx` `cy_from_top` `r` `fill` `outline` |
| `underline_field` | `label` `x` `line_to` `y_from_top` `label_size` |
| `checkbox_row` | `items[]` `x` `y_from_top` `box_size` `gap` |

### 输出

`<name>.pdf` + `<name>_preview.png` + `hangtag_result.json`（status/outputs/warnings/log）。

行为：越界防护（EPS 0.5mm，跳过+告警）；不调用 Quit；文档保持打开。

---

## 3. hangtag_fill.py — 模板填充引擎

```
python hangtag_fill.py --template <模板.cdr> --mapping <map.json> --out <dir> --name <名> [--list-only]
```

### mapping schema（JSON 对象，两种键可混用）

```json
{ "原文精确匹配": "新文字",
  "#9": "按序号替换(从1起, 见 --list-only)" }
```

- 规范化匹配：键与模板文字**去除空白/换行**后比对（`\r` 分行文字自动命中）
- 替换后：水平中心恢复 + 越界自动缩放（容器=包含文字中心的最小大对象，边距 1.5mm，字号下限 3pt）

### 流程

复制模板副本 → OpenDocument → 枚举文字（递归群组+PowerClip）→ 替换 → `Save()`（原样 .cdr）→ 复制为转曲版 → OpenDocument → 全文 `ConvertToCurves` → `Save()`（转曲 .cdr）→ PDF（TextAsCurves/CMYK）+ PNG → 结果 JSON。

### 输出

`<name>_原样.cdr` / `<name>_转曲.cdr` / `<name>.pdf` / `<name>_preview.png` + `hangtag_fill_result.json`（含 `replaced[]` 与 `warnings[]`）。

---

## 4. template_register.py — 模板登记器

```
python template_register.py --template <模板.cdr> --id <模板id> [--lib <库目录>]
```

行为：复制模板到 `templates/<id>/template.cdr` → COM 分析（257 对象级）→ 生成 `meta.json` 草稿 → 更新 `templates/index.json`。

### meta.json schema

| 键 | 内容 |
|---|---|
| `template_id` / `source_file` / `format` | 标识与格式（X4） |
| `page` | `{width, height}` mm |
| `sets[]` | 卡组聚类：`set_id/card_size/card_count/bbox/location(on|off_page)/cards[].role(待标)` |
| `fields[]` | `shape_idx` `placeholder` `field`(TODO_待命名) `field_cn` `max_chars` `bbox` `status` |
| `assets` | `bitmaps[]`（含颜色模式核对项）/ `powerclips[]` / `loose_curves` |
| `holes` | `{"strategy": "沿用模板已有孔对象", "circle_4mm": n, "bar_12x2.5": n}` |

入库后人工回填：`fields[].field`（语义名）、`max_chars`、`sets[].cards[].role`（正/背）→ `status: ready`。

---

## 5. 核心 Python 函数（引擎内复用）

```python
# 连接（EnsureDispatch 早期绑定，禁 Quit）
connect() -> app

# 几何（陷阱 #21：禁用 PositionX/Y，用包围盒）
shape.LeftX / BottomY / RightX / TopY

# 遍历（递归群组 + PowerClip）
def walk(shapes): yield s; walk(s.Shapes); walk(s.PowerClip.Shapes)

# 焊接（接口类型参数绕过）
main._oleobj_.Invoke(main._oleobj_.GetIDsOfNames(0, "Weld"), 0, 1, True, other._oleobj_)
# 返回 PyIDispatch → win32com.client.Dispatch(res) 包回

# 阵列拼版（R7+ 规划用）
shaperange.StepAndRepeat(count_minus_1, dx, dy)
doc.CreateShapeRangeFromArray(r1, r2)

# 保存 .cdr（X4 版本）
opt = app.CreateStructSaveAsOptions()
opt.Version = 1400            # cdrVersion14
opt.Overwrite = True
doc._oleobj_.Invoke(doc._oleobj_.GetIDsOfNames(0, "SaveAs"), 0, 1, True, path, opt._oleobj_)
```

## 6. COM 陷阱全文

见 `references/api_gotchas.md`（21 条，含每条的实测证据与修复方法）。
