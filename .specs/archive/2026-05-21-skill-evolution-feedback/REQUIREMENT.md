# REQUIREMENT — skill-evolution-feedback

## 用户故事
作为 flow-go 用户，在使用过程中提出改进建议（如"单一职责+渐进式披露"），我希望 skill 能自动捕获这些反馈并在验收时分析归类，以便 skill 自我进化不断优化。

## 验收准则（AC）

### AC-1：用户输入实时记录
- Given 一个活跃 Change 正在执行
- When 用户发送任意消息
- Then 消息原文追加到 `.specs/<id>/user-inputs.jsonl`，格式为 `{"ts":"...","change_id":"...","stage":"...","input":"..."}`
- And 无活跃 Change 时不触发记录

### AC-2：验收阶段反馈分类
- Given 7-验收阶段执行
- When `.specs/<id>/user-inputs.jsonl` 存在
- Then 运行 `feedback_classifier.py` 将用户输入分为 project/skill/preference/noise 四类
- And skill 反馈追加到 `.specs/evolution/skill-feedback.jsonl`（跨 change 持久）

### AC-3：SUGGEST 进化路径
- Given 归档完成后且 `skill-feedback.jsonl` 含未处理条目
- When 自动进化触发
- Then 运行 `evolution_reflect.py --mode suggest` 生成改进假设报告
- And 展示假设摘要请用户确认
- And 不自动修改任何 skill 文件

### AC-4：一次性洞察
- Given 用户显式提出 skill 改进建议
- When suggest 模式处理该反馈
- Then 跳过 3 次重复门槛，直接生成洞察（one_shot=True）
- And 洞察仍需用户确认

### AC-5：特殊流程覆盖
- Given 热修归档时 `user-inputs.jsonl` 存在且行数 > 5
- Then 可选运行 feedback_classifier.py（高置信度模式）
- Given 废弃流程
- Then user-inputs.jsonl 随目录移动，不触发分析

### AC-6：归档生命周期
- Given 归档流程执行
- Then `.specs/<id>/user-inputs.jsonl` 随目录移动到 archive/
- And `.specs/evolution/skill-feedback.jsonl` 跨 change 持久保留

## 范围排除
- 不实现 skill 文件自动修改
- 不修改 evolution_signal.py
- 不增加 `.flowgo-config` 的 `user_input_capture` 配置项
