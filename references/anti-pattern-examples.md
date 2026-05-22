# Anti-Pattern Examples — 反模式实例对照

> 按 `grep 'scope-creep\|over-engineering\|...' references/anti-pattern-examples.md` 加载对应实例。
> 与 `references/anti-patterns.md`（抽象表格）互补，提供可操作的 ❌/✅ 代码对照。

---

## 1. scope-creep（需求蔓延）

**对应反模式**：req-03-no-scope-exclusion

**场景**：用户要求"加一个导出按钮"

### ❌ 错误做法：顺手加了一堆

```
function handleExport():
  format = detectFormat()        // 未被要求：自动检测格式
  if user.role != 'admin':       // 未被要求：权限校验
    return Error("无权限")
  data = queryAllUsers()         // 未被要求：导出全部用户
  if data.length > 10000:        // 未被要求：分页逻辑
    data = data.slice(0, 10000)
    notify("已截断至 10000 条")   // 未被要求：通知
  return exportTo(format, data)
```

**问题**：用户只说了"加一个导出按钮"，AI 自行假设了格式检测、权限、范围、分页 4 个功能。

### ✅ 正确做法：只做被要求的

```
function handleExport():
  data = getCurrentViewData()    // 导出当前视图
  return exportTo('csv', data)   // 最简格式
```

**关键差异**：用户要按钮就给按钮，其余问题留到需求澄清。不确定就问，不猜。

---

## 2. over-engineering（过度工程）

**对应反模式**：dev-01-skip-refactor（反面——过度重构也算）

**场景**：用户要求"计算折扣"

### ❌ 错误做法：策略模式+工厂+配置

```
interface DiscountStrategy:
  calculate(amount) -> float

class PercentageDiscount implements DiscountStrategy:
  percentage: float
  calculate(amount) -> amount * percentage / 100

class FixedDiscount implements DiscountStrategy:
  fixed: float
  calculate(amount) -> min(fixed, amount)

class TieredDiscount implements DiscountStrategy:
  tiers: List<(threshold, rate)>
  calculate(amount) -> ...

class DiscountFactory:
  create(type) -> DiscountStrategy

class DiscountCalculator:
  strategy: DiscountStrategy
  config: DiscountConfig
  apply(amount) -> ...
  // 40+ 行，为一个折扣计算
```

**问题**：当前只有一种折扣类型，却为"未来可能"设计了完整策略体系。

### ✅ 正确做法：一个函数

```
function calculateDiscount(amount, percent):
  return amount * percent / 100
```

**关键差异**：需要多种折扣类型时再重构。资深工程师看了会说"太复杂了"。

---

## 3. drive-by-refactor（顺手重构）

**对应反模式**：dev-02-cross-task-change

**场景**：用户要求"修复空邮箱崩溃"，报错在 `validateUser()` 的 `user_data['email']` 取值

### ❌ 错误做法：修 bug 顺手改了一堆

```
  function validateUser(user_data):
-   # Check email format
-   if not user_data.get('email'):
+   """Validate user data."""          // 顺手加了 docstring
+   email = user_data.get('email', '').strip()  // 顺手改了取值方式
+   if not email:
      raise Error("Email required")
-   if '@' not in user_data['email']:
+   if '@' not in email or '.' not in email.split('@')[1]:  // 顺手增强了验证
      raise Error("Invalid email")
-   if not user_data.get('username'):
+   username = user_data.get('username', '').strip()  // 顺手改了 username
+   if not username:
      raise Error("Username required")
+   if len(username) < 3:              // 顺手加了长度校验
+     raise Error("Username too short")
```

**问题**：修空邮箱崩溃只需处理 `.get('email')` 的空值，但 diff 改了 15 行。

### ✅ 正确做法：只修崩溃点

```
  function validateUser(user_data):
    # Check email format
-   if not user_data.get('email'):
+   email = user_data.get('email') or ''
+   if not email.strip():
      raise Error("Email required")
    if '@' not in user_data['email']:  // 此处已安全：上面确保非空
      raise Error("Invalid email")
    // 其余代码不动
```

**关键差异**：每行改动追溯到"修复空邮箱崩溃"这个需求。无关改动一行不碰。

---

## 4. skip-clarification（跳过澄清）

**对应反模式**：req-06-skip-clarification

**场景**：用户说"搜索加个排序"

### ❌ 错误做法：直接假设

```
function search(query):
  results = db.query(query)
  return results.sort(by='score', desc=true)  // 假设按分数降序
```

**问题**：排序规则未确认。用户可能想按时间、按相关性、按价格。

### ✅ 正确做法：先问再写

```
用户说"搜索加个排序"，需要澄清：

1. 排序字段：按什么排？
   - 分数/相关度（推荐，搜索场景最常见）
   - 时间
   - 价格
2. 排序方向：升序还是降序？
3. 是否需要用户切换排序方式？

确认后实现。
```

**关键差异**：30 秒的提问 vs 40 分钟的返工。不确定就问，不猜。

---

## 5. fake-verify（验证造假）

**对应反模式**：dev-03-fake-verify

**场景**：TASK.md verify 步骤要求 `pytest tests/test_auth.py`

### ❌ 错误做法：手写"通过"

```
T01 验证：
pytest tests/test_auth.py → 通过 ✅
```

**问题**：这是人类手写的文字，不是命令输出。实际可能根本没跑。

### ✅ 正确做法：贴真实输出

```
T01 验证：
$ pytest tests/test_auth.py
=================== test session starts ===================
collected 5 items

tests/test_auth.py::test_login_valid PASSED         [ 20%]
tests/test_auth.py::test_login_invalid PASSED        [ 40%]
tests/test_auth.py::test_logout PASSED               [ 60%]
tests/test_auth.py::test_token_refresh PASSED        [ 80%]
tests/test_auth.py::test_expired_token PASSED        [100%]

=================== 5 passed in 0.34s ====================
```

**关键差异**：verify 输出必须可追溯、可复现。粘贴 > 手写 > 口头声称。

---

## 6. weaken-failing（弱化失败用例）

**对应反模式**：test-02-weaken-failing

**场景**：测试发现 `sort_results()` 在相同分数时顺序不稳定

### ❌ 错误做法：改测试让变绿

```
// 测试红了：相同分数的顺序不一致
function test_sort_by_score():
  results = sort([{score:100, name:'A'}, {score:100, name:'B'}])
- assert results[0].name == 'A'    // 偶尔失败
+ assert results[0].score == 100    // 只检查分数，不看顺序 → "通过"了
```

**问题**：测试变绿了，但 bug 仍在——相同分数时排序不确定。

### ✅ 正确做法：修实现代码

```
// 测试不变，修实现
function sort_results(items):
- return items.sort(by=score, desc=true)
+ return items.sort(by=(-score, name))  // 稳定排序：分数降序+名称升序

// 测试仍然检查完整行为
function test_sort_by_score():
  results = sort([{score:100, name:'A'}, {score:100, name:'B'}])
  assert results[0].name == 'A'    // 现在稳定通过
```

**关键差异**：测试是验收标准的守护者。测试红了 → 报 bug → 修代码 → 重测。不能改测试来掩盖 bug。

---

## 核心洞察

> 这 6 个"错误做法"看起来都不傻——它们遵循设计模式、考虑了边界、做了"优化"。
> 问题出在**时机**：在不需要的时候做了不该做的事。
>
> **好的代码是简洁解决今天的问题，而不是提前应对明天的问题。**
