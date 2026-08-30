#!/usr/bin/env python3
"""24 帧转台渲染驱动：通过 Kimi WebBridge daemon 驱动浏览器里的
render_turntable.html（见 skill assets/），把 AI 3D 模型逐帧渲染成 JPEG，
作为小红书容器内实时 3D 失败时的帧动画兜底。

前置：
1. WebBridge 已安装（Chrome 扩展 + Kimi 客户端运行，daemon 在 127.0.0.1:10086）
2. 渲染页可通过 http 访问（file:// 不允许 navigate）：
   在项目根起 python3 -m http.server <port>，用完必须 kill

用法：
  python3 render_turntable.py --url http://127.0.0.1:8123/path/render_turntable.html \
      --out <输出目录> --frames 24 --session my-session
"""
import argparse, base64, json, subprocess, sys, math, os, time

def cmd(payload):
    out = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://127.0.0.1:10086/command",
         "-H", "Content-Type: application/json", "-d", json.dumps(payload)],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    if not d.get("ok"):
        raise RuntimeError(d.get("error"))
    return d["data"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="渲染页 http URL")
    ap.add_argument("--out", required=True, help="帧输出目录")
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--session", default="turntable-render")
    ap.add_argument("--wait", type=float, default=6.0, help="navigate 后等待模型加载秒数")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    cmd({"session": a.session, "action": "navigate", "url": a.url})
    time.sleep(a.wait)
    st = cmd({"session": a.session, "action": "evaluate",
              "code": 'window.renderReady ? "ready" : (window.renderError || "loading")'})
    if st.get("value") != "ready":
        print("渲染页未就绪:", st.get("value"), file=sys.stderr)
        sys.exit(1)

    for i in range(a.frames):
        ang = i * math.pi * 2 / a.frames
        d = cmd({"session": a.session, "action": "evaluate",
                 "code": f"window.renderFrame({ang:.6f})"})
        v = d.get("value", "")
        if not v.startswith("data:"):
            print(f"帧 {i} 失败: {v}", file=sys.stderr)
            sys.exit(1)
        b64 = v.split(",", 1)[1]
        name = os.path.join(a.out, f"f{i:02d}.jpg")
        open(name, "wb").write(base64.b64decode(b64))
        print(f"帧 {i}: {len(b64)//1024} KB")
    print(f"完成：{a.frames} 帧 → {a.out}")

if __name__ == "__main__":
    main()
