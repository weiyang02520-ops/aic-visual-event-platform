# 模型 Provider 契约

日期：2026-09-22

## 当前 provider

| provider | 作用 | 当前状态 |
|---|---|---|
| `motion_cpu` | 纯 CPU 帧差连通区域基线 | 可用，解释性强，不代表训练模型准确率 |
| `fixture` | 读取 JSONL 中的预计算 objects，并可转发显式 keypoints metadata | 可用，只用于规则/接口验收，不是姿态模型 |
| `onnx` | 预留真实 ONNX 模型运行时 | 只有模型文件、`onnxruntime` 和输入/输出契约同时具备时才可用 |
| `ultralytics` | 可选 person/pose provider adapter | 需要 `ultralytics`、`AI_ULTRALYTICS_MODEL_PATH` 和可加载的模型文件；没有这些条件时明确 unavailable |

## 选择和降级

`AI_DETECTOR_PROVIDER` 可请求 provider。若请求的 provider 不可用，registry 会选 `motion_cpu`，并在 `/api/v1/providers/detectors` 中返回 unavailable 原因、selected 状态和模型路径。JSONL 来源固定选择 `fixture`，避免把 fixture 当成模型推理。

请求 `AI_DETECTOR_PROVIDER=ultralytics` 时，provider 接受本地帧 payload 中的 `image` / `frame` / `bgr` / `rgb`，调用 Ultralytics-compatible `model.predict()`，只把 person boxes 和可用的 COCO17 `nose`、`left_wrist`、`right_wrist` 关键点归一化为现有 `Detection` metadata。下游 tracker、relation、keypoint action 和 scene reasoner 不变。模型输出缺失、坐标非法或 confidence 越界时 fail closed。

安装可选 provider：

```powershell
python -m pip install -e ".[pose]"
$env:AI_DETECTOR_PROVIDER = "ultralytics"
$env:AI_ULTRALYTICS_MODEL_PATH = "C:\path\to\verified-pose-model.pt"
```

当前工作树没有安装 `ultralytics`，也没有模型权重；因此 provider adapter 的 fake-result 和 frame/fact integration tests 已验证，真实模型运行、准确率和延迟仍是 `UNVERIFIED`。模型权重不进入 Git 仓库。

即使 `AI_ONNX_MODEL_PATH` 指向文件且 `onnxruntime` 已安装，当前 ONNX provider 仍保持 unavailable，直到具体模型的输入/输出 adapter 被实现并测试；不会因为“文件存在”就把它选成可运行 provider。

## ONNX 边界

当前没有老师数据、类别表、输入尺寸、归一化方式、输出张量格式或已验收权重，因此没有擅自下载或绑定一个 YOLO/ONNX 模型。安装可选依赖：

```powershell
python -m pip install -e ".[model]"
$env:AI_ONNX_MODEL_PATH = "C:\path\to\verified-model.onnx"
```

即使运行时和文件存在，仍需为具体模型实现输入/输出 adapter，经过样本测试后才能把它标记为可用。当前代码会明确 fallback 到 `motion_cpu`。

## 验收

AI 当前全套测试为 363 passed；其中 provider 契约覆盖 `motion_cpu`、JSONL `fixture`、ONNX 明确 fallback、Ultralytics adapter normalization 和 `/api/v1/providers/detectors` REST 状态。motion_cpu 接受 0–255 有限非布尔灰度值并保留小数强度；注册对象/人员 embedding 属于独立的 CPU baseline 契约，详见 `REGISTRY_EMBEDDINGS.md`。JSONL 恢复坏行会标记 observation gap 并重置跨帧状态；时序 reasoner 对显式 `source_id` 执行同源配对；全量测试不代表真实 detector 准确率。
