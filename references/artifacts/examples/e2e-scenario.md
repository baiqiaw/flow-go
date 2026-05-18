# 端到端场景演练：「用户登录功能」

> 展示 flow-go 8 阶段完整流程，包含正常路径和异常场景。新用户建议先读本文件理解全局。

---

## 场景背景

**项目**：一个已有注册功能的 Web 应用，需要新增「用户登录」功能。
**团队**：AI agent 扮演全部 6 角色，用户为决策者。
**复杂度**：STANDARD（涉及前端+后端+数据库，但无外部依赖）。

---

## 阶段 0 — 需求（产品经理）

### 用户输入

```
go
```

由于 STATE.md 不存在，系统判断为新项目，路由到 0-需求。

### 角色声明

```
✅ 路由：0-需求
✅ Change-ID：CH-20240315-001
✅ 复杂度：STANDARD
✅ 当前角色：产品经理
✅ 角色红线：禁止写实现代码、改技术设计
✅ 第一动作：与用户确认需求范围
```

### 产出：CHANGE.md

```markdown
# Change：用户登录功能

## 概要
为已注册用户提供登录功能，支持邮箱+密码方式。

## 业务动机
当前用户注册后无法登录，核心链路断裂，阻塞所有后续功能。

## 范围
- 邮箱+密码登录
- 登录状态保持（session）
- 登录失败提示
## 范围排除
- OAuth 第三方登录（后续 change）
- 找回密码（后续 change）
```

### 产出：REQUIREMENT.md

```markdown
# 需求规格：用户登录功能

## AC-1：正常登录
Given 用户已注册（邮箱 test@example.com，密码正确）
When 用户在登录页输入邮箱和密码并点击登录
Then 跳转到首页，显示用户昵称

## AC-2：密码错误提示
Given 用户已注册
When 输入错误密码
Then 显示「邮箱或密码错误」，不提示具体哪个字段错误

## AC-3：未注册邮箱
Given 该邮箱未注册
When 用户尝试登录
Then 显示「邮箱或密码错误」（不泄露注册信息）

## AC-4：登录状态保持
Given 用户已成功登录
When 关闭浏览器后重新打开
Then 7 天内仍保持登录状态

## 非功能需求
- 登录响应时间 < 500ms（P95）
- 密码不明文传输（HTTPS + 哈希）
```

### 需求评审

评审员检查：
- AC 是否可测试 → ✅ 每个 AC 都有 Given/When/Then
- 非功能需求是否有量化指标 → ✅ 500ms / HTTPS
- 范围排除是否合理 → ✅ OAuth/找回密码明确延后

结果：`CH-20240315-001-REVIEW.md` 标记 **PASS**。

### Handoff（0→1）

产品经理传递给技术经理：
- ✅ 业务动机清晰（核心链路断裂）
- ✅ AC 优先级（AC-1/2/3 为 Must，AC-4 为 Should）
- ✅ 范围排除及理由
- ✅ 非功能约束（500ms / HTTPS）

---

## 阶段 1 — 设计（技术经理）

### 产出：DESIGN.md

```markdown
# 技术设计：用户登录功能

## 架构
- 前端：React 登录表单 → POST /api/login
- 后端：Express 路由 → bcrypt 验证 → JWT 签发
- 存储：users 表（已有）

## 数据流
1. 前端 POST {email, password}
2. 后端查 users 表，bcrypt.compare 验证
3. 成功 → 签发 JWT（7天有效期），Set-Cookie
4. 失败 → 返回 401，统一错误信息

## API 设计
POST /api/login
  Request: { email: string, password: string }
  Success 200: { user: { id, nickname }, token }
  Error 401: { message: "邮箱或密码错误" }

## 数据库变更
无新表，使用现有 users 表的 email/password_hash 字段。

## 关键决策
- 选择 JWT 而非 session（无状态，易扩展）
- 密码用 bcrypt（已有库，无需新增依赖）

## 风险清单
| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 暴力破解 | 中 | 高 | 登录失败 5 次锁定 15 分钟 |
```

### 设计评审

评审员检查：
- API 设计是否覆盖全部 AC → ✅
- 安全方案是否充分 → ✅ bcrypt + 速率限制
- 数据库变更是否合理 → ✅ 无新表

结果：`CH-20240315-001-REVIEW.md` 追加设计评审 **PASS**。

---

## 阶段 2 — 任务（项目经理）

### 产出：TASK.md

```xml
<task-plan change-id="CH-20240315-001">

<task id="T01" priority="must">
  <title>后端登录 API</title>
  <description>实现 POST /api/login，含 bcrypt 验证和 JWT 签发</description>
  <read_files>src/routes/auth.ts, src/models/user.ts</read_files>
  <verify>curl -X POST http://localhost:3000/api/login -d '{"email":"test@example.com","password":"wrong"}' -s | jq .code</verify>
  <depends_on></depends_on>
</task>

<task id="T02" priority="must" parallel="true">
  <title>前端登录表单</title>
  <description>创建登录页面，表单提交到 /api/login，处理成功/失败</description>
  <read_files>src/pages/, src/components/</read_files>
  <verify>npm run build</verify>
  <depends_on></depends_on>
</task>

<task id="T03" priority="must">
  <title>登录状态中间件</title>
  <description>JWT 验证中间件，保护需登录的路由</description>
  <read_files>src/middleware/, src/routes/</read_files>
  <verify>curl -H "Authorization: Bearer <token>" http://localhost:3000/api/me -s | jq .user</verify>
  <depends_on>T01</depends_on>
</task>

<task id="T04" priority="should">
  <title>登录失败锁定</title>
  <description>连续失败 5 次锁定 15 分钟，防止暴力破解</description>
  <read_files>src/routes/auth.ts</read_files>
  <verify>for i in $(seq 1 6); do curl -X POST http://localhost:3000/api/login -d '{"email":"test@example.com","password":"wrong"}' -s; done</verify>
  <depends_on>T01</depends_on>
</task>

</task-plan>
```

### 任务评审

评审员检查：
- 任务粒度是否可单次 context 完成 → ✅（每个任务 1-3 文件）
- depends_on 是否合理 → ✅ T01 是 T03/T04 的前置
- verify 命令是否可执行 → ✅
- 优先级排序 → Must: T01/T02/T03, Should: T04

结果：评审 **PASS**。

---

## 阶段 3 — 开发（开发员）

### 执行 T01：后端登录 API

开发员读取 `src/routes/auth.ts` 和 `src/models/user.ts`，实现登录逻辑。

产出 SUMMARY-T01.md：
```markdown
## 开发摘要：T01-后端登录API

### 改动文件
| 文件 | 变更 |
|------|------|
| src/routes/auth.ts | 新增 POST /api/login 路由 |
| src/utils/jwt.ts | 新增 JWT 签发工具函数 |

### verify 输出
```
$ curl -X POST ... | jq .code
401
```

### 交叉评审
评审通过，无幻觉，无越界改动。
```

### 执行 T02（与 T01 并行）

T02 完成后产出 SUMMARY-T02.md。

### 执行 T03 → T04

按依赖顺序完成。

---

## 阶段 4 — 测试（测试员）

### 产出：TEST.md

```markdown
# 测试报告：用户登录功能

## 测试矩阵

| AC | 测试用例 | 结果 |
|----|---------|------|
| AC-1 | 正确邮箱+密码登录 → 跳转首页 | ✅ PASS |
| AC-2 | 错误密码 → 显示统一错误 | ✅ PASS |
| AC-3 | 未注册邮箱 → 显示统一错误 | ✅ PASS |
| AC-4 | 登录后关闭浏览器，7天内保持登录 | ✅ PASS |
| 安全 | 连续 5 次失败 → 锁定 15 分钟 | ✅ PASS |
| 性能 | 登录响应 P95 < 500ms | ✅ 230ms |

## Bug 清单
（无）
```

---

## 阶段 5 — 审查（技术经理）

### 产出：REVIEW.md

```markdown
# 代码审查：用户登录功能

## Spec 合规
- AC-1~4 全部有测试覆盖 ✅
- 非功能需求（500ms/HTTPS）满足 ✅

## 代码质量
- 无硬编码密钥 ✅
- 无 SQL 拼接 ✅
- 错误信息统一 ✅

## 严重项
0 项（经循环评审确认）
```

---

## 阶段 6 — 部署（运维）

### 产出：DEPLOY.md

```markdown
# 部署记录：用户登录功能

## 环境
- 生产环境：AWS ECS
- 数据库：无迁移（使用现有 users 表）

## 部署步骤
1. docker build → ECR push
2. ECS 滚动更新
3. 健康检查通过 ✅

## 回滚方案
ECS 回滚到上一版本镜像，30 秒内完成。
```

---

## 阶段 7 — 验收（产品经理 + 项目经理）

### 产出：UAT.md

```markdown
# 验收报告：用户登录功能

## AC 验收
| AC | 验收结果 |
|----|---------|
| AC-1 正常登录 | ✅ 通过 |
| AC-2 密码错误提示 | ✅ 通过 |
| AC-3 未注册邮箱 | ✅ 通过 |
| AC-4 登录状态保持 | ✅ 通过 |

## 非功能验收
- 响应时间：230ms（目标 <500ms）✅
- 安全：HTTPS + bcrypt + 速率限制 ✅

## 验收结论：通过
```

---

## 异常场景演练

### 场景 A：设计阶段发现需求遗漏

**触发点**：技术经理在 1-设计阶段发现 REQUIREMENT.md 缺少「密码重试限制」需求。

**处理流程**：
1. 技术经理**不自行假设**（角色红线），回溯到产品经理
2. 产品经理补充 AC-5：「连续失败 5 次锁定 15 分钟」
3. 更新 REQUIREMENT.md，在 REVIEW.md 记录回溯事件
4. 技术经理继续设计

**回溯记录**：
```
| # | 从阶段 | 到阶段 | 原因 | 时间 |
| 1 | 1-设计 | 0-需求 | 需求遗漏：密码重试限制 | T+2h |
```

### 场景 B：测试阶段发现 Bug

**触发点**：测试员发现 AC-4「关闭浏览器后保持登录」在 Safari 上失效。

**处理流程**：
1. 测试员**不自行修代码**（角色红线），记录 Bug
2. 回溯到开发员修复（SUMMARY-T02 更新 cookie 设置）
3. 重新测试通过

### 场景 C：紧急热修

**触发点**：上线后发现 JWT secret 硬编码在代码中。

**处理流程**：
1. 用户输入 `热修`
2. 路由到热修流程（跳过 0-需求 / 1-设计）
3. 开发员修复（移到环境变量）→ 技术经理审查 → 运维部署
4. 热修**不允许跳过审查**（闸门硬规则）

---

## 复杂度对比

同一需求在不同复杂度下的闸门差异：

| 阶段 | LITE | STANDARD | HEAVY |
|------|------|----------|-------|
| 1-设计 | 跳过 | CHANGE + REQUIREMENT + 评审 PASS | 同 STANDARD + 安全审查 |
| 2-任务 | 跳过 | REQUIREMENT + DESIGN + 评审 PASS | 同 STANDARD + 依赖拓扑分析 |
| 3-开发 | CHANGE.md（含内联 AC） | DESIGN + TASK + 评审 PASS | 同 STANDARD + 文件数 ≤ 5 |
| 5-审查 | 跳过 | TEST + 全部 SUMMARY | 同 STANDARD + 性能审查 |
| 6-部署 | 跳过 | REVIEW.md（严重项 = 0） | 同 STANDARD + 灰度发布方案 |

> LITE 适合：紧急 hotfix、单行配置修改、文档纠错。
> HEAVY 适合：涉及支付/安全/数据迁移的变更。
