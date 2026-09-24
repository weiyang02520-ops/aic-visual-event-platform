# 注册对象/人员的 CPU 特征匹配契约

日期：2026-09-22  
状态：原型已实现并测试，未宣称真实身份识别准确率

## 1. 为什么补这一层

计划书要求支持自定义物品登记和注册式人员区分。仅保存名称或参考 URI 不能完成匹配，因此 AI 服务现在允许登记一个经过外部提取或本地生成的数值特征向量，并用余弦相似度返回候选。

## 2. 当前算法

`visual_event_ai.embeddings` 提供三部分：

1. `gray_embedding`：把有限、非布尔、范围为 `[0,255]` 的等宽灰度矩阵切成 `4×4` 网格，提取网格平均强度和 16-bin 强度直方图，得到 32 维归一化向量；浮点强度保留，不会截断或裁剪；
2. `normalize_vector`：拒绝空/全零向量、布尔值、数字字符串、非有限值和维度不一致；使用抗溢出的范数计算归一化有限大数值；
3. `match_embeddings`：对注册向量计算余弦相似度，按相似度排序，并根据 `[0,1]` 内的有限非布尔实数阈值标记 `accepted`。

这是可解释的 CPU heuristic，不是人脸识别、ReID、深度模型或比赛准确率结果。光照、视角、遮挡和相似物品会导致误匹配；真实模型到位后，可替换特征提取器而保持登记与匹配 API 不变。

## 3. 登记示例

```http
POST /api/v1/objects
Content-Type: application/json

{"name":"药盒","embedding":[1,0]}
```

服务会把向量归一化后保存到 SQLite 的对象 payload。人员接口同理：

```http
POST /api/v1/persons
Content-Type: application/json

{"display_name":"家属","role":"family","embedding":[0.8,0.2]}
```

## 4. 匹配示例

```http
POST /api/v1/registry/match
Content-Type: application/json

{"kind":"object","embedding":[0.98,0.02],"threshold":0.8}
```

也可以直接传灰度矩阵，让服务生成 32 维 baseline：

```json
{"kind":"all","gray":[[0,0,255],[0,0,255]],"threshold":0.8}
```

响应按相似度降序排列：

```json
[
  {"registry_id":"...","label":"药盒","kind":"object","similarity":0.9998,"accepted":true}
]
```

没有登记特征时返回空数组。布尔值和数字字符串会被请求 schema 拒绝并返回 `422`；空向量、全零向量、非矩形灰度矩阵和越界/非有限灰度值会返回 `400`。整数与浮点输入均可用。候选维度与查询维度不一致时，该候选会被忽略。没有达到阈值的候选仍可返回，但 `accepted=false`，前端应保留人工复核，不应强行改写为确定身份。对象/人员登记遇到空或全零向量也返回 `400`，不会保存无效记录。

## 5. 与帧管线的边界

当前 JSONL fixture 中若检测对象带有 `embedding` 字段，analysis job 会在 Detector/Tracker 后调用登记候选并把前五个匹配写入 `PrimitiveFact.metadata.registry_matches`。真实图像仍需要根据老师提供的摄像头分辨率、对象类别、隐私和模型输入约束选择可靠的 crop/embedding 提取器。后续可把当前 baseline 替换为 `AppearanceMatcher`：

```text
Frame → Detector/Tracker → crop/gray embedding → registry match
      → PrimitiveFact(subject/object identity + similarity)
      → scene plugin → UnifiedEvent → human review
```

当前已实现的是“带 embedding 的 fixture → registry match → PrimitiveFact metadata”链路；在真实接入前不得把这个 baseline 当成人脸识别，也不得把 `accepted` 当成医学或安全决策。涉及老人身份、健康和机器人执行时，默认保留 `unknown/ambiguous` 和人工确认。

## 6. 验收

测试覆盖固定维度、归一化、排序/阈值、坏数据处理、REST 登记/匹配和本地 fixture 到 `registry_matches` 的 analysis job 链路。测试证明的是契约和可重复算法，不证明真实场景准确率；最新全量测试数以 `agent-state/TEST_EVIDENCE.md` 为准。
