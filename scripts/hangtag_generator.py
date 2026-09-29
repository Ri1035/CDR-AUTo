# -*- coding: utf-8 -*-
"""
coreldraw-hangtag 参数化吊牌生成器
- 输入：JSON 配置（卡片尺寸/颜色/打孔/正背面元素）
- 输出：印刷级 PDF + PNG 预览 + hangtag_result.json
- 退出码：0 成功 / 2 配置错误 / 3 连接失败 / 4 导出失败
用法：
  python hangtag_generator.py --config card.json --out "E:/输出目录"
"""
import os
import sys
import json
import argparse

import win32com.client

RESULT = {"status": "running", "outputs": {}, "warnings": [], "log": []}
EXIT_OK, EXIT_CONFIG, EXIT_CONNECT, EXIT_EXPORT = 0, 2, 3, 4

PAGE_W, PAGE_H = 210.0, 297.0   # A4
GAP = 3.0

FONT_MAP = {"cn": "Microsoft YaHei", "en": "Arial"}


def log(msg):
    RESULT["log"].append(str(msg))
    print(msg, flush=True)


def die(code, msg):
    log("FATAL: %s" % msg)
    RESULT["status"] = "error"
    RESULT["error"] = msg
    sys.exit(code)


# ---------- 连接 ----------

def connect():
    try:
        app = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application")
        log("已连接 CorelDRAW (EnsureDispatch)")
    except Exception as e:
        # gen_py 缓存损坏重试一次
        import glob, stat, shutil
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "gen_py")
        cleared = []
        for f in glob.glob(os.path.join(base, "*", "FBF4300F-*")):
            try:
                shutil.rmtree(f, onerror=lambda fn, p, ex: (os.chmod(p, stat.S_IWRITE), fn(p)))
                cleared.append(f)
            except Exception:
                pass
        if cleared:
            log("已清理损坏 gen_py 缓存: %s" % cleared)
            try:
                app = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application")
            except Exception as e2:
                die(EXIT_CONNECT, "CorelDRAW 连接失败（清理缓存后仍失败）: %s" % e2)
        else:
            die(EXIT_CONNECT, "CorelDRAW 连接失败: %s" % e)
    app.Visible = True
    return app


# ---------- CMYK / 基础绘制 ----------

def cmyk(app, c):
    return app.CreateCMYKColor(int(c[0]), int(c[1]), int(c[2]), int(c[3]))


def fill(shape, app, c):
    shape.Fill.ApplyUniformFill(cmyk(app, c))


def no_fill(shape):
    try:
        shape.Fill.ApplyNoFill()
    except Exception:
        pass


def no_outline(shape):
    try:
        shape.Outline.SetNoOutline()
    except Exception:
        pass


def outline(shape, app, width, c):
    try:
        shape.Outline.SetProperties(width, cmyk(app, c))
    except Exception:
        try:
            shape.Outline.Width = width
            shape.Outline.Color = cmyk(app, c)
        except Exception:
            pass


def style_text(t, app, size, font, bold, c):
    try:
        fp = t.Text.FontProperties
        fp.Name = FONT_MAP.get(font, font)
        fp.Style = 1 if bold else 0
    except Exception:
        pass
    try:
        t.Text.Story.Size = size   # 字号唯一有效写法（磅）
    except Exception as e:
        log("  字号设置失败: %s" % e)
    try:
        fill(t, app, c)
    except Exception:
        pass
    return t


def hline(layer, app, x1, x2, y_cd, thick, c):
    r = layer.CreateRectangle(min(x1, x2), y_cd - thick / 2.0, max(x1, x2), y_cd + thick / 2.0, 0, 0, 0, 0)
    no_outline(r)
    fill(r, app, c)
    return r


def y_from_top(card_top, y_top_mm):
    """距顶 mm -> CorelDRAW y-up 坐标（元素基线/中心）。"""
    return card_top - y_top_mm


# ---------- 元素渲染 ----------

def render_elements(layer, app, elements, x0, card_w, card_top, default_text, default_primary, card_h):
    """在卡片左上角锚点 (x0, card_top) 下渲染元素数组；含越界防护（EPS=0.5mm 容差）。"""
    EPS = 0.5
    warns = RESULT.setdefault("warnings", [])

    def warn(msg):
        warns.append(msg)
        print("  [警告] %s" % msg, flush=True)

    def x_in(lft_rel, rgt_rel, what):
        """相对卡左缘的横向范围校验，超界返回 True。"""
        if lft_rel < -EPS or rgt_rel > card_w + EPS:
            warn("[越界] %s 横向超出卡片 (左%.1f 右%.1f 卡宽%.1f)，已跳过" % (what, lft_rel, rgt_rel, card_w))
            return True
        return False

    for i, el in enumerate(elements):
        try:
            etype = el.get("type")
            color = el.get("color", default_text)
            # ellipse 用 cy_from_top（圆心），其余用 y_from_top
            key = "cy_from_top" if etype == "ellipse" else "y_from_top"
            if key not in el:
                log("  [警告] 元素 %d (%s) 缺少字段 %s（跳过）" % (i, etype, key))
                continue
            y_top_mm = float(el[key])
            y_cd = y_from_top(card_top, y_top_mm)

            if y_top_mm < -EPS or y_top_mm > card_h + EPS:
                warn("[越界] 元素 %d (%s) 纵向超出卡片 (距顶%.1f 卡高%.1f)，已跳过" % (i, etype, y_top_mm, card_h))
                continue

            if etype == "text":
                font = el.get("font", "cn")
                size = float(el.get("size", 7))
                bold = bool(el.get("bold", False))
                align = el.get("align", "left")
                t = layer.CreateArtisticText(0, y_cd, el["text"])
                style_text(t, app, size, font, bold, color)
                if align == "center":
                    t.PositionX = x0 + card_w / 2.0 - t.SizeWidth / 2.0
                elif align == "right":
                    t.PositionX = x0 + el.get("x", card_w) - t.SizeWidth
                else:
                    t.PositionX = x0 + el.get("x", 0)
                t.PositionY = y_cd
                # 渲染后宽度校验（超界移除）
                if x_in(t.PositionX - x0, t.PositionX - x0 + t.SizeWidth, "text '%s'" % el["text"][:12]):
                    try:
                        t.Delete()
                    except Exception:
                        pass

            elif etype == "line":
                x1r, x2r = float(el["x1"]), float(el["x2"])
                if x_in(min(x1r, x2r), max(x1r, x2r), "line"):
                    continue
                lc = el.get("color", default_primary)
                hline(layer, app, x0 + x1r, x0 + x2r, y_cd,
                      float(el.get("width_mm", 0.25)), lc)

            elif etype == "rect":
                w, h = float(el["w"]), float(el["h"])
                xr = float(el["x"])
                if x_in(xr, xr + w, "rect") or h < 0 or y_top_mm + h > card_h + EPS:
                    if y_top_mm + h > card_h + EPS:
                        warn("[越界] rect 纵向超出卡片 (顶%.1f+高%.1f > %.1f)，已跳过" % (y_top_mm, h, card_h))
                    if x_in(xr, xr + w, "rect"):
                        pass
                    continue
                r = layer.CreateRectangle(x0 + xr, y_cd - h, x0 + xr + w, y_cd, 0, 0, 0, 0)
                if el.get("fill"):
                    fill(r, app, el["fill"])
                else:
                    no_fill(r)
                if el.get("outline"):
                    outline(r, app, float(el.get("outline_mm", 0.2)), el["outline"])
                else:
                    no_outline(r)

            elif etype == "ellipse":
                cxr, r = float(el["cx"]), float(el["r"])
                if x_in(cxr - r, cxr + r, "ellipse") or y_top_mm - r < -EPS or y_top_mm + r > card_h + EPS:
                    if y_top_mm - r < -EPS or y_top_mm + r > card_h + EPS:
                        warn("[越界] ellipse 纵向超出卡片 (距顶%.1f 半径%.1f)，已跳过" % (y_top_mm, r))
                    continue
                cx, cy = x0 + cxr, y_cd
                e = layer.CreateEllipse(cx - r, cy - r, cx + r, cy + r)   # 对角两点
                if el.get("fill"):
                    fill(e, app, el["fill"])
                else:
                    no_fill(e)
                if el.get("outline"):
                    outline(e, app, 0.2, el["outline"])
                else:
                    no_outline(e)

            elif etype == "underline_field":
                label = el.get("label", "")
                size = float(el.get("label_size", 7))
                line_to = float(el["line_to"])
                if x_in(0, line_to, "underline_field"):
                    continue
                t = layer.CreateArtisticText(0, y_cd, label)
                style_text(t, app, size, el.get("font", "cn"), False, color)
                t.PositionX = x0 + el.get("x", 5)
                t.PositionY = y_cd
                hline(layer, app, t.PositionX + t.SizeWidth + 1, x0 + line_to, y_cd, 0.22, color)

            elif etype == "checkbox_row":
                box = float(el.get("box_size", 3))
                gap = float(el.get("gap", 28))
                cx = x0 + el.get("x", 5)
                for item in el.get("items", []):
                    t = layer.CreateArtisticText(0, y_cd, item)
                    style_text(t, app, float(el.get("size", 6.5)), el.get("font", "cn"), False, color)
                    t.PositionX = cx
                    t.PositionY = y_cd
                    bx = cx + t.SizeWidth + 1.5
                    if bx + box - x0 > card_w + EPS:
                        warn("[越界] checkbox '%s' 尾端 %.1f 超出卡宽 %.1f，该项及之后已跳过" % (item, bx + box - x0, card_w))
                        try:
                            t.Delete()
                        except Exception:
                            pass
                        break
                    b = layer.CreateRectangle(bx, y_cd - box / 2.0, bx + box, y_cd + box / 2.0, 0, 0, 0, 0)
                    no_fill(b)
                    outline(b, app, 0.2, color)
                    cx = bx + box + gap
            else:
                log("  [警告] 未知元素类型: %s（跳过）" % etype)
        except KeyError as ke:
            log("  [警告] 元素 %d 缺少字段 %s（跳过）" % (i, ke))
        except Exception as e:
            log("  [警告] 元素 %d 渲染失败: %s（跳过）" % (i, e))


def draw_hole(layer, app, hole_cfg, colors, x0, card_w, card_top, card_h):
    """打孔位：背景色圆（挖洞视觉效果）。"""
    if not hole_cfg.get("enabled"):
        return
    d = float(hole_cfg.get("d", 4))
    cx = x0 + float(hole_cfg.get("cx", card_w / 2.0))
    cy = y_from_top(card_top, float(hole_cfg.get("cy_from_top", 7)))
    r = d / 2.0
    e = layer.CreateEllipse(cx - r, cy - r, cx + r, cy + r)
    fill(e, app, hole_cfg.get("color", colors.get("hole", [0, 0, 0, 28])))
    no_outline(e)


def card_base(layer, app, x0, y_top, w, h, bg):
    """卡片基底：白填充 + K25 细描边直角矩形。"""
    r = layer.CreateRectangle(x0, y_top - h, x0 + w, y_top, 0, 0, 0, 0)
    fill(r, app, [0, 0, 0, 0])
    outline(r, app, 0.15, [0, 0, 0, 25])
    if bg and tuple(bg) != (0, 0, 0, 0):
        inner = layer.CreateRectangle(x0 + 0.3, y_top - h + 0.3, x0 + w - 0.3, y_top - 0.3, 0, 0, 0, 0)
        fill(inner, app, bg)
        no_outline(inner)
    return r


# ---------- 主流程 ----------

def validate(cfg):
    if not cfg.get("name"):
        return "缺少 name"
    card = cfg.get("card") or {}
    if not card.get("width") or not card.get("height"):
        return "缺少 card.width / card.height"
    if not cfg.get("front"):
        return "缺少 front 元素数组"
    return None


def main():
    ap = argparse.ArgumentParser(description="CorelDRAW 参数化吊牌生成器")
    ap.add_argument("--config", required=True, help="配置 JSON 路径")
    ap.add_argument("--out", required=True, help="输出目录")
    args = ap.parse_args()

    try:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        die(EXIT_CONFIG, "配置读取失败: %s" % e)
    err = validate(cfg)
    if err:
        die(EXIT_CONFIG, "配置校验失败: %s" % err)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    name = cfg["name"]
    card_w = float(cfg["card"]["width"])
    card_h = float(cfg["card"]["height"])
    layout = cfg.get("layout", "2up")
    colors = cfg.get("colors", {})
    text_c = colors.get("text", [0, 0, 0, 85])
    primary_c = colors.get("primary", [0, 0, 0, 100])
    bg_c = colors.get("background", [0, 0, 0, 0])
    hole_cfg = cfg.get("hole", {"enabled": False})

    app = connect()

    # 清理无标题遗留文档（不动用户文件）
    try:
        for d in list(app.Documents):
            try:
                if not d.FileName:
                    d.Close()
            except Exception:
                pass
    except Exception:
        pass

    if layout == "single":
        pw, ph = card_w, card_h
    else:
        pw, ph = PAGE_W, PAGE_H
    doc = app.CreateDocument()
    doc.Unit = 3
    doc.ActivePage.SetSize(pw, ph)
    log("画布已建 %gx%gmm（layout=%s）" % (pw, ph, layout))
    layer = doc.ActivePage.ActiveLayer

    if layout == "single":
        positions = [("front", (pw - card_w) / 2.0, ph)]
    else:
        total = card_w * 2 + GAP
        xf = (pw - total) / 2.0
        xb = xf + card_w + GAP
        cy = (ph - card_h) / 2.0
        positions = [("front", xf, cy + card_h), ("back", xb, cy + card_h)]

    for side, (sname, x0, y_top) in zip(["front", "back"], positions):
        elements = cfg.get(sname) or []
        card_base(layer, app, x0, y_top, card_w, card_h, bg_c)
        draw_hole(layer, app, hole_cfg, colors, x0, card_w, y_top, card_h)
        render_elements(layer, app, elements, x0, card_w, y_top, text_c, primary_c, card_h)
        log("%s 面已渲染（%d 个元素）" % (sname, len(elements)))

    # 导出
    outputs = {}
    pdf_path = os.path.join(out_dir, "%s.pdf" % name)
    try:
        ps = doc.PDFSettings
        ps.ColorMode = 1            # CMYK
        ps.Bleed = float(cfg.get("pdf", {}).get("bleed", 0))
        ps.IncludeBleed = bool(cfg.get("pdf", {}).get("bleed", 0))
        ps.CropMarks = bool(cfg.get("pdf", {}).get("crop_marks", False))
        ps.TextAsCurves = True
        ps.PublishRange = 1
        ps.PageRange = "1"
        doc.PublishToPDF(pdf_path)
        outputs["pdf"] = pdf_path
        log("PDF 已导出: %s (%d 字节)" % (pdf_path, os.path.getsize(pdf_path)))
    except Exception as e:
        die(EXIT_EXPORT, "PDF 导出失败: %s" % e)

    png_path = os.path.join(out_dir, "%s_preview.png" % name)
    try:
        doc.Export(png_path, 802, 1, None, None)
        outputs["png"] = png_path
        log("PNG 预览已导出: %s" % png_path)
    except Exception as e:
        die(EXIT_EXPORT, "PNG 导出失败: %s" % e)

    RESULT["status"] = "done"
    RESULT["outputs"] = outputs
    result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hangtag_result.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(RESULT, f, ensure_ascii=False, indent=2)
    log("完成。CorelDRAW 文档保持打开（.cdr 请手动 Save As）。")


if __name__ == "__main__":
    try:
        main()
        sys.exit(EXIT_OK)
    except SystemExit:
        raise
    except Exception as e:
        log("FATAL: %s" % e)
        RESULT["status"] = "error"
        RESULT["error"] = str(e)
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hangtag_result.json"),
                      "w", encoding="utf-8") as f:
                json.dump(RESULT, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        sys.exit(4)
