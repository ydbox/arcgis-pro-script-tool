# arcgis-pro-script-tool

一个 Agent Skill（标准 `SKILL.md` 格式）：让 AI 按固定规范编写、修改、调试 **ArcGIS Pro 脚本工具（arcpy / Python 3）**。Claude Code、Codex、Cursor、Gemini CLI、Copilot、Trae、Kiro、CodeBuddy、Qoder、通义灵码等支持 skill 的 AI 都能用；网页版 AI 可以上传文件使用。

内容来自 20 份历史需求提示词和 36 个实际在用的脚本。有问题的写法（会误删数据、遍历漏掉要素数据集、多值参数含空格时失败等）都已改掉，关键结论在 ArcGIS Pro 3.7.1 上实测过。

## 安装

### 方式一：一条命令装到多个 AI（推荐，需要 Node.js）

```bash
# 交互式：会列出本机检测到的 AI，选要装到哪些、装全局还是当前项目
npx skills add ydbox/arcgis-pro-script-tool

# 直接指定：-g 表示全局（不加就装到当前项目），-a 后面可以跟多个 AI
npx skills add ydbox/arcgis-pro-script-tool -g -a claude-code codex cursor trae -y
```

- `-a '*'` 表示装到全部支持的 AI。
- 默认用符号链接，创建失败时加 `--copy`。
- 更新：`npx skills update`。

### 方式二：git clone 到对应目录

把仓库克隆到你用的 AI 读取 skill 的目录，文件夹名保持 `arcgis-pro-script-tool`：

```powershell
# 例：装到 Codex 的全局目录（PowerShell）
git clone https://github.com/ydbox/arcgis-pro-script-tool.git "$HOME\.codex\skills\arcgis-pro-script-tool"
```

| AI | 全局目录（所有项目可用） | 项目目录（只在该项目可用） | `npx skills -a` 标识 |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | `claude-code` |
| Codex | `~/.codex/skills/` | `.agents/skills/` | `codex` |
| Cursor | `~/.cursor/skills/` | `.agents/skills/` | `cursor` |
| Gemini CLI | `~/.gemini/skills/` | `.agents/skills/` | `gemini-cli` |
| GitHub Copilot | `~/.copilot/skills/` | `.agents/skills/` | `github-copilot` |
| OpenCode | `~/.config/opencode/skills/` | `.agents/skills/` | `opencode` |
| Kimi Code CLI | `~/.agents/skills/` | `.agents/skills/` | `kimi-code-cli` |
| Trae / Trae CN | `~/.trae/skills/` / `~/.trae-cn/skills/` | `.trae/skills/` | `trae` / `trae-cn` |
| Kiro CLI | `~/.kiro/skills/` | `.kiro/skills/` | `kiro-cli` |
| CodeBuddy | `~/.codebuddy/skills/` | `.codebuddy/skills/` | `codebuddy` |
| Qoder | `~/.qoder/skills/` | `.qoder/skills/` | `qoder` |
| 通义灵码 Lingma | `~/.lingma/skills/` | `.lingma/skills/` | `lingma` |
| Qwen Code | `~/.qwen/skills/` | `.qwen/skills/` | `qwen-code` |
| Windsurf | `~/.codeium/windsurf/skills/` | `.windsurf/skills/` | `windsurf` |

- Windows 下 `~` 指 `C:\Users\<用户名>`。
- 目录取自 `skills` CLI 1.7.0 的定义（2026-09）。某个 AI 改了目录的话，以它的官方文档为准；也可以直接用方式一，由 CLI 自动处理。
- 更新：进入安装目录执行 `git pull`。

装好后重启对应的 AI。说"写一个 ArcGIS Pro 脚本工具……"或者贴出工具参数表，这个 skill 就会自动触发。

### 方式三：不支持 skill 的网页版 AI（ChatGPT、DeepSeek、Kimi、豆包等）

1. 上传以下 5 个文件作为附件，或者放进"项目 / 知识库"：`SKILL.md`、`references/` 下的 3 个 `.md`、`templates/script_tool_template.py`。
2. 然后说："按 SKILL.md 的规则帮我写 ArcGIS Pro 脚本工具：<需求>"。

网页版 AI 不能在你的电脑上运行代码，所以"自检"那一步要你自己在 Pro 里跑。

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
| `scripts/run_tool_test.py` | AI 自检时在命令行实跑工具；Bash、PowerShell、cmd 下中文都不乱码 |

## 环境

- Windows + ArcGIS Pro 3.x（在 3.7.1 / Python 3.13 上验证过）。
- AI 要能在本机执行命令，才能做自检。
- 旧版 ArcMap 10.x / Python 2.7 只在需求里明确说明时才用，写法见 `SKILL.md` 末尾。
