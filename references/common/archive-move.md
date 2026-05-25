# 归档移动验证

将 `.specs/<id>/` 移动到归档目录并验证移动成功。

## 参数

- `{target_subpath}`：归档目标子路径
  - 归档 → `""`（即 `.specs/archive/<date>-<id>/`）
  - 废弃 → `"abandoned/"`（即 `.specs/archive/abandoned/<date>-<id>/`）

## 步骤

1. **执行移动**：`mkdir -p .specs/archive/{target_subpath} && mv .specs/<id>/ .specs/archive/{target_subpath}<date>-<id>/`（date 格式 YYYYMMDD）
2. **即时验证**：`test ! -d .specs/<id> && test -d .specs/archive/{target_subpath}<date>-<id>`。两项全通过才继续。原路径仍存在或新路径不存在 → 停下排查（路径拼写错误 / 文件被占用 / 权限问题），修复后重新验证，禁止跳过
3. **硬闸门验证**（禁止跳过）：执行以下命令确认移动成功，任一失败则归档流程中断：
   - `ls .specs/<id>/` → 必须报错「No such file or directory」（原路径已不存在）
   - `ls .specs/archive/{target_subpath}<date>-<id>/STATE.md` → 必须成功（新路径存在且内容完整）
   - 两项验证通过 → 输出「✅ 归档移动验证通过：.specs/<id>/ → .specs/archive/{target_subpath}<date>-<id>/」
   - 验证失败 → 输出具体失败原因并等待修复

> ⚠️ 验证通过前，禁止执行任何索引更新或 STATE.md 清理操作。未验证就清理 = 目录永远留在原位无法自动恢复。
