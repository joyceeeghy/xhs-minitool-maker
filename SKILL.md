---
name: xhs-minitool-maker
description: 小红书互动小工具内容的全流程制作技能。覆盖六个阶段——话题构思（古风历史向已验证，可拓展到外国文化或任何文化主题）、史料/资料收集、AI 生图（博物馆风对比墙、穿越同框、封面排版）、AI 3D 模型（Meshy 图生 3D + 浏览器自动化驱动真实浏览器）、小红书小工具 H5 开发/校验/打包（30MB 纯离线包规范与容器兼容兜底）、发布物料（标题、14 字描述、3:4 封面、1:1 图标）。当用户要做小红书小工具/小程序内容、可交互的文化科普 H5、古风/历史/外国文化主题互动页面、把选题做成「可玩可扫码」的工具，或需要文物风 AI 生图与 AI 3D 模型嵌入网页时使用。Agent 通用，遵循 agentskills.io 的 SKILL.md 规范。
---

# 小红书互动小工具 · 全流程制作

把「文化选题」做成「小红书可扫码把玩的互动 H5 小工具」。已验证案例：古风男装《腰间两千年》（腰带 EDC 主线 + 12 节点时间轴 + 对比墙 + 3D 试穿间）。

## 运行环境要求（Agent 通用）

本 skill 遵循 agentskills.io 的 SKILL.md 规范，可装入任何支持该规范的 Agent（Claude Code、Codex、Kimi Work、Cursor 等）。运行时需要宿主 Agent 具备以下**能力**（不绑定具体产品）：

| 能力 | 用途 | 实现举例 |
|---|---|---|
| 文件读写 + 命令执行 | 开发、打包、Pillow 排版 | 各 Agent 自带 |
| AI 生图 | 对比墙/同框/封面底图 | 生图插件、MCP 生图工具、或任何文生图 API |
| 浏览器自动化 | 驱动**用户登录态的真实浏览器**（Meshy 建模/抓包、截图自检） | Kimi WebBridge、Playwright MCP、Chrome DevTools MCP、browser-use 等任一 |
| Python 3 + Pillow | 封面排版、图片压缩 | 系统 Python 即可 |

若某能力缺失：阶段三/四可跳过或用兜底方案（如 2D 纯 CSS 小工具、程序化建模），skill 其余阶段不受影响。

## 三条铁律（来自实战踩坑）

1. **规范显式注入**：动手前先把平台规范文档/skill 拿到手并通读（小红书小工具规范见下「阶段五」），不要凭记忆假设容器能力。
2. **品味与验收属于人**：切入点选择、视觉方向、真机验收由用户拍板；每个阶段结束给出可验收的产物（文档/图/截图/二维码）。
3. **永远准备兜底形态**：小红书容器限制多，任何「高级能力」（3D、贴图、网络）都要有降级方案，且降级后内容依然成立。

## 六阶段流程

### 阶段一：话题构思
用「小物件切入公式」：选一个身上/手边的**小物件**做主线 → 拉出**形态迁移线**（历代形态）→ 做**古今功能对照** → 接一个**目标受众视角钩子**（对研发讲系统工程/权限编码/EDC，对女性用户讲妆容/香囊/穿搭……）。
详细公式、已验证选题库、外国文化拓展框架见 [references/topic-playbook.md](references/topic-playbook.md)。
**产出**：完整大纲文档（主线 + 支线 + 每节史料要点 + 金句），存工作区。

### 阶段二：资料收集
- 每个物件收集：年代、出土地/馆藏、形制要点、1 个冷知识或故事（钩子用）。
- 信源纪律：事实性内容须可追溯；AI 生成的「文物图」必须标注 AI 生成，不冒充真文物。
- 收集真实文物/实物参考图（供 AI 生图垫图与 3D 建模参考）。

### 阶段三：AI 生图
用任一 AI 生图能力（插件/MCP/API）批量生成：历代形态对比墙、穿越时空同框、文物风格化渲染、封面底图。
提示词配方、参数、封面文字排版纪律（图内不生成正文文字，用 Pillow 后期排版）见 [references/image-prompts.md](references/image-prompts.md)。
**验收**：逐张目检；改字不重 P，整图重生成。

### 阶段四：AI 3D 模型（可选但强烈推荐）
不要白模。流程：AI 生成正面全身图 → Meshy 图生 3D → 文本贴图 → 抓包下载 GLB → 压缩到 ~1.6MB → base64 内嵌。
Meshy 无公开下载入口，必须用浏览器自动化能力驱动**用户自己登录态的真实浏览器**完成（Kimi WebBridge / Playwright MCP / Chrome DevTools MCP 等任一）。安装方法、积分开销、抓包方法、压缩命令、兜底方案（24 帧转台）全部见 [references/ai-3d-pipeline.md](references/ai-3d-pipeline.md)；渲染模板在 [assets/render_turntable.html](assets/render_turntable.html)，驱动脚本在 [scripts/render_turntable.py](scripts/render_turntable.py)。

### 阶段五：小工具开发、校验与打包
- 形态：纯离线 H5（index.html + assets），three.js r128 + OrbitControls 本地化，全部资源进包。
- 硬约束：zip ≤ 30MB；**禁止网络请求**（fetch/XHR 需打离线补丁）；**.glb 等二进制扩展名被禁**（转 base64 内嵌 .js）。
- 容器兼容性实测踩坑与兜底（fetch(blob:) 被拦、贴图通道、帧动画回退）见 [references/minitool-spec.md](references/minitool-spec.md)。
- 打包用 [scripts/pack_minitool.sh](scripts/pack_minitool.sh)；按 minitool-zip-builder skill 校验（获取方式见 minitool-spec.md）。
- 验收双通道：本地 http.server + 浏览器自动化截图自检 → 用户手机扫码实测。加版本标记（如 v2.3）确认用户扫的是新包。

### 阶段六：发布物料
小红书所需：标题、≤14 字描述、3:4 PNG 封面、1:1 ≤5MB PNG 工具图标、发布文案。
规格与已验证文案结构见 [references/publish-kit.md](references/publish-kit.md)。

## 协作模式建议

- 用户给方向（主题 + 切入点偏好）后，先出大纲再动手做物料；不要跳过阶段一直接做图。
- 用户「放手」授权后（如睡觉离开），按阶段顺序自主推进，每阶段留痕（产物 + 过程截图存 `过程截图/`）。
- 全程产物归档到一个项目文件夹（大纲、参考图、模型、截图、发布物料、历史版本）。
- 结束后主动沉淀：把新的踩坑/配方补进本 skill 的 references（迭代入口）。
