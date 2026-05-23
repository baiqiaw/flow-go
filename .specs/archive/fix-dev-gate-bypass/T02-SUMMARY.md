# T02-SUMMARY — 修复开发完成门禁

## 变更概述
修复 gate_artifacts.py 阶段 4 闸门检查为空的问题，增加 SUMMARY.md、代码提交、PROGRESS 残留三项检查。

## 变更文件
1. `references/scripts/gate_artifacts.py`
   - 新增 `import glob, subprocess`
   - `check_artifacts()` 新增 `project_dir=None` 参数（向后兼容）
   - 阶段 4 特殊检查：SUMMARY.md glob、git diff HEAD、PROGRESS.md glob
   - subprocess 异常捕获：TimeoutExpired/FileNotFoundError → warning
2. `references/scripts/gate_check.py`
   - 传递 `project_dir=args.project_dir` 给 check_artifacts()

## 沿用检查
- 沿用 check_artifacts 返回结构 `{passed, missing, warnings, info}`
- 沿用 subprocess 异常处理模式（同 gate_l1.py）

## 自检
- 未改 REQUIREMENT / DESIGN ✅
- 未改 gate_l1/l2/l3/blast 模块 ✅
- 调试日志已清理 ✅（无调试日志）

## verify 结果
```
T02 verify PASS
```

## 验证闭环
- 功能不变：闸门通过的场景仍通过，新增检查仅在缺失时拦截 ✅
- verify 通过 ✅
