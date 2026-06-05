# 重型模式

只有当主文档里定义的触发条件明确命中时，才进入这里；否则默认仍按轻量模式处理。

## 重型规则

1. 先确认项目是单一 git root 还是多个独立 git root。确认后，仍以整个业务工作区作为检索边界；如果项目确实存在多个独立 git root，再把它们当成同一个业务工作区的一部分分析。
2. 先读根级关键文件：`settings.gradle`、`settings.gradle.kts`、`gradle.properties`、`gradle/libs.versions.toml`、`config.gradle`、`dependencies.gradle`，以及项目实际存在的 `[ROOT_EXTRA_GRADLE_FILES]`；如果工程使用 `buildSrc/`、`build-logic/`、included build 或其它 convention plugin 目录，也一并列入根级上下文。
3. 再读目标模块的 `build.gradle`、`build.gradle.kts`、`gradle.properties` 和 Manifest；如果模块存在 flavor 或平台目录，必须同时检查对应 sourceSet。
4. 如果目标模块还带额外平台脚本、装配脚本或独立依赖脚本，也要把它们一并列入必读项，例如 `[MODULE_EXTRA_GRADLE_FILES]`。
5. 把源码 / AAR 切换、开关脚本、版本映射和代码生成配置视为功能上下文的一部分。本地看得到的源码路径，可能在线上或当前构建模式下并不会生效。
6. 如果项目里有“默认按外部依赖 / AAR 处理”的模块或 loader，把它们视为外部依赖上下文的一部分；除非任务明确要求深入本地目录，否则不要把它当成稳定可读的本地源码模块。
7. 使用 `git status`、`git diff`、`git log`、`git blame` 等对比或历史能力时，先确认项目是单 git 还是多 git；如果是多 git，再按目标文件所属 module 或 git root 执行，不要用错误 git root 的结果替代真实上下文。
8. 大文件、生成表、埋点表在重型模式下也不自动全量通读；即使进入重型模式，也先检索目标符号、字段、配置段，再局部读取命中片段。
9. 修改代码时要服从项目现有 Android 官方和第三方开源技术栈及版本约束，不要默认按最新写法、最新 API 或最新依赖版本实现。
10. 命中特殊模块时，先看它的 `sourceSets`、自定义源码目录或构建脚本，不要预设它采用常规 `src/main` 目录结构。

## 重型工作流

### 1. 建立上下文

先读根级文件，理解：
- `settings.gradle` / `settings.gradle.kts` 里的模块注册、`pluginManagement`、`dependencyResolutionManagement`、included build
- `config.gradle`、依赖脚本、版本目录或共享配置里的源码 / AAR / flavor / 版本切换
- `dependencies.gradle`、`libs.versions.toml`、`buildSrc/`、`build-logic/` 或团队自定义依赖映射 / convention plugin
- `gradle.properties` 里的全局平台开关、构建参数和环境差异

同时识别项目当前技术栈和版本基线，例如 Kotlin、AGP、AndroidX、OkHttp、RxJava、Retrofit、Compose、Fresco、Glide 以及 Java / Android 编译配置。写方案、改代码、补调用方式时，都要优先兼容现有版本，而不是套用默认的新范式。

然后只读取当前任务真正相关的目标模块文件。只有在全工作区检索表明依赖方或调用方确实相关时，再扩展到更多模块。

### 2. 全局检索

默认优先使用 `rg --no-ignore` 和 `rg --files --no-ignore`。检索范围覆盖：
- `**/*.kt`
- `**/*.java`
- `**/*.xml`
- `**/*.gradle`
- `**/*.gradle.kts`
- `**/gradle.properties`
- `**/*.toml`
- `**/*.pro`
- `**/*.aidl`
- `**/*.proto`
- `**/CMakeLists.txt`
- `**/Android.mk`

默认至少排除：
- `**/build/**`
- `**/.git/**`
- `**/.gradle/**`
- `venv/**`
- 其它明显的生成物、缓存或打包产物目录

需要检索模式、查询顺序和结果分层时，再读 [search-playbook.md](search-playbook.md)。

### 3. 深查平台差异

不要只停留在 `src/main`。需要检查：
- `src/main`
- `src/[flavorA]`
- `src/[flavorB]`
- `src/debug`
- `src/release`
- 平台专属 Manifest
- 平台专属 Gradle 脚本
- 资源覆盖目录

如果目标项目有主品牌包、海外版、定制版或渠道差异，先以当前构建参数判断默认运行目标；但在修改共享逻辑、平台分支逻辑或资源覆盖逻辑前，必须同时评估其它变体的影响。

同名资源也要按覆盖关系来分析。像 `color`、`drawable`、`string`、`layout` 这类资源，可能在多个 sourceSet 中名字相同但实际值不同；不要只因为资源名一致就判定行为一致，必须结合实际定义与覆盖顺序判断。

### 4. 高风险改动检查

在提出改动方案、落地修改或写 review 之前，先过 [risk-checklist.md](risk-checklist.md) 里的强制检查项，尤其关注：
- 跨模块影响
- 共享公共层或核心入口层
- 服务契约变化
- 源码 / AAR 切换导致的差异
- 默认按外部依赖处理的模块带来的盲区
- 现有技术栈和版本兼容性
