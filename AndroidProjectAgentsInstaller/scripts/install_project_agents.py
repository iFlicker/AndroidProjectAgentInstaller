#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SKILL_NAME = "AndroidProjectAgentsInstaller"
MANAGED_BEGIN = f"<!-- BEGIN {SKILL_NAME} -->"
MANAGED_END = f"<!-- END {SKILL_NAME} -->"
REVIEW_RELATIVE_PATH = Path("ProjectAgents/references/project-agents-onboarding-review.md")
SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".svn",
    ".hg",
    "build",
    "dist",
    "node_modules",
    "out",
    "tmp",
    "__pycache__",
    "ProjectAgents",
}
GENERIC_RESOURCE_FILE_NAMES = {
    "colors",
    "strings",
    "styles",
    "themes",
    "dimens",
    "attrs",
    "ids",
    "integers",
    "arrays",
    "bools",
    "plurals",
    "drawables",
}
ROUTER_PATTERNS = [
    (re.compile(r"\bARouter\b|@Route\b"), "ARouter"),
    (re.compile(r"\bServiceLoader\b"), "ServiceLoader"),
    (re.compile(r"\bRouter\b|\broute(path|r)?\b", re.IGNORECASE), "router / service discovery"),
    (re.compile(r"\bHilt\b|\bDagger\b"), "Hilt / Dagger"),
    (re.compile(r"\bKoin\b"), "Koin"),
]
EVENT_BUS_PATTERNS = [
    (re.compile(r"\bEventBus\b"), "EventBus"),
    (re.compile(r"\bLiveEventBus\b"), "LiveEventBus"),
    (re.compile(r"\bRxBus\b"), "RxBus"),
    (re.compile(r"\bFlowBus\b"), "FlowBus"),
]
PLACEHOLDER_ORDER = [
    "PROJECT_NAME",
    "PRIMARY_APP_NAME",
    "SECONDARY_APP_NAME_OR_FLAVOR",
    "APP_SHELL_MODULE",
    "APP_MAIN_MODULE",
    "COMMON_MODULE",
    "FEATURE_MODULE_EXAMPLE_A",
    "FEATURE_MODULE_EXAMPLE_B",
    "FEATURE_MODULE_EXAMPLE_C",
    "FEATURE_MODULE_EXAMPLES",
    "UI_COMPONENT_MODULE",
    "SERVICE_LAYER_PATTERN",
    "SPECIAL_MODULE_OR_DEPENDENCY",
    "MODULE_WITH_LOCAL_AGENTS_EXAMPLES",
    "RESOURCE_PREFIX_EXAMPLES",
    "ROOT_EXTRA_GRADLE_FILES",
    "MODULE_EXTRA_GRADLE_FILES",
    "EXTENSION_FILE_EXAMPLES",
    "UTILITY_FILE_EXAMPLES",
    "BASE_CLASS_EXAMPLES",
    "PLATFORM_SERVICE_MODULES",
    "CROSS_CUTTING_MODULES",
    "ROUTER_OR_SERVICE_DISCOVERY",
    "EVENT_BUS_OR_MESSAGE_BUS",
    "PLACEHOLDER",
]


@dataclass
class ModuleInfo:
    name: str
    path: Path
    build_file: Path | None
    module_type: str


@dataclass
class SuggestedValue:
    value: str
    confidence: str
    reason: str


@dataclass
class FileAction:
    path: Path
    action: str
    detail: str
    incoming_path: Path | None = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_text(content: str) -> str:
    return content.replace("\r\n", "\n").rstrip() + "\n"


def template_root() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "template"


def detect_project_name(project_root: Path) -> tuple[str, str]:
    for settings_name in ("settings.gradle.kts", "settings.gradle"):
        settings_path = project_root / settings_name
        if not settings_path.exists():
            continue
        text = read_text(settings_path)
        match = re.search(r'rootProject\.name\s*=\s*["\']([^"\']+)["\']', text)
        if match:
            return match.group(1).strip(), f"from `{settings_name}`"
    return project_root.name, "from target directory name"


def discover_modules(project_root: Path) -> list[ModuleInfo]:
    module_names: list[str] = []
    for settings_name in ("settings.gradle.kts", "settings.gradle"):
        settings_path = project_root / settings_name
        if not settings_path.exists():
            continue
        text = read_text(settings_path)
        for token in re.findall(r":[A-Za-z0-9_.-]+(?:[:][A-Za-z0-9_.-]+)*", text):
            if token not in module_names:
                module_names.append(token)

    if not module_names:
        for build_path in iter_project_files(project_root, allowed_suffixes={".gradle", ".kts"}):
            if build_path.name not in ("build.gradle", "build.gradle.kts"):
                continue
            rel_parent = build_path.parent.relative_to(project_root)
            if rel_parent == Path("."):
                continue
            module_name = ":" + str(rel_parent).replace(os.sep, ":")
            if module_name not in module_names:
                module_names.append(module_name)

    modules: list[ModuleInfo] = []
    for module_name in module_names:
        module_path = project_root / module_name.lstrip(":").replace(":", os.sep)
        build_file = None
        for candidate in ("build.gradle.kts", "build.gradle"):
            candidate_path = module_path / candidate
            if candidate_path.exists():
                build_file = candidate_path
                break
        module_type = detect_module_type(build_file)
        modules.append(
            ModuleInfo(
                name=module_name,
                path=module_path,
                build_file=build_file,
                module_type=module_type,
            )
        )
    return modules


def detect_module_type(build_file: Path | None) -> str:
    if build_file is None or not build_file.exists():
        return "unknown"
    text = read_text(build_file).lower()
    if "com.android.application" in text or "android.application" in text:
        return "application"
    if "com.android.dynamic-feature" in text or "android.dynamic.feature" in text:
        return "dynamic-feature"
    if "com.android.library" in text or "android.library" in text:
        return "library"
    if "java-library" in text:
        return "java-library"
    return "unknown"


def module_leaf(module_name: str) -> str:
    return module_name.split(":")[-1]


def score_module(module: ModuleInfo, keyword_scores: list[tuple[str, int]]) -> int:
    haystack = f"{module.name} {module_leaf(module.name)}".lower()
    score = 0
    for keyword, value in keyword_scores:
        if keyword in haystack:
            score += value
    return score


def choose_best_module(
    modules: list[ModuleInfo],
    keyword_scores: list[tuple[str, int]],
    preferred_types: set[str] | None = None,
    exclude: set[str] | None = None,
) -> ModuleInfo | None:
    exclude = exclude or set()
    candidates = [m for m in modules if m.name not in exclude]
    if preferred_types:
        preferred = [m for m in candidates if m.module_type in preferred_types]
        if preferred:
            candidates = preferred
    if not candidates:
        return None
    ranked = sorted(
        candidates,
        key=lambda module: (score_module(module, keyword_scores), -len(module.name)),
        reverse=True,
    )
    if score_module(ranked[0], keyword_scores) == 0:
        return None
    return ranked[0]


def format_module_name(module_name: str) -> str:
    return module_name


def format_module_list(modules: list[str]) -> str:
    return "、".join(format_module_name(module) for module in modules)


def detect_primary_and_secondary_apps(
    project_name: str,
    application_modules: list[ModuleInfo],
    flavor_names: list[str],
) -> tuple[SuggestedValue, SuggestedValue]:
    if application_modules:
        primary_module = application_modules[0]
        primary_value = f"{module_leaf(primary_module.name)}（{primary_module.name}）"
        primary_reason = "from the first application module"
    else:
        primary_value = project_name
        primary_reason = "fallback to project name because no application module was detected"

    if len(application_modules) > 1:
        secondary_value = f"{module_leaf(application_modules[1].name)}（{application_modules[1].name}）"
        secondary_reason = "from the second application module"
        secondary_confidence = "medium"
    elif flavor_names:
        secondary_value = " / ".join(flavor_names[:3]) + " flavor"
        secondary_reason = "from `productFlavors` in the primary application module"
        secondary_confidence = "medium"
    else:
        secondary_value = "TODO(确认是否存在次要 App、品牌包或 flavor；如无则删掉这句)"
        secondary_reason = "no second application module or flavor definition was detected"
        secondary_confidence = "low"

    return (
        SuggestedValue(primary_value, "medium", primary_reason),
        SuggestedValue(secondary_value, secondary_confidence, secondary_reason),
    )


def detect_flavors(build_file: Path | None) -> list[str]:
    if build_file is None or not build_file.exists():
        return []
    text = read_text(build_file)
    if "productFlavors" not in text:
        return []
    start = text.find("productFlavors")
    brace_start = text.find("{", start)
    if brace_start == -1:
        return []
    depth = 0
    end = brace_start
    while end < len(text):
        char = text[end]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    block = text[brace_start:end]
    names: list[str] = []
    for match in re.finditer(r'create\("([^"]+)"\)|create\(\'([^\']+)\'\)|^\s*([A-Za-z0-9_]+)\s*\{', block, re.MULTILINE):
        value = next(group for group in match.groups() if group)
        if value not in {"productFlavors", "create", "dimension"} and value not in names:
            names.append(value)
    return names[:5]


def iter_project_files(project_root: Path, allowed_suffixes: set[str] | None = None):
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIRS and not name.startswith(".DS_Store")
        ]
        base_path = Path(dirpath)
        for filename in filenames:
            path = base_path / filename
            if allowed_suffixes and path.suffix not in allowed_suffixes:
                continue
            yield path


def detect_local_agent_modules(project_root: Path, modules: list[ModuleInfo]) -> list[str]:
    module_paths = sorted(
        [(module.path.resolve(), module.name) for module in modules if module.path.exists()],
        key=lambda item: len(str(item[0])),
        reverse=True,
    )
    hits: list[str] = []
    for path in iter_project_files(project_root):
        if path.name not in {"AGENTS.md", "CLAUDE.md"}:
            continue
        if path.parent == project_root:
            continue
        if "ProjectAgents" in path.parts:
            continue
        resolved = path.parent.resolve()
        module_name = None
        for module_path, candidate_name in module_paths:
            if resolved == module_path or module_path in resolved.parents:
                module_name = candidate_name
                break
        module_name = module_name or ":" + str(path.parent.relative_to(project_root)).replace(os.sep, ":")
        if module_name not in hits:
            hits.append(module_name)
        if len(hits) >= 3:
            break
    return hits


def collect_named_file_examples(project_root: Path) -> tuple[list[str], list[str], list[str]]:
    extensions: list[str] = []
    utilities: list[str] = []
    base_classes: list[str] = []
    for path in iter_project_files(project_root, allowed_suffixes={".kt", ".java"}):
        name = path.name
        stem = path.stem
        if len(extensions) < 3 and re.search(r"(Ext|Extensions)\.(kt|java)$", name):
            if name not in extensions:
                extensions.append(name)
        if len(utilities) < 3 and re.search(r"(Util|Utils|Helper)\.(kt|java)$", name):
            if name not in utilities:
                utilities.append(name)
        if len(base_classes) < 3 and re.search(r"Base.*(Activity|Fragment|Dialog|Adapter)$", stem):
            if stem not in base_classes:
                base_classes.append(stem)
    return extensions, utilities, base_classes


def detect_resource_prefixes(project_root: Path) -> list[str]:
    prefixes: Counter[str] = Counter()
    for path in iter_project_files(project_root):
        if "res" not in path.parts:
            continue
        stem = path.stem
        if "_" not in stem:
            continue
        prefix = stem.split("_", 1)[0]
        if prefix in GENERIC_RESOURCE_FILE_NAMES or len(prefix) < 2:
            continue
        prefixes[prefix] += 1
    return [f"{prefix}_" for prefix, _ in prefixes.most_common(3)]


def detect_root_extra_gradle_files(project_root: Path) -> list[str]:
    extras: list[str] = []
    excluded = {
        "settings.gradle",
        "settings.gradle.kts",
        "build.gradle",
        "build.gradle.kts",
        "gradle.properties",
    }
    for path in sorted(project_root.iterdir()):
        if not path.is_file():
            continue
        if path.name in excluded:
            continue
        if path.suffix in {".gradle", ".kts", ".toml"} or path.name.endswith(".gradle.kts"):
            extras.append(path.name)
    return extras


def detect_module_extra_gradle_files(candidates: list[ModuleInfo]) -> list[str]:
    extras: list[str] = []
    for module in candidates:
        if not module.path.exists():
            continue
        for path in sorted(module.path.iterdir()):
            if not path.is_file():
                continue
            if path.name in {"build.gradle", "build.gradle.kts", "gradle.properties"}:
                continue
            if path.suffix in {".gradle", ".kts"} or path.name.endswith(".gradle.kts"):
                if path.name not in extras:
                    extras.append(path.name)
    return extras[:5]


def search_project_patterns(project_root: Path, patterns: list[tuple[re.Pattern[str], str]]) -> str | None:
    allowed_suffixes = {".gradle", ".kts", ".properties", ".kt", ".java", ".xml", ".toml"}
    for path in iter_project_files(project_root, allowed_suffixes=allowed_suffixes):
        try:
            if path.stat().st_size > 1_000_000:
                continue
        except OSError:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, label in patterns:
            if pattern.search(text):
                return label
    return None


def build_placeholder_suggestions(project_root: Path) -> dict[str, SuggestedValue]:
    project_name, project_name_reason = detect_project_name(project_root)
    modules = discover_modules(project_root)
    application_modules = [module for module in modules if module.module_type == "application"]
    shell_keywords = [("shell", 12), ("launcher", 10), ("host", 8), ("app", 8), ("main", 4)]
    common_keywords = [("common", 12), ("core", 10), ("shared", 8), ("base", 8), ("foundation", 7)]
    ui_keywords = [("ui", 12), ("widget", 10), ("design", 9), ("component", 9), ("view", 7)]
    service_keywords = [("service", 12), ("router", 10), ("api", 9), ("provider", 9), ("contract", 8), ("facade", 8), ("bridge", 6)]
    feature_keywords = [("feature", 12), ("business", 7), ("biz", 7), ("home", 6), ("module", 4)]
    platform_service_keywords = [("platform", 10), ("service", 9), ("data", 8), ("network", 8), ("infra", 8), ("api", 7)]
    cross_cutting_keywords = [("map", 9), ("chat", 9), ("im", 8), ("media", 8), ("pay", 8), ("payment", 8), ("web", 6), ("rn", 6)]
    special_keywords = [("aar", 12), ("loader", 11), ("legacy", 8), ("sdk", 7), ("shell", 5), ("host", 5), ("plugin", 5)]

    app_shell_module = choose_best_module(application_modules or modules, shell_keywords)
    app_main_module = choose_best_module(
        modules,
        [("main", 12), ("home", 8), ("app", 5), ("core", 4)],
        exclude={app_shell_module.name} if app_shell_module else None,
    ) or app_shell_module
    common_module = choose_best_module(modules, common_keywords, preferred_types={"library", "java-library"})
    ui_module = choose_best_module(modules, ui_keywords)
    service_module = choose_best_module(modules, service_keywords)
    special_module = choose_best_module(modules, special_keywords)

    feature_modules = [
        module.name
        for module in sorted(modules, key=lambda item: score_module(item, feature_keywords), reverse=True)
        if score_module(module, feature_keywords) > 0
        and module.name not in {
            *(name for name in [app_shell_module.name if app_shell_module else None, app_main_module.name if app_main_module else None, common_module.name if common_module else None, ui_module.name if ui_module else None, service_module.name if service_module else None] if name),
        }
    ][:3]
    if len(feature_modules) < 3:
        for module in modules:
            if module.name in feature_modules:
                continue
            if module.name in {
                *(
                    name
                    for name in [
                        app_shell_module.name if app_shell_module else None,
                        app_main_module.name if app_main_module else None,
                        common_module.name if common_module else None,
                        ui_module.name if ui_module else None,
                        service_module.name if service_module else None,
                    ]
                    if name
                ),
            }:
                continue
            feature_modules.append(module.name)
            if len(feature_modules) >= 3:
                break

    platform_service_modules = [
        module.name
        for module in sorted(modules, key=lambda item: score_module(item, platform_service_keywords), reverse=True)
        if score_module(module, platform_service_keywords) > 0
    ][:3]
    cross_cutting_modules = [
        module.name
        for module in sorted(modules, key=lambda item: score_module(item, cross_cutting_keywords), reverse=True)
        if score_module(module, cross_cutting_keywords) > 0
    ][:3]

    flavor_names = detect_flavors(app_shell_module.build_file if app_shell_module else None)
    primary_app, secondary_app = detect_primary_and_secondary_apps(project_name, application_modules, flavor_names)
    local_agent_modules = detect_local_agent_modules(project_root, modules)
    extension_files, utility_files, base_classes = collect_named_file_examples(project_root)
    resource_prefixes = detect_resource_prefixes(project_root)
    root_extra_gradle_files = detect_root_extra_gradle_files(project_root)
    module_extra_gradle_files = detect_module_extra_gradle_files(
        [module for module in [app_shell_module, app_main_module, common_module] if module]
    )
    router_pattern = search_project_patterns(project_root, ROUTER_PATTERNS)
    event_bus_pattern = search_project_patterns(project_root, EVENT_BUS_PATTERNS)

    suggestions: dict[str, SuggestedValue] = {
        "PROJECT_NAME": SuggestedValue(project_name, "high", project_name_reason),
        "PRIMARY_APP_NAME": primary_app,
        "SECONDARY_APP_NAME_OR_FLAVOR": secondary_app,
        "APP_SHELL_MODULE": module_suggestion(app_shell_module, "the best application/shell match", low_todo="TODO(确认 APK / App Bundle 壳工程模块)"),
        "APP_MAIN_MODULE": module_suggestion(app_main_module, "the best core/main match", low_todo="TODO(确认主应用逻辑聚合模块)"),
        "COMMON_MODULE": module_suggestion(common_module, "the best common/core/shared match", low_todo="TODO(确认共享业务 / 通用能力模块)"),
        "FEATURE_MODULE_EXAMPLE_A": indexed_module_suggestion(feature_modules, 0, "feature-like module candidates"),
        "FEATURE_MODULE_EXAMPLE_B": indexed_module_suggestion(feature_modules, 1, "feature-like module candidates"),
        "FEATURE_MODULE_EXAMPLE_C": indexed_module_suggestion(feature_modules, 2, "feature-like module candidates"),
        "FEATURE_MODULE_EXAMPLES": list_suggestion(feature_modules, "feature-like module candidates", "TODO(补充 2 到 3 个业务模块示例)"),
        "UI_COMPONENT_MODULE": module_suggestion(ui_module, "the best UI/component match", low_todo="TODO(确认通用 UI 组件模块)"),
        "SERVICE_LAYER_PATTERN": module_or_phrase_suggestion(
            service_module,
            "service / router / provider / facade 契约层",
            "the best service-layer match",
        ),
        "SPECIAL_MODULE_OR_DEPENDENCY": module_suggestion(
            special_module,
            "module name suggests AAR/loader/legacy behavior",
            low_todo="TODO(确认历史特殊模块、AAR 切换模块或高隐式耦合依赖)",
        ),
        "MODULE_WITH_LOCAL_AGENTS_EXAMPLES": list_suggestion(
            local_agent_modules,
            "detected module-local `AGENTS.md` / `CLAUDE.md` files",
            "TODO(补充已确认存在 module 级 agent 文档的模块名)",
        ),
        "RESOURCE_PREFIX_EXAMPLES": file_list_suggestion(
            resource_prefixes,
            "from the most common resource filename prefixes",
            "TODO(确认资源前缀，例如 `app_`、`common_`)",
            transform=lambda item: item,
        ),
        "ROOT_EXTRA_GRADLE_FILES": file_list_suggestion(
            root_extra_gradle_files,
            "from extra root-level Gradle/config files",
            "TODO(确认根级额外 Gradle 文件；如无则删掉示例)",
        ),
        "MODULE_EXTRA_GRADLE_FILES": file_list_suggestion(
            module_extra_gradle_files,
            "from extra Gradle files under key modules",
            "TODO(确认目标模块额外 Gradle 脚本；如无则删掉示例)",
        ),
        "EXTENSION_FILE_EXAMPLES": file_list_suggestion(
            extension_files,
            "from `*Ext*` / `*Extensions*` source files",
            "TODO(补充项目里常用扩展函数文件名)",
        ),
        "UTILITY_FILE_EXAMPLES": file_list_suggestion(
            utility_files,
            "from `*Util*` / `*Helper*` source files",
            "TODO(补充项目里常用工具类文件名)",
        ),
        "BASE_CLASS_EXAMPLES": file_list_suggestion(
            base_classes,
            "from `Base*Activity` / `Base*Fragment` style classes",
            "TODO(补充常用 Activity / Fragment 基类)",
        ),
        "PLATFORM_SERVICE_MODULES": list_suggestion(
            platform_service_modules,
            "from platform/service/data/network-like module names",
            "TODO(补充平台服务或基础设施模块)",
        ),
        "CROSS_CUTTING_MODULES": list_suggestion(
            cross_cutting_modules,
            "from map/chat/payment/media/web-like module names",
            "TODO(补充横向能力模块，例如地图、IM、支付、媒体)",
        ),
        "ROUTER_OR_SERVICE_DISCOVERY": SuggestedValue(
            router_pattern or "TODO(确认路由或服务发现机制，例如 ARouter、ServiceLoader、Hilt EntryPoint)",
            "medium" if router_pattern else "low",
            "from source/build file keyword matches" if router_pattern else "no router/service-discovery pattern was detected",
        ),
        "EVENT_BUS_OR_MESSAGE_BUS": SuggestedValue(
            event_bus_pattern or "TODO(确认事件总线或消息总线机制，例如 EventBus、RxBus、FlowBus)",
            "medium" if event_bus_pattern else "low",
            "from source/build file keyword matches" if event_bus_pattern else "no event-bus pattern was detected",
        ),
        "PLACEHOLDER": SuggestedValue("TODO(仍需人工确认的项目位)", "low", "generic fallback for any remaining placeholders"),
    }
    return suggestions


def module_suggestion(module: ModuleInfo | None, reason: str, low_todo: str) -> SuggestedValue:
    if not module:
        return SuggestedValue(low_todo, "low", "no confident module match was detected")
    return SuggestedValue(format_module_name(module.name), "medium", reason)


def module_or_phrase_suggestion(module: ModuleInfo | None, phrase: str, reason: str) -> SuggestedValue:
    if not module:
        return SuggestedValue(f"TODO(确认{phrase})", "low", "no confident service-layer module was detected")
    return SuggestedValue(f"{format_module_name(module.name)} 一类 {phrase}", "medium", reason)


def indexed_module_suggestion(modules: list[str], index: int, reason: str) -> SuggestedValue:
    if index < len(modules):
        return SuggestedValue(format_module_name(modules[index]), "medium", reason)
    return SuggestedValue("TODO(补充业务模块示例)", "low", "fewer than the requested number of feature module candidates were detected")


def list_suggestion(values: list[str], reason: str, low_todo: str) -> SuggestedValue:
    if not values:
        return SuggestedValue(low_todo, "low", "no confident candidates were detected")
    return SuggestedValue(format_module_list(values), "medium", reason)


def file_list_suggestion(
    values: list[str],
    reason: str,
    low_todo: str,
    transform=lambda item: item,
) -> SuggestedValue:
    if not values:
        return SuggestedValue(low_todo, "low", "no confident candidates were detected")
    return SuggestedValue("、".join(transform(value) for value in values), "medium", reason)


def replace_placeholders(content: str, suggestions: dict[str, SuggestedValue]) -> str:
    rendered = content
    for name, suggestion in suggestions.items():
        rendered = rendered.replace(f"[{name}]", suggestion.value)
    return rendered


def contains_known_placeholders(content: str, suggestions: dict[str, SuggestedValue]) -> bool:
    return any(f"[{name}]" in content for name in suggestions)


def incoming_path_for(target_path: Path) -> Path:
    if target_path.suffix:
        return target_path.with_name(f"{target_path.stem}.incoming{target_path.suffix}")
    return target_path.with_name(f"{target_path.name}.incoming")


def install_entry_file(
    project_root: Path,
    relative_path: Path,
    rendered_text: str,
    block_text: str,
) -> FileAction:
    target_path = project_root / relative_path
    if not target_path.exists():
        write_text(target_path, normalize_text(rendered_text))
        return FileAction(relative_path, "created", "created the entry file from the template")

    existing = read_text(target_path)
    if "ProjectAgents/ProjectAgents.md" in existing:
        return FileAction(relative_path, "unchanged", "the entry file already points at `ProjectAgents/ProjectAgents.md`")

    managed_block = f"{MANAGED_BEGIN}\n{block_text}\n{MANAGED_END}"
    if MANAGED_BEGIN in existing and MANAGED_END in existing:
        updated = re.sub(
            re.escape(MANAGED_BEGIN) + r".*?" + re.escape(MANAGED_END),
            managed_block,
            existing,
            flags=re.DOTALL,
        )
    else:
        updated = existing.rstrip() + "\n\n" + managed_block + "\n"
    write_text(target_path, normalize_text(updated))
    return FileAction(relative_path, "updated", "appended an idempotent pointer block without overwriting existing instructions")


def install_generic_file(
    project_root: Path,
    relative_path: Path,
    rendered_text: str,
    suggestions: dict[str, SuggestedValue],
) -> FileAction:
    target_path = project_root / relative_path
    if not target_path.exists():
        write_text(target_path, normalize_text(rendered_text))
        return FileAction(relative_path, "created", "created the file from the rendered template")

    if relative_path == Path("ProjectAgents/CHANGELOG.md"):
        return FileAction(relative_path, "unchanged", "preserved the existing changelog and will append a new entry if files change")

    existing = read_text(target_path)
    if normalize_text(existing) == normalize_text(rendered_text):
        return FileAction(relative_path, "unchanged", "already matches the rendered template")

    if contains_known_placeholders(existing, suggestions):
        updated = replace_placeholders(existing, suggestions)
        if normalize_text(updated) != normalize_text(existing):
            write_text(target_path, normalize_text(updated))
            return FileAction(relative_path, "updated", "filled placeholders in the existing file while preserving custom content")
        return FileAction(relative_path, "unchanged", "existing file only needed placeholder checks and required no changes")

    incoming_path = incoming_path_for(target_path)
    if incoming_path.exists():
        existing_incoming = read_text(incoming_path)
        if normalize_text(existing_incoming) == normalize_text(rendered_text):
            return FileAction(
                relative_path,
                "unchanged",
                "preserved the existing file; a matching `.incoming` merge candidate already exists",
                incoming_path=incoming_path.relative_to(project_root),
            )
    write_text(incoming_path, normalize_text(rendered_text))
    return FileAction(
        relative_path,
        "incoming",
        "preserved the existing file and wrote a rendered `.incoming` copy for manual merge",
        incoming_path=incoming_path.relative_to(project_root),
    )


def render_template_tree(
    project_root: Path,
    suggestions: dict[str, SuggestedValue],
) -> list[FileAction]:
    actions: list[FileAction] = []
    root = template_root()
    file_paths = sorted(path for path in root.rglob("*") if path.is_file())
    for source_path in file_paths:
        relative_path = source_path.relative_to(root)
        rendered_text = replace_placeholders(read_text(source_path), suggestions)
        if relative_path == Path("AGENTS.md"):
            actions.append(
                install_entry_file(
                    project_root,
                    relative_path,
                    rendered_text,
                    "请阅读 [ProjectAgents/ProjectAgents.md](ProjectAgents/ProjectAgents.md)。",
                )
            )
        elif relative_path == Path("CLAUDE.md"):
            actions.append(
                install_entry_file(
                    project_root,
                    relative_path,
                    rendered_text,
                    "@ProjectAgents/ProjectAgents.md",
                )
            )
        else:
            actions.append(install_generic_file(project_root, relative_path, rendered_text, suggestions))
    return actions


def git_user_name(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    value = result.stdout.strip()
    return value or "unknown"


def append_changelog_entry(project_root: Path, actions: list[FileAction]) -> None:
    changelog_path = project_root / "ProjectAgents/CHANGELOG.md"
    if not changelog_path.exists():
        return
    changed_paths = [
        f"`{action.path.as_posix()}`"
        for action in actions
        if action.action in {"created", "updated", "incoming"}
    ]
    if not changed_paths:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_user = git_user_name(project_root)
    entry_lines = [
        "",
        f"## {timestamp} | Codex | git: {git_user}",
        "",
        "- Files: " + ", ".join(changed_paths + [f"`{REVIEW_RELATIVE_PATH.as_posix()}`"]),
        "- Summary: Installed or updated ProjectAgents seed files via `$AndroidProjectAgentsInstaller`.",
        "- Summary: Generated onboarding review notes and placeholder suggestions for the target Android project.",
        "",
    ]
    with changelog_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry_lines))


def write_review_file(
    project_root: Path,
    suggestions: dict[str, SuggestedValue],
    actions: list[FileAction],
) -> None:
    created = [action for action in actions if action.action == "created"]
    updated = [action for action in actions if action.action == "updated"]
    incoming = [action for action in actions if action.action == "incoming"]
    unresolved = [
        (name, suggestion)
        for name, suggestion in suggestions.items()
        if "TODO(" in suggestion.value
    ]

    lines = [
        "# ProjectAgents Onboarding Review",
        "",
        f"- Generated at: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- Skill: `$AndroidProjectAgentsInstaller`",
        f"- Target root: `{project_root}`",
        "",
        "## Outcome",
        "",
    ]

    if created:
        lines.append("- Created: " + ", ".join(f"`{action.path.as_posix()}`" for action in created))
    if updated:
        lines.append("- Updated: " + ", ".join(f"`{action.path.as_posix()}`" for action in updated))
    if incoming:
        lines.append(
            "- Preserved existing files and staged `.incoming` copies: "
            + ", ".join(f"`{action.incoming_path.as_posix()}`" for action in incoming if action.incoming_path)
        )
    if not any((created, updated, incoming)):
        lines.append("- No template files changed; the project already matched the rendered install output.")

    lines.extend(
        [
            "",
            "## Placeholder Review",
            "",
        ]
    )
    for name in PLACEHOLDER_ORDER:
        suggestion = suggestions.get(name)
        if not suggestion:
            continue
        lines.append(
            f"- `{name}`: {suggestion.value} (`{suggestion.confidence}`; {suggestion.reason})"
        )

    lines.extend(
        [
            "",
            "## Compatibility Notes",
            "",
            "- Existing `AGENTS.md` / `CLAUDE.md` files are never replaced wholesale; the installer only appends a managed pointer block when needed.",
            "- Existing `ProjectAgents/*.md` files that still contain template placeholders are updated in place with best-effort substitutions.",
            "- Existing `ProjectAgents/*.md` files with custom content are preserved; rendered template copies are written as `.incoming.md` files for manual merge.",
            "",
            "## Follow-up",
            "",
            "- Fold confirmed stable facts from this review back into `ProjectAgents/ProjectAgents.md` and the relevant `ProjectAgents/references/*.md` files.",
            "- Resolve every `TODO(` item before treating the onboarding as complete.",
            "- Review every `.incoming.md` file and either merge it or delete it after the merge decision is made.",
        ]
    )

    if unresolved:
        lines.extend(
            [
                "",
                "## Open Review Items",
                "",
            ]
        )
        for name, suggestion in unresolved:
            lines.append(f"- `{name}`: {suggestion.value}")

    write_text(project_root / REVIEW_RELATIVE_PATH, normalize_text("\n".join(lines)))


def ensure_android_project_hint(project_root: Path) -> str | None:
    if (project_root / "settings.gradle").exists() or (project_root / "settings.gradle.kts").exists():
        return None
    build_files = list(iter_project_files(project_root, allowed_suffixes={".gradle", ".kts"}))
    if build_files:
        return None
    return "Warning: no Gradle settings/build files were detected. The installer can still copy the template, but every project-specific suggestion will be low confidence."


def copy_template_for_debug(project_root: Path, destination: Path) -> None:
    source = template_root()
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the ProjectAgents Android guidance template into a target project."
    )
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Target Android project root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--dump-template",
        help="Optional debug path. When set, copy the raw template tree to this path and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        raise SystemExit(f"Target project root does not exist: {project_root}")

    if args.dump_template:
        copy_template_for_debug(project_root, Path(args.dump_template).resolve())
        print(f"Copied template assets to {Path(args.dump_template).resolve()}")
        return 0

    warning = ensure_android_project_hint(project_root)
    suggestions = build_placeholder_suggestions(project_root)
    actions = render_template_tree(project_root, suggestions)
    write_review_file(project_root, suggestions, actions)
    append_changelog_entry(project_root, actions)

    if warning:
        print(warning)
    print(f"Installed ProjectAgents guidance into {project_root}")
    print(f"Review notes: {project_root / REVIEW_RELATIVE_PATH}")
    print(
        "Close or disable the `AndroidProjectAgentsInstaller` skill after installation; "
        "otherwise semantic auto-invocation may trigger it again in later tasks."
    )
    incoming_actions = [action for action in actions if action.action == "incoming"]
    if incoming_actions:
        print("Manual merge required for:")
        for action in incoming_actions:
            print(f"  - {action.incoming_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
