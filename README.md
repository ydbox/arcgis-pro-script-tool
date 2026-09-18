# arcgis-pro-script-tool

一个 Claude Code skill：让 AI 按固定规范编写、修改、调试 **ArcGIS Pro 脚本工具（arcpy / Python 3）**。

内容来自 20 份历史需求提示词和 36 个实际在用的脚本。有问题的写法（会误删数据、遍历漏掉要素数据集、多值参数含空格时失败等）都已改掉，关键结论在 ArcGIS Pro 3.7.1 上实测过。

## 安装

本仓库是私有仓库，需要先被邀请为协作者。

```bash
# 全局安装（所有项目都能用）
gh repo clone ydbox/arcgis-pro-script-tool ~/.claude/skills/arcgis-pro-script-tool

# 或者只装到某个项目
gh repo clone ydbox/arcgis-pro-script-tool <项目目录>/.claude/skills/arcgis-pro-script-tool
```

装好后重启 Claude Code。说"写一个 ArcGIS Pro 脚本工具……"或者贴出工具参数表，这个 skill 就会自动触发。

更新：到安装目录里执行 `git pull`。

## 用法

需求越完整，AI 越少追问。建议按 [`references/request-template.md`](references/request-template.md) 里的模板写需求，至少包括：

- 一句话目标和处理步骤（有歧义的规则给一个"输入 → 输出"例子）
- Pro 里配好的工具参数表
- 数据情况：格式、坐标系、规模
- 验收标准，以及测试数据路径（有的话 AI 写完会直接跑一遍）

## 文件结构

| 文件 | 作用 |
| --- | --- |
| `SKILL.md` | 工作流：整理需求 → 核对后一次性提问 → 编码 → 自检 → 交付；以及硬规则 |
| `references/parameter-types.md` | 各种参数数据类型在 Python 里怎么读；参数表体检 |
| `references/pitfalls.md` | 常见的坑：遍历、字段、几何、Excel、编码、锁、性能、需求文档本身 |
| `references/request-template.md` | 需求填空模板（说明了旧模板哪些内容不用再写） |
| `templates/script_tool_template.py` | 新脚本的代码骨架 |

## 环境

- ArcGIS Pro 3.x（在 3.7.1 / Python 3.13 上验证过）
- 旧版 ArcMap 10.x / Python 2.7 只在需求里明确说明时才用，写法见 `SKILL.md` 末尾
