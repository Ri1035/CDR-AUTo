# -*- coding: utf-8 -*-
"""
模板登记器（template_register.py）— 模板库入库工具
把一个 .cdr 模板"摸清构成"并登记进模板库：
  1. 复制模板到 templates/<id>/template.cdr
  2. COM 分析：页面/卡片聚类（按尺寸+位置）/文字清单/位图/PowerClip/孔位
  3. 生成 <id>/meta.json 草稿（fields 的 field 名留 TODO，由用户/agent 语义命名后回填）
  4. 更新 templates/index.json 索引
用法：
  python template_register.py --template 模板.cdr --id baby_set_v1 --lib "C:/.../templates"
"""
import os
import sys
import json
import shutil
import argparse

import win32com.client

RESULT = {"status": "running", "log": [], "warnings": []}


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
        app.Visible = True
        log("已连接 CorelDRAW")
    except Exception as e:
        die(3, "连接失败: %s" % e)
    return app


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


def analyze(doc):
    pg = doc.ActivePage
    objs = []
    for s in walk(pg.Shapes):
        try:
            lx, bx, rx, ty = s.LeftX, s.BottomY, s.RightX, s.TopY
            t = s.Type
        except Exception:
            continue
        w, h = rx - lx, ty - bx
        o = {"type": t, "lx": round(lx, 2), "by": round(bx, 2),
             "rx": round(rx, 2), "ty": round(ty, 2), "w": round(w, 2), "h": round(h, 2)}
        try:
            st = s.Text.Story
            if st is not None and st.Text is not None:
                o["text"] = st.Text
                o["is_text"] = True
        except Exception:
            pass
        try:
            if s.Bitmap is not None:
                o["is_bitmap"] = True
        except Exception:
            pass
        try:
            if s.PowerClip is not None:
                o["is_powerclip"] = True
        except Exception:
            pass
        objs.append(o)
    return objs, pg.SizeWidth, pg.SizeHeight


def cluster_cards(objs):
    """矩形卡聚类：同尺寸 + 垂直带重叠 + 水平邻近（间隙 < 卡宽）归为一套。"""
    rects = [o for o in objs if o["type"] == 1 and o["w"] > 20 and o["h"] > 30
             and not (11.4 <= o["w"] <= 12.6)]
    # 按尺寸分组（容差 1mm）
    groups = {}
    for r in rects:
        key = None
        for k in groups:
            if abs(k[0] - r["w"]) <= 1 and abs(k[1] - r["h"]) <= 1:
                key = k; break
        groups.setdefault(key or (round(r["w"]), round(r["h"])), []).append(r)
    sets = []
    for (w, h), rs in sorted(groups.items(), key=lambda kv: (-kv[1][0]["ty"], kv[1][0]["lx"])):
        rs.sort(key=lambda o: o["lx"])
        # 按水平间隙切套（相邻卡左缘差 > 卡宽*1.2 则分套）
        chunks, cur = [], [rs[0]]
        for prev, cur_r in zip(rs, rs[1:]):
            if cur_r["lx"] - (prev["lx"] + prev["w"]) > w * 1.2:
                chunks.append(cur); cur = [cur_r]
            else:
                cur.append(cur_r)
        chunks.append(cur)
        for i, chunk in enumerate(chunks):
            xs = [o["lx"] for o in chunk]; ys = [o["by"] for o in chunk]
            sets.append({
                "set_id": "set_%dx%d_%d" % (round(w), round(h), i + 1),
                "card_size": [w, h], "card_count": len(chunk),
                "bbox": [round(min(xs), 2), round(min(ys), 2),
                         round(max(o["rx"] for o in chunk), 2), round(max(o["ty"] for o in chunk), 2)],
                "location": "on_page" if min(ys) >= 0 and max(ys) <= 297 else "off_page",
                "cards": [{"bbox": [o["lx"], o["by"], o["rx"], o["ty"]],
                           "role": "TODO(正/背)"} for o in chunk]
            })
    return sets, rects


def collect_fields(objs):
    """文字字段清单（idx 按全局枚举顺序）。"""
    fields = []
    idx = 0
    for o in objs:
        idx += 1
        if o.get("is_text"):
            fields.append({
                "shape_idx": idx,
                "placeholder": o.get("text", ""),
                "field": "TODO_%d" % len(fields),
                "bbox": [o["lx"], o["by"], o["rx"], o["ty"]],
                "font": "TODO(登记时核对)",
                "max_chars": "TODO(建议值)",
                "note": ""
            })
    return fields, idx


def collect_assets(objs):
    return {
        "bitmaps": [{"bbox": [o["lx"], o["by"], o["rx"], o["ty"]], "w": o["w"], "h": o["h"],
                     "color_mode": "TODO(核对 CMYK/灰度)", "is_powerclip": o.get("is_powerclip", False)}
                    for o in objs if o.get("is_bitmap")],
        "powerclips": [{"bbox": [o["lx"], o["by"], o["rx"], o["ty"]], "type": o["type"]}
                       for o in objs if o.get("is_powerclip")],
        "loose_curves": sum(1 for o in objs if o["type"] == 3),
        "ungrouped_note": "模板含大量未群组对象时，填充按文字对象定位（不依赖群组）"
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--id", required=True, help="模板 ID（英文/数字/下划线）")
    ap.add_argument("--lib", default=None, help="模板库根目录（默认 <仓库>/templates）")
    args = ap.parse_args()

    if not os.path.isfile(args.template):
        die(2, "模板不存在: %s" % args.template)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lib = args.lib or os.path.join(repo, "templates")
    tdir = os.path.join(lib, args.id)
    if os.path.exists(tdir):
        die(2, "模板 ID 已存在: %s（换一个 id 或先删除）" % args.id)
    os.makedirs(tdir, exist_ok=True)

    # 1) 复制模板
    tfile = os.path.join(tdir, "template.cdr")
    shutil.copy(args.template, tfile)
    log("模板已入库: %s (%d 字节)" % (tfile, os.path.getsize(tfile)))

    # 2) COM 分析
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
    doc = app.OpenDocument(tfile)
    doc.Unit = 3
    objs, pw, ph = analyze(doc)
    log("分析完成：%d 对象，页面 %.0fx%.0fmm" % (len(objs), pw, ph))

    sets, rects = cluster_cards(objs)
    fields, total = collect_fields(objs)
    assets = collect_assets(objs)

    # 孔位（沿用模板，不做坐标规范化——记录存在性）
    holes = {"strategy": "沿用模板已有孔对象", "circle_4mm": 0, "bar_12x2.5": 0}
    for o in rects:
        pass
    for o in objs:
        if o["type"] == 2 and 3.4 <= o["w"] <= 4.6 and abs(o["w"] - o["h"]) < 0.4:
            holes["circle_4mm"] += 1
        if o["type"] == 1 and 11.4 <= o["w"] <= 12.6 and 1.9 <= o["h"] <= 3.0:
            holes["bar_12x2.5"] += 1

    doc.Close()

    # 3) meta.json 草稿
    meta = {
        "template_id": args.id,
        "source_file": os.path.basename(args.template),
        "format": "X4(v14)——由 X4 实机保存，兼容 2020",
        "page": {"width": round(pw, 2), "height": round(ph, 2)},
        "sets": sets,
        "fields": fields,
        "assets": assets,
        "holes": holes,
        "status": "draft——field 名/max_chars/卡片 role 由用户或 agent 语义命名后回填",
        "registered_at": __import__("datetime").datetime.now().isoformat(timespec="seconds")
    }
    meta_path = os.path.join(tdir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    log("meta.json 草稿已生成: %s（%d 个字段待语义命名）" % (meta_path, len(fields)))

    # 4) 更新 index.json
    index_path = os.path.join(lib, "index.json")
    index = {"templates": []}
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except Exception:
            pass
    index["templates"] = [t for t in index.get("templates", []) if t.get("id") != args.id]
    index["templates"].append({"id": args.id, "dir": os.path.relpath(tdir, lib),
                               "sets": len(sets), "fields": len(fields),
                               "format": "X4", "status": "draft"})
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    log("index.json 已更新（共 %d 个模板）" % len(index["templates"]))

    RESULT["status"] = "done"
    RESULT["outputs"] = {"template": tfile, "meta": meta_path, "index": index_path}
    rp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_register_result.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(RESULT, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        log("FATAL: %s" % e)
        RESULT["status"] = "error"
        sys.exit(4)
