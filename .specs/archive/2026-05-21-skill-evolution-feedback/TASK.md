# TASK — skill-evolution-feedback

## 变更类型
feature

## 任务列表

### T01: SKILL.md 增加前置动作·用户输入记录
- **优先级**: MustHave
- **depends_on**: -
- **write_files**: SKILL.md
- **verify**: grep「前置动作」SKILL.md 成功
- **描述**: 在 SKILL.md 第一步之前增加「前置动作·用户输入记录」章节。每条用户输入追加到 `.specs/<id>/user-inputs.jsonl`，格式 `{"ts":"...","change_id":"...","stage":"...","input":"..."}`。仅在有活跃 Change 时执行。

### T02: 新建 feedback_classifier.py
- **优先级**: MustHave
- **depends_on**: -
- **write_files**: references/scripts/feedback_classifier.py
- **verify**: `python3 references/scripts/feedback_classifier.py --help` 成功
- **描述**: 新建用户输入分类脚本。输入 `--specs-dir .specs/<id>`，读取 user-inputs.jsonl，分类为 project/skill/preference/noise。skill 反馈追加到 `.specs/evolution/skill-feedback.jsonl`。支持 `--complexity LITE` 高置信度模式。

### T03: 7-acceptance.md 增加对话反馈分类步骤
- **优先级**: MustHave
- **depends_on**: T02
- **write_files**: references/stages/7-acceptance.md
- **verify**: grep「feedback_classifier」references/stages/7-acceptance.md 成功
- **描述**: 在验收步骤 5（进化反思）中，信号检测后增加步骤 5a「对话反馈分类」。运行 feedback_classifier.py 分类用户输入，skill 反馈追加到 skill-feedback.jsonl。

### T04: evolution_reflect.py 增加 suggest 模式 + 一次性洞察
- **优先级**: MustHave
- **depends_on**: T02
- **write_files**: references/scripts/evolution_reflect.py
- **verify**: `python3 references/scripts/evolution_reflect.py --mode suggest --help` 成功
- **描述**: 新增 `suggest()` 函数和 `--mode suggest --feedback <path>` CLI 入口。按 Jaccard 相似度聚类 skill 反馈，生成改进假设（action_type=suggest_improvement）。增加一次性洞察：category=skill 的用户显式建议跳过 3 次门槛。

### T05: SKILL.md 第七步增加 SUGGEST 路径
- **优先级**: MustHave
- **depends_on**: T04
- **write_files**: SKILL.md
- **verify**: grep「SUGGEST 路径」SKILL.md 成功
- **描述**: 在第七步「自动进化触发」中，CAPTURE/FIX/BITTER PILL 旁边增加 SUGGEST 路径。触发条件：skill-feedback.jsonl 含未处理条目。不自动修改 skill 文件。

### T06: special-flows.md 热修归档增加可选反馈分析
- **优先级**: ShouldHave
- **depends_on**: T02
- **write_files**: references/stages/special-flows.md
- **verify**: grep「feedback_classifier」references/stages/special-flows.md 成功
- **描述**: 在热修流程归档步骤中，如 user-inputs.jsonl 存在且行数 > 5，可选运行 feedback_classifier.py（高置信度模式）。废弃流程不触发分析。

### T07: meta-artifacts.md 新增 user-inputs.jsonl 格式定义
- **优先级**: ShouldHave
- **depends_on**: -
- **write_files**: references/artifacts/meta-artifacts.md
- **verify**: grep「user-inputs.jsonl」references/artifacts/meta-artifacts.md 成功
- **描述**: 在 meta-artifacts.md 中增加 user-inputs.jsonl 的格式定义和 evolution/ 目录文件分类（持久 vs per-change）。

### T08: SKILL.md 第二步增加 user_input_capture 配置项
- **优先级**: CouldHave
- **depends_on**: T01
- **write_files**: SKILL.md
- **verify**: grep「user_input_capture」SKILL.md 成功
- **描述**: 在配置项表中增加 `user_input_capture`（默认 true，设 false 关闭输入记录）。

## 执行顺序
T01 + T02 + T07 可并行 → T03 + T04 + T06（依赖 T02）→ T05（依赖 T04）→ T08（依赖 T01）
