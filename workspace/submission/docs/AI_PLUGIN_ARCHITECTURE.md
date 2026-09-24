# AI 插件架构

## 1. 设计目的

插件层把通用视觉事实与场景语义分离。新增养老子场景、工作室规则或机器人任务时，只增加 manifest 和插件实现，不复制视频解码、检测、跟踪、证据和 REST 代码。

## 2. Manifest 契约

每个插件目录包含 `manifest.json` 与 `plugin.py`。manifest 声明 `plugin_id`、名称、版本、描述和入口。入口实现 `evaluate(facts)`，可选实现 `mock_facts(source)`，不能依赖前端状态或私有机器人协议。

## 3. 生命周期

```text
scan -> validate manifest -> dynamic import -> loaded
                                 |              |
                         import error       enabled/disabled
                                                |
                                      evaluate in parallel
                                                |
                                      event or degraded state
```

`PluginManager` 启动时扫描目录、校验 manifest、动态导入模块并记录错误。插件可以由 REST API 全局启用/停用；异常被隔离为插件 degraded，不得让其它插件和主服务一起崩溃。

## 4. 现有插件

### elderly_care

输入人物、药盒、区域和时间事实，输出 `suspected_medication` 等事件。规则强调“疑似”与证据时间窗；未经过医疗数据和临床验证，不提供诊断、用药建议或健康结论。

### workshop

输入工作台、工具、物料和人员关系事实，输出物品进入、离开、缺失或状态变化事件。它用于验证相同视觉底座可以迁移到非养老场景。

## 5. 并行与去重

多个插件共享同一批 `PrimitiveFact`，并行评估后按事件 ID/时间窗去重。插件版本随事件保存，便于复盘规则变化。当前测试覆盖同时启用、停用、异常隔离、确定性 fixture 和基本冷却；跨进程分布式锁和高吞吐压力测试留给真实部署阶段。

## 6. 前端控制

Plugins 页面调用真实的 `/api/v1/plugins/{plugin_id}/toggle`，不只修改本地 UI。Mock repository 以相同方法模拟，确保演示模式与 Real 模式接口形状一致。

## 7. 新插件模板

```python
class ExamplePlugin:
    plugin_id = "example"
    version = "0.1.0"

    def evaluate(self, facts):
        return []
```

新插件必须提供：触发条件、最短持续时间、去重/冷却、置信度来源、证据策略、异常处理、单元测试和 README 说明。若使用模型或外部服务，必须在 `THIRD_PARTY_NOTES.md` 登记。
