# HTML 文档模板说明

生成 HTML 格式的 API 文档时，使用下方的完整模板结构。

## 数据结构约定

生成 HTML 前，先将接口数据整理为以下结构（在脑海中组织，不需要输出）：

```
modules: [
  {
    id: "module-1",
    name: "用户模块",
    apis: [
      {
        id: "api-1-1",
        name: "用户登录",
        method: "POST",       // GET/POST/PUT/DELETE/PATCH
        path: "/api/user/login",
        description: "...",
        params: [...],        // 请求参数列表
        paramExample: "...",  // 请求参数 JSON 样例
        responseParams: [...],
        successExample: "...",
        failExample: "..."
      }
    ]
  }
]
```

单文件时 modules 只有一个元素，name 取自文件名或 Controller 类名。

## HTTP 方法颜色

| 方法 | 颜色 |
|------|------|
| GET | `#61affe` (蓝) |
| POST | `#49cc90` (绿) |
| PUT | `#fca130` (橙) |
| DELETE | `#f93e3e` (红) |
| PATCH | `#50e3c2` (青) |

## 完整 HTML 模板

将下方模板中的 `{{TITLE}}`、`{{NAV_ITEMS}}`、`{{CONTENT_SECTIONS}}` 替换为实际内容后写入文件。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}} - API 文档</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 14px; color: #333; background: #f7f8fa; display: flex; min-height: 100vh; }

  /* 左侧导航 */
  .sidebar { width: 260px; min-width: 260px; background: #fff; border-right: 1px solid #e8eaed; height: 100vh; position: sticky; top: 0; overflow-y: auto; display: flex; flex-direction: column; }
  .sidebar-header { padding: 20px 16px 12px; border-bottom: 1px solid #e8eaed; }
  .sidebar-header h1 { font-size: 15px; font-weight: 600; color: #1a1a2e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .sidebar-header p { font-size: 12px; color: #999; margin-top: 4px; }
  .nav { padding: 8px 0; flex: 1; }
  .nav-group { margin-bottom: 2px; }
  .nav-group-title { display: flex; align-items: center; gap: 6px; padding: 8px 16px; font-size: 12px; font-weight: 600; color: #666; text-transform: uppercase; letter-spacing: 0.5px; cursor: pointer; user-select: none; transition: background 0.15s; }
  .nav-group-title:hover { background: #f5f6f8; }
  .nav-group-title .arrow { margin-left: auto; font-size: 10px; color: #bbb; transition: transform 0.2s; }
  .nav-group-title.collapsed .arrow { transform: rotate(-90deg); }
  .nav-group-items { overflow: hidden; }
  .nav-item { display: flex; align-items: center; gap: 8px; padding: 7px 16px 7px 28px; cursor: pointer; transition: background 0.15s; border-left: 2px solid transparent; }
  .nav-item:hover { background: #f5f6f8; }
  .nav-item.active { background: #f0f7ff; border-left-color: #1677ff; }
  .nav-item.active .nav-item-name { color: #1677ff; font-weight: 500; }
  .nav-item-badge { font-size: 10px; font-weight: 600; padding: 1px 5px; border-radius: 3px; color: #fff; flex-shrink: 0; }
  .nav-item-name { font-size: 13px; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* 右侧内容 */
  .main { flex: 1; overflow-y: auto; padding: 32px 40px; max-width: 900px; }
  .module-section { margin-bottom: 48px; }
  .module-title { font-size: 20px; font-weight: 700; color: #1a1a2e; margin-bottom: 24px; padding-bottom: 10px; border-bottom: 2px solid #e8eaed; }
  .api-card { background: #fff; border: 1px solid #e8eaed; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }
  .api-header { display: flex; align-items: center; gap: 12px; padding: 14px 20px; cursor: pointer; user-select: none; }
  .api-header:hover { background: #fafbfc; }
  .method-badge { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; color: #fff; flex-shrink: 0; min-width: 52px; text-align: center; }
  .api-path { font-family: "SFMono-Regular", Consolas, monospace; font-size: 14px; color: #333; font-weight: 500; }
  .api-name { font-size: 13px; color: #888; margin-left: auto; flex-shrink: 0; }
  .api-toggle { margin-left: 8px; color: #bbb; font-size: 12px; transition: transform 0.2s; flex-shrink: 0; }
  .api-toggle.open { transform: rotate(180deg); }
  .api-body { border-top: 1px solid #f0f0f0; padding: 20px; display: none; }
  .api-body.open { display: block; }
  .api-desc { font-size: 13px; color: #666; margin-bottom: 20px; line-height: 1.6; }
  .section-title { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 10px; margin-top: 20px; }
  .section-title:first-child { margin-top: 0; }

  /* 参数表格 */
  .param-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .param-table th { background: #f7f8fa; padding: 8px 12px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #e8eaed; white-space: nowrap; }
  .param-table td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; color: #444; vertical-align: top; }
  .param-table tr:last-child td { border-bottom: none; }
  .param-table tr:hover td { background: #fafbfc; }
  .param-name { font-family: "SFMono-Regular", Consolas, monospace; color: #c7254e; }
  .param-type { font-family: "SFMono-Regular", Consolas, monospace; color: #0070c1; font-size: 12px; }
  .required-yes { color: #f5222d; font-weight: 500; }
  .required-no { color: #999; }

  /* 代码块 */
  .code-block { background: #1e1e2e; border-radius: 6px; padding: 14px 16px; font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; line-height: 1.6; color: #cdd6f4; overflow-x: auto; white-space: pre; }
  .code-tabs { display: flex; gap: 0; margin-bottom: 0; border-bottom: 1px solid #e8eaed; }
  .code-tab { padding: 6px 14px; font-size: 12px; color: #888; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; }
  .code-tab.active { color: #1677ff; border-bottom-color: #1677ff; font-weight: 500; }
  .code-panel { display: none; }
  .code-panel.active { display: block; }
</style>
</head>
<body>

<nav class="sidebar">
  <div class="sidebar-header">
    <h1>{{TITLE}}</h1>
    <p>API 接口文档</p>
  </div>
  <div class="nav">
    {{NAV_ITEMS}}
  </div>
</nav>

<main class="main" id="main">
  {{CONTENT_SECTIONS}}
</main>

<script>
  // 导航折叠
  document.querySelectorAll('.nav-group-title').forEach(title => {
    title.addEventListener('click', () => {
      title.classList.toggle('collapsed');
      const items = title.nextElementSibling;
      items.style.display = title.classList.contains('collapsed') ? 'none' : '';
    });
  });

  // 接口展开/折叠
  document.querySelectorAll('.api-header').forEach(header => {
    header.addEventListener('click', () => {
      const body = header.nextElementSibling;
      const toggle = header.querySelector('.api-toggle');
      body.classList.toggle('open');
      toggle.classList.toggle('open');
    });
  });

  // 导航点击高亮 + 滚动
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const target = document.getElementById(item.dataset.target);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // 自动展开
        const body = target.querySelector('.api-body');
        const toggle = target.querySelector('.api-toggle');
        if (body && !body.classList.contains('open')) {
          body.classList.add('open');
          toggle && toggle.classList.add('open');
        }
      }
    });
  });

  // 代码 tab 切换
  document.querySelectorAll('.code-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const group = tab.closest('.code-group');
      group.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
      group.querySelectorAll('.code-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      group.querySelector('#' + tab.dataset.panel).classList.add('active');
    });
  });

  // 滚动时自动高亮导航
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        document.querySelectorAll('.nav-item').forEach(item => {
          item.classList.toggle('active', item.dataset.target === id);
        });
      }
    });
  }, { threshold: 0.3 });
  document.querySelectorAll('.api-card').forEach(card => observer.observe(card));
</script>
</body>
</html>
```

## NAV_ITEMS 生成规则

每个模块生成一个 `nav-group`，模块下每个接口生成一个 `nav-item`：

```html
<div class="nav-group">
  <div class="nav-group-title">
    <span>用户模块</span>
    <span class="arrow">▼</span>
  </div>
  <div class="nav-group-items">
    <div class="nav-item" data-target="api-1-1">
      <span class="nav-item-badge" style="background:#49cc90">POST</span>
      <span class="nav-item-name">用户登录</span>
    </div>
  </div>
</div>
```

## CONTENT_SECTIONS 生成规则

每个模块生成一个 `module-section`，每个接口生成一个 `api-card`：

```html
<section class="module-section">
  <h2 class="module-title">用户模块</h2>

  <div class="api-card" id="api-1-1">
    <div class="api-header">
      <span class="method-badge" style="background:#49cc90">POST</span>
      <span class="api-path">/api/user/login</span>
      <span class="api-name">用户登录</span>
      <span class="api-toggle">▼</span>
    </div>
    <div class="api-body">
      <p class="api-desc">用户通过账号密码登录，返回 token 和用户信息</p>

      <div class="section-title">请求参数</div>
      <table class="param-table">
        <thead>
          <tr><th>参数名称</th><th>参数说明</th><th>类型</th><th>必填</th><th>取值范围</th><th>示例值</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="param-name">account</span></td>
            <td>登录账号</td>
            <td><span class="param-type">string</span></td>
            <td><span class="required-yes">是</span></td>
            <td>-</td>
            <td>jack123</td>
          </tr>
        </tbody>
      </table>

      <div class="section-title" style="margin-top:20px">请求 / 响应示例</div>
      <div class="code-group">
        <div class="code-tabs">
          <div class="code-tab active" data-panel="req-api-1-1">请求示例</div>
          <div class="code-tab" data-panel="res-ok-api-1-1">成功响应</div>
          <div class="code-tab" data-panel="res-err-api-1-1">失败响应</div>
        </div>
        <div class="code-panel active" id="req-api-1-1">
          <div class="code-block">{
  "account": "jack123",
  "password": "Jack@123456"
}</div>
        </div>
        <div class="code-panel" id="res-ok-api-1-1">
          <div class="code-block">{
  "code": 200,
  "msg": "登录成功",
  "data": { "token": "eyJhbGci..." }
}</div>
        </div>
        <div class="code-panel" id="res-err-api-1-1">
          <div class="code-block">{
  "code": 401,
  "msg": "密码错误",
  "data": null
}</div>
        </div>
      </div>

      <div class="section-title">响应参数</div>
      <table class="param-table">
        <thead>
          <tr><th>参数名称</th><th>参数说明</th><th>类型</th><th>必返</th><th>示例值</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="param-name">code</span></td>
            <td>响应码</td>
            <td><span class="param-type">int</span></td>
            <td><span class="required-yes">是</span></td>
            <td>200</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</section>
```

## 注意事项

- GET 接口没有请求体时，请求示例 tab 改为显示 URL，如 `GET /api/user/info?userId=10001`
- 代码块中的 JSON 要格式化缩进，不要压缩成一行
- 每个 `code-panel` 的 id 要唯一，建议用 `req-{api-id}`、`res-ok-{api-id}`、`res-err-{api-id}` 格式
- 单文件时 `module-title` 可省略，直接列 `api-card`
