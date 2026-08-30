# xhs-minitool-maker · 小红书互动小工具制作 Skill

把「文化选题」做成「小红书可扫码把玩的互动 H5 小工具」的全流程 Agent Skill。

已验证案例：古风男装《腰间两千年》（腰带 EDC 主线 + 12 节点时间轴 + 对比墙 + 3D 试穿间）。

## 它能做什么

覆盖从一个选题到小红书发布的六个阶段：

1. **话题构思** — 「小物件切入公式」：小物件主线 → 形态迁移线 → 古今功能对照 → 受众视角钩子
2. **资料收集** — 年代、馆藏、形制、冷知识；信源可追溯，AI 图必标注
3. **AI 生图** — 历代对比墙、穿越同框、文物风格化渲染、封面底图（含提示词配方）
4. **AI 3D 模型** — AI 生图 → Meshy 图生 3D → GLB 压缩 → base64 内嵌（含完整抓包与压缩管线）
5. **H5 开发/校验/打包** — 纯离线包，zip ≤ 30MB，禁止网络请求，二进制转 base64 内嵌，含容器兼容性踩坑与兜底方案
6. **发布物料** — 标题、14 字描述、3:4 封面、1:1 图标、发布文案

## 目录结构

```
xhs-minitool-maker/
├── SKILL.md                      # 主入口：六阶段流程 + 三条铁律
├── references/
│   ├── topic-playbook.md         # 选题公式、已验证选题库、外国文化拓展
│   ├── image-prompts.md          # AI 生图提示词配方与封面排版纪律
│   ├── ai-3d-pipeline.md         # Meshy 图生 3D 全流程（安装/积分/抓包/压缩/兜底）
│   ├── minitool-spec.md          # 小红书小工具容器规范与兼容性踩坑
│   └── publish-kit.md            # 发布物料规格与已验证文案结构
├── scripts/
│   ├── pack_minitool.sh          # 小工具打包脚本
│   └── render_turntable.py       # 转台渲染驱动脚本（3D 兜底方案）
└── assets/
    └── render_turntable.html     # 转台渲染模板
```

## 安装

把整个文件夹复制到 Kimi Work 的 skills 目录即可：

```bash
cp -r xhs-minitool-maker \
  "$HOME/Library/Application Support/kimi-desktop/daimon-share/daimon/skills/"
```

重启或刷新会话后，跟 Kimi 说「我要做一个小红书小工具」即可触发。

## 三条铁律（来自实战踩坑）

1. **规范显式注入**：动手前先把平台规范文档拿到手并通读，不凭记忆假设容器能力
2. **品味与验收属于人**：切入点、视觉方向、真机验收由人拍板，每阶段产出可验收的产物
3. **永远准备兜底形态**：容器限制多，任何高级能力（3D、贴图、网络）都要有降级方案

## License

MIT
