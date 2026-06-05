# ProjectAgents

`ProjectAgents.md` 是项目统一维护的项目级 Agents，用于指导多个 AI agent app 在同一 Android 项目内进行分析、检索、修改和评审。

## Tool Support

- Codex：根目录 `AGENTS.md` 指向 `ProjectAgents/ProjectAgents.md`
- Cursor：默认支持根目录 `AGENTS.md`
- Claude Code：根目录 `CLAUDE.md` 通过 `@ProjectAgents/ProjectAgents.md` 引入
- Antigravity：`.agents/rules/project-agents.md` 通过 `@/ProjectAgents/ProjectAgents.md` 导入

## 推荐做法

- 把稳定项目知识优先沉淀到 `ProjectAgents/ProjectAgents.md` 或 `ProjectAgents/references/`
- 不要把长期有效的信息只留在某个 app 的私有 memory、rule 或一次性会话上下文里
- 让根目录入口文件尽量保持薄，只负责把不同 agent app 导向同一份主文档
