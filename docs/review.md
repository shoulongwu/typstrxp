# 实验指导与 dataset 审阅报告（v0.2 历史记录）

> 后续用户修订见 [v0.3 修订记录](revision-0.3.md)；当前编辑范围与凭据路由以 experiments_guide.md 和 configs/pilot.json 为准。

审阅日期：2026-09-21。范围：用户提供的 2 个文件及当前本机环境。
结论：C0 → C1 → C2 的研究主线可以保留，但原版判定规则不宜直接用于正式统计。
本轮已修订材料并提供离线基础结构，尚未声称完整运行器已经完成。

## 已发现的问题与处理

| 重要性 | 原稿问题 | 本轮处理 |
| --- | --- | --- |
| 高 | dataset 标为 C1，实际上是 10 道真实场景 C0 任务 | 改为 C0_01–C0_10，保留 legacy_id，C1 独立建库 |
| 高 | 页数在 2–4、2–5、严格 2、2–3 之间冲突 | 用户授权放宽后统一 2–5 页，质量独立报告 |
| 高 | 编译通过就算 FIXED，删除/隐藏目标亦可过关 | 保留 prefix 编译门控，增加目标语义核验与 SEMANTIC_REGRESSION |
| 高 | 看到相同 prior 就判持续，和 NO_TARGET_EDIT 重叠 | 未有效修改目标优先 NO_TARGET_EDIT，主动修改才考虑持续/复发 |
| 高 | 同属 LaTeX 就可能算同一 prior | 同时要求 prior、procedure、目标、执行上下文和失败关联 |
| 高 | prefix gate 默认 true，原有失败可能遮蔽截断依赖 | 使用 VERIFIED / NON_SELF_CONTAINED / UNKNOWN 三态，事前留证 |
| 高 | suffix 未改就认为错误原已存在；改过的 block 出错就认为修复引入 | 空间关系和因果归属分离，不确定保留 UNCERTAIN |
| 高 | “三个独立 run”和“三个有效 run”混用 | 固定三次机会，协议违规不补跑，不足三个有效 run 不给二值阳性 |
| 高 | 重试次数会影响 event 数及 PCR，分母缺失规则不完整 | event 与 attempt 分层，空分母 NA，明确各指标分母及覆盖率 |
| 中 | 源码关键词和至少 50 行被命名为 semantic_checker | 改为有明确限制的 topic_screen，移除行数质量代理 |
| 中 | C0 给出 #set page 和标题源码示例，影响自然错误观察 | 移除实现示例，数学内容改描述性记法；承认仍非完全无提示条件 |
| 中 | 生成伪真实论文实验数据、履历、财务结论，增加真实性混杂 | 简历/商业案例标虚构，论文模拟数据标 illustrative |
| 中 | BCE 描述像能消除所有梯度消失；导数乘积直接代表完整网络梯度 | 限定为输出 logit，补充权重 Jacobian 的作用 |
| 中 | 试卷评分表只有 Question 1–4，但实际有 14 题 | 改为 Part I–IV，明确学生题面、不给解答，时长为虚构布局元数据 |
| 中 | SAME_PRIOR_RECURRENT 与 RECURRED 拼写不一致 | 统一 SAME_PRIOR_RECURRED |
| 中 | 首诊断被隐含视为源码最靠前位置 | 固定输出顺序，要求对完整 prefix 的先前错误和依赖审查 |
| 中 | schema 的成功字段预设 true/FIXED 可能污染未完成记录 | 要求未知值 null/UNKNOWN，排除 run 的 strict_ppl 为 null |
| 中 | 缺少配置冻结、采样、上下文隔离与截尾说明 | 补模型条件、独立调用、停止规则、缺失与聚类分析 |

上述方法学修订属于实施建议，协议仍为 draft，不代表已经完成预注册。
尤其“语义门控”“C0 失败尝试从同一快照重试”“C0/C2 共用提示词”是实质设计明确化，正式实验前应连同 checker 和采样计划统一冻结。

## 用户已确定的信息

- 用户补充 API 服务方：星渡 Xindu（https://xindu.xyz）。
- 用户提供实际 model ID：`qwen3.8-flash`、`glm-5.3-flash`、`deepseek-v4.1-flash`；以这些 ID 替代前述口头显示名称。
- 调用方式：API。
- 金额预算：不设上限；实验重复次数与终止规则照常固定。
- 页数：允许放宽，由本轮统一为 2–5 页。

配置已补齐 `https://xindu.xyz/v1` 与上述 ID，统一使用 `XINDU_API_KEY`。只读探测确认网站返回 200，`/v1/models` 未认证返回 401，提示支持 Authorization Bearer。这只证明认证入口响应，不证明模型权限或生成端点兼容。密钥通过本机环境变量提供，不进入仓库。

## 本机与实现状态

- 本机可执行 Typst 为 `0.15.1 (9dfd3a08)`，指导指定 `0.12.0`；本轮只核验版本，没有用 0.15.1 冒充正式结果。
- 普通数据检查可以运行；`--require-ready` 会因未满足正式条件而返回失败。
- 数据定义改为 JSON，Python 入口保留 TASKS / TASK_MAP；原 `semantic_checker` lambda 接口有意移除，调用方需改用 topic_screen 或真正语义验证。
- locality checker 仅证明文本修改范围合规，不判定语义、编译成功或 PPL。
- 9 个离线测试通过：覆盖 Unicode/变长 block、空 suffix、越界空白、重叠锚点、重复文本、删除目标和关键词假语义问题。
- 当前目录没有有效 Git 元数据，`.git` 是环境提供的只读目录；已建立文件结构，但没有创建提交或声称 Git 初始化成功。
- 未调用模型 API，没有真实实验数据。

## 实施前仍须补足的内容

1. 安装并隔离 Typst 0.12.0，固定字体、资源及编译超时；实际验证编译器坐标与原始 stderr。
2. 可靠 block parser 与人工 fallback。故障输入下简单括号扫描不足以承担正式 oracle。
3. 为 10 道 C0 题编写逐项 rubric；为每个实际出现的 candidate 编写并冻结 C1 atomic task/checker。
4. 完整 prefix gate、prior occurrence 对齐、语义保持检查与盲审流程。
5. 实现 artifact store、API adapter、C0/C1/C2 状态机与统计汇总，区分请求失败、输出截断、编译错误和待审。
6. 试点确定采样重复数、定位/可验证性/审核一致率阈值，再冻结正式实验。

目前只有 10 题且类别数不均（3/2/2/1/2），两篇论文主题相近；适合作为 pilot，不宜直接外推整个 Typst 任务分布。
自然场景任务同时要求内容创作和排版，会混入学科知识/写作负担。建议后续另设“给定正文仅排版”对照集；本轮未混入现有 C0 条件，避免改变研究对象。
强语义 checker 和 prefix gate 将引入筛选；报告全部排除与截尾，不能只展示最后能进入 C2 的案例。

## 技术核查资料

Typst 官方 [语法说明](https://www.typst.app/docs/reference/syntax/) 区分 markup、math、code 及 raw/comment，支持“正则命中不等于执行 procedure”的审阅意见。
官方 [Context](https://www.typst.app/docs/reference/context/) 与 [Query](https://typst.app/docs/reference/introspection/query/) 描述依赖文档上下文的行为，提示截断可能改变待测语义。
这些链接是现行文档，只用于概念核查；0.12.0 具体行为仍须由固定版本 fixtures 验证。
