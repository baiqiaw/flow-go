# SUMMARY — T08

## 做了什么
在现有 evolution_signal.py 中扩展 CLI，新增 --write-lessons 参数。main() 中，当 --write-lessons 且 result 包含 strong_signals 时，导入 lessons_writer.write() 并调用写入 LESSONS.md。无 strong_signals 时输出提示跳过。不改变 detect() 核心逻辑。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/evolution_signal.py | 修改 | argparse 新增 --write-lessons flag + main() 新增写入逻辑 |

## Verify 输出
```
无强信号，跳过 LESSONS 写入
T08 PASS: --write-lessons 参数可用
```

## 沿用既有抽象（grep 结果）
- lessons_writer.write：按需导入（仅在 --write-lessons 时加载）→ 沿用渐进式披露模式

## 越界检查
- TASK write_files：1 项（evolution_signal.py）
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无

## 交叉评审（独立子代理）
### 评审轮次: 1/3
### 评审矩阵
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | --write-lessons 参数已注册，strong_signals 写入逻辑正确 |
| 设计对齐 | PASS | 遵循 DESIGN.md 进化闭环数据流 |
| 测试证据 | PASS | --help 输出包含 --write-lessons |
| 边界卫生 | PASS | 仅修改 evolution_signal.py |
| 反幻觉 | PASS | lessons_writer 按需导入，模块已存在 |
| 质量底线 | PASS | 无 bug/无密钥/无空 catch |

### 发现问题
- 无

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 交叉评审轮次 | 1/3 |
| 代码行数变化 | +10 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 1 个沿用 / 0 个新建 |
