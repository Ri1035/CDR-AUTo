# -*- coding: utf-8 -*-
"""
模板填充引擎（R6）— hangtag_fill.py
流程：复制模板副本 → OpenDocument → 枚举文字 → 按 mapping 替换 → Save() 存回
      → 复制为转曲版 → OpenDocument → 全文转曲 → Save() → 导出 PDF/PNG
用法：
  python hangtag_fill.py --template 模板.cdr --mapping map.json --out 输出目录 --name 名称
mapping 格式（二选一，可混用）：
  {"原文精确匹配": "新文字", ...}          # 按内容替换（全部命中对象）
  {"#3": "新文字", ...}                    # 按枚举序号替换（从 1 开始，见 --list）
退出码：0 成功 / 2 参数错误 / 3 连接失败 / 4 执行失败
"""
import os
import sys
import json
import shutil
import argparse

import win32com.client

RESULT = {"status": "running", "outputs": {}, "replaced": [], "warnings": [], "log": []}


def log(msg):
    RESULT["log"].append(str(msg))
    print(msg, flush=True)


def die(code, msg):
    log("FATAL: %s" % msg)
    RESULT["status"] = "error"
    RESULT["error"] = msg
    sys.exit(code)


def connect():
    try:
        app = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application")
        log("已连接 CorelDRAW")
    except Exception as e:
        die(3, "CorelDRAW 连接失败: %s" % e)
    app.Visible = True
    return app


def cmyk(app, c):
    return app.CreateCMYKColor(int(c[0]), int(c[1]), int(c[2]), int(c[3]))


def walk(shapes):
    for s in shapes:
        yield s
        try:
            if s.Shapes.Count:
                for x in walk(s.Shapes):
                    yield x
        except Exception:
            pass
        try:
            pc = s.PowerClip
            if pc is not None:
                for x in walk(pc.Shapes):
                    yield x
        except Exception:
            pass


def list_text_shapes(doc):
    """枚举全部文字对象：[{idx(1起), text, left_x, right_x, top_y}]"""
    out = []
    for pg_i in range(1, doc.Pages.Count + 1):
        doc.Pages(pg_i).Activate()
        for s in walk(doc.ActivePage.Shapes):
            try:
                st = s.Text.Story
                if st is None or st.Text is None:
                    continue
                out.append({"idx": len(out) + 1, "shape": s, "text": st.Text,
                            "lx": s.LeftX, "rx": s.RightX, "ty": s.TopY, "page": pg_i})
            except Exception:
                continue
    return out


def norm_key(s):
    """规范化映射键：去空白/换行（解决多行文字 \\r 匹配失效）。"""
    import re
    return re.sub(r"\s+", "", s or "")


def containers_of(doc):
    """收集候选容器（大对象）：[{lx,by,rx,ty,w,h,area}]，按面积升序（优先最小包含）。"""
    out = []
    for s in walk(doc.ActivePage.Shapes):
        try:
            lx, bx, rx, ty = s.LeftX, s.BottomY, s.RightX, s.TopY
            w, h = rx - lx, ty - bx
        except Exception:
            continue
        if w > 30 and h > 60:
            out.append({"lx": lx, "by": bx, "rx": rx, "ty": ty, "w": w, "h": h, "area": w * h})
    out.sort(key=lambda c: c["area"])
    return out


def container_for(containers, cx, cy):
    """包含点 (cx,cy) 的最小面积容器；无则 None。"""
    for c in containers:
        if c["lx"] - 0.5 <= cx <= c["rx"] + 0.5 and c["by"] - 0.5 <= cy <= c["ty"] + 0.5:
            return c
    return None


def fit_and_center(shape, app, container, old_cx, warnings, what):
    """替换后：恢复水平中心 → 越界检测 → 自动缩放字号（保持中心），最多 6 次迭代。"""
    try:
        cur_cx = (shape.LeftX + shape.RightX) / 2.0
        shape.Move(old_cx - cur_cx, 0)
    except Exception:
        pass
    if container is None:
        return
    MARGIN = 1.5
    avail_l, avail_r = container["lx"] + MARGIN, container["rx"] - MARGIN
    avail_w = avail_r - avail_l
    for _ in range(6):
        try:
            lx, rx = shape.LeftX, shape.RightX
        except Exception:
            return
        if lx >= avail_l - 0.2 and rx <= avail_r + 0.2:
            return
        try:
            st = shape.Text.Story
            cur = st.Size
        except Exception:
            return
        w = rx - lx
        if w <= 0.1:
            return
        ratio = max(0.25, min(1.0, avail_w / w))
        new_size = max(3.0, cur * ratio)
        if abs(new_size - cur) < 0.05:
            break
        st.Size = new_size
        try:
            shape.Move(old_cx - (shape.LeftX + shape.RightX) / 2.0, 0)
        except Exception:
            pass
    try:
        if shape.RightX > avail_r + 0.3 or shape.LeftX < avail_l - 0.3:
            warnings.append("[越界] %s 缩放后仍超容器，字号已压至下限" % what)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--list-only", action="store_true", help="仅列出文字清单不修改")
    args = ap.parse_args()

    if not os.path.isfile(args.template):
        die(2, "模板不存在: %s" % args.template)
    try:
        with open(args.mapping, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception as e:
        die(2, "映射读取失败: %s" % e)
    os.makedirs(args.out, exist_ok=True)

    app = connect()
    try:
        for d in list(app.Documents):
            try:
                if not d.FileName:
                    d.Close()
            except Exception:
                pass
    except Exception:
        pass

    # 1) 复制模板 → 原样版工作副本
    work_cdr = os.path.join(args.out, "%s_原样.cdr" % args.name)
    shutil.copy(args.template, work_cdr)
    log("模板已复制 → %s" % work_cdr)

    doc = app.OpenDocument(work_cdr)
    doc.Unit = 3
    texts = list_text_shapes(doc)
    log("文字对象共 %d 个" % len(texts))

    if args.list_only:
        for t in texts:
            log("#%d p%d @(%0.1f,%0.1f) %r" % (t["idx"], t["page"], t["lx"], t["ty"], t["text"][:30]))
        doc.Close()
        RESULT["status"] = "listed"
        sys.exit(0)

    # 2) 按映射替换（精确 → 规范化模糊 → #序号），替换后居中+越界缩放
    by_content = {k: v for k, v in mapping.items() if not k.startswith("#")}
    by_norm = {norm_key(k): v for k, v in mapping.items() if not k.startswith("#")}
    by_index = {int(k[1:]): v for k, v in mapping.items() if k.startswith("#")}
    containers = containers_of(doc)
    log("候选容器 %d 个" % len(containers))
    for t in texts:
        new_val = None; src = None
        if t["text"] in by_content:
            new_val = by_content[t["text"]]; src = "内容匹配"
        elif norm_key(t["text"]) in by_norm:
            new_val = by_norm[norm_key(t["text"])]; src = "规范化匹配"
        elif t["idx"] in by_index:
            new_val = by_index[t["idx"]]; src = "序号#%d" % t["idx"]
        if new_val is None:
            continue
        try:
            shape = t["shape"]
            st = shape.Text.Story
            old = st.Text
            old_cx = (t["lx"] + t["rx"]) / 2.0
            st.Text = new_val
            # 中心恢复 + 越界缩放（容器=包含文字中心点的最小容器）
            cont = container_for(containers, (shape.LeftX + shape.RightX) / 2.0,
                                 (shape.BottomY + shape.TopY) / 2.0)
            fit_and_center(shape, app, cont, old_cx, RESULT["warnings"],
                           "#%d %r→%r" % (t["idx"], old[:10], new_val[:10]))
            RESULT["replaced"].append({"idx": t["idx"], "from": old[:30], "to": new_val[:30], "via": src})
            log("  替换#%d (%s): %r → %r" % (t["idx"], src, old[:20], new_val[:20]))
        except Exception as e:
            RESULT["warnings"].append("替换 #idx=%d 失败: %s" % (t["idx"], e))

    # 3) Save() 存回原样 .cdr
    doc.Save()
    RESULT["outputs"]["editable_cdr"] = work_cdr
    log("原样 .cdr 已保存: %s (%d 字节)" % (work_cdr, os.path.getsize(work_cdr)))
    doc.Close()

    # 4) 转曲版：复制原样 → OpenDocument → 全文转曲 → Save()
    curves_cdr = os.path.join(args.out, "%s_转曲.cdr" % args.name)
    shutil.copy(work_cdr, curves_cdr)
    doc2 = app.OpenDocument(curves_cdr)
    doc2.Unit = 3
    conv = 0
    for s in walk(doc2.ActivePage.Shapes):
        try:
            if s.Text.Story is not None:
                s.ConvertToCurves(); conv += 1
        except Exception:
            pass
    doc2.Save()
    doc2.Close()
    RESULT["outputs"]["curves_cdr"] = curves_cdr
    log("转曲 .cdr 已保存（转曲 %d 个文字对象）: %s" % (conv, curves_cdr))

    # 5) PDF（文字转曲）+ PNG 预览（以原样版为准）
    doc3 = app.OpenDocument(work_cdr)
    pdf_path = os.path.join(args.out, "%s.pdf" % args.name)
    try:
        ps = doc3.PDFSettings
        ps.ColorMode = 1
        ps.TextAsCurves = True
        ps.PublishRange = 1
        ps.PageRange = "1"
        doc3.PublishToPDF(pdf_path)
        RESULT["outputs"]["pdf"] = pdf_path
        log("PDF 已导出: %s (%d 字节)" % (pdf_path, os.path.getsize(pdf_path)))
    except Exception as e:
        die(4, "PDF 导出失败: %s" % e)
    png_path = os.path.join(args.out, "%s_preview.png" % args.name)
    try:
        doc3.Export(png_path, 802, 1, None, None)
        RESULT["outputs"]["png"] = png_path
        log("PNG 预览已导出: %s" % png_path)
    except Exception as e:
        RESULT["warnings"].append("PNG 导出失败: %s" % e)
    doc3.Close()

    RESULT["status"] = "done"
    rp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hangtag_fill_result.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(RESULT, f, ensure_ascii=False, indent=2)
    log("完成。CorelDRAW 文档保持打开。")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        log("FATAL: %s" % e)
        RESULT["status"] = "error"
        RESULT["error"] = str(e)
        sys.exit(4)
