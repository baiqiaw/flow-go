# UAT — worktree-first-isolation

## 验收日期
2026-05-26

## AC 验收结果

| AC | 描述 | P0/P1 | 结果 | 证据 |
|----|------|-------|------|------|
| 1 | worktree 自动创建 | P0 | ✅ | SKILL.md worktree list --porcelain ×1，索引表 ×0 |
| 2 | git worktree list 替代索引表 | P0 | ✅ | discover_active_changes ×2 |
| 3 | 并行 change 隔离 | P0 | ✅ | SKILL.md 0/1/>1 worktree 分支 ×3 |
| 4 | 归档流程拆分 | P0 | ✅ | special-flows.md worktree内/main中 ×3 |
| 5 | validate_state 新格式 | P1 | ✅ | 5 测试全通过 |
| 6 | commit 前断言 | P1 | ✅ | test ! -d ×2 |
| 7 | 旧归档兼容 | P1 | ✅ | test_backward_compat_archive 通过 |
| 8 | gate_check 不受影响 | P1 | ✅ | TestGateCheck + CLI 通过 |

## 全量回归
```
pytest tests/ -v → 27 passed, 0 failed
```

## 健康评分
93.9 / 100（A级）🟢 Green

## Bug 汇总
所有严重度 = 0，无 bug。

## 验收签字
- 产品经理：✅ 8/8 AC 全 PASS，根治方案生效
- 项目经理：✅ 测试全通过，健康评分 A 级，可归档
