# T01-SUMMARY — 修复测试绕过

## 变更概述
修复 3-develop.md 中允许绕过非相关测试失败的机制，强制 0 失败要求。

## 变更文件
1. `references/stages/3-develop.md`
   - 步骤 3：移除"已有问题"概念，前置健康检查改为强制
   - 步骤 9：verify 明确要求 0 失败，禁止区分失败来源
   - 完成条件：增加"代码已提交"
2. `references/anti-patterns.md`
   - 新增 dev-06（绕过非相关测试失败）
   - 新增 dev-07（未提交代码就宣布完成）

## 沿用检查
- 无需沿用既有抽象（纯文本编辑）

## 自检
- 未改 REQUIREMENT / DESIGN ✅
- 调试日志已清理 ✅（无调试日志）

## verify 结果
```
T01 verify PASS
```

## 验证闭环
- 功能不变：仅修改文字描述，未改变已有逻辑行为 ✅
- verify 通过 ✅
