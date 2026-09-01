# AI 3D 模型管线（Meshy + 浏览器自动化）

## 为什么需要浏览器自动化

Meshy（及多数网页 3D 工具）没有公开下载 API，且浏览器的程序化文件上传会被 CDP 拦截。因此需要一种「浏览器自动化能力」，让 AI 驱动**用户自己登录态下的真实浏览器**：点击、上传、抓包、截图。这是整个 3D 管线的前提。

**任何满足这个条件的实现都可以**，按 Agent 环境任选：

| 实现 | 适用环境 | 特点 |
|---|---|---|
| Kimi WebBridge | Kimi Work | 本地 HTTP daemon（`127.0.0.1:10086`），curl 直调，本文流程即以它为参考实现 |
| Playwright MCP | Claude Code / Codex 等 | 用 `channel:"chrome"` + 持久化用户 profile 复用登录态 |
| Chrome DevTools MCP | Claude Code / Codex 等 | 接管已打开的 Chrome，天然带用户登录态 |
| browser-use 等 | 通用 | 注意配置持久化 profile 目录 |

下文以 WebBridge 协议为例；换其他实现时，把「navigate / evaluate / screenshot / 点击坐标」映射到等价动作即可，流程步骤不变。

### 参考实现：Kimi WebBridge 安装（3 步）
1. Chrome 应用商店安装 **Kimi WebBridge** 扩展；
2. 保持 Kimi 客户端运行，本地服务自动起在 `127.0.0.1:10086`；
3. 官方介绍：https://www.kimi.com/zh-cn/features/webbridge

### WebBridge 调用要点（curl 直连 daemon；其他实现请映射到等价动作）

```bash
curl -s -X POST http://127.0.0.1:10086/command -H 'Content-Type: application/json' \
  -d '{"session":"<会话名>","action":"<动作>","<参数名>":"<值>"}'
```

- 参数放**顶层**（不是 params 对象）；`navigate` 参数是 `url`，`evaluate` 参数是 `code`，`screenshot` 返回临时文件路径（`data.path`，复制出来用）。
- `file://` 不允许 navigate——本地页面用 `python3 -m http.server` 临时起服务，**用完必须 kill**（`kill $(lsof -ti:<端口>)`）。
- evaluate 返回值在 `data.value`。

## 建模流程（以 Meshy 为例，全 API 驱动）

1. **先生成参考图**：用 AI 生图能力生成「正面全身、A/T pose、服装配饰齐全、纯色背景」的人物/物件图。用户要求不要白模——模型必须穿衣服、带配饰。
2. **取令牌**：从 Meshy 页面 cookie 拼 `sb-auth-auth-token.0`+`.1` → 去 `base64-` 前缀 → atob → JSON 取 `access_token` 作 Bearer；401 就重新 navigate 刷新 cookie 再取。
3. **上传参考图**：`POST /meshyd-api/web/v1/files/images?skipNameGeneration`（FormData，Bearer 头）→ 拿 `result.id` 和签名 `url`。UI 的 DataTransfer 注入时灵时不灵，不要依赖。
4. **建任务**：`POST /meshyd-api/web/v2/tasks`：
   - 图生 3D：`{name, mode:"draft", phase:"draft", args:{draft:{aiModel:"blueberry", modelType:"standard", imageId, imageIds:[id], imageUrls:[url], shouldTransferImageStyle:true, ultraMode:true, multiView:false, symmetryMode:0, license:"private"}}}`
   - 文本贴图（图生贴图失败率高，别用）：`{name, mode:"texture", phase:"texture", parent:<草稿任务ID>, args:{draft:{...同上}, texture:{prompt:<服装细节中文描述>, artStyle:"realistic"}}}`
   - 轮询：`GET /meshyd-api/web/v2/tasks/{id}` 到 `status=SUCCEEDED`。
5. **下载 GLB**：任务结果的 `result.result.texture.modelUrl` 是 `.meshy` 私有容器（非 zip，不可直接用）。GLB 走 UI：点任务卡片 → 底栏绿色下载按钮（坐标按视口比例 `elementsFromPoint` 定位，勿写死）→ 面板选 glb 点「下载」→ 落 `~/Downloads`。shell 直连 api.meshy.ai 不通时加 `--proxy http://127.0.0.1:7897`（系统代理）。
6. **压缩**：`npx @gltf-transform/cli optimize in.glb out.glb --compress false --texture-compress webp --texture-size 512 --simplify-ratio 0.02`，若减不动（默认 error 阈值太小）再补 `simplify --ratio 0.02 --error 0.01`——118MB → 313KB~1.9MB。
7. **材质修黑**：Meshy PBR 材质金属度高，three.js 无环境贴图会渲成黑色剪影——traverse 置 `metalness=0`、`roughness≥0.6`，场景加 HemisphereLight + 正面 DirectionalLight 补光（实时渲染与转台帧渲染都要加）。
8. **内嵌**：小红书容器禁 `.glb` 扩展名 → base64 后包成 `window.XXX_GLB_B64 = "data:model/gltf-binary;base64,…"` 的 .js 文件，运行时 atob 解码 + `GLTFLoader.parse(arrayBuffer)`。

## 容器兼容性兜底（关键踩坑）

小红书容器会拦截 `fetch(blob:)`（报错 "Load failed"），而 three.js r128 GLTFLoader 在有 `createImageBitmap` 的环境默认走 ImageBitmapLoader（内部 fetch blob 贴图）→ 解析必败。两道防线：

1. **强制 TextureLoader 路径**：把 GLTFLoader.js 中 `if ( typeof createImageBitmap !== 'undefined' && … )` 的条件改为 `if ( false )`，贴图改走 `<img>` 元素加载。
2. **24 帧转台兜底**：若 `<img>` 路径仍失败，自动切换到预渲染帧动画——本地用浏览器自动化驱动渲染页逐帧渲染 24 张 JPEG（`assets/render_turntable.html` 模板 + `scripts/render_turntable.py` 驱动，默认走 WebBridge 协议，`--endpoint` 可换其他 daemon），小工具内以「自动旋转 + 拖动转身」的帧动画呈现。24 帧 480×552 JPEG 仅约 200KB。
   - 渲染页已参数化：`render_turntable.html?js=<glb.js路径>&var=<window变量名>`，加 `&t=<时间戳>` 防浏览器缓存旧页面。
   - 每套造型渲一套转台帧（如 `turntable-tang/`），GLB 失败时切到该造型自己的帧动画。
   - 帧动画触发逻辑：parse 失败 → 隐藏 canvas、插入 `<img>` 轮播；保留 DBG 版本标记直到真机验证通过。

## 验收纪律

- 本地 http.server + 浏览器自动化截图确认 AI 模型默认加载（不是程序化回退）。
- **真机扫码验收不可替代**——桌面正常 ≠ 容器正常（本项目唯一的致命 bug 就是用户扫码发现的）。
- 界面留版本号（如 v2.3），确认用户扫的是新包。
