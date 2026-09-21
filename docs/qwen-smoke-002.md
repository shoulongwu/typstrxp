# Qwen 3.8 Flash 异常修复与冒烟测试 002

日期：2026-09-21。任务：`C0_01`。模型：`qwen3.8-flash`。服务：Qianwen-compatible API。
性质：针对 001 的空正文异常做一次独立开发复测；不是正式实验，不运行 C1/C2，不给 Strict PPL 结论。

## 异常与修复

001 的 repair 虽然返回 HTTP 200，却只有 74,554 字符的 reasoning content，没有 assistant content，且 finish reason 是字符串 `"null"`。这不是有效模型输出。

Qwen 官方兼容接口文档说明 `qwen3.8-flash` 支持 `reasoning_effort`，默认强度较高，并建议长输出使用流式传输。试点配置因此固定为：

- `reasoning_effort: "medium"`
- `max_tokens: 32768`
- `stream: true`
- `stream_options.include_usage: true`

运行器逐行保存原始 SSE，分别拼接 `reasoning_content` 与 `content`，忽略中间 chunk 的空或字符串 `"null"` 结束标记，并要求最终 `finish_reason=stop`。只有非空正文和最终 `stop` 同时满足才标记 `COMPLETE`。reasoning-only 响应现在标记为 `INCOMPLETE_REASONING_ONLY`，不会写成可编译 source。

参数依据：[Qwen OpenAI Chat Completions 官方文档](https://help.aliyun.com/en/model-studio/qwen-api-via-openai-chat-completions)。

## 固定输入与环境

- dataset：`0.2.0-draft`
- protocol：`0.3.0-draft`
- prompt SHA-256：`1dca822eaed5e061a78d82ffee90560003b53205e14e32353aa68c5fdf41e256`
- Typst：`0.12.0 (737895d7)`
- Typst binary SHA-256：`71013695dfcfef0a92c7df42f63fdea3e8f12fd72220a55a03c9a6729b322b78`
- repair scope：`prefix_through_target`
- temperature：provider default；seed 未提供

## C0 generation

接口通过 SSE 返回完整正文：

- HTTP：200
- finish reason：`stop`
- latency：64.84 s
- prompt/completion/total tokens：583 / 5,221 / 5,804
- provider 报告 reasoning tokens：1,748
- assistant content：10,294 Unicode characters，186 physical source lines
- reasoning content：3,825 characters
- raw response SHA-256：`b00bb5c1f3ce68c031245d86188398098923d4cfc5f06a6a6c97477a9ae8d616`
- normalized source SHA-256：`453b00facfb8810052ab678055343bccd4d96117fa135d31b2a772dd6d2afe0f`

Typst 0.12.0 编译失败。首个诊断位于页眉配置中的 `#emph(Advanced Linear Algebra — Lecture Notes)`；模型把普通文本作为函数参数代码解析，随后还触发同一顶层表达式内的相关错误。

人工选择包含首诊断的完整顶层 `#set page(...)` 作为 target block，code-point 半开区间为 `[0, 284)`。该表达式定界完整、无用户定义的前向依赖，并独立表达页眉/页脚配置，prefix gate 标为 `VERIFIED`。

## 唯一一次 repair

repair 同样通过 SSE 返回完整正文：

- HTTP：200
- finish reason：`stop`
- latency：69.59 s
- prompt/completion/total tokens：5,248 / 5,043 / 10,291
- provider 报告 reasoning tokens：1,563
- assistant content：10,316 Unicode characters
- reasoning content：5,291 characters
- raw response SHA-256：`bc362742b82e6f9c6c2851a56ca2df62a61c63190a5a5f9d644b71b7d246e71e`
- normalized source SHA-256：`2c1b1455debf3dd4deda10d94e05d2d3e71c245a13e7b1c37b0e42590a731c89`

自动检查结果：

- target block 后的 suffix 逐字符不变；
- 修复后的 `[0, new_end)` prefix 用 Typst 0.12.0 编译成功；
- 完整文件继续编译失败，首个可见错误已推进到后续 `definition` 定义；
- 完整文件的后续错误是 generation 已存在但此前被首错误遮蔽的独立问题，不属于本次 target 的修复失败。

repair 把页眉的 `counter(page) != 1` 改为 `counter(page) > 1`，对正常正整数页码等价；同时把破折号改写为 `--`。自动检查不能证明排版完全等价，因此 `semantic_preservation` 保持 `PENDING_REVIEW`，本冒烟不据此给出 `FIXED` 或 Strict PPL 标签。

## 结论

复测贯通了：完整流式 generation → 最终结束状态校验 → Typst 编译 → 自包含 target/prefix gate → 完整流式 repair → 后文不变检查 → 修复前缀编译。001 的 reasoning-only 空正文异常在新配置下没有复现，运行器也已能明确拒绝该类无效响应。

原始 artifacts 保存在被 `.gitignore` 排除的 `runs/qwen-smoke-002/`；包含请求、提示词、原始 SSE、源码、诊断、用量、字体清单和边界证据，不含密钥。
