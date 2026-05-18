# 工件示例 — SUMMARY.md

> 示例：T01 任务完成后的 SUMMARY.md，展示好工件的标准。

---

```markdown
# SUMMARY — T01

## 做了什么
创建 POST /login 路由和 login 参数验证器。邮箱校验格式，密码校验长度 ≥ 8。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| src/routes/login.ts | 新增 | POST /login 路由，调用 validator 后返回结果 |
| src/validators/login.ts | 新增 | email 格式校验 + password 长度校验 |
| src/routes/auth.ts | 修改 | 新增 import login 路由并注册 |

## Verify 输出
```
$ npm test -- src/routes/login.test.ts

PASS src/routes/login.test.ts
  POST /login
    ✓ 应返回 200 当邮箱密码正确 (12ms)
    ✓ 应返回 400 当邮箱格式错误 (5ms)
    ✓ 应返回 400 当密码为空 (3ms)
    ✓ 应返回 400 当密码少于8位 (4ms)

Tests: 4 passed, 4 total
Time: 0.8s
```

## 沿用既有抽象（grep 结果）
- 参数验证：找到 src/middleware/validate.ts → 沿用其 validate() 函数
- 路由注册：找到 src/routes/auth.ts → 沿用 registerRoute() 模式
- 错误响应：未找到统一错误格式 → 新建（后续 T02 可沿用）

## 越界检查
- TASK write_files：2 项（login.ts, login.ts validator）
- 实际 diff 涉及：3 项（+ auth.ts 注册路由）
- auth.ts 属于必要注册改动，已在 TASK read_files 中列出
- 越界：0

## 已知问题
- 无

## 交叉评审（独立子代理）
### 评审轮次: 1/3
### 评审矩阵
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | 实现 vs T01 action/done 完全对齐 |
| 设计对齐 | PASS | 遵循 DESIGN.md 的路由+验证分离方案 |
| 测试证据 | PASS | verify 输出 4/4 通过，覆盖正向+3种错误 |
| 边界卫生 | PASS | auth.ts 改动在 read_files 范围内 |
| 反幻觉 | PASS | validate.ts 经 grep 确认存在 |
| 质量底线 | PASS | 无空 catch、无密钥、无 bug |

### 发现问题
- 无

### 修复记录
| 轮次 | 问题 | 修复 | re-verify |
|------|------|------|----------|

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 4/4（首次） |
| 交叉评审轮次 | 1/3 |
| 代码行数变化 | +85 / -0 |
| 改动文件数 | 3 个 |
| 沿用既有抽象 | 2 个沿用 / 1 个新建 |
```

---

## 好工件特征

- [x] 改动文件表完整（含变更类型）
- [x] verify 输出是真实命令输出（非"通过"二字）
- [x] 沿用既有抽象有 grep 结果（非猜测）
- [x] 越界检查有数值对比
- [x] 没改 REQUIREMENT / DESIGN
- [x] 交叉评审 6 维全 PASS
- [x] 交叉评审未超过 3 轮
- [x] 量化指标完整
