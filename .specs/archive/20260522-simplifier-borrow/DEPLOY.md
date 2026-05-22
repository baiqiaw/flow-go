# DEPLOY — simplifier-borrow

## 部署方式
本地 skill 变更，无需生产部署。合并到 main 即生效。

## 合并状态
- 分支：worktree-simplifier-borrow → main（--no-ff merge）
- 提交：a6d0304 + merge commit
- 冲突：无

## 部署验证
- SKILL.md 在 main 分支可正常读取 ✅
- references/stages/ 3 个文件在 main 分支可正常读取 ✅
- flow-go skill symlink 指向 main 分支 ✅

## 回滚方案
`git revert <merge-commit-sha>` 即可回退全部 6 项优化。
