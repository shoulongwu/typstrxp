# Qwen 3.8 Flash 冒烟测试 001

日期：2026-09-21。任务：`C0_01`。模型：`qwen3.8-flash`。服务：Qianwen-compatible API。
性质：一次真实 C0 生成加最多一次修复的开发冒烟；不是正式实验，不运行 C1/C2，不给 Strict PPL 结论。

## 固定输入与环境

- dataset：`0.2.0-draft`
- protocol：`0.3.0-draft`
- prompt SHA-256：`1dca822eaed5e061a78d82ffee90560003b53205e14e32353aa68c5fdf41e256`
- Typst：`0.12.0 (737895d7)`
- Typst binary SHA-256：`71013695dfcfef0a92c7df42f63fdea3e8f12fd72220a55a03c9a6729b322b78`
- repair scope：`prefix_through_target`
- sampling：provider default；接口未返回可核实的 temperature/seed

## C0 生成

API 请求成功并得到完整 assistant content：

- HTTP：200
- finish reason：`stop`
- latency：519.56 s
- prompt/completion/total tokens：621 / 31,042 / 31,663
- provider 报告 reasoning tokens：26,534
- assistant content：13,031 Unicode characters，482 physical source lines
- raw response SHA-256：`c6432f11ee522f0556bb83a850fd968a1997f213c919542f723d5c44e4ef3aff`
- normalized source SHA-256：`03ef4dd03e54fb0c64c905dc6dd9746e8ec206a1d3b4f24206cff5c1c35b11c9`

Typst 0.12.0 编译失败。首个主诊断：

```text
error: unknown variable: imes
source.typ:31:190
... complete $3 \times 3$ example.
```

人工定位的最小 target block 是 `$3 \times 3$`，code-point 半开区间 `[1010, 1022)`。
该 balanced inline-math block 没有后置 label、resource、query、state 或后文 definition 依赖，prefix gate 标为 `VERIFIED`。

事件候选分类：

```text
error_category = MATH
prior_family = LATEX
procedure_family = MULTIPLICATION_SYMBOL
is_prior_candidate = true
```

这只是 C0 prior candidate，不能直接称为 Strict PPL。

## 唯一一次 repair

输入为原任务、完整原始 source、真实 compiler diagnostic、target block，以及允许编辑的 `[0, 1022)` prefix。要求返回完整源码，目标 block 后的 suffix 必须逐字符不变。

接口返回 HTTP 200，但没有可用 assistant content：

- reported model：`qwen3.8-flash`
- latency：591.71 s
- prompt/completion/total tokens：5,457 / 19,849 / 25,306
- provider 报告 reasoning tokens：19,849
- assistant content characters：0
- reasoning content characters：74,554
- finish reason：字符串 `"null"`
- raw response SHA-256：`79567fc29ec7221d563b6254128d4dfc23f320b8d1c21ecbb330279c97b29144`

Outcome：`NO_USABLE_ASSISTANT_CONTENT`。没有 `source_after`，所以不能执行 locality、prefix compile、语义保持或 SAME_PRIOR 检查。
本次 repair run 不进入有效 C2 分母，也不能分类为 `NO_TARGET_EDIT`、`OTHER_REPAIR_FAIL` 或 Strict PPL。

## 冒烟结论

已实际贯通：数据加载 → Qwen C0 生成 → 原始证据保存 → Typst 0.12.0 编译 → 首诊断提取 → target/prefix 人工 gate → repair API 调用。

未贯通：repair 后 locality 与 prefix compilation；原因是 provider 返回空 assistant content。
本次还暴露出两个运行问题：完整生成与修复各约 9–10 分钟；repair 在消费 19,849 completion tokens 后仍未返回源码。正式 pilot 前应预注册空输出/异常 finish reason 的重试政策和输出预算，且不能把这种无效输出补跑成“直到得到三个有效 run”。

原始 artifacts 保存在被 `.gitignore` 排除的 `runs/qwen-smoke-001/`，包括请求、提示词、原始 JSON、源码、诊断、字体清单和 boundary evidence；密钥未写入 artifacts。
