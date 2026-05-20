# REQUIREMENT — repo-hardening

## 用户故事
作为 flow-go 项目维护者，我想加强主分支保护并完善 README 文档，以便协作者遵循规范的代码提交流程，新用户能快速了解和安装本项目。

## 验收准则（BDD）

### AC-1 主分支启用管理员级保护
**Given**: GitHub 仓库 baiqiaw/flow-go 的 main 分支已有基础保护规则
**When**: 查看分支保护配置
**Then**: `enforce_admins` 设置为 `true`，所有协作者（包括管理员）必须遵循保护规则

### AC-2 主分支允许自推自批（支持 AI Agent 自动化）
**Given**: 主分支已启用 PR 审查要求
**When**: 仓库所有者（baiqiaw）通过 AI Agent 提交 PR
**Then**: `require_last_push_approval` 设置为 `false`，允许最后推送者自行批准

### AC-3 主分支要求会话解决
**Given**: PR 上存在未解决的 review 评论会话
**When**: 尝试合并 PR
**Then**: `required_conversation_resolution` 设置为 `true`，所有会话必须标记为已解决才能合并

### AC-4 README 包含项目描述
**Given**: 用户访问仓库首页
**When**: 阅读 README.md
**Then**: 能看到 flow-go 是什么、解决什么问题、核心价值的完整描述

### AC-5 README 包含多工具安装和更新方法
**Given**: 用户想要在不同 AI 编程工具中使用 flow-go
**When**: 阅读 README.md 的安装章节
**Then**: 能找到 Claude Code、Codex CLI、Trae 等主流工具的具体安装步骤和更新方法

### AC-6 README 包含使用说明
**Given**: 用户已安装 flow-go
**When**: 阅读 README.md 的使用章节
**Then**: 能找到基础使用方法（`go` / 阶段关键词 / 新需求描述）、配置说明、常见流程指引

### AC-7 CODEOWNERS 限制批准权限
**Given**: 仓库已配置 CODEOWNERS 文件并启用 `require_code_owner_reviews`
**When**: 非所有者提交 PR
**Then**: 必须获得 @baiqiaw 的批准才能合并，其他协作者无法作为合格批准者

## 非功能需求
- 安全：主分支保护规则应防止绕过，包括管理员
- 兼容：README 安装说明需覆盖 Claude Code、Codex CLI、Trae 等主流 AI 编程工具
- 可读性：README 面向初次接触项目的用户，需简洁明了

## Out of Scope（范围排除）
- 不配置 CI/CD 流水线
- 不配置 GitHub Actions
- 不涉及仓库其他分支的保护规则

## Principles（设计约束原则）
- README 保留现有的核心内容（流程图、项目结构、核心机制），在其基础上完善
- 主分支保护规则采用 GitHub 原生功能，不引入外部工具
- 保护规则的严格程度应平衡安全性与协作效率

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| 启用 enforce_admins | 确保管理员也遵循 PR 流程，避免绕过审核直接推送 | 所有推送必须通过 PR |
| 禁用 require_last_push_approval | 不排除最后推送者作为批准者，支持 AI Agent 自动 PR + 合并 | 配合 CODEOWNERS 仅 @baiqiaw 可实际批准 |
| 配置 CODEOWNERS 限制批准权限 | 只有 @baiqiaw 能作为 approver，其他人提 PR 必须由所有者批准 | 精确控制审批权限 |
| README 以完善为主而非重写 | 现有内容基本正确，只需补充缺失章节 | 保持风格一致性 |

## 术语表
| 术语 | 含义 |
|------|------|
| enforce_admins | GitHub 分支保护选项，使管理员也受保护规则约束 |
| require_last_push_approval | 要求非最后推送者的审批才能合并（本项目中设为 false） |
| conversation resolution | PR 中的 review 评论会话需标记为已解决 |
| CODEOWNERS | GitHub 仓库文件，定义哪些人员/团队可以审查和批准特定代码 |
| SKILL.md | AI 工具通用技能定义文件（YAML frontmatter + Markdown），被 Claude Code / Codex CLI / Trae / OpenCode / OpenClaw 等工具识别 |
