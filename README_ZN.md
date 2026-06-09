# Codex Project Manager

<p>
  <a href="README.md"><strong>English</strong></a>
  ·
  <a href="README_ZN.md"><strong>中文</strong></a>
</p>

Codex Project Manager 是一个仓库本地的 Codex 插件，用来在阶段边界保存项目上下文。
它帮助仓库维护三类长期信息：

- 项目规则：`AGENTS.md`
- 项目知识：`memories/<module>/<topic>.md`
- 项目本地可复用工作流：`.agents/skills/`

插件默认保持保守：它可以提出个人或全局 memory 候选，但不会自动写入。个人 memory 只有在用户明确批准后才保存。

## 仓库内容

```text
codex-plugin-dev/
  .agents/plugins/marketplace.json
  plugins/codex-project-manager/
    .codex-plugin/plugin.json
    skills/
      codex-project-manager-init/SKILL.md
      project-memory-locations/SKILL.md
      project-review/SKILL.md
      project-skill-review/SKILL.md
    scripts/project_manager/
      apply.py
      classify.py
      init.py
      memory_paths.py
      models.py
      review.py
    templates/hooks.json
memories/
  <module>/
    <topic>.md
tests/codex_project_manager/
```

唯一固定的 memory 路径约定是 `memories/<module>/<topic>.md`。`module` 应来自真实项目组件，只有组件边界明确后才创建对应结构。

## 当前仓库设置

本仓库已经完成 Codex Project Manager 初始化：

- `AGENTS.md` 保存仓库工作规则。
- `memories/` 是组件级长期项目记忆的根目录。
- `.agents/skills/` 用于未来的项目本地 skill。
- `.codex/hooks.json` 安装了可选的 Project Manager 提醒 hook。

## 依赖

- 支持 plugin marketplace 的 Codex CLI
- Python 3.9 或更高版本
- `pytest`，用于运行测试

插件脚本没有额外运行时 Python 依赖，只使用标准库。

## 安装插件

从仓库根目录运行：

1. 添加仓库本地 marketplace：

```bash
codex plugin marketplace add ./codex-plugin-dev
```

预期输出包含：

```text
Added marketplace `repo-local`
```

2. 验证 marketplace 已注册：

```bash
rg -n "repo-local|codex-plugin-dev" ~/.codex/config.toml
```

预期输出应包含 `marketplaces.repo-local`，并指向本仓库的 `codex-plugin-dev` 目录。

3. 打开 Codex，在 `Repo Local` marketplace 中安装或启用 `Project Manager` 插件。

当前 CLI 提供 marketplace 管理，但没有单独的 `codex plugin install` 命令。添加 marketplace 后，通过 Codex 插件界面安装。

## 验证安装文件

验证插件元数据：

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool .codex/hooks.json >/dev/null
```

所有命令都应以状态码 `0` 退出。

运行测试：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/codex_project_manager -q
```

预期结果：

```text
23 passed
```

## 核心工作流

### 1. 初始化仓库

安装并启用插件后使用。

在 Codex 输入框中输入 `/`，搜索并触发 `codex-project-manager-init`。这是 slash 列表中的 skill 入口。

初始化流程会询问：

- 要写入 `AGENTS.md` 的项目规则
- 可选的 `memories/<module>/` 模块名
- 是否安装可选的 `.codex/hooks.json` 提醒 hook

默认行为：

- 仅在 `AGENTS.md` 不存在时创建它。
- 如果 `AGENTS.md` 已存在，只追加受限的 `## Codex Project Manager Rules` section。
- 只为用户确认的 module 创建 `memories/<module>/` 目录。
- 不预创建 topic 文件；长期笔记之后写入 `memories/<module>/<topic>.md`。
- 如果 `.agents/skills/` 不存在，则创建它。
- 只有用户确认后才安装 `.codex/hooks.json`，且不会覆盖已有文件。

本地 smoke test：

```bash
tmpdir="$(mktemp -d)"
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --root "$tmpdir" \
  --rules "Run focused tests before closing plugin edits" \
  --module frontend
```

预期 JSON 包含 `agents`、`memories`、`project_skills` 和 `hook`。

### 2. 定位项目记忆

当需要判断长期项目知识应该保存到哪里时使用。

在 Codex 中调用：

```text
@Project Manager decide where this project memory should be stored
```

该 skill 使用一个路径约定：

```text
memories/<module>/<topic>.md
```

module 名来自真实仓库组件。只有在组件和 topic 都明确，并且确实有长期知识需要保存时，才创建 topic 文件。

### 3. 复盘已完成工作

在编码阶段、调试阶段、review 线程或架构解释完成后使用。

在 Codex 中调用：

```text
@Project Manager review this finished work and suggest project memory updates
```

review 流程会把候选内容分类为：

- `rule`：应写入 `AGENTS.md` 的项目规则
- `knowledge`：应写入 `memories/` 的项目事实
- `personal_memory`：需要用户明确批准后才能保存的个人偏好候选

本地 smoke test：

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
```

输出是 JSON：

```json
{
  "suggestions": [
    {
      "id": "r1",
      "kind": "rule",
      "destination": "AGENTS.md"
    }
  ]
}
```

实际 demo 会输出四条建议，覆盖三类 review 结果。

### 4. 复盘项目本地 skills

当某个工作阶段产生了可复用的项目本地流程、坑点、验证模式或工具使用模式时使用。

在 Codex 中调用：

```text
@Project Manager review this finished work for project skill updates
```

该流程只处理 `.agents/skills/`。它不会更新 `AGENTS.md`、`memories/` 或个人/全局 memory。它会建议：

- 更新已有 `.agents/skills/<skill>/SKILL.md`
- 在 `references/`、`templates/` 或 `scripts/` 下添加支持文件
- 创建新的 class-level skill：`.agents/skills/<skill-name>/`

写入前会先询问用户接受哪些建议。

## 可选 Hook 提醒

仓库包含 `.codex/hooks.json`，来自：

```text
codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json
```

hook 会在可能发生写入或编辑工具使用后输出低噪声提醒：

```text
Project Manager: recent file-writing activity detected. Consider running $project-review if this stage is complete.
```

可以直接测试 hook 命令：

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --detect-only
```

预期结果是上面的单行提醒。

## 脚本参考

### `init.py`

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/init.py \
  --rules "Run focused tests" \
  --module frontend
```

- `--rules`：要写入的项目规则；可重复传入
- `--module`：要在 `memories/` 下初始化的项目模块；可重复传入
- `--project-skills-dir`：项目 skill 目录，默认 `.agents/skills`
- `--install-hook`：如果 `.codex/hooks.json` 不存在，则从模板安装
- `--root`：目标仓库根目录，默认当前目录

### `review.py`

```bash
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --demo
python3 codex-plugin-dev/plugins/codex-project-manager/scripts/project_manager/review.py --detect-only
```

- `--demo`：以 JSON 输出示例 review 建议
- `--detect-only`：输出 hook 提醒并以状态码 `0` 退出

### `apply.py`

`apply.py` 包含用户接受建议后使用的辅助函数：

- `append_agents_rule(path, rule_line)`
- `append_memory_note(path, title, body)`
- `write_project_skill(path, title, body)`

示例：

```bash
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, "codex-plugin-dev/plugins/codex-project-manager/scripts")

from project_manager.apply import append_agents_rule, append_memory_note

append_agents_rule(Path("AGENTS.md"), "- Run focused pytest before closing frontend edits")
append_memory_note(
    Path("memories/frontend/state-model.md"),
    "State Cache",
    "The frontend state cache is invalidated after successful saves.",
)
PY
```

## 开发

运行全部测试：

```bash
.venv/bin/python -m pytest tests/codex_project_manager -q
```

运行聚焦测试：

```bash
.venv/bin/python -m pytest tests/codex_project_manager/test_classify.py -q
.venv/bin/python -m pytest tests/codex_project_manager/test_init.py -q
.venv/bin/python -m pytest tests/codex_project_manager/test_memory_paths.py tests/codex_project_manager/test_apply.py -q
.venv/bin/python -m pytest tests/codex_project_manager/test_review.py -q
```

验证 JSON 文件：

```bash
python3 -m json.tool codex-plugin-dev/.agents/plugins/marketplace.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool codex-plugin-dev/plugins/codex-project-manager/templates/hooks.json >/dev/null
python3 -m json.tool .codex/hooks.json >/dev/null
```

## 安全模型

- 建议和写入分离。
- 全局 memory 候选只作为建议。
- 项目本地写入必须在用户确认后执行。
- `AGENTS.md`、`memories/` 和 `.agents/skills/` 是项目长期上下文的目标位置。
