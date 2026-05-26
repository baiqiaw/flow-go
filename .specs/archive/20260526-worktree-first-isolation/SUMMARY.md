# SUMMARY — worktree-first-isolation（全任务汇总）

## 做了什么
实现 worktree-first 隔离：每个 change 从创建 change-id 时就在独立 worktree 中工作，用 git 物理隔离替代手动 STATE.md 索引表同步。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| SKILL.md | 重写 | 第一步改用 git worktree list、横切关注点 change_id 改为路径推导、第七步移除索引表操作 |
| references/stages/0-requirement.md | 增强 | 新增步骤 3.5 Worktree 创建（含 EnterWorktree + Bash 回退） |
| references/stages/2-task.md | 简化 | 步骤 0 从 worktree 创建改为 worktree 验证 |
| references/stages/special-flows.md | 重构 | 归档流程拆为 worktree+main 两阶段、6 个特殊流程索引表清理、commit 断言+change-id 规范 |
| references/scripts/validate_state.py | 重写 | 删除索引表解析，新增 discover_active_changes() |
| references/artifacts/meta-artifacts.md | 简化 | STATE.md 模板无索引表，移除一致性约束和旧格式迁移 |
| references/common/pipeline-continuation.md | 修改 | 索引表操作改为 worktree 创建 |
| tests/conftest.py | 修改 | tmp_project fixture 改为新格式 STATE.md |
| tests/test_scripts.py | 重写 | TestValidateState 5 个用例重写 + 向后兼容测试 |

## Verify 输出
- T01: grep 索引表 → 0, worktree list → 2 ✅
- T02: 0-requirement 3.5 → 匹配, 2-task EnterWorktree → 0 ✅
- T03: 索引表 → 0, worktree → 35 ✅
- T04: 旧函数 → 0, 新函数 → 2, meta/pipeline 索引表 → 0 ✅
- T05: pytest 27 passed, 0 failed ✅

## 沿用既有抽象
- per-change STATE.md 格式不变
- archive-move.md 硬闸门验证不变
- cross-review-matrix.md 不变
- gate_check.py 不变

## 越界检查
- TASK write_files：9 文件
- 实际 diff 涉及：9 文件
- 越界：0

## 已知问题
- 无
