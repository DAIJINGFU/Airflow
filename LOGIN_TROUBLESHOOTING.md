# Airflow 3.1.3 登录问题排查与解决方案

## ✅ API 认证测试结果（已验证成功）

### 测试 1: Token 获取

```powershell
$body = @{username='admin'; password='SNZ5mDTmNdBDT2bS'} | ConvertTo-Json
$response = Invoke-WebRequest -Uri 'http://localhost:8080/auth/token' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing
```

**结果**: ✅ 201 Created - Token 获取成功

### 测试 2: 使用 Token 访问 UI

```powershell
$headers = @{Authorization = "Bearer <token>"}
$response = Invoke-WebRequest -Uri 'http://localhost:8080/ui/config' -Headers $headers -UseBasicParsing
```

**结果**: ✅ 200 OK - 认证完全正常

## 🔍 浏览器登录失败的可能原因

### 问题 1: 浏览器缓存了旧的认证信息

**症状**:

- API 测试成功
- 浏览器登录失败（401 Unauthorized）
- 日志显示 "JWT token is not valid: Signature verification failed"

**原因**:
浏览器可能缓存了之前的 token 或 session，而这些旧凭据与当前的 secret_key 不匹配

### 问题 2: 浏览器 Cookie/Session 问题

**症状**: POST /auth/token 返回 201，但后续请求返回 403

**原因**: 浏览器存储的旧 session cookie 与新的 secret_key 冲突

## 💡 解决方案（按优先级）

### 方案 1: 清除浏览器缓存和 Cookie（推荐）⭐

1. 打开浏览器开发者工具（F12）
2. 进入 Application/应用程序 标签
3. 清除 localhost:8080 的所有 Cookie 和 Storage
4. 或者直接使用 **隐私/无痕模式** 访问 http://localhost:8080

### 方案 2: 硬刷新页面

- Windows: `Ctrl + F5` 或 `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

### 方案 3: 使用其他浏览器

如果 Chrome 有问题，尝试使用 Edge、Firefox 等其他浏览器

### 方案 4: 重启容器清除所有状态（最后手段）

```powershell
docker compose -f docker-compose-standalone.yml down
docker compose -f docker-compose-standalone.yml up -d
# 重新获取新密码
docker logs airflow_new-airflow-standalone-1 2>&1 | Select-String "Password for user"
```

## 📝 当前验证的登录凭据

**用户名**: `admin`  
**密码**: `SNZ5mDTmNdBDT2bS`  
**URL**: http://localhost:8080

**状态**: ✅ API 测试完全正常，问题出在浏览器端

## 🧪 验证步骤

1. ✅ 容器运行正常
2. ✅ 密码文件存在且正确: `/opt/airflow/simple_auth_manager_passwords.json.generated`
3. ✅ API Token 获取成功（201 Created）
4. ✅ 使用 Token 访问 UI 配置成功（200 OK）
5. ⚠️ 浏览器登录待用户验证

## 🎯 下一步操作

**请使用以下任一方式测试登录**:

1. **推荐方式**: 使用浏览器隐私模式/无痕模式访问 http://localhost:8080
2. **备选方式**: 清除浏览器的 localhost:8080 缓存和 Cookie 后重试

如果以上方式都失败，请告知具体的错误信息（最好提供浏览器开发者工具 Console 和 Network 面板的截图）。
