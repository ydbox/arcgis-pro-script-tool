# -*- coding: utf-8 -*-
"""
在命令行测试 ArcGIS Pro 脚本工具，任何终端下（Bash / PowerShell / cmd）中文输出都正常。

用法（要用 ArcGIS Pro 自带的 Python 运行）：
    "<Pro 安装目录>\\bin\\Python\\envs\\arcgispro-py3\\python.exe" run_tool_test.py <工具脚本.py> <参数0> <参数1> ...
    可选参数留空时写 #

效果：
    - 在子进程里运行工具脚本；arcpy.GetParameterAsText(i) 会读到这些命令行参数
    - arcpy 消息是按系统代码页（中文 Windows 上是 GBK）输出的；这里统一解码后按 UTF-8 打印
    - 完整输出同时写到 <工具脚本>.test.log（UTF-8）。终端显示仍然乱码时，直接读这个文件
    - 退出码与工具脚本一致：0 表示成功，非 0 表示失败
"""
import ctypes
import os
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    tool, args = sys.argv[1], sys.argv[2:]
    env = dict(os.environ)
    # 去掉会让 Python 改用 UTF-8 输出的设置。子进程里 Python 的输出和 arcpy 的原生消息都按系统代码页输出，才能用同一种编码解码
    for key in ("PYTHONIOENCODING", "PYTHONUTF8"):
        env.pop(key, None)

    proc = subprocess.run([sys.executable, tool, *args], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    codepage = f"cp{ctypes.windll.kernel32.GetACP()}" if os.name == "nt" else "utf-8"
    text = proc.stdout.decode(codepage, errors="replace")

    log_path = os.path.splitext(tool)[0] + ".test.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(text)
        f.write(f"\n[exit code] {proc.returncode}\n")

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(text)
    print(f"[exit code] {proc.returncode}    [log] {log_path}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
