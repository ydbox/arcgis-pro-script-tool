# -*- coding: utf-8 -*-
"""
<工具中文名>（<EnglishName>）

功能：
    <做什么；输入 → 输出。>
    <如果会直接修改输入数据，在这里写明："注意：本工具直接修改输入数据，建议先备份。">

参数（序号与 Pro「工具属性 → 参数」一一对应）：
    0  <标注>    <数据类型>    <必填/可选>  <输入/输出>  <说明>
    1  <标注>    <数据类型>    <必填/可选>  <输入/输出>  <说明>

需求确认记录（向用户确认过的口径写在这里，方便以后改）：
    - <例：来源要素名称为空的行视为表格结束，而不是跳过>

运行环境：ArcGIS Pro 3.x / Python 3（arcgispro-py3）
命令行测试（可选参数留空时写 #）：
    在 cmd 窗口里直接运行：
        "<Pro 安装目录>\\bin\\Python\\envs\\arcgispro-py3\\python.exe" 本文件.py <参数0> <参数1> ...
    由 AI 在终端里运行：用 skill 自带的 scripts/run_tool_test.py，中文不会乱码
"""
import os
import time
import traceback

import arcpy


# =========================================================== 通用辅助函数
# 这些函数是这个工具要用到的；用不到的就删掉，不要留着

def log(msg, level="info"):
    """输出到 Pro 消息窗口；命令行运行时 arcpy 也会打印到控制台。"""
    {"info": arcpy.AddMessage, "warn": arcpy.AddWarning, "error": arcpy.AddError}[level](msg)


def is_empty(text):
    """Pro 里可选参数留空返回 ""；命令行里留空通常写 "#"。两种都当作空。"""
    return text is None or str(text).strip() in ("", "#")


def get_text(index, default=""):
    text = arcpy.GetParameterAsText(index)
    return default if is_empty(text) else text.strip()


def get_bool(index, default=False):
    # 不用 GetParameter：命令行运行时它返回的是字符串 'false'，而 'false' 的真值是 True
    text = arcpy.GetParameterAsText(index)
    return default if is_empty(text) else text.strip().lower() == "true"


def get_number(index, cast=float, default=None):
    text = arcpy.GetParameterAsText(index)
    if is_empty(text):
        return default
    try:
        return cast(text.strip())
    except ValueError:
        raise ValueError(f"参数 {index} 应为数字，实际为：{text}")


def split_multi(text):
    """多值参数 → 列表。Pro 会给含空格的路径加单引号：a;'C:\\有 空格\\b.shp'。"""
    if is_empty(text):
        return []
    items = (s.strip().strip("'\"") for s in str(text).split(";"))
    return [s for s in items if s and s != "#"]


def parse_linear_unit(text, to_unit="Meters"):
    """线性单位参数 '10 Meters' → 换算成 to_unit 的浮点数。没写单位时按 to_unit 处理。"""
    value, _, unit = str(text).strip().partition(" ")
    factor = arcpy.LinearUnitConversionFactor(unit.strip(), to_unit) if unit.strip() else 1.0
    return float(value) * factor


def catalog_path(layer_or_path):
    """图层名 → 数据源路径。注意：转换后就不再受图层选择集和定义查询的限制了。"""
    return arcpy.Describe(layer_or_path).catalogPath


def walk_gdb(workspace, datatype=("FeatureClass", "Table")):
    """遍历 GDB 里的全部要素类和表，包括要素数据集里的；返回完整路径。
    不要用 arcpy.ListFeatureClasses()，它只列出根目录下的。"""
    for root, _dirs, names in arcpy.da.Walk(workspace, datatype=list(datatype)):
        for name in names:
            yield os.path.join(root, name)


def find_field(dataset, name):
    """不区分大小写地查找字段，返回 Field 对象；找不到返回 None。"""
    lookup = {f.name.lower(): f for f in arcpy.ListFields(dataset)}
    return lookup.get(str(name).lower())


class TempData:
    """登记本次运行产生的临时数据，结束时统一删除。
    只删除自己登记过的数据，绝不按"工作空间里的全部内容"去删。"""

    def __init__(self, workspace="memory"):
        # 默认用 memory；数据量大、要生成栅格或者某个工具不支持 memory 时，改成 arcpy.env.scratchGDB
        self.workspace = workspace
        self.items = []

    def new(self, base_name):
        path = arcpy.CreateUniqueName(base_name, self.workspace)
        self.items.append(path)
        return path

    def cleanup(self):
        for path in reversed(self.items):
            try:
                if arcpy.Exists(path):
                    arcpy.management.Delete(path)
            except Exception as exc:  # 清理失败不能掩盖主流程的结果
                log(f"临时数据删除失败，可以手动删除：{path}（{exc}）", "warn")
        self.items.clear()


class Progress:
    """大循环按间隔报告进度，避免每个要素都输出消息把 Pro 拖慢。"""

    def __init__(self, total, label="处理中", steps=20):
        self.total = max(int(total), 1)
        self.every = max(1, self.total // steps)
        self.label = label
        arcpy.SetProgressor("step", label, 0, self.total, self.every)

    def update(self, i):
        if i % self.every == 0 or i == self.total:
            arcpy.SetProgressorLabel(f"{self.label} {i}/{self.total}")
            arcpy.SetProgressorPosition(i)

    @staticmethod
    def close():
        arcpy.ResetProgressor()


# =========================================================== 业务逻辑

def process_one(item, temp):
    """处理单个对象。成功返回 True；可以跳过的情况用 log(..., "warn") 说明原因后返回 False。"""
    # TODO: 实现
    return True


def main():
    # ---- 1. 读取参数（序号必须与参数表一致）
    in_items = split_multi(arcpy.GetParameterAsText(0))
    out_path = get_text(1)
    some_flag = get_bool(2, default=False)

    # ---- 2. 校验：发现问题就明确报错，不要带着错误的输入继续算
    if not in_items:
        raise ValueError("没有可处理的输入")
    for item in in_items:
        if not arcpy.Exists(item):
            raise ValueError(f"输入不存在：{item}")

    # ---- 3. 执行
    arcpy.env.overwriteOutput = True
    temp = TempData()
    start = time.time()
    ok, failed = 0, []
    log("===== 开始：<工具中文名> =====")
    try:
        for i, item in enumerate(in_items, 1):
            log(f"[{i}/{len(in_items)}] {item}")
            try:  # 批处理：一个失败不影响其余的，记录原因，最后汇总
                if process_one(item, temp):
                    ok += 1
            except arcpy.ExecuteError:
                failed.append(item)
                log(f"  失败：{arcpy.GetMessages(2)}", "warn")
            except Exception as exc:
                failed.append(item)
                log(f"  失败：{exc}", "warn")

        if out_path:
            arcpy.SetParameterAsText(1, out_path)  # 只有方向为"输出/派生"的参数才需要回写
    finally:
        temp.cleanup()

    log(f"===== 完成：成功 {ok} 个，失败 {len(failed)} 个，用时 {time.time() - start:.1f} 秒 =====")
    if failed:
        log("失败清单：\n  " + "\n  ".join(failed), "warn")


if __name__ == "__main__":
    try:
        main()
    except arcpy.ExecuteError:
        log(arcpy.GetMessages(2), "error")
        raise  # 重新抛出：Pro 会把工具标记为失败，命令行运行时返回非 0
    except Exception:
        log(traceback.format_exc(), "error")
        raise
