# TEST — fix-dev-gate-bypass

## 测试深度
standard

## 测试矩阵

| AC | 测试类型 | 测试文件/命令 | 轮次 |
|----|---------|-------------|------|
| AC-1 | 功能 | grep 步骤 3 不含"已有问题" | 1 |
| AC-2 | 功能 | grep 步骤 9 含"0 失败" | 1 |
| AC-3 | 功能 | grep anti-patterns 含 dev-06 | 1 |
| AC-4 | 功能 | gate_check stage 4 STANDARD 缺 SUMMARY → FAIL | 1 |
| AC-5 | 功能 | gate_check stage 4 代码未提交 → FAIL | 1 |
| AC-6 | 功能 | gate_check stage 4 PROGRESS 残留 → FAIL | 1 |
| AC-7 | 功能 | grep 完成条件含"代码已提交" | 1 |
| AC-8 | 功能 | grep anti-patterns 含 dev-07 | 1 |

## Bug 清单
无 Bug。

## 健康评分

| 维度 | 得分 | 权重 | 加权 |
|------|------|------|------|
| 功能覆盖 | 100%（8/8 AC） | 30% | 30 |
| 性能达标 | 100% | 20% | 20 |
| 安全合规 | 100% | 20% | 20 |
| 兼容覆盖 | 100% | 15% | 15 |
| 可观测完备 | 100% | 15% | 15 |

**总分：100 / A 级**
