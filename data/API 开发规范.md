以下规范文本可直接粘贴至 Markdown/PDF 导出工具生成 `.pdf`。若需我针对具体团队技术栈（如 Spring Cloud / FastAPI / Django / Agent 框架）做裁剪，可进一步说明。

---

# API 开发规范

**版本**：v1.0
**适用范围**：Java（Spring Boot）与 Python（FastAPI / Django）后端服务，含传统业务 API 与 Agent 能力暴露接口。

---

## 1. 总则

1.1. **RESTful 为主，RPC 为辅**。对外暴露优先采用 HTTP + JSON；内部高性能微服务间可沿用 gRPC，但需通过 API Gateway 对外统一收敛。
1.2. **资源导向**。URI 必须代表资源（名词），禁止在 URI 中出现动词。
1.3. **无状态**。服务端不保存客户端会话状态，鉴权信息通过请求头传递。
1.4. **向下兼容**。接口一旦发布，禁止删除字段、修改字段语义或改变必填属性；变更必须通过版本化解决。

---

## 2. URI 与命名规范

| 规则                     | 示例                               | 禁止                                              |
| ------------------------ | ---------------------------------- | ------------------------------------------------- |
| 全小写， kebab-case      | `/api/v1/user-orders`              | `/api/v1/userOrders`、`/api/v1/User_Orders`       |
| 复数名词                 | `/api/v1/devices`                  | `/api/v1/device`                                  |
| 层级不超过 3 层          | `/api/v1/projects/{id}/tasks`      | `/api/v1/orgs/{id}/projects/{id}/tasks/{id}/logs` |
| 动作通过 HTTP 方法表达   | `POST /api/v1/tasks`               | `POST /api/v1/tasks/createTask`                   |
| 过滤/搜索用 Query String | `GET /api/v1/tasks?status=running` | `GET /api/v1/tasks/filterByStatus`                |

**特殊端点**：
- 批量操作：`POST /api/v1/tasks:batchDelete`（Google AIP 风格，冒号后缀表示自定义方法，仅限批量/复杂操作）
- 搜索建议：`POST /api/v1/tasks:search`（当 Query String 无法表达复杂查询体时）

---

## 3. HTTP 方法与状态码

### 3.1 方法语义

| 方法   | 幂等性    | 用途                                       |
| ------ | --------- | ------------------------------------------ |
| GET    | 是        | 获取资源，禁止带请求体                     |
| POST   | 否        | 创建资源，或触发异步任务                   |
| PUT    | 是        | 全量更新                                   |
| PATCH  | 否/视实现 | 部分更新（JSON Merge Patch 或 JSON Patch） |
| DELETE | 是        | 删除资源                                   |

### 3.2 状态码强制使用

| 场景                 | 状态码                                        |
| -------------------- | --------------------------------------------- |
| 成功查询             | `200 OK`                                      |
| 成功创建             | `201 Created`，响应头携带 `Location`          |
| 成功删除（无返回体） | `204 No Content`                              |
| 参数校验失败         | `400 Bad Request`                             |
| 未鉴权               | `401 Unauthorized`                            |
| 无权限               | `403 Forbidden`                               |
| 资源不存在           | `404 Not Found`                               |
| 资源冲突             | `409 Conflict`                                |
| 服务端内部错误       | `500 Internal Server Error`                   |
| 服务不可用/限流      | `503 Service Unavailable`，需带 `Retry-After` |

**禁止**：业务成功时返回 `200` 但响应体中自定义错误码覆盖；业务错误必须对应正确的 HTTP 状态码。

---

## 4. 请求与响应规范

### 4.1 统一响应体（仅针对业务 API，健康检查等除外）

```json
{
  "code": "SUCCESS",
  "message": "",
  "data": {},
  "requestId": "req_9f8d7e6c5b4a",
  "timestamp": "2024-01-15T09:30:00+08:00"
}
```

- `code`：业务结果码。`SUCCESS` 表示成功；失败时为机器可读的常量（如 `ORDER_NOT_FOUND`），禁止直接使用数字魔法值。
- `message`：人类可读描述，失败时必须提供，成功时可空。
- `data`：载荷，无数据时返回 `null` 或 `{}`，禁止返回字符串 `"null"`。
- `requestId`：全链路唯一追踪 ID，由网关或服务生成。
- `timestamp`：ISO 8601 格式，带时区偏移。

### 4.2 字段命名与时间

- JSON 字段统一使用 `camelCase`（Java/Python 序列化层负责映射）。
- 日期时间：`ISO 8601`（`2024-01-15T09:30:00+08:00`），禁止 `timestamp` 长整型或局部格式（如 `2024/01/15`）。
- 金额：使用整数分/厘传输，或字符串类型高精度小数，禁止 `float/double` 直接传金额。
- 空值：禁止返回 `undefined`；字段无值时显式置为 `null`，或根据场景省略该字段（需在文档中声明）。

### 4.3 分页规范

```json
// Request
GET /api/v1/tasks?pageNum=1&pageSize=20&sort=-createdAt

// Response
{
  "code": "SUCCESS",
  "data": {
    "list": [...],
    "pagination": {
      "pageNum": 1,
      "pageSize": 20,
      "total": 135,
      "totalPages": 7
    }
  }
}
```

- 页码从 1 开始。
- 排序字段 `sort`：前置 `-` 表示倒序，多字段用逗号分隔。
- 数据量大时，必须提供 `cursor`（游标）分页替代方案，避免深页码 `OFFSET` 性能灾难。

---

## 5. 错误处理

5.1. **错误响应体**（HTTP Status >= 400）：

```json
{
  "code": "INVALID_PARAMETER",
  "message": "Parameter 'email' must be a valid email address.",
  "details": [
    { "field": "email", "issue": "INVALID_FORMAT" }
  ],
  "requestId": "req_9f8d7e6c5b4a",
  "timestamp": "2024-01-15T09:30:00+08:00"
}
```

5.2. **禁止直接暴露内部异常堆栈**给客户端；生产环境堆栈必须脱敏，写入日志而非响应体。
5.3. **业务异常**必须映射为明确的状态码与错误码，禁止全局捕获后统一返回 `500`。

---

## 6. 安全规范

6.1. **传输层**：生产环境强制 HTTPS，HSTS 开启。
6.2. **鉴权**：统一使用 `Authorization: Bearer <token>` 或 `Authorization: <api-key>`，禁止在 URL 中传密钥。
6.3. **幂等性**：所有写操作（POST/PUT/PATCH/DELETE）必须支持幂等控制。客户端需携带 `Idempotency-Key: <uuid>`，服务端缓存该键至少 24 小时，重复请求返回首次结果。
6.4. **限流**：按应用 + 用户维度限流，返回 `429 Too Many Requests`。Agent 长会话场景需单独配置较低 QPS 但较高并发连接数。
6.5. **防重放**：敏感接口须校验请求时间戳（如 5 分钟有效窗口）或要求请求签名。
6.6. **输入校验**：
   - 拒绝非法 Content-Type；
   - 请求体大小限制（默认 10MB，文件上传接口除外）；
   - SQL 注入、XSS 过滤由 ORM/模板引擎兜底，禁止字符串拼接 SQL。
6.7. **敏感数据**：日志中禁止输出密码、Token、身份证号、手机号；接口响应中按需脱敏。

---

## 7. 版本控制

7.1. **URI 版本化**：`/api/v1/...`、`/api/v2/...`。
7.2. **Header 兼容**：同时支持 `X-API-Version: v2` 作为重写，但 URI 版本优先。
7.3. **弃用流程**：旧版本标记 `Deprecated`，保留至少 2 个版本周期（或按 SLA 约定），下线前提前通知并返回 `Sunset` 响应头。

---

## 8. 性能与稳定性

8.1. **超时**：
   - 网关层：默认 30s；
   - 服务间调用：根据 P99 设定，通常 3s - 10s；
   - 数据库查询：单条慢查询阈值 1s，强制索引审查。

8.2. **重试**：仅对幂等接口开启失败重试（最多 3 次，指数退避），非幂等接口禁止自动重试。
8.3. **压缩**：响应体 > 1KB 时启用 Gzip/Brotli。
8.4. **连接池**：数据库/Redis/HTTP Client 必须配置连接池大小与超时，禁止无界队列。
8.5. **异步化**：非核心路径（通知、日志、统计）必须异步解耦，使用消息队列或事件总线。

---

## 9. Java 后端实践（Spring Boot）

9.1. **框架约束**：
   - Web 层使用 Spring MVC 或 WebFlux；参数校验统一用 `jakarta.validation`，禁止手写校验逻辑。
   - 序列化使用 Jackson，禁用默认日期时间戳输出：`spring.jackson.date-format=yyyy-MM-dd'T'HH:mm:ssXXX`。

9.2. **异常处理**：通过 `@ControllerAdvice` 统一拦截，将业务异常（`BusinessException`）、校验异常（`MethodArgumentNotValidException`）映射为标准响应体。

9.3. **日志**：使用 SLF4J + Logback/Log4j2；日志格式包含 TraceId（MDC），JSON 化输出便于采集。

9.4. **接口文档**：强制使用 SpringDoc OpenAPI（Swagger v3），注解须准确标注 `required`、`example`、`deprecated`。

9.5. **线程安全**：Controller/Service 默认单例，禁止在实例字段中存储请求级状态。

---

## 10. Python 后端实践（FastAPI / Django）

10.1. **FastAPI**：
   - 依赖注入优先使用 `Depends`，数据库会话使用生成器 `yield` 确保释放。
   - 校验逻辑利用 Pydantic `BaseModel`，字段显式标注类型与 `Field(..., description="")`。
   - 异步路由必须声明 `async def`，但同步阻塞操作（如某些 ORM 查询）不得直接 await，应跑在线程池或改用异步驱动。

10.2. **Django / DRF**：
   - 使用 `Serializer` 做输入校验与输出序列化，禁止在 View 中直接操作 `request.data` 裸字典。
   - 查询优化：使用 `select_related` / `prefetch_related`，N+1 问题在开发阶段通过 `django-debug-toolbar` 或 CI 检测拦截。

10.3. **类型安全**：代码库必须配置 Mypy / Pyright，API 函数签名完整，禁止 `Any` 滥用。

---

## 11. Agent / AI 服务特殊规范

11.1. **流式响应**：LLM 生成类接口优先使用 SSE（`text/event-stream`）或 WebSocket，禁止长轮询。SSE 事件格式：

```
event: message
data: {"delta": "...", "finishReason": null}

event: done
data: [DONE]
```

11.2. **Tool / Function Calling**：
   - Tool Schema 严格遵循 JSON Schema，字段 `description` 必须准确（直接影响 LLM 调用决策）。
   - Tool 名称使用小写下划线 `snake_case`，长度不超过 64 字符。

11.3. **上下文长度控制**：服务端必须在进入 LLM 前做 Token 估算与截断（`max_tokens` 与历史窗口），禁止无限制传入导致 413/504。

11.4. **超时与取消**：流式接口必须监听客户端断开（SSE `abort` / WS `disconnect`），及时取消后台 LLM 推理任务，避免无效 Token 消耗。

11.5. **多 Agent 协作接口**：Agent 间通信优先采用内部 gRPC / 消息队列，对外暴露统一 Gateway；禁止前端直连内部 Agent 节点。

---

## 12. 文档与治理

12.1. **OpenAPI**：所有 HTTP 接口必须通过注解/类型推导生成 OpenAPI 3.0+ 文档，并托管至统一门户。
12.2. **变更评审**：接口变更须经过 Breaking Change 检查（字段删除、类型变更、必填项增加均视为 Breaking）。
12.3. **契约测试**：消费者驱动的契约测试（Pact）在 CI 中强制运行，防止服务端静默破坏消费者。
12.4. **监控**：接口级 RED 指标（Rate, Errors, Duration）必须接入，P99 延迟与 5xx 率配置告警。

---

**附则**：本规范由架构组负责解释，违反规范的新增代码禁止合并至主分支。现有存量接口按“新增遵守、存量逐步迁移”原则治理。