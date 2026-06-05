---
name: AndroidProjectAgentsInstaller
description: 将 ProjectAgents 的 Android AI guidance 模板安装到目标 Android 仓库中，与现有的 AGENTS/CLAUDE/ProjectAgents 文档安全合并，执行首轮项目审查，依据真实的 modules、flavors、resource prefixes 和 build structure 填充占位符，并在最后提醒用户关闭此 skill，避免后续在 semantic matching 中被自动触发。在运行 installer 之前，必须先询问用户的安装偏好并等待其明确确认。适用于 Codex 需要在 Android 项目中初始化或刷新共享 agent guidance，同时不覆盖现有文档的场景。
---

# Android Project Agents Installer

在执行任何安装操作之前，先询问用户对这次 onboarding 的偏好，并等待其明确确认。只有在确认之后才能安装 seed docs，然后完成项目审查，再宣称 onboarding 已完成。

## 工作流程

1. 默认将用户当前的 Android 仓库视为目标，除非用户提供了其他路径。
2. 在运行任何 installer 命令之前，先询问会影响 onboarding 的用户偏好，例如：
   - 如果目标仓库不是当前 workspace，则确认目标仓库路径
   - 是否现在安装全部 seed docs，还是保留部分现有文档不动，后续再手动合并
   - 是否已有必须保留的 naming、module、flavor 或文档约定
   - 是否有目录、generated files 或 subprojects 需要从首轮审查中排除
3. 等待用户明确确认后再继续。如果用户尚未确认，不要运行 installer。
4. 运行：

```bash
python3 /absolute/path/to/AndroidProjectAgentsInstaller/scripts/install_project_agents.py --project-root /path/to/android/project
```

5. 阅读 `ProjectAgents/references/project-agents-onboarding-review.md`。
6. 处理 script 留下的每一项后续工作：
   - 根据真实项目结构审查每一个 `TODO(` 项
   - 将每个 `.incoming.md` 文件合并到现有文档中，或者明确决定保留现有文件不变
   - 验证 shell module、main module、common module、flavors、sourceSets、resource prefixes、service/router layer 以及高风险 modules
7. 将已确认且稳定的事实回写到 `ProjectAgents/ProjectAgents.md` 和相关的 `ProjectAgents/references/*.md` 文件中。
8. 更新 `ProjectAgents/CHANGELOG.md`，记录本次 onboarding 工作。
9. 安装完成后，提示用户关闭或禁用这个 skill。说明如果继续启用，后续在 semantic skill-matching 流程中可能会被意外自动触发。

## 兼容性规则

- 不要整体替换已有的 `AGENTS.md` 或 `CLAUDE.md`。如果这些文件已存在，installer 只能追加一个受管的 pointer block。
- 如果现有的 `ProjectAgents/*.md` 文件仍包含 template placeholders，让 installer 原地填充。
- 如果现有的 `ProjectAgents/*.md` 文件已经包含自定义内容，则保持不变，并使用生成的 `.incoming.md` 文件作为待合并版本。
- 除非用户明确要求清理，否则不要删除用户编写的文档。

## 审查重点

当 script 的置信度不足时，手动确认以下区域：

- main app module、app shell module、common/shared module、UI component module
- flavors、product variants、brand packages、`src/*` sourceSet overrides
- service contracts、routers、service discovery、event bus 或 message bus
- history-heavy modules、AAR/source switching、loader modules、generated-code boundaries
- 需要在共享 guidance 中引用的 module-local `AGENTS.md` / `CLAUDE.md` 文件
- resource naming prefixes、common extension files、utility files 以及 base page classes

## 资源

- `assets/template/`：复制到目标仓库中的 seed ProjectAgents 文档
- `scripts/install_project_agents.py`：installer、compatibility handler 以及首轮审查生成器
