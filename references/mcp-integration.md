# MCP 扩展点

flow-go 默认以文件驱动（STATE.md / .specs/），不依赖外部 MCP。以下集成为可选增强。

## 可用 MCP Server

| MCP Server | 适用阶段 | 用途 | 回退方案 |
|-----------|---------|------|---------|
| GitHub MCP | 3-开发 / 5-审查 / 6-部署 | 自动创建 issue 关联 change、PR 创建与链接、CI 状态检查 | 手动 git 操作 + 文件记录 |
| Jira MCP | 0-需求 / 2-任务 / 7-验收 | 需求同步到 Jira issue、任务与 sprint 关联、验收状态更新 | 纯文件工件（REQUIREMENT/TASK/UAT） |
| Slack MCP | 7-验收后 | 验收结果通知团队频道 | 手动复制 UAT 摘要 |

## 使用原则

- MCP 数据为辅、文件为主。STATE.md + .specs/<id>/STATE.md 始终是唯一状态源
- MCP 不可用时自动回退到文件方案，不阻塞流程
- MCP 操作需在阶段步骤中显式声明（如「可选：如已配置 GitHub MCP，创建 issue 关联 change」）

## 命令示例

```bash
# GitHub MCP（3-开发阶段）
mcp__github__create_issue owner="myorg" repo="myrepo" title="[CH-001] 用户登录功能" body="关联 Change: CH-20240315-001"
mcp__github__create_pull_request owner="myorg" repo="myrepo" title="feat: 用户登录功能 (CH-001)" head="feat/login" base="main"
mcp__github__pull_request_read method="get_check_runs" owner="myorg" repo="myrepo" pullNumber=42

# Jira MCP（0-需求阶段）
mcp__jira__create_issue project="PROJ" summary="用户登录功能" type="Epic" description="Change-ID: CH-20240315-001"
mcp__jira__create_issue project="PROJ" summary="T01-后端登录API" type="Story" parent="PROJ-100"
mcp__jira__transition_issue issue="PROJ-100" status="Done"

# Slack MCP（7-验收后）
mcp__slack__post_message channel="#team" text="✅ CH-001 用户登录功能验收通过，评分 85/100 (A级)"
```
