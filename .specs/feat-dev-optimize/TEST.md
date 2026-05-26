# TEST — feat-dev-optimize

## 测试范围
4 个 reference 文件的增强改动。

## AC 验证结果

### AC-1 设计阶段并行子代理探索
- **Given**: 1-design.md 存在
- **When**: 读取步骤 1.5 内容
- **Then**: 包含 dispatch 2-3 个 explorer、model: sonnet、返回文件列表、降级规则、LITE 跳过条件
- **结果**: ✅ PASS（验证命令：grep "并行子代理探索" → 1 匹配）

### AC-2 交叉评审置信度过滤
- **Given**: cross-review-matrix.md 存在
- **When**: 读取置信度评分章节
- **Then**: 包含 0-100 评分标准、≥80 过滤规则、Critical/Important 分组
- **结果**: ✅ PASS（验证命令：grep "置信度评分" → 2 匹配，grep "≥80" → 2 匹配）

### AC-3 DESIGN.md 备选方案章节
- **Given**: spec-artifacts.md DESIGN.md 模板存在
- **When**: 读取 4.5 章节
- **Then**: 包含方案 A/B 模板、STANDARD/HEAVY 强制、LITE 跳过标注
- **结果**: ✅ PASS（验证命令：grep "4.5 备选方案" → 1 匹配，grep "LITE 跳过" → 1 匹配）

### AC-4 子代理模型选择
- **Given**: cross-review-matrix.md 调用参数表存在
- **When**: 检查子代理 model 列
- **Then**: 所有 5 个阶段行指定 sonnet
- **结果**: ✅ PASS（验证命令：grep "sonnet" → 6 匹配，含 5 行参数表 + 1 行约束）

### AC-5 审查阶段并行 reviewer
- **Given**: 5-review.md 步骤 3 存在
- **When**: 读取并行 reviewer 分组表
- **Then**: 包含 reviewer-1(R1+R3)、reviewer-2(R2+R4+安全)、reviewer-3(R5+R6)
- **结果**: ✅ PASS（验证命令：grep "reviewer-1\|reviewer-2\|reviewer-3" → 3 匹配）

## 回归测试
- 1-design.md 原有步骤 0-9 编号完整（步骤 1.5 插入不影响后续编号）
- cross-review-matrix.md 原有 3 套矩阵定义未变更
- 5-review.md 原有步骤 1-6 编号完整
- spec-artifacts.md 原有 CHANGE/REQUIREMENT/DESIGN/ARCHIVE 模板完整

## Bug 清单
（无）
