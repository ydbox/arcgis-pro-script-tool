---
name: arcgis-pro-script-tool
description: "Use when writing, modifying, or debugging an ArcGIS Pro script tool or arcpy script (Python 3) — e.g. 用户说「写一个 ArcGIS Pro 脚本工具」「适配我的工具参数表」、批量处理 GDB / 要素类 / 要素数据集 / 字段 / 栅格、按 Excel 规则表赋值或建库、输出 Excel 统计表、把结果加到活动地图；also for .pyt Python toolboxes and upgrading legacy ArcMap 10.x / Python 2.7 scripts."
compatibility: "Windows + ArcGIS Pro 3.x (arcpy). Works with any agent that supports Agent Skills (Claude Code, Codex, Cursor, Gemini CLI, Copilot, Trae, Kiro, CodeBuddy, Qoder, ...)."
metadata:
  version: "1.1.0"
  source: local-case-analysis
  analyzed_cases: "20 prompts (提示词案例) + 36 scripts (py)"
  verified_on: "ArcGIS Pro 3.7.1 / Python 3.13"
---

# ArcGIS Pro 脚本工具开发

用户的典型需求：给出**一段处理逻辑 + 一张 Pro 工具参数表**（有时附 Excel 规则表样例、GP 历史里复制出来的 Python 命令），要一个 `.py` 挂到 Pro 的脚本工具上直接用。这个 skill 把旧提示词里每次重复的约定、历史脚本里踩过的坑，固化成默认行为。

## 何时用 / 何时不用

- 用：写新的 arcpy 脚本工具；改造已有工具（单库改批量、加 Excel 输出、修 bug）；设计工具参数；写 `.pyt`；把 ArcMap 10.x 脚本迁移到 Pro。
- 不用：只在 Pro 里临时跑一次、不需要做成工具的操作——这种如果当前 AI 连着 ArcGIS Pro 的 MCP 服务就直接操作，否则给用户一行 GP 命令就行。

## 工作流

### 1. 读需求，整理需求卡

从用户消息或需求文件里提取以下内容，缺什么记下来：
- 一句话目标
- 处理步骤和规则（带"输入 → 输出"例子的优先采用）
- 参数表
- 数据情况：格式、有没有要素数据集、坐标系、数据规模、Excel 结构
- 输出方式：命名、放在哪、是否改原数据、是否加到地图
- 验收标准和测试数据

用户只给了一句话时，把 `references/request-template.md` 里的模板正文发给用户，让用户补充；能推断出来的内容不要追问。

### 2. 需求体检，然后一次性提问

写代码前逐项核对：
- 标题和正文一致吗？历史上出现过复制粘贴留下的错误：标题是 A 功能，正文却是 B 功能。
- 参数表：按 `references/parameter-types.md` 的"参数表体检"逐项查。
- 口径有歧义的地方，例如：空行是"结束"还是"跳过"；字段并集怎么合并；只处理选中的要素还是全部要素。
- 算法类工具（垂线、边坡、分割、平整……）：用文字复述你理解的算法。
- 会不会修改原数据？需不需要备份？
- 涉及面积、距离时，数据是投影坐标系还是地理坐标系？
- 需要 Spatial Analyst、3D Analyst 等扩展许可吗？

有**阻塞问题**就集中问：当前 AI 有提问工具的就用它（例如 Claude Code 的 AskUserQuestion）；没有的话，在回复里列出带编号的选择题，然后停下来等用户回答。一轮最多 4 个问题，每个问题给 2~4 个选项，第一项是推荐项。目标是**一轮问清**，历史上"边坡"工具来回确认了 4 轮以上。不阻塞、有常规做法的，直接按默认做，并在交付时写明"假设"。用户确认过的口径，写进脚本 docstring 的"需求确认记录"。

大工具（例如网格赋值的"面 → 线 → 点 → 栅格"）**分阶段交付**：先搭好统一的调度结构，每个阶段写完就验证，再做下一阶段。

### 3. 编码

复制 `templates/script_tool_template.py` 作为起点，再按下面的硬规则写。参数怎么读，查 `references/parameter-types.md`；写到遍历、Excel、几何、字段、连接时，查 `references/pitfalls.md` 对应的小节。

如果用户给了"GP 历史复制出来的 Python 命令"，就以它为准：工具名、参数、表达式照用，但里面的临时路径要换成参数或 `TempData`。

### 4. 自检（交付前必须做）

先找到 Pro 的 Python（下文写作 `<Pro python>`）：
- 安装目录记录在注册表 `HKLM\SOFTWARE\ESRI\ArcGISPro` 的 `InstallDir`；
- Python 在 `<InstallDir>\bin\Python\envs\arcgispro-py3\python.exe`；
- 用户在 Pro 里换过环境（例如克隆出 `arcgispro-py3-clone`），就用那个环境里的 python.exe。

1. **语法检查**（必做）：`<Pro python> -m py_compile <脚本>`。
2. **实跑**（有测试数据时必做）：`<Pro python> scripts/run_tool_test.py <脚本> <参数0> <参数1> …`，可选参数留空时写 `#`。
   - `GetParameterAsText` 会读到这些命令行参数（已实测）。
   - 这个运行脚本在 Bash、PowerShell、cmd 下中文输出都正常，退出码与工具一致，完整输出另存为 `<脚本>.test.log`（UTF-8）。终端显示乱码时，直接读这个日志文件。
   - **会修改输入数据的工具，先把测试数据复制一份，在副本上跑。**
   - 跑完按验收标准检查输出：要素数量、字段、取值、Excel 内容。
3. 如果当前 AI 连着 ArcGIS Pro 的 MCP 服务，也可以在用户当前打开的 Pro 里验证。
4. 如果 arcpy 因为许可或登录无法独立运行，照实说明"只做了语法检查，没有实跑"。

### 5. 交付

- **文件名**：沿用用户的习惯，`<EnglishName><中文名>.py`，例如 `BatchDeleteEmptyFields批量删除空值字段.py`。放在用户指定的目录；在 `E:\ai_coding\prj8` 下工作时，放 `py\`。
- **回复内容**：
  - 文件路径。
  - 参数表：序号、标注、数据类型、类型、方向、多值、依赖、过滤器、默认值。用户已经配好参数的，写明"与你的参数表一致"；有改动的，逐条列出。
  - 做了哪些验证、结果如何；没验证的也要说。
  - 做了哪些假设。
  - 会不会修改原数据。
- 用户还没配参数、又不想手动配时，可以提供 `.pyt`（参数写在代码里）。默认仍然给 `.py` 脚本工具，因为这是用户的习惯。

## 硬规则

这些是旧模板每次都要重复写的要求，加上历史脚本里暴露的问题。每个脚本都必须满足：

**结构**
- 文件头 `# -*- coding: utf-8 -*-`，然后是模块 docstring：功能、按序号列出的参数、需求确认记录、命令行测试方法。
- 有 `main()` 和 `if __name__ == "__main__":` 入口；参数只在 `main()` 里读取。
- 只保留真正用到的辅助函数。

**参数**
- 统一用 `GetParameterAsText` 读取，再用辅助函数转换：`get_bool`、`get_number`、`split_multi`、`parse_linear_unit`。
- 不用 `GetParameter` 读布尔值（命令行运行时会拿到字符串 `'false'`，而它的真值是 True）。
- 多值参数必须去掉每项两端的引号（历史脚本全都漏了这一步，路径含空格时会失败）。
- `""` 和 `"#"` 都视为空。

**消息**
- 用 AddMessage、AddWarning、AddError 报告成功、失败、异常和关键步骤。
- 格式：`===== 开始：工具名 =====` → `[i/n] 对象` → `===== 完成：成功 x，失败 y，用时 t 秒 =====`，最后列出失败清单。
- 大循环按间隔报告进度，不要每个要素都输出消息。

**错误**
- 入口处分开捕获 `arcpy.ExecuteError`（输出 `GetMessages(2)`）和 `Exception`（输出 `traceback`），**然后重新抛出**，让 Pro 显示"失败"。
- 批处理时，单个对象用 try 包住：失败了记录下来、继续处理下一个，最后汇总。
- 禁止裸 `except:`，禁止吞掉错误。
- 参数不合法时，给出能看懂的中文报错。

**数据安全**
- **只删除自己创建的临时数据**，绝不按"工作空间里的全部内容"去删。
- 不往来源数据、输入 GDB 里写字段或调试数据，除非需求就是要改原数据。
- 需求就是要改原数据的，在 docstring 里写明，开始运行时输出一条 AddWarning 提醒。

**资源**
- 临时数据用 `TempData`：默认放 `memory`，数据量大或输出栅格时放 `scratchGDB`；名称用 `CreateUniqueName` 生成；在 `finally` 里清理。
- `arcpy.env.overwriteOutput` 要显式设置。
- 其他环境设置用 `arcpy.EnvManager` 限定作用范围。
- 扩展许可要先 check out、再在 finally 里 check in。
- 游标一律用 `with arcpy.da.*Cursor`。

**遍历与字段**
- 遍历 GDB 用 `arcpy.da.Walk`，要覆盖要素数据集和独立表。
- OID 字段用 `OID@` 或 `OIDFieldName` 获取，不写死成 OBJECTID。
- 字段查找不区分大小写。
- 复制字段结构时用类型映射表（见 pitfalls §3）。

**性能**
- 先读成字典，再用一个 UpdateCursor 回写。
- 能用字典的地方不用 AddJoin + CalculateField。
- 不在循环里做 `SelectLayerByLocation`，也不重复遍历。

**加到地图**
- 方向为"输出"的参数，Pro 会自动加到地图，**不要再手动加**，否则图层会重复。
- 不是参数的额外结果，用 `activeMap.addDataFromPath`，并且要处理两种情况：不在 Pro 里运行、没有活动地图。不要用 `LayerFile` 加载数据路径。

## 旧版 ArcMap 10.x / Python 2.7

只在用户**明确说**要用 ArcMap 或 10.x 时才用这套写法。用户的旧模板针对的是 10.2.2。

- 不能用 f-string、`print()` 以外的 Python 3 语法、`pathlib`、类型注解。
- 中文字符串写 `u"..."`；文件头照旧模板加上 `reload(sys); sys.setdefaultencoding('utf8')`。
- 临时空间用 `in_memory`（没有 `memory`）；没有 `EnvManager`，要手动保存和恢复 `arcpy.env`。
- 10.1 之后才有 `arcpy.da`；10.2.2 可以用，但没有 `hasCurves`、`addDataFromPath`，地图操作用 `arcpy.mapping`。

## 参考文件

| 文件 | 什么时候读 |
| --- | --- |
| `references/parameter-types.md` | 读参数、核对参数表、加到地图 |
| `references/pitfalls.md` | 遍历、字段、几何、Excel、编码、锁、性能、需求文档本身的坑 |
| `references/request-template.md` | 用户需求不全时，给用户的填空模板（新版，说明了旧模板哪些内容不用再写） |
| `templates/script_tool_template.py` | 每个新脚本的起点 |
| `scripts/run_tool_test.py` | 自检时在命令行实跑工具；任何终端下中文都不乱码 |

如果本机有 `E:\ai_coding\prj8\py\`，可以参考以下范本：
- `BatchDeleteEmptyFields批量删除空值字段.py`：短小完整，结尾有汇总。
- `ExtractPinyinInitials提取拼音首字母.py`：先校验参数，只用一个 UpdateCursor。
- `line_z_to_dem.py`：进度条和临时数据清理；缺少许可检查，参考时要补上。
- `SrtToTrack.py`：编码回退，`has_z` 和 `projectAs` 的用法。

反面教材（不要照抄）：`ContinuousErasing连续擦除.py`（会清空用户的临时库）、`CurveDetector_Pro.py`（用 200 行"挨个试"来遍历 GDB）。
