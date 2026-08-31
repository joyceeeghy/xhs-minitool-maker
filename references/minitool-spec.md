# 小红书小工具：容器规范、踩坑表与打包

## 硬约束

- zip 包 ≤ **30MB**；入口 `index.html` 在 zip 根级；所有资源相对路径入包。
- **纯离线**：禁止任何网络请求（fetch/XHR/外链 CDN/外链字体图片）。第三方库（three.js 等）必须下载进 `assets/vendor/`。
- **扩展名黑名单**：`.glb` 等二进制模型文件不允许 → 转 base64 内嵌为 `.js`。
- CSP 严格：`blob:`/`data:` 的 fetch 会被拦（详见踩坑 #12）。

## 校验 skill：minitool-zip-builder

平台官方打包规范 skill，开工前下载通读，交付前按它自检：

```
https://fe-static.xhscdn.com/mini-tool/1.4.1/minitool-zip-builder.zip
```

解压后读 SKILL.md（Cursor/Claude Code → `.claude/`，Codex → `.codex/`，其余 → `.skill/`），按其指引校验、修复、打包。

## 推荐结构

```
minitool/
├── index.html            # 单页：时间轴 + 对比墙 + 3D 试穿间 + 番外同框
└── assets/
    ├── vendor/           # three.min.js r128 + GLTFLoader.js + OrbitControls.js + offline-shim.js
    ├── data.js           # 时间轴/对比墙内容数据
    ├── main.js           # 页面逻辑
    ├── viewer3d.js       # 3D 试穿间（程序化造型 + AI 模型 + 帧动画兜底）
    ├── shenyi-glb.js     # base64 内嵌模型（window.SHENYI_GLB_B64）
    ├── turntable/        # 24 帧兜底图 f00.jpg..f23.jpg
    └── images/           # AI 生图（对比墙、同框等，JPEG 1200×800）
```

## 踩坑表（实战中修过的，新的坑请追加）

| # | 坑 | 解法 |
|---|---|---|
| 1 | 容器禁 .glb 文件 | GLB → base64 → 内嵌 .js，atob 解码 + GLTFLoader.parse |
| 2 | 容器禁 fetch/XHR，three.js FileLoader 报错 | 字节级补丁 three.min.js 断网化（仅放行 blob:/data:） |
| 3 | Meshy 图生贴图失败 | 改文本描述贴图，一次成功 |
| 4 | Meshy 无公开下载 API | 浏览器自动化抓包：拦 XHR 头拿临时 JWT，调内部 tasks 接口 |
| 5 | CDP 文件上传被拦 | fetch 公网图 → Blob → DataTransfer 注入 input |
| 6 | GLB 118MB 超 30MB 限制 | gltf-transform 减面 98% + 贴图 512 → 1.6MB |
| 7 | three r128 不认 WebP 贴图 | 压缩时转 JPEG 贴图 |
| 8 | 断网补丁误伤 blob:/data: 贴图解码 | 补丁放行 blob:/data: 协议 |
| 9 | 桌面端 3D 画布过高裁头 | 容器限宽（如 480px）居中 |
| 10 | 局部 P 图改字痕迹重 | 放弃局部修补，整图 AI 重生成 |
| 11 | 手机端默认显示程序化回退（模具人台） | 默认加载 AI 模型 + 失败回退；真机扫码验收 |
| 12 | 容器拦 fetch(blob:) → GLB 贴图解析 "Load failed" | 强制 GLTFLoader 走 TextureLoader（Image）路径；仍败则 24 帧转台兜底 |
| 13 | 调试信息被静默回退吞掉 | 调试版关闭自动回退，把真实错误文案显示在界面上 + 版本号标记 |

## 打包与验证

```bash
bash scripts/pack_minitool.sh <minitool目录> <输出zip路径>
```

验证双通道：本地 `python3 -m http.server` + 浏览器自动化截图自检 → 用户手机扫码实测。两个阶段都要留截图存档。

### 2026-08-25 追加（批量 AI 真人模型战役）

| # | 坑 | 解法 |
|---|---|---|
| 14 | Meshy UI 上传后预览不显示、DataTransfer 注入时灵时不灵 | 放弃 UI 流程，全 API 驱动：`POST /meshyd-api/web/v1/files/images?skipNameGeneration`（FormData，Bearer 头）→ 拿 imageId/url；`POST /meshyd-api/web/v2/tasks` 建任务（mode/phase=draft 图生 3D；mode/phase=texture + parent=草稿ID + args.texture.prompt/artStyle 贴图）；`GET /meshyd-api/web/v2/tasks/{id}` 轮询 |
| 15 | Meshy Bearer token 获取与过期 | cookie `sb-auth-auth-token.0`+`.1` 拼接 → 去 `base64-` 前缀 → atob → JSON 取 access_token；401 时重新 navigate 页面刷新 cookie 再取 |
| 16 | 下载 GLB：.meshy 是私有容器非 zip；UI 下载按钮合成点击坐标会变 | 点卡片开详情 → 底栏绿色下载按钮（用 elementsFromPoint 按视口比例定位，勿写死）→ 面板「下载」；文件落到 ~/Downloads；shell 直连 api.meshy.ai 不通时需 `--proxy http://127.0.0.1:7897`（系统代理） |
| 17 | Meshy 模型在 three.js 里发黑 | PBR 材质 metalness 高 + 无环境贴图：traverse 置 metalness=0、roughness≥0.6，并加 HemisphereLight + 正面补光 |
| 18 | gltf-transform optimize 减面不达标 | 默认 simplify-error 阈值太小，减不动；需再跑 `simplify --ratio 0.02 --error 0.01`（118MB→313KB~1.9MB） |
| 19 | 浏览器缓存旧渲染页导致改了不生效 | http.server 渲染页 URL 加 `?t=$(date +%s)` 时间戳 |
| 20 | render_turntable.html 原来写死单个模型 | 已参数化：`?js=<glb.js路径>&var=<window变量名>` |

相关脚本沉淀：`脚本/wb_upload_api.py`（分块注入+API 上传拿 url）、渲染页参数化版 `脚本/render_turntable.html`。

### 2026-08-29 追加（一枕入梦 · 纯 2D 梦境小工具）

| # | 坑 | 解法 |
|---|---|---|
| 21 | 官方 zip-artifact-spec 的体积上限是 **10MB（建议 <2MB）**，比本文开头的 30MB 更严；以官方文档为准 | AI 生图 PNG 一律转 JPEG（宽 1200、q80、progressive），11 张图从 25MB 压到 1.4MB |
| 22 | AI 生成的「透明底」素材 PNG 背景有噪点/暗斑，直接叠加会脏 | Pillow 二次清理：`alpha<60 → 0` 且按颜色阈值（如金鱼 r≥150 且 g≥110）过滤暗斑，再裁 bbox 缩到 420px 宽做精灵图 |
| 23 | `position:fixed` 的全屏装饰元素（金鱼）会盖住卡片文字 | 装饰层 z-index 放内容层之下（内容 z2、装饰 z1），半透明卡片透出微光反而更梦幻 |
| 24 | 纯 2D 页面无需 three.js 也完全成立 | 梦境漫游=纵向滚动卡片 + IntersectionObserver 渐现 + CSS keyframes 游鱼 + SVG feTurbulence data:URI 颗粒层（CSP 允许 data: 图片） |

### 2026-08-30 追加（人与海的四千年 · 三叉戟小工具）

| # | 坑 | 解法 |
|---|---|---|
| 28 | Meshy 改版：`/zh/app` 路由 404（重定向循环） | 新工作台在 `/zh/workspace`；`/meshyd-api/*` 内部 API 不受影响，全 API 驱动流程照旧 |
| 29 | UI 下载 GLB 时误点卡片悬浮「下载」图标（60×24 小按钮），面板未开 | 先点底栏绿色下载按钮开面板，再按 innerText=「下载」+宽度最大的按钮定位面板内绿色下载条 |
| 30 | gltf-transform CLI `--texture-compress` 不收 jpeg（只有 ktx2/webp/avif/auto/false）；PNG 贴图 512 压不动（4.4MB） | 用 Node API：`textureCompress({encoder:sharp, targetFormat:'jpeg', quality:78, resize:[512,512]})` + `simplify --ratio 0.02 --error 0.01` → 119MB→652KB，JPEG 贴图 r128 兼容 |
| 31 | `new THREE.OrbitControls(opts)` 传参错误 | r128 签名是 `(camera, domElement)`，配置项逐个赋值 |
| 32 | 本地 http.server 端口被旧项目残留占用，新目录 404 | 换端口前先 `kill $(lsof -ti:<端口>)`；自检用 `?shot=1&t=时间戳` 防缓存 |

### 2026-08-30 追加（一秒两千年 · 时间精度小工具）

| # | 坑 | 解法 |
|---|---|---|
| 25 | headless Chrome 自检截图不响应 `#anchor` 滚动，分节截图全黑（panel 渐现 opacity:0 未触发） | 页面内置 `?shot=1` 自检模式：强制全部 panel 加 visible + hero 限高，再整页大窗口截图 |
| 26 | 部分生图工具 2K 不透明底只支持 1:1 / 16:9 | 竖版封面 2:3 用 1K 生成，Pillow LANCZOS 放大到 1024×1536 后排字 |
| 27 | 简单几何文物（日晷）不必走 Meshy；three.js 程序化建模 + CanvasTexture 画十二时辰盘，全离线零抓包 | 注意 CylinderGeometry 材质数组顺序 [侧,顶,底]，贴图面法线必须朝向镜头侧（dialGroup.rotation.x 符号决定看到的是字盘面还是空白背面） |
