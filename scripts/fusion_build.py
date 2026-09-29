# -*- coding: utf-8 -*-
"""
融合批次（R11+）：从 demo_mixed_v1 模板中融合三套设计元素为一套新吊牌（2 张）
- 正面 = 模板1 蓝色圆角卡(50x90+圆孔+主标题) + 模板3 椭圆照片 PowerClip（缩放置中）
- 背面 = 模板2 白背面(55x95+条形孔+洗涤说明) + 模板3 卖点文字（山间散养/自然喂养/贮存方式）
- 实现：Duplicate 页1→页2，按保留框筛选删除，重排，文字替换，导出
- 保留框（R5 精确坐标，中心点匹配）：
  F1 蓝卡 (135.05,106.57)-(185.05,196.57)
  F2 白背面 (102.2,-11.12)-(157.2,83.88)
  F3 椭圆照片卡 (47.19,-108.18)-(97.19,-28.18)  ← 排除大位图源图(type5且w>60)
  F4 胶囊卖点文字窄框 (184,-58)-(208,-44)
"""
import os
import win32com.client

TPL = r"C:/Users/Mayn/Documents/cdr_auto_test/tpl_fusion_base.cdr"
OUT = r"C:\Users\Mayn\Desktop\CDR AUTo\outputs\fusion"
NAME = "融合吊牌"
os.makedirs(OUT, exist_ok=True)

F1 = (135.05, 106.57, 185.05, 196.57)
F2 = (102.2, -11.12, 157.2, 83.88)
F3 = (47.19, -108.18, 97.19, -28.18)
F4 = (178.0, -100.0, 210.0, -44.0)
BOXES = [F1, F2, F3, F4]

app = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application")
app.Visible = True
doc = app.OpenDocument(TPL)
doc.Unit = 3
pg1 = doc.Pages(1)
print("直接在模板副本上就地融合（无跨页复制）")


def walk(shapes, in_pc=False):
    for s in shapes:
        yield s, in_pc
        try:
            if s.Shapes.Count:
                for x in walk(s.Shapes, in_pc):
                    yield x
        except Exception:
            pass
        try:
            pc = s.PowerClip
            if pc is not None:
                for x in walk(pc.Shapes, True):   # PowerClip 内容标记
                    yield x
        except Exception:
            pass


def center(o):
    return ((o["lx"] + o["rx"]) / 2.0, (o["by"] + o["ty"]) / 2.0)


def in_box(cx, cy, b):
    return b[0] - 1 <= cx <= b[2] + 1 and b[1] - 1 <= cy <= b[3] + 1


# 收集页 2 全部对象（含边界信息）
objs = []
for s, in_pc in walk(pg1.Shapes):
    try:
        o = {"shape": s, "lx": s.LeftX, "by": s.BottomY, "rx": s.RightX, "ty": s.TopY,
             "type": s.Type, "text": "", "in_pc": in_pc}
        o["w"] = o["rx"] - o["lx"]; o["h"] = o["ty"] - o["by"]
        try:
            st = s.Text.Story
            if st is not None and st.Text is not None:
                o["text"] = st.Text
        except Exception:
            pass
        objs.append(o)
    except Exception:
        pass
print("对象：", len(objs))

# 保留/删除判定
keep, delete = [], []
for o in objs:
    cx, cy = (o["lx"] + o["rx"]) / 2.0, (o["by"] + o["ty"]) / 2.0
    if o.get("in_pc"):
        keep.append((o, "PC")); continue   # PowerClip 内容强制保留（随容器）
    hit = next((b for b in BOXES if in_box(cx, cy, b)), None)
    if hit is None:
        delete.append(o); continue
    if o["type"] == 5 and o["w"] > 60:
        delete.append(o); continue   # 独立大源位图（未裁切素材），删
    keep.append((o, hit))
print("保留 %d / 删除 %d" % (len(keep), len(delete)))
for o, b in keep:
    print("  KEEP %s t=%d %0.1fx%0.1f @(%0.1f,%0.1f) %r" % (
        "F1" if b is F1 else "F2" if b is F2 else "F3" if b is F3 else "F4",
        o["type"], o["w"], o["h"], o["lx"], o["by"], o["text"][:16]))
for o in delete:
    try:
        o["shape"].Delete()
    except Exception:
        pass   # 级联删除时子对象引用失效，属正常

# 重排：正面组（F1）平移到 (95,57.5)；背面组（F2）平移到 (152,57.5)
dx1, dy1 = 95.0 - F1[0], 57.5 - F1[1]
dx2, dy2 = 152.0 - F2[0], 57.5 - F2[1]
for o, b in keep:
    if b == "PC":
        continue
    dx, dy = (dx1, dy1) if b is F1 else (dx2, dy2)
    try:
        o["shape"].Move(dx, dy)
    except Exception:
        pass

# 椭圆照片卡（F3）：缩放 0.8 → 40x64，中心放到正面卡中下部 (120.5, 100)
for o, b in keep:
    if b == "PC":
        continue
    if b is F3 and o["type"] == 2 and o["w"] > 20:
        try:
            sh = o["shape"]
            sh.SetSize(40.0, 64.0)
            cx = (sh.LeftX + sh.RightX) / 2.0
            cy = (sh.BottomY + sh.TopY) / 2.0
            sh.Move(120.5 - cx, 102.0 - cy)
            print("椭圆照片容器已置入正面卡中部 (40x64)")
        except Exception as e:
            print("椭圆缩放失败:", repr(e)[:80])
    if b is F4 and o.get("text"):
        try:
            o["shape"].Move(dx2, dy2)
            print("卖点文字已移至背面:", o["text"][:12])
        except Exception:
            pass

# 文字替换（融合语义）
REPLACE = {
    "HAPPY\rBABY": "NATURE\rFARM",
    "HAPPY BABY": "NATURE FARM",
    "山林散养蛋": "田园土鸡蛋",
    "山间散养": "高山牧场",
    "自然喂养": "五谷喂养",
    "贮存方式：阴凉干燥": "贮存方式：置阴凉避光",
    "Fashion": "NATURE",
    "Beauty with elegance.": "Crafted with care.",
}
for o, b in keep:
    if not o["text"]:
        continue
    key = o["text"].strip()
    new = None
    for k, v in REPLACE.items():
        if key == k or key.replace("\r", " ").replace("\n", " ") == k:
            new = v; break
    if new:
        try:
            old = o["shape"].Text.Story.Text
            o["shape"].Text.Story.Text = new
            print("  文字: %r → %r" % (old[:20], new))
        except Exception as e:
            print("  文字替换失败:", repr(e)[:60])

# 导出页 2 + Save
pdf = os.path.join(OUT, NAME + ".pdf")
png = os.path.join(OUT, NAME + "_preview.png")
try:
    ps = doc.PDFSettings
    ps.ColorMode = 1; ps.TextAsCurves = True
    ps.PublishRange = 1; ps.PageRange = "2"
    doc.PublishToPDF(pdf)
    print("PDF:", pdf, os.path.getsize(pdf))
except Exception as e:
    print("PDF fail:", repr(e)[:100])
try:
    doc.Export(png, 802, 1, None, None)
    print("PNG:", png, os.path.getsize(png))
except Exception as e:
    print("PNG fail:", repr(e)[:100])
doc.Save()
doc.Close()
print("FUSION DONE")
