# SUMMARY — T05

## 做了什么
创建 context_summarizer.py 上下文摘要生成脚本。实现 argparse CLI（--stage/--specs-dir/--skill-dir），从阶段指南读取「上下文需求清单」表格，按清单从上游工件提取必选字段，输出 Markdown 摘要到 stdout。无需求清单时优雅降级输出全文。退出码 0/1/2。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/context_summarizer.py | 新增 | 上下文摘要生成脚本，191 行 |

## Verify 输出
```
$ python3 references/scripts/context_summarizer.py --help 2>&1 | grep -q "context_summarizer"
$ echo $?
0
```

功能测试：
```
$ python3 context_summarizer.py --stage 3 --specs-dir .specs/data-flywheel
## 上下文摘要（3-阶段）
> 未找到上下文需求清单，输出主要工件全文
### CHANGE
# CHANGE — data-flywheel
...
```

退出码测试：
```
$ python3 context_summarizer.py --stage 3 --specs-dir /nonexistent; echo $?
错误：spec 目录不存在 — /nonexistent
2
```

## 沿用既有抽象（grep 结果）
- argparse CLI 风格：health_scorer.py → 沿用
- 退出码模式：trace_collector.py → 沿用（0/1/2）
- read_file 工具函数：trace_collector.py → 沿用

## 越界检查
- TASK write_files：1 项（references/scripts/context_summarizer.py）
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无

## 交叉评审（独立子代理）
### 评审轮次: 1/3
### 评审矩阵
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | 3 个 CLI 参数全部实现，需求清单解析+摘要生成+优雅降级均符合 DESIGN 3.5 定义 |
| 设计对齐 | PASS | 需求清单从阶段指南读取（ADR-005 B 方案），关键决策保留原文，描述性内容压缩 |
| 测试证据 | PASS | --help/功能测试/退出码测试全部实测通过 |
| 边界卫生 | PASS | 唯一输出文件与 TASK write_files 一致 |
| 反幻觉 | PASS | 全部 import 为 Python 标准库 |
| 质量底线 | PASS | 无密钥/无空 catch/无逻辑 bug |

### 发现问题
- 无

### 修复记录
无（首次即通过）

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 交叉评审轮次 | 1/3 |
| 代码行数变化 | +191 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 3 个沿用 / 0 个新建 |
