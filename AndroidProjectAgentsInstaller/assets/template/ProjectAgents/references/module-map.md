# 模块地图

用这份地图辅助判断模块职责和风险，不要把它当成全工作区检索的替代品。

> 把下面的示例模块名替换成目标项目真实结构；不适用的层级直接删掉。

## 分层

- `[APP_SHELL_MODULE]`：壳工程和 APK / App Bundle 构建入口；代码较少，主要负责组装。
- `[APP_MAIN_MODULE]`：主应用逻辑、导航中心或首页聚合入口；聚合度高，通常连接首页、Tab、路由入口和核心页面。
- `[SERVICE_LAYER_PATTERN]`：如果项目确实存在独立的跨模块服务契约层，就把它写在这里；如果没有，就删掉这一层，不要为了套模板强行抽象。
- `[PLATFORM_SERVICE_MODULES]`：平台服务、数据源和共享业务能力。
- `[UI_COMPONENT_MODULE]`：通用 UI 组件和标准化组件库。
- `[CROSS_CUTTING_MODULES]`：地图、聊天、RN、支付、媒体等横向能力组件。
- `[FEATURE_MODULE_EXAMPLES]`：按业务域拆分的上层业务模块。

## 典型模块职责

### 核心应用

- `[APP_SHELL_MODULE]`：主应用壳和 APK / App Bundle 构建器。
- `[APP_MAIN_MODULE]`：主应用逻辑、导航中心和核心聚合入口。

### 业务模块

- `[FEATURE_MODULE_EXAMPLE_A]`：业务域 A。
- `[FEATURE_MODULE_EXAMPLE_B]`：业务域 B。
- `[FEATURE_MODULE_EXAMPLE_C]`：业务域 C。

### 组件与基础能力

- `[UI_COMPONENT_MODULE]`：通用 UI 组件。
- `[COMMON_MODULE]`：共享业务逻辑聚合层，很多通用逻辑、常量、工具和跨域能力会落在这里。
- `[PLATFORM_SERVICE_MODULES]`：平台服务基础设施和通用平台能力接入。
- `[SPECIAL_MODULE_OR_DEPENDENCY]`：历史共享库、特殊组件或高影响面模块。

### 服务与契约

- `[SERVICE_LAYER_PATTERN]`：服务接口、DTO、路由契约或 facade 层；如果项目没有这一层，就删掉这里的描述。
- `[ROUTER_OR_SERVICE_DISCOVERY]`：如果项目存在模块服务暴露、路由分发、Navigation、DI entry point 等统一机制，就把真实方案写清楚。

## 模块间通信

- 先确认项目真实的跨模块通信方式，再写规则。有些项目通过服务接口、路由层、Facade 或共享契约通信，也有些项目允许 feature/domain/data 直接依赖，或通过 Navigation、DI、Compose 状态层协作。
- 把目标项目现有的路由框架、服务发现机制、Navigation、事件机制补到这里，例如 `[ROUTER_OR_SERVICE_DISCOVERY]`、`[EVENT_BUS_OR_MESSAGE_BUS]`。
- 调整跨模块接口、DTO、路由 path、事件名或服务查找逻辑时，要同时检查定义方、实现方、调用方和平台差异。

## 依赖规则

- 不要默认套用“业务模块不能直接依赖”这类规则。先把项目真实的依赖方向写清楚：哪些依赖被禁止，哪些通过服务层走，哪些允许按 feature/domain/data 分层直连。
- 业务模块、UI / 通用组件、基础能力模块之间的允许依赖方向，也按项目真实规则补充，不要保留空泛描述。
- 修改 Gradle 依赖前先判断是否真的进入重型模式，避免在普通业务问题中过早展开构建上下文。

## 高关注区域

- `[APP_MAIN_MODULE]`：聚合度最高、最敏感的平台核心模块
- `[COMMON_MODULE]`：共享能力集中，改动容易波及多个业务域
- `[SERVICE_LAYER_PATTERN]`：契约层，改动容易形成跨模块破坏
- `[SPECIAL_MODULE_OR_DEPENDENCY]`：历史特殊模块、AAR 切换模块或高耦合模块

## 实用阅读顺序

1. 默认先定位目标类、资源、页面或路由所在模块。
2. 再读目标模块内的直接调用链和相关资源。
3. 如果影响跨越平台、服务契约或装配边界，再检查：
- `[APP_MAIN_MODULE]`
- `[COMMON_MODULE]`
- `[SERVICE_LAYER_PATTERN]`
- `[ROUTER_OR_SERVICE_DISCOVERY]`
- 实际存在的 Navigation / DI / 状态同步机制
- 平台专属 sourceSet 和 Manifest 覆盖

## 技术栈提醒

模块分析不要脱离根工程版本基线。很多模块是独立版本化、可发布的，但实现时仍受根级依赖映射、Android 编译配置和项目现有主流技术栈约束。
