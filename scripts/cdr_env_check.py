# -*- coding: utf-8 -*-
"""
coreldraw-hangtag 环境自检
输出 JSON：python 位数 / pywin32 / CorelDRAW 连接与版本 / 修复提示
退出码：0 全部正常 / 1 存在问题（看 hints）
"""
import sys
import json
import struct


def main():
    result = {"ok": True, "python_bits": struct.calcsize("P") * 8, "pywin32": False,
              "coreldraw": {"connected": False, "version": None, "documents": None},
              "hints": []}

    if result["python_bits"] != 64:
        result["ok"] = False
        result["hints"].append("Python 必须是 64 位（CorelDRAW 为 64 位，位数必须匹配）")

    try:
        import win32com.client  # noqa
        result["pywin32"] = True
    except Exception:
        result["ok"] = False
        result["pywin32"] = False
        result["hints"].append(
            "pywin32 未安装或已丢失，执行: \"<PYTHON>\" -m pip install --no-cache-dir pywin32")

    if result["pywin32"] and result["python_bits"] == 64:
        try:
            app = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application")
            app.Visible = True
            result["coreldraw"]["connected"] = True
            result["coreldraw"]["version"] = str(app.Version)
            result["coreldraw"]["documents"] = int(app.Documents.Count)
            log_msg = "COM 连接正常"
        except Exception as e:
            result["ok"] = False
            msg = str(e)
            result["hints"].append(
                "CorelDRAW COM 连接失败: %s；若报 CLSIDToClassMap，删除 "
                "%%LOCALAPPDATA%%\\Temp\\gen_py\\<ver>\\FBF4300F-* 目录后重试" % msg[:160])
        else:
            result["log"] = log_msg

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
