# Project Agents

这套说明会被多个 AI agent app 共同读取和增量维护，例如 Codex、Cursor、Claude Code、Antigravity 等；新增的稳定项目认知、检索规则、结构变化和风险约束，必须优先沉淀到 `ProjectAgents/ProjectAgents.md` 或 `ProjectAgents/references/` 下的专题文件，不要只留在某个 app 私有记忆、临时规则或对话上下文里。

默认先用轻量模式处理高频日常任务，只有在复杂度明显升级时，才切到重型模式。

> 首次落地时，先把全文中的 `[PLACEHOLDER]` 替换成目标项目真实信息；如果某条规则不适用，就删掉，不要保留空壳。

## 项目结构现状

先建立两个总前提：
- 先确认整个工作区是单一 git root，还是多个独立 git root；确认后再按实际仓库形态理解检索边界、变更范围和 git 命令执行位置，不要在未确认前直接假设成多 git 或单 git。
- 当前运行目标通常是 `[PRIMARY_APP_NAME]`；如果项目存在品牌包、产品 flavor、海外版或平台分支，修改共享逻辑、资源覆盖或服务契约时，仍要评估 `[SECONDARY_APP_NAME_OR_FLAVOR]` 以及其它变体的影响。

当前工作区根目录下可见的本地 module，建议至少列出：
- `[APP_SHELL_MODULE]`
- `[APP_MAIN_MODULE]`
- `[COMMON_MODULE]`
- `[FEATURE_MODULE_EXAMPLE_A]`
- `[FEATURE_MODULE_EXAMPLE_B]`
- `[UI_COMPONENT_MODULE]`
- `[SERVICE_LAYER_PATTERN]`

如果项目确认存在多个独立 git root，再额外列出这些 git root 的目录边界和各自承载的模块范围。

还要按项目实际情况补充这些稳定事实：
- 如果根目录 `settings.gradle`、`settings.gradle.kts` 或其它装配脚本会注册“默认按外部依赖 / AAR 处理”的模块或 loader，把它们明确写出来，例如 `[SPECIAL_MODULE_OR_DEPENDENCY]`。
- 如果项目使用 `buildSrc/`、`build-logic/`、included build、`gradle/libs.versions.toml` 或其它 version catalog / convention plugin 机制，也要明确写出依赖版本、插件和公共构建逻辑实际从哪里生效。
- 如果项目不是所有 module 都带 `src/main + src/[flavor]` 结构，明确列出哪些模块存在双平台 / 多 flavor sourceSet。
- 如果存在历史特殊模块，源码布局不是常规 `src/main` 结构，也要在这里写明，避免 agent 套用错误目录预设。

## 文档维护约定

当使用过程里发现“这已经是稳定规则，不该只存在本次对话里”时，要立即落文档，并按粒度选择位置：
- 影响整个工作区的总规则、默认流程、结构现状、共性约束：更新 `ProjectAgents/ProjectAgents.md`
- 某个专题的细化说明，例如模块地图、检索手法、风险清单：更新 `ProjectAgents/references/` 下对应文件
- 如果现有专题文件都不适合承载，再新增一个 `references/*.md`，并在 `ProjectAgents.md` 里补入口说明

不要把这类稳定信息只写进某个 app 的专属规则、memory、scratchpad 或线程内总结，否则其它 agent app 无法继承。

需要更细的回写原则和落点示例时，再读 [references/doc-maintenance.md](references/doc-maintenance.md)。
每次对这些文档做稳定性更新后，还要在 [CHANGELOG.md](CHANGELOG.md) 追加一条简短变更记录，写清时间、app、git 提交人和本次改动重点。

## 默认模式

默认轻量模式是起手方式，适用于大多数分析、检索、修改和 review 任务。

### 默认规则

1. 先读当前任务直接相关的源码、资源和调用点，再决定是否扩大范围。
2. 如果目标 module 根目录下存在 module 级 `AGENTS.md`、`CLAUDE.md` 或其它本地 agent 说明，在涉及该 module 代码时一并阅读，并把它当作局部补充说明；项目级 `ProjectAgents.md` 仍是总入口。把目标项目里已确认存在这类说明的模块补成 `[MODULE_WITH_LOCAL_AGENTS_EXAMPLES]`。
3. 默认不把 `build.gradle`、`build.gradle.kts`、根级 Gradle 文件、Manifest 当成起手必读项；只有问题明显涉及依赖、注册、打包、构建行为、sourceSet 或 flavor 时，再补看。
4. 检索优先使用 `rg --no-ignore` 和 `rg --files --no-ignore`。轻量模式只是减少默认读取的上下文，不缩小文件定位边界。
5. 对大文件、生成表、常量表、埋点表禁止默认全量读取。先用 `rg` 精确搜索目标常量、关键字、调用点，再按命中位置读取必要片段。
6. 如果模块存在 `src/main`、`src/[flavorA]`、`src/[flavorB]`、`src/debug`、`src/release` 等 sourceSet，要检查源码和资源是否存在平台或环境差异。
7. 不对历史特殊模块、缺失源码依赖、AAR 切换机制或代码生成产物做默认预设；只有检索结果明确指向它们时，再补充分析。
8. 使用 `git status`、`git diff`、`git log`、`git blame` 等能力时，先确认项目是单 git 还是多 git；如果是多 git，再确认目标文件属于哪个 git root 并切到对应目录执行，不要用错误 git root 的结果判断业务代码变更。
9. 每次执行 Android 项目的 Gradle 编译命令后，必须在对应项目根目录额外运行一次 `./gradlew --stop`，主动停止 Gradle daemon 和相关常驻 Java 进程，降低本机内存占用。
10. 如果任务涉及 Android 官方文档查询，或需要通过 `adb` 操作设备做截图、UI 布局分析等，优先使用团队既有 Android CLI / `adb` / 内部脚本；如果当前 agent 环境可用 Android CLI skill 或同类能力，就优先复用；如果环境没有，就不要假设它存在。
11. 模块编译验证只在确有必要时才做，不要把编译当成每次任务的默认步骤；编译过程中禁止持续读取或跟踪日志，只在编译结束后一次性获取结尾成功状态或失败原因。
12. 修改代码时优先贴合项目现有写法和依赖风格，不要无依据引入更重或更新的实现方式。
13. 写 Kotlin 或 Java 时优先复用项目已有扩展函数、工具类、基类和辅助方法；把高频可复用入口补成真实文件名，例如 `[EXTENSION_FILE_EXAMPLES]`、`[UTILITY_FILE_EXAMPLES]`。
14. 新增资源必须遵守模块前缀命名，格式优先为 `模块前缀_用途_状态`；把真实前缀样例补成 `[RESOURCE_PREFIX_EXAMPLES]`。
15. 新增页面或改造页面时，先搜索同域已有页面的继承链和基类用法；把目标项目常用的 Activity / Fragment / 列表基类补成 `[BASE_CLASS_EXAMPLES]`。

### 默认工作流

#### 1. 聚焦目标

先回答这几个问题：
- 要看的核心对象是什么：类、方法、页面、资源、路由，还是某个模块
- 它的定义在哪
- 谁直接调用它
- 改动会先落在哪个模块或 sourceSet

如果这些问题还没答清，不要急着扩大全工作区，也不要先跳去读构建文件。

#### 2. 逐层检索

直接做全工作区搜索来定位文件，不要只在当前目录或已打开模块里搜索；如果项目确认存在多个 git root，还要覆盖其它相关 root。搜索必须加 `--no-ignore`，完全不考虑 `.gitignore`；区别只是定位后优先读取目标文件和直接引用链，不默认展开重型构建上下文。

如果命中的是大文件、表文件、常量汇总文件，不要直接整段展开。优先先搜关键字，再按命中行号读取局部上下文。

默认检索范围：
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

默认排除：
- `**/build/**`
- `**/.git/**`
- `**/.gradle/**`
- `venv/**`
- 其它明显生成物或缓存目录

推荐顺序：
1. 定义位置
2. 直接引用
3. 相关资源或布局引用
4. 依赖模块或上游入口
5. 必要时再看更大范围的间接影响

需要检索模式、查询顺序和结果分层时，再读 [references/search-playbook.md](references/search-playbook.md)。

#### 3. 检查平台差异

当模块含有平台目录、flavor 目录或构建变体目录时，重点检查：
- `src/main`
- `src/[flavorA]`
- `src/[flavorB]`
- `src/debug`
- `src/release`
- 资源覆盖关系
- 同名类、布局、字符串、图片或颜色是否在不同 sourceSet 下行为不同

如果当前改动只落在公共逻辑，也要快速确认是否会被平台、品牌包、渠道包或 flavor 覆盖实现改写掉。

#### 4. 谨慎修改或评审

在真正动手前，至少确认：
- 是否会影响多个模块
- 是否存在平台、flavor 或 sourceSet 差异
- 是否改到了公共契约、路由、Binding、资源 id 或对外接口
- 是否需要最小回归验证

如果有明显未知项，要直接说明，不要假装已经覆盖。

## 进入重型模式的条件

只有当任务明确命中以下情况之一时，才进入重型模式：
- 需要系统理解整个聚合工作区，而不是只分析目标模块和直接调用链
- 明确涉及根级 Gradle、模块注册、依赖映射、打包或复杂构建链路
- 明确涉及平台专属 Manifest、平台专属 Gradle 脚本或更深的 flavor / sourceSet 差异
- 明确涉及源码 / AAR 切换、缺失源码依赖、代码生成产物或历史特殊模块规则
- 改动跨越多个关键模块、服务契约或共享基础层，默认风险偏高

进入重型模式后，不要继续按主文档里的轻量节奏推进，改为按 [references/heavy-mode.md](references/heavy-mode.md) 的完整规则处理。

## 模块认知

需要模块职责、分层、模块间通信或风险预期时，再读 [references/module-map.md](references/module-map.md)。以下区域通常要特别关注，落地时替换成真实模块名：
- `[APP_MAIN_MODULE]`：聚合度最高、装配最复杂或入口最多的核心模块
- `[COMMON_MODULE]`：共享业务逻辑和通用能力聚合层
- `[SERVICE_LAYER_PATTERN]`：最底层契约 / 服务层
- `[UI_COMPONENT_MODULE]`：通用 UI 组件和标准化组件库
- `[SPECIAL_MODULE_OR_DEPENDENCY]`：历史特殊模块、AAR 切换模块或高隐式耦合模块

## 默认输出结构

当用户要求分析某个类、模块、bug 或改动时，默认覆盖：
1. 目标对象和职责
2. 定义位置
3. 直接引用位置；如果已进入重型模式，再补全工作区引用位置
4. 相关模块或调用链
5. 平台 / flavor / sourceSet 差异点（如果有）
6. 改动风险点
7. 建议验证方式
8. 仍不确定的假设或未知项
