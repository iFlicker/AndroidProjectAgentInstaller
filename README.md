# Android Project Agents Installer

这个仓库现在承载的是一个可分发的 skill：[`AndroidProjectAgentsInstaller`](/Users/lizhiyang/58/ProjectAgents/AndroidProjectAgentsInstaller/SKILL.md)。

它的目标不是单纯复制模板，而是让 agent 在目标 Android 项目里完成两件事：

1. 安装 `AGENTS.md`、`CLAUDE.md`、`.agents/rules/project-agents.md` 和 `ProjectAgents/` 文档。
2. 对目标项目做一轮首轮 review，尽量自动回填模块、flavor、资源前缀、服务层等稳定信息，并把剩余待确认项留在 review 文档里。

## Skill 目录

- `AndroidProjectAgentsInstaller/SKILL.md`：skill 触发说明和执行流程
- `AndroidProjectAgentsInstaller/scripts/install_project_agents.py`：安装 + 兼容处理 + 首轮 review 脚本
- `AndroidProjectAgentsInstaller/assets/template/`：原始 ProjectAgents 模板资产

## 兼容策略

- 现有 `AGENTS.md` / `CLAUDE.md` 不整体覆盖，只追加受控引导块。
- 现有 `ProjectAgents/*.md` 如果仍有模板占位符，会原地回填。
- 现有 `ProjectAgents/*.md` 如果已经有自定义内容，会保留原文件，并生成 `.incoming.md` 供后续合并。
- 每次安装都会生成 `ProjectAgents/references/project-agents-onboarding-review.md`，把自动识别结果和未完成 review 项列出来。
- 安装完成后应提示用户关闭这个 skill，否则在后续依赖语义识别的自动调用场景里可能继续被误触发。
