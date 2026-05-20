# CHANGE — repo-hardening

## Why（为什么做）
项目仓库有多人协作（或计划添加），主分支缺乏足够保护措施，存在未经审核直接推送的风险。同时 README.md 内容不够完善，缺少安装更新方法和详细使用说明，不利于新协作者快速上手。

## What（做什么）
1. 加强 GitHub 主分支保护规则，启用 enforce_admins 和 conversation resolution，禁用 require_last_push_approval（支持 AI Agent 自推自批）
2. 配置 CODEOWNERS 文件，限制只有 @baiqiaw 能审批和合并 PR
3. 更新 README.md，补充完整的项目描述、多工具安装更新方法和使用说明

## 影响面
- 涉及模块：GitHub 仓库配置、README.md 文档
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不涉及代码功能变更
- 不涉及 CI/CD pipeline 配置
- 不配置 GitHub Actions
- 不涉及仓库其他分支的保护规则

## 验收线
主分支保护规则配置到位（仅 @baiqiaw 可审批合并），CODEOWNERS 限制批准权限，README.md 内容完整覆盖三个章节且安装说明支持多工具

## 路径建议
最短路径，理由：纯配置 + 文档变更，无代码开发，无测试需求，可直接在 0-需求确认后进入 3-开发
