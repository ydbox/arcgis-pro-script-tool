# 高频坑清单

来源：20 份历史需求提示词 + 36 个实际在用的脚本（`E:\ai_coding\prj8\py\`）。标注【实测】的条目已在 ArcGIS Pro 3.7.1 上验证过。

## 1. 遍历与命名

- **【实测】`arcpy.ListFeatureClasses()` 只列根目录**，要素数据集里的要素类全部漏掉（用户在旧模板里专门记过这条"常犯错误"）。统一用 `arcpy.da.Walk(gdb, datatype=["FeatureClass", "Table"])`，它能同时覆盖根目录、要素数据集和独立表。不要只用 `arcpy.Exists("DLTB")` 判断要素类在不在，放在数据集里的会查不到。
- **需要区分"根目录要素类"和"数据集里的要素类"时**（例如复制 GDB 结构），用 `Walk` 的 `root` 判断：`root == gdb` 表示在根目录，否则 `os.path.basename(root)` 就是数据集名。
- **OID 字段不一定叫 OBJECTID**，也可能是 OID、FID、OBJECTID_1。游标里用 `"OID@"`；拼 SQL 时用 `Describe(ds).OIDFieldName` 加上 `arcpy.AddFieldDelimiters`。只要空结构、不要数据时，where 用 `f"{oid} < 0"`。
- **字段名大小写**：先建 `{f.name.lower(): f}` 字典再查，不要直接 `in` 比较。
- **输出名合法化**：`arcpy.ValidateTableName(name, workspace)` 和 `arcpy.ValidateFieldName(name, workspace)`。之前先把全角括号和全角空格换掉。shp 的字段名最多 10 个字符，合并后会被截断。
- **同名冲突**：临时数据用 `arcpy.CreateUniqueName`；用户能看到的输出如果需求要求"唯一"，加 `time.strftime("%Y%m%d_%H%M%S")` 后缀。

## 2. 图层与路径

- 输入参数是**要素图层**时，GP 工具和游标都**只处理选中的要素**。一旦用 `catalogPath` 转成路径，选择集和定义查询就失效了。要不要保留选择集，按需求判断，并在 docstring 里写明。
- **`AddJoin` 只接受图层或表视图**，传路径会报错，要先 `MakeFeatureLayer` 或 `MakeTableView`。连接后字段名会变成 `表名.字段名`，CalculateField 里写成 `!表名.字段名!`。用完 `RemoveJoin`。
- **能用字典就不用连接**：先用 SearchCursor 把连接表读成 `{key: value}`，再用一个 UpdateCursor 回写。比 AddJoin + CalculateField 更快，也不会碰到限定字段名的问题。历史需求里凡是写了"添加连接 → 计算字段 → 移除连接"的，默认用字典实现，除非用户明确要求用连接。

## 3. 字段

- **【实测】`ListFields` 返回的类型名不能直接传给 `AddField`**（历史 bug：WKT 工具直接 `AddField(field_type=field.type)`，然后失败被吞掉）。映射表：

  | ListFields `.type` | AddField `field_type` |
  | --- | --- |
  | String | TEXT（加上 `field_length=f.length`） |
  | Single | FLOAT |
  | Double | DOUBLE |
  | SmallInteger | SHORT |
  | Integer | LONG |
  | BigInteger | BIGINTEGER |
  | Date / DateOnly / TimeOnly / TimestampOffset | DATE / DATEONLY / TIMEONLY / TIMESTAMPOFFSET |
  | Guid / Blob / Raster | GUID / BLOB / RASTER |
  | OID / Geometry / GlobalID | 不复制（系统字段） |

- **空值判断**：`v is None or (isinstance(v, str) and v.strip() == "")`。数值 0 不是空值。
- **同一个字段在不同数据里类型可能不一样**：例如 YSJC 在一个库里是 SHORT，在另一个库里是 TEXT。拼 where 条件前先查字段类型，再决定要不要加引号。
- **CalculateField**：`expression_type="PYTHON3"`；空值要保护，例如 `(!KCXS! or 0)`；`field_type` 只在字段不存在、需要新建时才起作用。
- 批量删除字段用一次 `DeleteField(ds, [字段列表])`。判断"整列为空"时，用一次游标同时统计所有字段，不要每个字段都扫一遍全表。

## 4. 几何

- **【实测】曲线检测直接用 `geometry.hasCurves`**，不用解析 `geom.JSON` 找 `curveRings`。
- **按点重建几何**（`arcpy.Polyline(array, sr)`）会**丢掉曲线**；不传 `has_z=True` / `has_m=True` 还会丢 Z 值和 M 值。旋转、平移优先用几何对象自带的方法；必须重建时，从源几何读出 `hasZ` / `hasM` 再传进去。
- **`arcpy.edit.Densify`、`Snap` 等编辑工具直接改原数据**。要在 docstring 和开始时的警告消息里说明，并建议用户先备份，或者先复制一份再处理。
- **面积和长度**：投影坐标系用 `SHAPE@AREA` / `SHAPE@LENGTH`；地理坐标系用 `geom.getArea("GEODESIC", "SQUAREMETERS")` 或 `!shape.geodesicArea!`。不要默认单位是米：从 `sr.linearUnitName` 读取，或用 `arcpy.LinearUnitConversionFactor` 换算。经纬度差不要用 `/111320` 这种近似。
- **比较坐标系**用 `sr.factoryCode`；自定义坐标系的 factoryCode 是 0，这时再比较 `sr.exportToString()`。不要只比较 `.name`。
- **求范围的经纬度**：先把整个几何 `projectAs(目标坐标系)` 再取 extent，不要只投影左下角和右上角两个点。

## 5. Excel

本机 Pro 环境里有：pandas 3.0、openpyxl 3.1、xlrd 2.0（**只能读 .xls**）、xlwt 1.3（只能写 .xls）、pypinyin。

- **读取时按扩展名选引擎**：`.xlsx` 用 `engine="openpyxl"`，`.xls` 用 `engine="xlrd"`。建议 `pd.read_excel(path, sheet_name=..., dtype=str)`，缺失值用 `pd.isna(v)` 判断（pandas 3.0 里可能是 `NaN` 或 `pd.NA`）。
- **"C 列 = 名称，B 列 = 别名"这类按列字母的描述**：换算成 0 基索引（A=0）。同时确认第 1 行是不是表头、要不要跳过合并的标题行。
- **"读到空行就结束"还是"跳过空行"是两种不同的口径**。历史需求："来源要素名称为空（NaN）时表示已经没有要素需要处理了"，这是结束。口径不明确时要问用户，确认后写进 docstring 的"需求确认记录"。
- **只读第一张工作表**：`sheet_name=0`。按名称读取时（例如"面要素""线要素"），工作表不存在要给出明确报错，并列出实际有哪些工作表。
- **输出优先用 .xlsx**：.xls 最多 65536 行。用户明确要 .xls 时照做，但数据可能超过 65536 行的话要提醒。
- **排版**（合并单元格、边框、列宽、字体）：用 openpyxl。可以先 `arcpy.conversion.TableToExcel` 导出再打开排版，也可以直接用 openpyxl 写。列宽按 `len(str(v).encode("gbk"))` 估算，中文宽度才准。
- **Excel 文件被占用**时会抛 `PermissionError`，要翻译成"请先关闭 Excel 中的 xxx 文件"。

## 6. 文本与编码

- 读 srt、csv、txt：依次尝试 `utf-8-sig`、`gbk`、`gb18030`。写 CSV 用 `utf-8-sig`，Excel 打开才不会乱码。
- 拼音首字母：环境里已经有 `pypinyin`，不要自己维护 GB2312 编码区间表（多音字、生僻字会出错）。
- **【实测】命令行测试时的中文输出**：arcpy 的 AddMessage 由原生代码按系统代码页（GBK）输出，`PYTHONIOENCODING` 管不到它。可是一旦设了这个变量（有些 AI 的终端默认就设了），Python 自己的 print 和 traceback 会改用 UTF-8，两种编码混在一起，怎么解码都有一部分是乱码。PowerShell 回传输出时还会再转一次编码。所以**不要靠调终端编码**，统一用 `scripts/run_tool_test.py` 运行：它会清掉这些变量，按系统代码页解码，再以 UTF-8 输出，并另存一份日志文件。在 Bash 和 PowerShell 下都验证过。

## 7. 临时数据、锁、环境

- **绝不批量删除用户提供的工作空间里的内容**。历史 bug：连续擦除工具在 finally 里 `env.workspace = 临时工作空间; for fc in ListFeatureClasses(): Delete(fc)`，用户如果填了一个已有的 GDB，里面的数据会被清空。只删自己登记过的临时数据（见模板里的 `TempData`）。
- **不要往来源数据里写字段或调试数据**（历史 bug：给来源图层加 GWFZ 字段；把调试用的分割线写进输入 GDB）。需要中间字段时，先复制到临时空间再加。
- `memory` 是 Pro 的内存工作空间（旧写法 `in_memory` 仍然能用，但新代码统一写 `memory`）。数据量大、要输出栅格或者某个工具不支持时，改用 `arcpy.env.scratchGDB`。
- **环境设置**用 `with arcpy.EnvManager(cellSize=..., mask=..., extent=..., outputCoordinateSystem=..., XYTolerance=...)` 限定作用范围，不要直接改全局 `arcpy.env` 又不恢复。`overwriteOutput` 要显式设置。
- **扩展许可**：用到 `arcpy.sa` 或 `arcpy.ddd` 时，先 `arcpy.CheckExtension("Spatial") == "Available"`，再 `CheckOutExtension`，在 finally 里 `CheckInExtension`。拿不到许可要明确报错。
- **方案锁**：数据在 Pro 地图里打开时，加字段、删字段、改别名可能会失败。先 `arcpy.TestSchemaLock(ds)`，失败就提示用户"从地图中移除 xxx 后重试"。不要用 `sleep` 循环去等。
- `arcpy.sa` 返回的是 Raster 对象，需要 `.save(path)` 才会保存下来。`ExtractMultiValuesToPoints` 的 `in_rasters` 用 `"栅格路径 输出字段名"` 成对写法，显式指定字段名。

## 8. 性能

- **读一次，写一次**：先用 SearchCursor 建字典，再用一个 UpdateCursor 回写。不要在循环里对每一行再开游标或者做 `SelectLayerByLocation`。
- 批量处理多个规则或多个要素类时，**遍历、查找（例如 `da.Walk` 找来源要素）只做一次并缓存**，不要每条规则都重新遍历一遍。
- 大数据叠加分析用 `PairwiseIntersect`、`PairwiseDissolve` 等成对工具。需要按空间分块时，先建空间索引。
- 消息：大循环每 5% 左右报告一次进度（模板里的 `Progress`），**不要每个要素都 AddMessage**。历史上 CurveDetector_Pro 每个要素输出 4~6 条消息，大数据时会严重拖慢。

## 9. 需求文档本身的坑

历史提示词里真实出现过的情况，写代码前要先核对：

- **标题和正文对不上（复制粘贴留下的）**：「计算矢量范围的坐标值」的正文其实是「批量创建 GDB 模板」；「批量修改弧段要素」的开头写的是「统计规划地类变化情况」。发现不一致就先问，不要猜。
- **参数表错别字、依赖关系写错、序号重复**：见 `parameter-types.md` 的"参数表体检"。
- **"如图 1""图 2（目标效果）"但没有附图**：AI 看不到图时，请用户提供图片文件路径，或者用文字描述（输入长什么样、期望输出长什么样）。
- **只给了算法名，没给算法口径**（例如边坡、垂线、平整）：先用文字复述你理解的算法，给出 A/B/C 选项和推荐项，让用户确认后再写。历史上"边坡范围"工具就因为这个来回确认了 4 轮以上。
- **需求里夹着的"GP 历史复制出来的 Python 命令"**：这是最可靠的信息，工具名、参数、字段表达式都以它为准。但里面的路径（例如 `ArcGISProTemp12388\无标题\Default.gdb`）是临时路径，要换成参数或临时工作空间。
