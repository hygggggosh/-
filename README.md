# Hermes Chat

KivyMD Android 客户端，对接本机 Hermes Gateway（`http://127.0.0.1:8642`）。

## 桌面预览（Termux）

```bash
pip install kivy kivymd requests
python3 main.py
```

## 打包 APK

本项目用 GitHub Actions 云端构建，**不要在 Termux 本地交叉编译**（要下 ~2GB SDK/NDK，跑不动）。

### 用法

1. 把代码 push 到 GitHub
2. 进仓库 → Actions → Build Android APK → Run workflow
3. 等 ~10-15 分钟（首次更久，要下 SDK/NDK/Gradle）
4. 在 workflow run 页面底部 Artifacts 下载 `hermeschat-debug-apk`

### 配置

`buildozer.spec` 已设：
- `package.name = hermeschat`
- `package.domain = com.hermes`
- `android.api = 33`
- `requirements = python3,kivy,kivymd,requests`
- `android.permissions = INTERNET`

`main.py` 里写死了 `HERMES_API` 和 `API_KEY`，要改的话改完再 push。

## 触发条件

- push 到 `main` 改 `main.py` / `buildozer.spec` / workflow 文件 → 自动构建
- 其他情况 → Actions 页面手动 Run workflow