---
name: markdown-to-feishu-skill
description: "把本地 Markdown 文档写入飞书/Lark 知识库（Wiki）：在知识空间新建 Wiki 节点、写入正文为在线文档、并把文档引用的本地图片/资源按原文位置上传插入以保证文档完整性。支持写入用户指定的已有知识库（space_id / 名称 / wiki URL），也支持写入已有 docx 文档。当用户说『把这篇 markdown/这份文档发到飞书知识库 / 上传到 Lark wiki / 同步到知识空间 / 导入飞书 wiki 并保留图片 / 把带图片的文章整理进知识库』，或给出一个 .md 文件并要求归档到飞书/Lark 知识库时，使用本 skill。即使用户只说『传到飞书知识库』而没提图片，也要用本 skill，因为图片完整性是核心价值。不负责：编辑已有在线文档正文（走 lark-doc）、纯 Drive 文件管理（走 lark-drive）、知识库成员/权限管理（走 lark-wiki）。"
metadata:
  requires:
    bins: ["lark-cli"]
    python: ">=3.9"
  config: "飞书信息从 skill 根目录 .env 读取（复制 .env.example 填写）；用 scripts/feishu_config.py 加载，App Secret 会掩码。"
  cliHelp: "lark-cli wiki +node-create --help; lark-cli docs +media-insert --help; lark-cli docs +update --help"
---

# markdown-to-feishu

把本地 Markdown（可能带图片）完整写入飞书/Lark 知识库。核心难点是**图片完整性**：飞书原生 markdown 导入只会自动下载**网络 URL** 图片，本地路径图片（`![](./img/a.png)`）会被直接丢弃。本 skill 把"导入正文 + 把每张本地图片放到正确位置"的流程固定下来，保证每次都不丢图、且图片位置与原文一致。

**开始前 MUST：** 先用 Read 读取已安装的 [`lark-shared`](../lark-shared/SKILL.md)（认证、`--as` 身份、`--dry-run`、相对路径限制、高风险 exit 10 协议）。若仓库内没有 lark-shared，运行 `lark-cli skills read lark-shared` 或参考 `~/.claude/skills/lark-shared/SKILL.md`。

## 推荐：一键导入（scripts/import_with_images.py）

绝大多数场景直接用这个脚本——它把「新建 Wiki 节点 → 写入正文 → 逐张定位插图 → 清理占位符」全链路编排好，已端到端验证（图片位置 100% 命中、占位符全部清除）：

```bash
python3 <skill>/scripts/import_with_images.py <file>.md \
  --title "文档标题" \
  [--space-id <SPACE_ID>] \
  [--parent-node-token <NODE_TOKEN>] \
  [--doc-id <已有docx文档ID提供则写入已有文档而非新建>] \
  [--keep-markers]   # 调试用：保留占位符不清理
```

- `--space-id` 缺省时读 `.env` 的 `space_id`；`--title` 缺省取 MD 文件名。
- 脚本不读 App Secret，全程走已认证的 `lark-cli`（先 `lark-cli auth login`，user 身份）。
- 成功后打印 JSON：`doc_id`、`url`、`images_total`、`images_inserted`。

### 它内部怎么做的（理解原理才能排错）

1. **解析 + 占位**：每张图片替换成唯一文本 marker（`FEISHU-IMG-<idx>-<8位hex>`）；外网 `http/https` 图片先下载到临时目录，本地缺失/下载失败的图保留原 markdown 引用（不丢内容）。
2. **新建节点**：`wiki +node-create --obj-type docx` 建空文档（或 `--doc-id` 写入已有）。
3. **写正文**：`docs +update --command append --doc-format markdown` 写入带 marker 的正文。
4. **定位插图**：逐张 `docs +media-insert --file <图> --selection-with-ellipsis "<marker>" --before`——该命令内部完成「建空 image block → 上传素材 → 绑定 token」三步并自动回滚。`--file` 只接受 cwd 下相对路径，脚本会先把图暂存到 cwd 的唯一相对文件名再插入、插完即删。
5. **清理**：`docs +fetch --detail with-ids` 拿到各 marker 段落的 block_id，`block_delete` 批量删除。

> 关键事实（实证）：**飞书原生 MD 导入不会为本地图片生成空 image block**，所以"导入后替换空 block"行不通；marker 占位 + `media-insert --before` 定位才是可靠路径。

## 配置从 .env 读取（飞书信息）

本 skill 的飞书信息统一从 skill 根目录的 `.env` 读取，避免每次对话重复指定。复制 `.env.example` 为 `.env` 填写即可；`.env` 已被仓库根 `.gitignore` 忽略，不会提交。所有字段都可选——留空就回退到对话里临时指定（目标库）或 lark-cli 既有配置（凭证）。

工作流开始时**先读一次配置**：

```bash
python3 <skill>/scripts/feishu_config.py        # 打印当前配置（App Secret 已掩码为 ****）
```

返回 JSON 字段：
- `app_id` / `app_secret` / `brand`：可选的应用凭证。`_has_app_credentials` 为 false 时**不要**自己拼凭证，直接沿用 lark-cli 已初始化的应用（`~/.lark-cli/config.json`）。仅当用户在 `.env` 配了另一套凭证时，先 `lark-cli config init --app-id <FEISHU_APP_ID> --app-secret-stdin`（secret 走 stdin，**绝不**放进命令行参数或打印到终端）。
- `as_identity`：默认身份（见「关键约束」），用作各命令 `--as` 的默认值（缺省 `user`）。首次以 user 身份访问前需 `lark-cli auth login`（按 lark-shared 的 split-flow）。
- `space_id` / `wiki_url` / `space_name`：默认目标知识库，优先级 `space_id` > `wiki_url` > `space_name`。`_has_target_space` 为 true 时直接用它定位；为 false 时回退到对话里临时指定。
- `parent_node_token`：可选，新建节点时挂到的父节点（对应脚本的 `--parent-node-token`）。

> 安全：`feishu_config.py` 已对 `app_secret` 掩码，可放心打印。**不要**用 `cat .env` 或其它方式把明文 secret 回显到终端。

## 关键约束

- **相对路径**：lark-cli 的 `--file` / `--content @file` 只接受 cwd 下的相对路径，绝对路径报 `unsafe file path`。一键脚本已内部处理（图片暂存到 cwd 唯一相对文件名再插入、插完即删；正文也写到 cwd 临时文件）。手工调用 `docs +media-insert` 时务必自己遵守这条。
- **身份**：知识库/文档是用户个人资源，**始终带 `--as user`**（不带常被解析成 bot，看到的是应用空间）。脚本默认 user，可被 `--as` 或 `.env` 的 `FEISHU_AS` 覆盖。
- **写操作前告知**：新建节点、写正文、插图都是写操作。批量执行前把计划（目标空间、标题、图片张数）告诉用户。`wiki +space-create` / `+node-delete` 等是高风险写，按 lark-shared 的 exit 10 协议处理。
- **缺图不静默**：本地图片不存在或外网图下载失败时，脚本保留原始 markdown 引用并在 stderr 告警（不丢内容）。看到告警要把缺失清单显式反馈用户，问补文件还是接受占位。

## 工作流程

绝大多数情况直接跑 `import_with_images.py`（见顶部「推荐：一键导入」），它已把下面五步编排好，无需手工拆步：

1. **解析 + 占位**：每张图换成唯一 marker；外网图下载到临时目录，缺失/失败图保留原引用。
2. **建节点**：`wiki +node-create --obj-type docx`（或 `--doc-id` 写入已有文档）。
3. **写正文**：`docs +update --command append --doc-format markdown`。
4. **定位插图**：逐张 `docs +media-insert --file <图> --selection-with-ellipsis "<marker>" --before --align center [--caption <alt>]`。
5. **清理 + 核对**：`docs +fetch --detail with-ids` 取 marker block_id → `block_delete` 删占位 → 返回 `doc_id` / `url` / `images_inserted`/`images_total`。

> 需要拆步排错时，可以手工逐条跑上面的命令；命令语义与脚本完全一致。`docs +media-insert` 的 `--doc` 用文档 `document_id`（docx token / `doxcn...` 或 `/docx/` URL），**不接受 `/wiki/...` URL**。

## 失败与边界

- `node-create` / `media-insert` / `update` 命中 `missing scope` / `permission denied` / `not found`：默认停止，按 lark-shared 区分身份处理（user 走 `auth login --scope`，bot 走 console_url），不要盲目切身份重试。
- 网络瞬时错误 / timeout：脚本内置 3 次退避重试（实测命中过一次 media-insert timeout）；其余错误直接返回不重试。
- markdown 无图：脚本自动退化为「建节点 + 写正文」，跳过插图与清理。
- 同一 marker 文本理论唯一（带 8 位 hex 后缀）；若手工用业务文本做 selection 且重复，改用 `'前缀...后缀'` 形式的 `--selection-with-ellipsis`。

## 参考

- [lark-shared](../lark-shared/SKILL.md) — 认证、身份、相对路径、exit 10
- [lark-wiki](../lark-wiki/SKILL.md) — 知识空间/节点（`+node-create`、space 解析）
- [lark-doc](../lark-doc/SKILL.md) — `+media-insert`、`+update`（append / block_delete）、`+fetch` 核对
