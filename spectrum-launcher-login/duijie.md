

# Spectrum Launcher 正版登录对接详细文档

## 1️⃣ 系统架构概览

```
+-----------------+         HTTP         +--------------------+
| Minecraft       |<------------------->| Flask API          |
| 启动器/模块      |                     | (launcher_login.py)|
+-----------------+                     +--------------------+
          |                                      |
          | PyQt6 GUI (内嵌浏览器)                |
          |                                      |
          v                                      v
   Microsoft 登录页面                         授权码捕获 -> Token 获取
          |
          v
   Xbox Live -> XSTS -> Minecraft Token
```

**组件说明：**

1. **launcher\_login.py**

   * PyQt6 内嵌浏览器完成 Microsoft 登录
   * Flask 提供 HTTP API 接口 (`/get_token`)
   * 自动处理 Microsoft → Xbox Live → XSTS → Minecraft Token

2. **mc\_auth\_api.py**

   * 封装 HTTP 请求，提供对接接口给启动器或其他模块

3. **launcher\_example.py**

   * 对接示例，获取 Minecraft Token 并启动 Minecraft 客户端

---

## 2️⃣ 登录器安装与启动

### 2.1 环境要求

* Python ≥ 3.10
* PyQt6
* PyQt6-WebEngine
* Flask
* requests

安装依赖：

```bash
pip install PyQt6 PyQt6-WebEngine Flask requests
```

### 2.2 启动登录器

```bash
python launcher_login.py
```

* 打开内嵌浏览器窗口
* 用户选择 Microsoft 账号登录
* Flask 监听端口 `54188`，捕获授权码

**注意**：Flask 端口必须与 **Redirect URI** 一致，例如 `http://localhost:54188/callback`

---

## 3️⃣ Flask API 对接接口

| 接口           | 方法  | 参数           | 返回说明                                                                                                         |
| ------------ | --- | ------------ | ------------------------------------------------------------------------------------------------------------ |
| `/callback`  | GET | `code` (授权码) | 登录器内部使用，捕获授权码并调用 Token 流程                                                                                    |
| `/get_token` | GET | 无            | JSON 返回 Minecraft Token，如成功：<br>`json { "minecraft_access_token": "...", "username": "...", "uuid": "..." }` |

---

## 4️⃣ 对接模块

**文件：`mc_auth_api.py`**

```python
import requests

BASE_URL = "http://localhost:54188"

def start_login():
    """
    启动登录器流程并返回登录页面 URL
    """
    try:
        resp = requests.get(f"{BASE_URL}/login")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def get_minecraft_token():
    """
    获取 Minecraft Access Token 和用户信息
    """
    try:
        resp = requests.get(f"{BASE_URL}/get_token")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
```

**对接说明：**

* `start_login()`：获取登录页面 URL，可用于外部模块提示用户登录
* `get_minecraft_token()`：循环调用直到获取 Minecraft Token

---

## 5️⃣ 启动器调用示例

**文件：`launcher_example.py`**

```python
import subprocess
import time
from mc_auth_api import start_login, get_minecraft_token

def main():
    # 1. 启动登录流程
    login_info = start_login()
    if "error" in login_info:
        print("启动登录器失败:", login_info["error"])
        return

    print("请在内嵌浏览器完成 Microsoft 登录")
    print("登录页面 URL:", login_info.get("auth_url"))

    # 2. 等待授权码获取 Minecraft Token
    mc_token = None
    while mc_token is None:
        time.sleep(2)
        mc_token = get_minecraft_token()
        if mc_token.get("error"):
            mc_token = None

    print("=== 登录成功 ===")
    print("用户名:", mc_token["username"])
    print("UUID:", mc_token["uuid"])
    print("Minecraft Access Token:", mc_token["minecraft_access_token"])

    # 3. 启动 Minecraft 客户端
    java_path = "java"  # 可替换为完整 java 路径
    minecraft_jar = "MinecraftLauncher.jar"  # 替换客户端 jar 路径
    args = [
        java_path, "-jar", minecraft_jar,
        "--accessToken", mc_token["minecraft_access_token"],
        "--username", mc_token["username"],
        "--uuid", mc_token["uuid"]
    ]
    subprocess.Popen(args)
    print("Minecraft 客户端已启动")

if __name__ == "__main__":
    main()
```

---

## 6️⃣ 对接流程说明

1. **调用 `start_login()`**

   * 获取 Microsoft 登录页面 URL
   * 打开内嵌浏览器进行登录

2. **完成 Microsoft 登录**

   * Flask 捕获授权码 `code`

3. **获取 Microsoft Token → Xbox Live → XSTS → Minecraft Token**

   * PyQt6 内部完成
   * 状态显示全部文字，自动换行

4. **调用 `get_minecraft_token()`**

   * 循环等待直到返回 `minecraft_access_token`

5. **启动 Minecraft**

   * 使用 `accessToken`、`username`、`uuid` 启动客户端

---

## 7️⃣ 注意事项

1. **端口与 Redirect URI**

   * Flask 监听端口必须和 Microsoft 应用注册的 Redirect URI 一致

2. **Scope 配置**

   ```python
   SCOPES = ["XboxLive.signin","offline_access","user.read"]
   ```

3. **状态显示**

   * PyQt6 GUI 使用 QTextEdit 自动换行显示全部信息
   * 无需固定高度，文字完整显示

4. **多次登录/记住状态**

   * 可缓存 `minecraft_access_token`
   * Token 有效期内可直接启动，无需再次登录

5. **启动参数可扩展**

   * 分辨率、内存、Mod 目录等

---

## 8️⃣ 可扩展功能建议

* **多账号支持**：管理多个 Minecraft 账户
* **自动记住登录状态**：Token 缓存
* **启动器美化**：内嵌浏览器、状态栏、按钮布局自适应
* **错误处理**：捕获登录失败或 Token 无效情况

---

✅ **总结**

* 登录器提供完整 Microsoft → Xbox Live → XSTS → Minecraft 登录流程
* 对接模块通过 HTTP API 获取 Minecraft Token
* 启动器示例展示如何使用 Token 启动 Minecraft 客户端
* 可扩展功能支持多账号、记住登录状态、启动参数优化

