# 工具参数 → Python 读取对照

用户给的参数表通常是 Pro「工具属性 → 参数」页的直接转录，列包括：序号、标注、名称、数据类型、类型（必填/可选/派生）、方向、多值、依赖关系、过滤器、默认值。**序号就是 `GetParameterAsText(i)` 的 i**。

## 两种运行方式，行为不一样（本机 Pro 3.7 已实测）

| 运行方式 | `GetParameterAsText(i)` | `GetParameter(i)` | 可选参数留空 |
| --- | --- | --- | --- |
| 在 Pro 里作为脚本工具运行 | 字符串 | **按类型返回的对象**（布尔 → `bool`，坐标系 → `SpatialReference`，值表 → `ValueTable`） | `""` |
| 命令行 `python 脚本.py 参数0 参数1 …` | 读 `sys.argv[i+1]` | **也是字符串**（布尔是 `'true'`） | 字面量 `"#"`，不会自动转成空 |

结论：**统一用 `GetParameterAsText` 再自己转换**，并把 `""` 和 `"#"` 都视为空。这样同一个脚本既能在 Pro 里跑，也能在命令行用测试数据跑（见 SKILL.md 的"自检"一节）。辅助函数在 `templates/script_tool_template.py` 里。

## 数据类型对照

| 中文界面数据类型 | 英文 | `GetParameterAsText` 返回 | 处理方式 |
| --- | --- | --- | --- |
| 要素图层 | Feature Layer | 地图图层名，或完整路径 | GP 工具和 `arcpy.da` 游标都能直接用，且**只处理选中的要素**（有选择集时）。需要真实路径（拼输出名、`os.path`、判断所在 GDB）时用 `arcpy.Describe(v).catalogPath` |
| 要素类 | Feature Class | 完整路径 | 直接用 |
| 表 / 表视图 | Table / Table View | 路径或表视图名 | 同要素图层 |
| 栅格数据集 / 栅格图层 | Raster Dataset / Layer | 路径或图层名 | `arcpy.Raster(v)`；`arcpy.sa` 的函数直接传 |
| 工作空间 | Workspace | `.gdb` 或文件夹路径 | `arcpy.Describe(v).workspaceType`：`LocalDatabase`（GDB）/ `FileSystem`（文件夹）/ `RemoteDatabase`（SDE） |
| 文件夹 | Folder | 路径 | `os.walk`（shp、tif、srt 等文件）或 `arcpy.da.Walk`（GIS 数据） |
| 文件 | File | 路径（过滤器限制扩展名） | 按扩展名分支：`.xls` → xlrd，`.xlsx` → openpyxl / pandas |
| 字段 | Field | 字段名 | 通常"依赖"某个输入图层；写入前确认字段存在、类型和长度合适 |
| 字符串 + 值列表 | String (Value List) | 选中项文本 | 与值列表**逐字**比较（中文值要一字不差）；比较前 `strip()` |
| 布尔 | Boolean | `'true'` / `'false'` | `to_bool()` |
| 双精度 / 长整型 | Double / Long | `'12.5'` / `'3'` | `float()` / `int()`，空值先判断 |
| 线性单位 | Linear Unit | `'10 Meters'`（单位是英文关键字） | 传给 GP 工具时直接用原字符串；自己算数时用 `parse_linear_unit()` 换成米（内部用 `arcpy.LinearUnitConversionFactor`） |
| 空间参考 / 坐标系 | Spatial Reference / Coordinate System | 坐标系 WKT 字符串 | 传给 `CreateFeatureclass` 等工具可以直接用字符串；需要对象时 `sr = arcpy.SpatialReference(); sr.loadFromString(text)` |
| 值表 | Value Table | `'a 1;b 2'` | 按 `;` 分行、按空格分列；列值里有空格时会带引号 |
| **多值 `[xxx]`** | Multivalue | `"a;b;'C:\\有 空格\\c.shp'"` | `split_multi()`：按 `;` 拆开，去掉每项两端的引号 |
| 派生输出 | Derived | — | 脚本结束前 `arcpy.SetParameterAsText(i, 输出路径)` |

## 输出参数与"加到地图"

- 方向为**输出**的要素类 / 图层 / 栅格参数，工具运行结束后 Pro 会**自动**加到当前地图（`arcpy.env.addOutputsToMap` 默认为 True）。这时**不要**再用代码手动加，否则地图里会出现两个同名图层。
- 只有**不是输出参数**的结果（比如一次生成多个要素类、过程数据需要给用户看）才手动加：

```python
def add_to_active_map(path):
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
    except OSError:
        log("不在 ArcGIS Pro 内运行，跳过加载到地图", "warn")
        return
    m = aprx.activeMap
    if m is None:
        log("没有活动地图，跳过加载", "warn")
        return
    m.addDataFromPath(path)          # 不要用 arcpy.mp.LayerFile(路径)：LayerFile 只接受 .lyrx
```

## 参数表体检（写代码前做）

历史参数表里出现过的问题，写代码前逐项检查：

- 序号重复或不连续（例如两行都是序号 1）。
- "依赖关系"写的是一个不存在的参数名（例如 `road_1yr`，实际叫 `road_lyr`）。
- 名称和标注对不上，或者有错别字（名称会出现在 Python 调用里，错一个字就会用错参数）。
- 方向为输出的参数被设成"必填 + 输入"，或者反过来。
- 选"字段"类型却没有设依赖，用户就选不了字段。
- 需求正文提到了某个输入，参数表里却没有（或者反过来）。

有问题就在第一轮提问里一起列出来，给出建议的修正版参数表。
