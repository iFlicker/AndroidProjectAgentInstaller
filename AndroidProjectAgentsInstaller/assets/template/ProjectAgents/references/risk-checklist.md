# 风险检查清单

在实际修改前以及写 review 时，都要过这份清单。

## 强制检查项

- 确认改动是否跨模块影响。
- 确认是否同时影响多个品牌包、平台包、flavor、渠道或 sourceSet 路径。
- 确认链路是否经过 `[APP_MAIN_MODULE]`、`[COMMON_MODULE]` 或其它高聚合公共层。
- 确认是否涉及 `[SERVICE_LAYER_PATTERN]` 的契约、接口、DTO、路由 path、事件名或服务查找逻辑变化。
- 确认受影响模块是否可能因为源码 / AAR 切换、feature toggle、代码生成或构建参数而切到另一套实现。
- 确认是否依赖了默认按外部依赖 / AAR 处理的模块，尤其是 `[SPECIAL_MODULE_OR_DEPENDENCY]`，以及其它当前未纳入稳定源码认知的依赖。
- 确认改动是否依赖平台专属 Manifest、资源覆盖或 Gradle 脚本行为。
- 确认改动是否符合项目现有 Android 官方和第三方开源技术栈及版本约束。

## 技术栈与版本检查

先从根级和目标模块文件确认当前版本基线，再决定实现方式。至少留意：
- Kotlin
- AGP
- AndroidX 与常用 Jetpack 组件
- Compose Compiler
- OkHttp
- RxJava / Coroutines / Flow
- Retrofit
- Compose 或 View 体系
- 图片库，例如 Fresco、Glide、Coil
- Java 语言级别与 Android 编译配置

不要默认引入或使用只适配更高版本技术栈的写法，例如：
- 仅适用于更高 Kotlin 版本的语法或标准库能力
- 仅适用于更新 AGP / Gradle DSL 的配置方式
- 当前项目未使用或版本不兼容的 AndroidX API
- 与现有网络、图片、异步库版本不兼容的调用方式、拦截器、适配器或扩展

如果需要推断某个实现是否安全，先回到依赖脚本、版本目录、根级 Gradle 配置和目标模块 `build.gradle` / `build.gradle.kts` 里核对版本与现有用法，再决定是否修改。

## Kotlin / Java 安全编码检查

- Kotlin 中优先使用 `?.`、`?:`、`?.let` 等空安全写法，避免 `!!`；Java 中访问对象属性前必须检查 null，并按项目习惯补充注解。
- 外部传入参数、网络 / 数据库 / JSON 返回值、跨模块 DTO 字段都要做空值兜底，不要假设服务方一定返回完整数据。
- 数组、List、Map、JSONArray 等访问前必须确认空值和边界；不要直接用不可信 index 访问集合。
- 集合判空优先沿用项目既有工具和扩展函数，不要重复新增等价工具。
- 遍历集合时避免在遍历过程中直接修改原集合；需要修改时使用副本、迭代器或明确安全的集合 API。

## Compose 检查

- 如果项目使用 Compose，确认状态归属是否正确，`remember`、`rememberSaveable`、`derivedStateOf` 不要替代本该上提的业务状态。
- 检查 `LaunchedEffect`、`DisposableEffect`、`SideEffect` 的 key 和触发时机，避免把一次性事件写成会重复执行的副作用。
- 检查 `Flow`、`StateFlow`、`LiveData` 到 Compose state 的收集方式是否沿用项目现有规范，例如生命周期感知收集。
- 检查列表 `key`、大块可重组区域和 `Modifier` 顺序，避免无意义重组、状态错位或点击 / 布局行为漂移。

## 内存与生命周期检查

- 单例、全局 manager、缓存、路由服务等长生命周期对象不要持有 Activity 或 Fragment context；需要 context 时优先使用 ApplicationContext。
- 在 `onDestroy`、`onDestroyView` 或对应生命周期里清理网络请求、Handler 回调、广播接收器、订阅和协程任务。
- Handler、Runnable、长生命周期 View、Adapter 回调等不要隐式持有页面实例；必要时使用静态内部类、弱引用或生命周期感知组件。
- 图片、列表、地图、WebView、RN 容器等重资源页面要关注释放时机，避免缓存或回调链导致页面无法回收。
- 使用缓存时优先沿用项目已有缓存策略，不要无边界持有大对象集合。

## 平台检查

如果工作区使用了 `src/main + src/[flavor] + src/[buildType]` 模式，不要只看：
- `src/main`
- 公共 `build.gradle`
- 当前激活的默认运行变体

还要检查：
- `src/[flavorA]`
- `src/[flavorB]`
- `src/debug`
- `src/release`
- 平台专属 Manifest
- 资源覆盖
- 平台专属 Gradle 脚本

对于资源改动，额外确认：
- 是否存在同名 `color`、`drawable`、`string`、`layout` 或其它资源分别定义在多个 sourceSet
- 当前运行变体命中的是否其实不是同一份资源值
- 修改是否会只影响一个变体，或意外改变另一个变体的覆盖结果

如果目标模块存在额外平台脚本或装配脚本，也要把 `[MODULE_EXTRA_GRADLE_FILES]` 补成真实文件名并列入检查项。

## 验证建议

选择能覆盖真实风险的最小验证方式：
- 优先查找并复用项目已有的 `test/`、`androidTest/`、截图测试、宏基准、baseline profile、lint、detekt 或自定义 Gradle 校验任务。
- 直接改动源码模块的 compile
- 受影响功能入口的最小回归路径
- 共享逻辑在多平台、多 flavor 间分支选择时的平台敏感验证
- Compose 页面或状态逻辑改动时，优先补或复用现有的 UI 测试、截图测试或预览验证手段
- AAR / 源码切换、代码生成或依赖解析相关的构建验证

如果无法完成验证，要明确说明，并点出剩余风险。

## tools 提醒

如果项目里已有 `tools/`、`scripts/`、`gradle task` 或团队内部扫描脚本能覆盖大范围检索、ID 清理、Binding 清理或共享 layout 分析，优先复用，而不是重新写一套。
