#!/usr/bin/env python3
"""
database-tools-skills 统一入口
薄路由层 — 所有业务逻辑由 scripts/ 和 lib/ 模块实现
"""

import argparse
import os
import sys

# Windows 控制台中文输出兼容
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# 确保 scripts/ 和 lib/ 可导入
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)
sys.path.insert(0, os.path.join(TOOL_DIR, "scripts"))


def add_connection_args(parser):
    """添加通用连接参数"""
    conn = parser.add_argument_group("连接参数")
    conn.add_argument("--profile", help="使用配置文件中的 profile 名称")
    conn.add_argument("--dsn", help="完整数据库连接字符串")
    conn.add_argument("--host", "-H", help="数据库主机")
    conn.add_argument("--port", "-p", help="数据库端口")
    conn.add_argument("--user", "-U", help="数据库用户")
    conn.add_argument("--password", "-W", help="数据库密码")
    conn.add_argument("--dbname", "-d", help="数据库名称")
    conn.add_argument("--env-file", help=".env 文件路径")


def get_connection_for(engine, args):
    """基于引擎类型和参数获取连接"""
    from lib.connection import from_args
    # 创建一个带 engine 属性的命名空间
    args.engine = engine
    return from_args(args, engine=engine)


# ============================================================
# 数据字典生成
# ============================================================

def generate_data_dict(snapshot, title=None):
    """
    将 SchemaSnapshot 转换为数据字典 Markdown 文档。
    包含：文档头、目录、每张表的字段/索引/约束详情。
    """
    from datetime import datetime

    lines = []
    db_info = f"{snapshot.host}:{snapshot.port}/{snapshot.database}" if snapshot.host else snapshot.database
    doc_title = title or f"{snapshot.schema_name} 数据字典"

    lines.append(f"# {doc_title}\n")
    lines.append(f"- **数据库**: {db_info}")
    lines.append(f"- **Schema**: {snapshot.schema_name}")
    lines.append(f"- **引擎**: {snapshot.db_engine}")
    lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **表数量**: {len(snapshot.tables)}\n")

    # 目录
    lines.append("## 目录\n")
    for tbl in snapshot.tables:
        anchor = tbl.name.lower().replace("_", "-")
        comment_hint = f" — {tbl.comment}" if tbl.comment else ""
        lines.append(f"- [{tbl.name}](#{anchor}){comment_hint}")
    lines.append("")

    # 每张表详情
    for tbl in snapshot.tables:
        lines.append(f"---\n")
        lines.append(f"## {tbl.name}\n")
        if tbl.comment:
            lines.append(f"> {tbl.comment}\n")

        # 基本信息
        meta_parts = []
        if tbl.engine:
            meta_parts.append(f"引擎: {tbl.engine}")
        if tbl.collation:
            meta_parts.append(f"字符集: {tbl.collation}")
        if tbl.row_count is not None:
            meta_parts.append(f"估算行数: {tbl.row_count:,}")
        if tbl.total_size:
            meta_parts.append(f"总大小: {tbl.total_size}")
        if meta_parts:
            lines.append("**" + " | ".join(meta_parts) + "**\n")

        # 字段列表
        lines.append("### 字段\n")
        lines.append("| 序号 | 字段名 | 类型 | 可空 | 默认值 | 说明 |")
        lines.append("|------|--------|------|------|--------|------|")
        for col in tbl.columns:
            nullable = "YES" if col.is_nullable else "NO"
            default = col.default or ""
            comment = col.comment or ""
            # 转义 | 防止破坏表格
            comment = comment.replace("|", "\\|")
            default = str(default).replace("|", "\\|")
            lines.append(
                f"| {col.ordinal_position} | `{col.name}` | {col.raw_type} "
                f"| {nullable} | {default} | {comment} |"
            )
        lines.append("")

        # 索引
        non_pk_indexes = [i for i in tbl.indexes if not i.is_primary]
        pk_indexes = [i for i in tbl.indexes if i.is_primary]
        if pk_indexes or non_pk_indexes:
            lines.append("### 索引\n")
            lines.append("| 索引名 | 类型 | 列 | 唯一 |")
            lines.append("|--------|------|-----|------|")
            for idx in tbl.indexes:
                idx_type = "PRIMARY" if idx.is_primary else idx.index_type
                cols_str = ", ".join(idx.columns) if idx.columns else (idx.definition or "")
                unique = "YES" if idx.is_unique else "NO"
                lines.append(f"| `{idx.name}` | {idx_type} | {cols_str} | {unique} |")
            lines.append("")

        # 约束（外键）
        fk_constraints = [c for c in tbl.constraints if c.type == "FOREIGN KEY"]
        if fk_constraints:
            lines.append("### 外键约束\n")
            lines.append("| 约束名 | 本表列 | 引用表 | 引用列 |")
            lines.append("|--------|--------|--------|--------|")
            for con in fk_constraints:
                local_cols = ", ".join(con.columns)
                ref_table = f"{con.foreign_schema}.{con.foreign_table}" if con.foreign_schema else (con.foreign_table or "")
                ref_cols = ", ".join(con.foreign_columns)
                lines.append(f"| `{con.name}` | {local_cols} | {ref_table} | {ref_cols} |")
            lines.append("")

    return "\n".join(lines)


def generate_data_dict_html(snapshot, title=None):
    """
    将 SchemaSnapshot 转换为 HTML 数据字典文档。
    左侧固定菜单（表名 + 注释），右侧内容区，样式清爽干净。
    """
    from datetime import datetime

    db_info = f"{snapshot.host}:{snapshot.port}/{snapshot.database}" if snapshot.host else snapshot.database
    doc_title = title or f"{snapshot.schema_name} 数据字典"
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 左侧菜单项
    menu_items = []
    for tbl in snapshot.tables:
        anchor = f"tbl-{tbl.name}"
        label = tbl.name
        comment = f'<span class="menu-comment">{tbl.comment}</span>' if tbl.comment else ""
        menu_items.append(
            f'<li><a href="#{anchor}">{label}{comment}</a></li>'
        )
    menu_html = "\n".join(menu_items)

    # 每张表的内容
    table_sections = []
    for tbl in snapshot.tables:
        anchor = f"tbl-{tbl.name}"
        comment_html = f'<p class="table-comment">{tbl.comment}</p>' if tbl.comment else ""

        meta_parts = []
        if tbl.engine:
            meta_parts.append(f"引擎: {tbl.engine}")
        if tbl.collation:
            meta_parts.append(f"字符集: {tbl.collation}")
        if tbl.row_count is not None:
            meta_parts.append(f"估算行数: {tbl.row_count:,}")
        if tbl.total_size:
            meta_parts.append(f"总大小: {tbl.total_size}")
        meta_html = f'<p class="table-meta">{" &nbsp;|&nbsp; ".join(meta_parts)}</p>' if meta_parts else ""

        # 字段表格
        col_rows = []
        for col in tbl.columns:
            nullable = "YES" if col.is_nullable else "NO"
            default = col.default or ""
            comment = col.comment or ""
            col_rows.append(
                f"<tr><td>{col.ordinal_position}</td><td><code>{col.name}</code></td>"
                f"<td>{col.raw_type}</td><td>{nullable}</td>"
                f"<td>{default}</td><td>{comment}</td></tr>"
            )
        col_table = (
            '<table><thead><tr><th>#</th><th>字段名</th><th>类型</th>'
            '<th>可空</th><th>默认值</th><th>说明</th></tr></thead><tbody>'
            + "\n".join(col_rows) + "</tbody></table>"
        )

        # 索引表格
        idx_html = ""
        if tbl.indexes:
            idx_rows = []
            for idx in tbl.indexes:
                idx_type = "PRIMARY" if idx.is_primary else idx.index_type
                cols_str = ", ".join(idx.columns) if idx.columns else (idx.definition or "")
                unique = "YES" if idx.is_unique else "NO"
                idx_rows.append(
                    f"<tr><td><code>{idx.name}</code></td><td>{idx_type}</td>"
                    f"<td>{cols_str}</td><td>{unique}</td></tr>"
                )
            idx_html = (
                '<h4>索引</h4><table><thead><tr><th>索引名</th><th>类型</th>'
                '<th>列</th><th>唯一</th></tr></thead><tbody>'
                + "\n".join(idx_rows) + "</tbody></table>"
            )

        # 外键表格
        fk_html = ""
        fk_constraints = [c for c in tbl.constraints if c.type == "FOREIGN KEY"]
        if fk_constraints:
            fk_rows = []
            for con in fk_constraints:
                local_cols = ", ".join(con.columns)
                ref_table = f"{con.foreign_schema}.{con.foreign_table}" if con.foreign_schema else (con.foreign_table or "")
                ref_cols = ", ".join(con.foreign_columns)
                fk_rows.append(
                    f"<tr><td><code>{con.name}</code></td><td>{local_cols}</td>"
                    f"<td>{ref_table}</td><td>{ref_cols}</td></tr>"
                )
            fk_html = (
                '<h4>外键约束</h4><table><thead><tr><th>约束名</th><th>本表列</th>'
                '<th>引用表</th><th>引用列</th></tr></thead><tbody>'
                + "\n".join(fk_rows) + "</tbody></table>"
            )

        table_sections.append(f"""
    <section id="{anchor}" class="table-section">
      <h2>{tbl.name}</h2>
      {comment_html}
      {meta_html}
      <h4>字段</h4>
      {col_table}
      {idx_html}
      {fk_html}
    </section>""")

    content_html = "\n".join(table_sections)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{doc_title}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         font-size: 14px; color: #333; background: #f7f8fa; display: flex; height: 100vh; overflow: hidden; }}

  /* 左侧菜单 */
  nav {{ width: 240px; min-width: 200px; background: #fff; border-right: 1px solid #e5e7eb;
        display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0; }}
  .nav-header {{ padding: 16px; border-bottom: 1px solid #e5e7eb; }}
  .nav-header h1 {{ font-size: 13px; font-weight: 600; color: #111; line-height: 1.4; word-break: break-all; }}
  .nav-header p {{ font-size: 11px; color: #888; margin-top: 4px; }}
  .nav-search {{ padding: 8px 12px; border-bottom: 1px solid #e5e7eb; }}
  .nav-search input {{ width: 100%; padding: 5px 8px; border: 1px solid #d1d5db;
                       border-radius: 4px; font-size: 12px; outline: none; }}
  .nav-search input:focus {{ border-color: #6366f1; }}
  nav ul {{ list-style: none; overflow-y: auto; flex: 1; padding: 6px 0; }}
  nav ul li a {{ display: block; padding: 6px 16px; color: #444; text-decoration: none;
                 font-size: 13px; line-height: 1.4; transition: background .15s; }}
  nav ul li a:hover {{ background: #f3f4f6; color: #111; }}
  nav ul li a.active {{ background: #eef2ff; color: #4f46e5; font-weight: 500; }}
  .menu-comment {{ display: block; font-size: 11px; color: #9ca3af; margin-top: 1px; }}

  /* 右侧内容 */
  main {{ flex: 1; overflow-y: auto; padding: 32px 40px; }}
  .page-header {{ margin-bottom: 32px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }}
  .page-header h1 {{ font-size: 22px; font-weight: 700; color: #111; }}
  .page-header .meta {{ font-size: 12px; color: #888; margin-top: 8px; display: flex; gap: 16px; flex-wrap: wrap; }}

  .table-section {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
                    padding: 24px; margin-bottom: 24px; }}
  .table-section h2 {{ font-size: 16px; font-weight: 600; color: #111; margin-bottom: 4px; }}
  .table-comment {{ font-size: 13px; color: #6b7280; margin-bottom: 8px; }}
  .table-meta {{ font-size: 12px; color: #9ca3af; margin-bottom: 16px; }}
  .table-section h4 {{ font-size: 13px; font-weight: 600; color: #374151;
                       margin: 16px 0 8px; text-transform: uppercase; letter-spacing: .04em; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  thead tr {{ background: #f9fafb; }}
  th {{ padding: 8px 12px; text-align: left; font-weight: 600; color: #6b7280;
        border-bottom: 1px solid #e5e7eb; white-space: nowrap; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #f3f4f6; color: #374151; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #fafafa; }}
  code {{ font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px;
          background: #f3f4f6; padding: 1px 5px; border-radius: 3px; color: #4f46e5; }}
</style>
</head>
<body>
<nav>
  <div class="nav-header">
    <h1>{doc_title}</h1>
    <p>{len(snapshot.tables)} 张表 &nbsp;·&nbsp; {gen_time}</p>
  </div>
  <div class="nav-search">
    <input type="text" id="search" placeholder="搜索表名…" oninput="filterMenu(this.value)">
  </div>
  <ul id="menu">
{menu_html}
  </ul>
</nav>
<main id="main">
  <div class="page-header">
    <h1>{doc_title}</h1>
    <div class="meta">
      <span>数据库: {db_info}</span>
      <span>Schema: {snapshot.schema_name}</span>
      <span>引擎: {snapshot.db_engine}</span>
      <span>生成时间: {gen_time}</span>
    </div>
  </div>
{content_html}
</main>
<script>
  // 菜单搜索
  function filterMenu(q) {{
    q = q.toLowerCase();
    document.querySelectorAll('#menu li').forEach(li => {{
      li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
    }});
  }}
  // 滚动高亮菜单
  const sections = document.querySelectorAll('.table-section');
  const links = document.querySelectorAll('nav a');
  const observer = new IntersectionObserver(entries => {{
    entries.forEach(e => {{
      if (e.isIntersecting) {{
        links.forEach(a => a.classList.remove('active'));
        const active = document.querySelector(`nav a[href="#${{e.target.id}}"]`);
        if (active) {{
          active.classList.add('active');
          active.scrollIntoView({{block: 'nearest'}});
        }}
      }}
    }});
  }}, {{root: document.getElementById('main'), threshold: 0.2}});
  sections.forEach(s => observer.observe(s));
</script>
</body>
</html>"""


# ============================================================
# PG 子命令
# ============================================================

def cmd_pg(args):
    from scripts import pg_inspector, pg_index_advisor

    profile = getattr(args, "profile", None)
    if profile:
        from lib.connection import from_profile
        conn = from_profile(profile, password=getattr(args, "password", None))
    else:
        conn = pg_inspector.get_connection(args)

    try:
        sub = args.pg_command

        if sub == "schemas":
            for s in pg_inspector.list_schemas(conn):
                print(s)

        elif sub == "tables":
            tables = pg_inspector.list_tables(conn, args.schema)
            for t in tables:
                flags = []
                if t["hasindexes"]:
                    flags.append("idx")
                if t["hastriggers"]:
                    flags.append("trg")
                flag_str = f" [{','.join(flags)}]" if flags else ""
                print(f"  {t['tablename']}{flag_str}")

        elif sub == "inspect":
            output = pg_inspector.export_schema_info(
                conn, args.schema, args.table, args.format
            )
            print(output)

        elif sub == "ddl":
            ddl = pg_inspector.generate_ddl(conn, args.schema, args.table)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(ddl)
                print(f"DDL 已写入: {args.output}")
            else:
                print(ddl)

        elif sub == "report":
            report = pg_index_advisor.generate_report(conn, args.schema)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"报告已写入: {args.output}")
            else:
                print(report)

        elif sub == "optimize":
            concurrently = not getattr(args, "no_concurrently", False)
            ddl = pg_index_advisor.generate_optimization_ddl(conn, args.schema, concurrently)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(ddl)
                print(f"优化脚本已写入: {args.output}")
            else:
                print(ddl)

        elif sub == "dict":
            from lib.snapshot import export_pg
            snapshot = export_pg(conn, args.schema)
            if args.table:
                snapshot.tables = [t for t in snapshot.tables if t.name in args.table]
            fmt = getattr(args, "format", "markdown")
            title = getattr(args, "title", None)
            doc = generate_data_dict_html(snapshot, title=title) if fmt == "html" else generate_data_dict(snapshot, title=title)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(doc)
                print(f"数据字典已写入: {args.output}（共 {len(snapshot.tables)} 张表）")
            else:
                print(doc)

        elif sub == "seed":
            limit = getattr(args, "limit", None)
            sql = pg_inspector.generate_seed(conn, args.schema, args.table, limit)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(sql)
                print(f"Seed 脚本已写入: {args.output}")
            else:
                print(sql)

        else:
            print(f"未知 PG 子命令: {sub}", file=sys.stderr)
            sys.exit(1)

    finally:
        conn.close()


# ============================================================
# MySQL 子命令
# ============================================================

def cmd_mysql(args):
    from scripts import mysql_inspector, mysql_index_advisor

    profile = getattr(args, "profile", None)
    if profile:
        from lib.connection import from_profile
        conn = from_profile(profile, password=getattr(args, "password", None))
    else:
        conn = mysql_inspector.get_connection(args)

    try:
        sub = args.mysql_command

        if sub == "schemas":
            for s in mysql_inspector.list_schemas(conn):
                print(s)

        elif sub == "tables":
            tables = mysql_inspector.list_tables(conn, args.schema)
            for t in tables:
                engine = t.get("engine") or ""
                comment = t.get("table_comment") or ""
                extra = f" [{engine}]" if engine else ""
                if comment:
                    extra += f" -- {comment}"
                print(f"  {t['table_name']}{extra}")

        elif sub == "inspect":
            output = mysql_inspector.export_schema_info(
                conn, args.schema, args.table, args.format
            )
            print(output)

        elif sub == "ddl":
            mode = getattr(args, "mode", "show")
            if mode == "show":
                ddl = mysql_inspector.generate_ddl_show(conn, args.schema, args.table)
            else:
                ddl = mysql_inspector.generate_ddl(conn, args.schema, args.table)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(ddl)
                print(f"DDL 已写入: {args.output}")
            else:
                print(ddl)

        elif sub == "report":
            report = mysql_index_advisor.generate_report(conn, args.schema)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"报告已写入: {args.output}")
            else:
                print(report)

        elif sub == "optimize":
            ddl = mysql_index_advisor.generate_optimization_ddl(conn, args.schema)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(ddl)
                print(f"优化脚本已写入: {args.output}")
            else:
                print(ddl)

        elif sub == "dict":
            from lib.snapshot import export_mysql
            snapshot = export_mysql(conn, args.schema)
            if args.table:
                snapshot.tables = [t for t in snapshot.tables if t.name in args.table]
            fmt = getattr(args, "format", "markdown")
            title = getattr(args, "title", None)
            doc = generate_data_dict_html(snapshot, title=title) if fmt == "html" else generate_data_dict(snapshot, title=title)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(doc)
                print(f"数据字典已写入: {args.output}（共 {len(snapshot.tables)} 张表）")
            else:
                print(doc)

        elif sub == "seed":
            limit = getattr(args, "limit", None)
            sql = mysql_inspector.generate_seed(conn, args.schema, args.table, limit)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(sql)
                print(f"Seed 脚本已写入: {args.output}")
            else:
                print(sql)

        else:
            print(f"未知 MySQL 子命令: {sub}", file=sys.stderr)
            sys.exit(1)

    finally:
        conn.close()


# ============================================================
# Diff 子命令
# ============================================================

def cmd_diff(args):
    from lib.snapshot import load_snapshot, export_pg, export_mysql
    from lib.differ import SchemaDiffer, MigrationGenerator
    from lib.formatters import MarkdownFormatter
    from lib.connection import from_profile, connect_pg, connect_mysql

    def resolve_source(spec, password=None):
        """解析 source/target: profile 名, DSN, 或 JSON 文件路径"""
        # JSON 文件
        if spec.endswith(".json") and os.path.exists(spec):
            return load_snapshot(spec)

        # profile
        from lib.config import get_profile
        prof = get_profile(spec)
        if prof:
            conn = from_profile(spec, password=password)
            engine = prof["engine"]
            schema = getattr(args, "schema", None) or "public"
            try:
                if engine in ("pg", "postgresql"):
                    return export_pg(conn, schema)
                else:
                    return export_mysql(conn, schema)
            finally:
                conn.close()

        # DSN
        if spec.startswith("postgresql://") or spec.startswith("postgres://"):
            conn = connect_pg(dsn=spec)
            schema = getattr(args, "schema", None) or "public"
            try:
                return export_pg(conn, schema)
            finally:
                conn.close()

        if spec.startswith("mysql://"):
            conn = connect_mysql(dsn=spec)
            schema = getattr(args, "schema", None)
            if not schema:
                from urllib.parse import urlparse
                schema = urlparse(spec).path.lstrip("/")
            try:
                return export_mysql(conn, schema)
            finally:
                conn.close()

        raise ValueError(f"无法解析来源: {spec} (支持 profile 名、DSN 或 .json 文件)")

    source = resolve_source(args.source, getattr(args, "password", None))
    target = resolve_source(args.target, getattr(args, "password", None))

    differ = SchemaDiffer()
    diff_result = differ.diff(source, target)

    # 格式化输出
    report = MarkdownFormatter.diff_report(diff_result)
    print(report)

    # 如果同引擎，生成迁移 DDL
    if source.db_engine == target.db_engine:
        gen = MigrationGenerator(source.db_engine)
        migration = gen.generate(diff_result)
        if migration.strip():
            print("\n---\n")
            print("# 迁移 DDL\n")
            print(migration)
    else:
        print("\n> 跨引擎对比（PG ↔ MySQL），仅生成对照报告，不生成迁移 DDL。\n")


# ============================================================
# Snapshot 子命令
# ============================================================

def cmd_snapshot(args):
    from lib.snapshot import export_pg, export_mysql, save_snapshot
    from lib.connection import from_profile
    from lib.config import get_profile

    profile = args.profile
    prof = get_profile(profile)
    if not prof:
        print(f"未找到 profile: {profile}", file=sys.stderr)
        sys.exit(1)

    conn = from_profile(profile, password=getattr(args, "password", None))
    engine = prof["engine"]
    schema = getattr(args, "schema", None)

    try:
        if engine in ("pg", "postgresql"):
            snapshot = export_pg(conn, schema or "public")
        else:
            db = prof.get("connection", {}).get("database") or prof.get("connection", {}).get("dbname")
            snapshot = export_mysql(conn, schema or db)
    finally:
        conn.close()

    output = args.output or f"snapshot_{profile}_{snapshot.schema_name}.json"
    save_snapshot(snapshot, output)
    print(f"快照已保存: {output}")


# ============================================================
# Config 子命令
# ============================================================

def cmd_config(args):
    from lib import config

    sub = args.config_command

    if sub == "set":
        params = {}
        if args.host:
            params["host"] = args.host
        if args.port:
            params["port"] = args.port
        if args.user:
            params["user"] = args.user
        if args.dbname:
            params["dbname"] = args.dbname
        if args.dsn:
            params["dsn"] = args.dsn

        config.set_profile(args.name, args.engine, **params)
        print(f"Profile '{args.name}' 已保存")

    elif sub == "list":
        profiles = config.list_profiles()
        if not profiles:
            print("没有已配置的 profile")
            return
        for name, prof in profiles.items():
            eng = prof.get("engine", "?")
            conn_info = prof.get("connection", {})
            host = conn_info.get("host", "")
            port = conn_info.get("port", "")
            db = conn_info.get("dbname") or conn_info.get("database", "")
            print(f"  {name}: [{eng}] {host}:{port}/{db}")

    elif sub == "remove":
        if config.remove_profile(args.name):
            print(f"Profile '{args.name}' 已删除")
        else:
            print(f"未找到 profile: {args.name}", file=sys.stderr)
            sys.exit(1)


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="database-tools-skills 统一入口 — PostgreSQL / MySQL 数据库工具集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s pg schemas --dsn postgresql://user:pass@localhost/mydb
  %(prog)s pg inspect --schema public --profile dev
  %(prog)s pg dict --schema public --output dict.md --profile dev
  %(prog)s mysql tables --schema mydb --host 127.0.0.1 --user root
  %(prog)s mysql dict --schema mydb --output dict.md
  %(prog)s diff --source dev --target prod
  %(prog)s snapshot --profile dev -o dev_snapshot.json
  %(prog)s config set dev --engine pg --host localhost --dbname mydb
  %(prog)s config list
""",
    )

    sub = parser.add_subparsers(dest="command", help="可用命令组")

    # ---- pg ----
    pg_parser = sub.add_parser("pg", help="PostgreSQL 相关命令")
    add_connection_args(pg_parser)
    pg_sub = pg_parser.add_subparsers(dest="pg_command", help="PG 子命令")

    pg_sub.add_parser("schemas", help="列出所有用户 schema")

    p = pg_sub.add_parser("tables", help="列出指定 schema 下的表")
    p.add_argument("--schema", "-s", default="public")

    p = pg_sub.add_parser("inspect", help="查看表结构详情")
    p.add_argument("--schema", "-s", default="public")
    p.add_argument("--table", "-t", nargs="*")
    p.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")

    p = pg_sub.add_parser("ddl", help="生成 DDL 脚本")
    p.add_argument("--schema", "-s", default="public")
    p.add_argument("--table", "-t", nargs="*")
    p.add_argument("--output", "-o")

    p = pg_sub.add_parser("report", help="生成完整性能分析报告")
    p.add_argument("--schema", "-s", default="public")
    p.add_argument("--output", "-o")

    p = pg_sub.add_parser("optimize", help="生成优化 DDL 脚本")
    p.add_argument("--schema", "-s", default="public")
    p.add_argument("--no-concurrently", action="store_true")
    p.add_argument("--output", "-o")

    p = pg_sub.add_parser("dict", help="导出数据字典文档（Markdown 或 HTML）")
    p.add_argument("--schema", "-s", default="public")
    p.add_argument("--table", "-t", nargs="*", help="指定表名（不填则导出全部）")
    p.add_argument("--title", help="文档标题（默认: <schema> 数据字典）")
    p.add_argument("--format", "-f", choices=["markdown", "html"], default="markdown", help="输出格式（默认: markdown）")
    p.add_argument("--output", "-o", help="输出文件路径（不填则打印到终端）")

    p = pg_sub.add_parser("seed", help="导出表数据为 INSERT 初始化脚本")
    p.add_argument("--schema", "-s", default="public")
    p.add_argument("--table", "-t", nargs="*")
    p.add_argument("--limit", "-l", type=int, help="每张表最多导出行数")
    p.add_argument("--output", "-o")

    # ---- mysql ----
    mysql_parser = sub.add_parser("mysql", help="MySQL 相关命令")
    add_connection_args(mysql_parser)
    mysql_sub = mysql_parser.add_subparsers(dest="mysql_command", help="MySQL 子命令")

    mysql_sub.add_parser("schemas", help="列出所有用户数据库")

    p = mysql_sub.add_parser("tables", help="列出指定数据库下的表")
    p.add_argument("--schema", "-s", required=True)

    p = mysql_sub.add_parser("inspect", help="查看表结构详情")
    p.add_argument("--schema", "-s", required=True)
    p.add_argument("--table", "-t", nargs="*")
    p.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")

    p = mysql_sub.add_parser("ddl", help="生成 DDL 脚本")
    p.add_argument("--schema", "-s", required=True)
    p.add_argument("--table", "-t", nargs="*")
    p.add_argument("--output", "-o")
    p.add_argument("--mode", choices=["show", "build"], default="show")

    p = mysql_sub.add_parser("report", help="生成完整性能分析报告")
    p.add_argument("--schema", "-s", required=True)
    p.add_argument("--output", "-o")

    p = mysql_sub.add_parser("optimize", help="生成优化 DDL 脚本")
    p.add_argument("--schema", "-s", required=True)
    p.add_argument("--output", "-o")

    p = mysql_sub.add_parser("dict", help="导出数据字典文档（Markdown 或 HTML）")
    p.add_argument("--schema", "-s", required=True)
    p.add_argument("--table", "-t", nargs="*", help="指定表名（不填则导出全部）")
    p.add_argument("--title", help="文档标题（默认: <schema> 数据字典）")
    p.add_argument("--format", "-f", choices=["markdown", "html"], default="markdown", help="输出格式（默认: markdown）")
    p.add_argument("--output", "-o", help="输出文件路径（不填则打印到终端）")

    p = mysql_sub.add_parser("seed", help="导出表数据为 INSERT 初始化脚本")
    p.add_argument("--schema", "-s", required=True)
    p.add_argument("--table", "-t", nargs="*")
    p.add_argument("--limit", "-l", type=int, help="每张表最多导出行数")
    p.add_argument("--output", "-o")

    # ---- diff ----
    diff_parser = sub.add_parser("diff", help="跨数据库结构对比")
    diff_parser.add_argument("--password", "-W", help="数据库密码")
    diff_parser.add_argument("--source", required=True, help="源 (profile名 / DSN / snapshot.json)")
    diff_parser.add_argument("--target", required=True, help="目标 (profile名 / DSN / snapshot.json)")
    diff_parser.add_argument("--schema", "-s", help="Schema/数据库名称")

    # ---- snapshot ----
    snap_parser = sub.add_parser("snapshot", help="导出结构快照")
    snap_parser.add_argument("--profile", required=True, help="Profile 名称")
    snap_parser.add_argument("--password", "-W", help="数据库密码")
    snap_parser.add_argument("--schema", "-s", help="Schema/数据库名称")
    snap_parser.add_argument("--output", "-o", help="输出文件路径")

    # ---- config ----
    config_parser = sub.add_parser("config", help="配置管理")
    config_sub = config_parser.add_subparsers(dest="config_command", help="配置子命令")

    p_set = config_sub.add_parser("set", help="设置 profile")
    p_set.add_argument("name", help="Profile 名称")
    p_set.add_argument("--engine", required=True, choices=["pg", "mysql"])
    p_set.add_argument("--host")
    p_set.add_argument("--port")
    p_set.add_argument("--user")
    p_set.add_argument("--dbname")
    p_set.add_argument("--dsn")

    config_sub.add_parser("list", help="列出所有 profile")

    p_rm = config_sub.add_parser("remove", help="删除 profile")
    p_rm.add_argument("name", help="Profile 名称")

    # 解析
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "pg":
        if not getattr(args, "pg_command", None):
            pg_parser.print_help()
            sys.exit(1)
        cmd_pg(args)

    elif args.command == "mysql":
        if not getattr(args, "mysql_command", None):
            mysql_parser.print_help()
            sys.exit(1)
        cmd_mysql(args)

    elif args.command == "diff":
        cmd_diff(args)

    elif args.command == "snapshot":
        cmd_snapshot(args)

    elif args.command == "config":
        if not getattr(args, "config_command", None):
            config_parser.print_help()
            sys.exit(1)
        cmd_config(args)


if __name__ == "__main__":
    main()
