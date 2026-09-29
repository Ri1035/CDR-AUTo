# CorelDRAW 2020 COM API 实测陷阱清单（pywin32 / gencache 早期绑定）

> 全部条目在本机 CorelDRAW Graphics Suite 2020（14.0，64 位 Windows）实测验证。
> VBA 文档写法在该版 COM 大多不存在或静默失效——遇到"设了没反应"先查本清单。

## 1. 连接

- ✅ `win32com.client.gencache.EnsureDispatch("CorelDRAW.Application")` —— **必须早期绑定**，晚期绑定 `Dispatch` 会让属性 setter（填色/字体/PDF 设置）静默失效。
- ❌ `GetActiveObject` 多数机器报 `(-2147221021, '操作无法使用')`（ROT 未注册）→ 统一用 EnsureDispatch（未运行则拉起新可见实例）。
- `app.Visible = True` 可视化运行；**禁止 `app.Quit()`**（用户文档保持打开）。
- 清理脚本自己产生的无标题文档：`for d in list(app.Documents): if not d.FileName: d.Close()`（不动用户命名文件）。

## 2. gen_py 缓存损坏

- 报错：`module 'win32com.gen_py.FBF4300F-...x0x14x0' has no attribute 'CLSIDToClassMap'`
- 修复：删除 `%LOCALAPPDATA%\Temp\gen_py\3.13\FBF4300F-D921-11D1-B806-00A0C90646A9x0x14x0` **目录**（是目录且可能只读，用 `shutil.rmtree` + chmod），下次连接自动重生成。

## 3. 文字

| 目的 | 唯一有效写法 |
|---|---|
| 字号 | `shape.Text.Story.Size = 磅值`（默认 24pt；**`FontProperties.Size` 静默无效**） |
| 字体名 | `shape.Text.FontProperties.Name = "Microsoft YaHei"` |
| 粗体 | `shape.Text.FontProperties.Style = 1`（无 `.Bold`） |
| 局部字号 | `shape.Text.Range(0, n).Size = 8` |
| 水平居中 | `t.PositionX = cx - t.SizeWidth / 2.0`（对齐 API 不可靠） |
| 定位 | `t.PositionX / PositionY`（艺术字基线点） |

- 段落文本：`layer.CreateParagraphText(L, B, R, T, text)` ✅（L,B,R,T，y-up）。
- **文本内 `\n` 不产生换行**（被忽略）→ 多条目必须拆独立文本对象。
- 窄段落框会把英文品牌名（如 LANLIVE STUDIO）断行拆开 → 文案避免在窄框写英文词组。

## 4. 形状

- `layer.CreateRectangle(L, B, R, T, CornerX, CornerY, fRound, fMirror)`；直角传 0,0,0,0。
- `layer.CreateEllipse(L, B, R, T)` 收**对角两点**（圆：`cx-r, cy-r, cx+r, cy+r`），不是 L,B,W,H。
- **`Layer` 没有 `CreateLine`** → 水平线用细矩形（高 0.2mm）。
- `Layer.CreatePolygon` 存在；`CreateShapeFromCurve` 不存在于 Layer；`Layer.CreateCurve` 参数签名不明（传 0 报转换错误）→ 自由多边形轮廓改用 **Weld 矩形法**（见第 10 条）。
- 旋转：`shape.RotationCenterX/Y = ...; shape.Rotate(deg)`（正值逆时针）。

## 5. 填充 / 描边

- 纯色：`shape.Fill.ApplyUniformFill(color)`；无填充：`shape.Fill.ApplyNoFill()`。
- 去描边：`shape.Outline.SetNoOutline()`；设描边：`shape.Outline.SetProperties(width, color)`。
- ❌ `shape.Fill.UniformFillRGB(...)`、`shape.Fill.Type = 1` 不存在。
- CMYK 色工厂：**`app.CreateCMYKColor(c, m, y, k)`**（Document 上没有）。RGB：`app.CreateRGBColor(r,g,b)`。

## 6. 布尔 / 接口类型参数（Weld/Trim/SaveAs 通病）

pywin32 对**声明为接口类型的参数**传 Shape/字符串报 `The Python instance can not be converted to a COM object`。绕过：

```python
dispid = main._oleobj_.GetIDsOfNames(0, "Weld")
res = main._oleobj_.Invoke(dispid, 0, 1, True, other._oleobj_)
main = win32com.client.Dispatch(res)   # 包回 Shape 继续 fill/outline
```

`doc.SaveAs(path)` 无法用此法救（FileName 参数问题），`.cdr` 一律手动 Save As。

## 7. 多页 / 页面

- 加页：`doc.AddPages(n)`；激活：`doc.Pages(i).Activate()`；取层：`doc.ActivePage.ActiveLayer`。
- 页面边界 `LeftX/BottomY/RightX/TopY` **只读**；可写 `SizeWidth/SizeHeight`。
- `SetSize` 锚点：**底边固定，向上扩展**（TopY 变化）。
- 专用图层：`page.CreateLayer("NAME"); layer.Activate()`；整层平移：`layer.Shapes.All().Move(dx, dy)`。

## 8. 导出

- PDF：`doc.PDFSettings` → `ColorMode=1`(CMYK)、`Bleed`、`IncludeBleed`、`CropMarks`、`TextAsCurves=True`、`PublishRange`（1=当前页，2=全部页）、`PageRange` → `doc.PublishToPDF(path)`。
- PNG：`doc.Export(path, 802, 1, None, None)`（802=cdrPNG；1=当前页）。**PNG 默认包含页面外对象**（超出画布的内容也会导出）。
- 超画布完整 PDF：临时 `SetSize` 扩页 → `layer.Shapes.All().Move(0, dy)` → PublishToPDF → Move 回 + SetSize 还原。
- 页面外对象在 PDF 中被按页面裁剪。

## 9. 单位 / 坐标

- `doc.Unit = 3`（mm）；1=inch，4=pixel。
- 坐标原点**页面左下角，y 轴向上**。配置文件习惯"距顶 mm"时内部换算：`y_cd = card_h - y_from_top`。
- 字号单位是**磅**（pt），与文档单位无关。

## 10. 环境 / 执行

- 必须关闭沙箱运行（脚本要触达真实 CorelDRAW 进程与桌面文件系统）。
- Python 内路径用 Windows 盘符 `E:/x/y`，不要 `/e/x`。
- pywin32 必须正常 `pip install pywin32` 进 site-packages；`--target` 会丢 `.pyd`（`No module named 'pywintypes'`）。
- 受管 Python 可能被重置，pywin32 丢失就重装。
- 导出耗时 5-15 秒/次属正常；PNG 导出 100KB 级别为合理预览体积。

## 11. 坐标读取陷阱（v1.1 新增，视觉裁决法发现）

- **`Shape.PositionX/Y` 的参考点不固定**（默认参考点随对象创建/操作历史变化），同一对象两次会话读数可能相差数十毫米——**严禁用 PositionX/Y 做几何计算**。
- ✅ 正确写法：`Shape.LeftX / BottomY / RightX / TopY`（明确包围盒边界，参考点无关）；宽高 = RightX-LeftX / TopY-BottomY。
- **视觉裁决法**：数值读数可疑时，导出 PNG 预览（`doc.Export(path, 802, 1, None, None)`，页面外对象也包含）用读图核对，一锤定音。
- CDR X4+ 文件格式为 **ZIP 容器**（文件头 `PK`），内部 `content/riffData.c` 的 RIFF `vrsn` 块记录格式版本（X4=0x0578=1400）。
- PowerClip 内容对象遍历：`shape.PowerClip.Shapes`；其坐标仍是页面绝对坐标。
- Shape.Type 数值实测（本机）：1=矩形, 2=椭圆, 3=曲线, 5=位图, 6=文字, 7=群组。

## 12. 文字与位图属性读取（R8 实测补充）

- **字体名**：`shape.Text.FontProperties.Name`（Text 层）或 `Text.Story.Font`——**`Story.FontProperties` 不存在**（Story 只管字号/对齐等段落属性）
- **字号**：`Text.Story.Size`（读回也走这里，磅）
- 多格式混排文字的 Story.Font 可能为空 → 需逐字符 `Text.Range(i, i+1).FontProperties.Name`
- **位图颜色模式**：`shape.Bitmap.Mode`（无 ColorMode 属性）；实测用户已转 CMYK 的图 Mode=5（即 CMYK 基线值）
- 位图转换（N7 图片 CMYK 化）：`Bitmap.ConvertTo(mode)` / `ConvertToBW` / `ConvertToPaletted` 存在
- 位图其他有用属性：`ResolutionX/Y`（dpi）、`IsEPS`、`ExternallyLinked`、`Embedded`
- 图层跳过：`doc.Layers` / `page.Layers` 按图层名过滤（NOTES 注释层），遍历时跳过该层 Shapes

## 13. COM 文件参数必须绝对路径（R12 回归实测）

- `PublishToPDF` / `SaveAs` / `OpenDocument` 等的路径参数若为**相对路径**，会按 **CorelDRAW 进程的 cwd**（非 Python cwd）解析——轻则写到别处，重则 `com_error E_FAIL 无描述`。
- ✅ 修复：所有脚本入口对路径参数 `os.path.abspath()` 后再使用。
- 排错经验：同代码"之前成功后来失败"时，先核对**运行目录**是否变了。
