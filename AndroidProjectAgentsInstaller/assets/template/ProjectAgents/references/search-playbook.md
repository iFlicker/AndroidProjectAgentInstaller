# 检索手册

先确认项目是单一 git root 还是多个独立 git root。确认后仍按全工作区检索；如果项目确实包含多个 git root，不要把搜索限制在当前 root。所有 `rg` / `rg --files` 搜索都必须加 `--no-ignore`，完全不考虑 `.gitignore`。

对大文件、生成表、常量汇总文件、埋点表，不要默认全量读取。先 `rg --no-ignore -n` 搜目标常量、关键字、调用点，再按命中行号读取局部上下文。

## 默认范围

检索范围覆盖：
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
- 打包产物、生成物和缓存目录

## 推荐命令

列出候选文件：

```bash
rg --files --no-ignore . \
  -g '**/*.kt' -g '**/*.java' -g '**/*.xml' -g '**/*.gradle' -g '**/*.gradle.kts' -g '**/gradle.properties' \
  -g '**/*.toml' -g '**/*.pro' -g '**/*.aidl' -g '**/*.proto' -g '**/CMakeLists.txt' -g '**/Android.mk' \
  -g '!**/build/**' -g '!**/.git/**' -g '!**/.gradle/**' -g '!venv/**'
```

检索内容：

```bash
rg --no-ignore -n "PATTERN" . \
  -g '**/*.kt' -g '**/*.java' -g '**/*.xml' -g '**/*.gradle' -g '**/*.gradle.kts' -g '**/gradle.properties' \
  -g '**/*.toml' -g '**/*.pro' -g '**/*.aidl' -g '**/*.proto' -g '**/CMakeLists.txt' -g '**/Android.mk' \
  -g '!**/build/**' -g '!**/.git/**' -g '!**/.gradle/**' -g '!venv/**'
```

命中大文件后读取局部片段：

```bash
sed -n 'START,ENDp' PATH
```

不要对大文件直接做整段展开，例如：
- `sed -n '1,400p' PATH`
- `cat PATH`
- 一次性读取整个埋点表、常量表、生成代码文件

## 查询清单

### 类

按这个顺序搜索：
1. 简单类名
2. 全限定名
3. `import`
4. 继承与实现关系
5. 构造调用和工厂调用
6. 反射或字符串引用

### 方法与字段

不要只查直接代码调用，还要检查：
- XML attributes
- Binding usage
- `R.id` and `R.layout`
- `include` and `merge`
- `ConstraintSet`
- 路由声明和字符串路由
- Manifest 声明
- Gradle 常量和 build config 引用
- 如果字段来自大表文件，先查字段名和调用点，再回读字段定义附近上下文

### 资源

必须跨 Java、Kotlin、XML 一起检索，不要假设资源只会在所属模块内使用。

同名资源必须额外检查 sourceSet 覆盖关系。`color`、`drawable`、`string`、`layout` 等资源可能同时定义在 `src/main`、`src/[flavorA]`、`src/[flavorB]`、`src/debug`、`src/release` 中，名字一样但具体值、样式或引用目标不同。分析资源行为时要同时给出：
- 资源名对应的全部定义位置
- 当前运行变体实际命中的定义
- 其它关键变体是否命中不同定义
- 修改后是否会改变覆盖关系

## 结果分类

输出结果时，尽量分成四类：
- 定义位置
- 直接引用
- 间接影响
- 平台差异点

## 文档回写提醒

如果在检索过程中发现的是稳定的新结构、新规则或高频误区，不要只在当前回答里口头说明。应把结论回写到：
- `ProjectAgents/ProjectAgents.md`：适合全局规则
- `ProjectAgents/references/*.md`：适合专题化补充
