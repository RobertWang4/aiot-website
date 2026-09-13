# AIoT P.S.A. 官网

Astro 5 + Tailwind v4 静态站，内容全部来自 `src/content/` 下的 JSON。改 JSON → `npm run build` → 部署 `dist/`。

## 常用命令

```bash
npm install        # 首次
npm run dev        # 本地预览 http://localhost:4321
npm run build      # 生成 dist/
npm run preview    # 预览 dist/
npm run scrape     # 重新从 recon.org.pl 抓取内容（一次性迁移工具，正常不需要再跑）
```

## 内容结构

```
src/content/
  site.json                 品牌名、logo、联系方式、社交链接、两种语言的导航
  pl/ en/                   两种语言结构完全相同
    home.json               首页：hero / asia / services.cards / maturity / noBlame / closing
    about.json              关于：blocks[]
    services.json           服务分类索引：10 个分类 → 服务 id 列表
    services-page.json      服务总览页文案：blocks[]
    services/<id>.json      每个服务详情页：title / description / blocks[]
                            （分类页 /services/c/<分类id>/ 和安全文化页 /safety-culture/ 由 services.json 与 home.json 自动生成）
    gallery.json            画廊：blocks[] 里的 image
    clients.json            客户 logo：blocks[] 里的 image
    contact.json            联系页文案：blocks[]
public/img/                 图片；logo.jpg 是站点 logo
```

`blocks[]` 支持 5 种块：

```json
{ "type": "heading", "level": 2, "eyebrow": "小标签(可选)", "text": "标题" }
{ "type": "paragraph", "text": "段落" }
{ "type": "list", "ordered": false, "items": ["a", "b"] }
{ "type": "image", "src": "/img/xxx.jpg", "alt": "" }
{ "type": "cta", "label": "按钮文字", "href": "/en/contact/" }
```

## 常见改动

- **换公司信息**：改 `site.json` 的 `brand`、`contact`；logo 替换 `public/img/logo.jpg`。
- **改首页文案**：改 `pl/home.json` 和 `en/home.json` 对应字段。
- **新增一个服务**：在 `pl/services/` 和 `en/services/` 各加一个 `<id>.json`（`hasPage: true`），再把 `<id>` 加进两种语言 `services.json` 对应分类的 `services` 数组。id 两种语言必须相同。
- **删服务**：从 `services.json` 数组里移除 id 即可（文件可留着）。
- **换图片**：把新图放到 `public/img/`，改 JSON 里的 `src`。

所有 JSON 在构建时用 zod 校验（`src/lib/content.ts`），字段写错会直接报错并指出文件。

## 部署

已接 GitHub Pages：推送到 `main` 自动构建发布到 https://robertwang4.github.io/aiot-website/ （工作流在 `.github/workflows/deploy.yml`，子路径由 `astro.config.mjs` 里的 `BASE_PATH` 处理）。

换其他托管也可以，`dist/` 是纯静态：

- **Vercel / Netlify**：导入仓库，框架选 Astro，构建命令 `npm run build`，输出目录 `dist`。
- **Cloudflare Pages**：同上。
- 部署前把 `astro.config.mjs` 里的 `site` 改成正式域名（影响 sitemap 和 hreflang）。

## 目录说明

- `scripts/scrape.py` + `scripts/scrape-report.md`：从源站抓取内容的脚本和报告。
- `demo/`：选型阶段的 4 个风格 demo（industrial / dark-tech / saas / immersive），仅供参考，正式站是白色简约风。
