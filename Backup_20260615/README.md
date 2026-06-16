# 用友雲 Teams App - 部署指南

## 📁 文件清單

```
TeamsApp/
├── manifest.json      ← Teams App 配置（需替換 ${TEAMS_APP_ID} 和 ${TAB_URL}）
├── index.html          ← 中間頁（iframe 載入用友雲）
├── color.png           ← App 圖標（彩色 96×96）
├── outline.png         ← App 圖標（白色透明 32×32）
└── README.md           ← 本文件
```

---

## 🔧 第一步：準備圖標

### 圖標 A：從用友雲官網取得 Logo
1. 開啟 https://c2.yonyoucloud.com/
2. 按 F12 → 選取左上角的用友 Logo 圖片
3. 右鍵另存為 → 保存為 `color.png`

### 圖標 B：建立 outline 版本（白色透明背景）
用任何圖片編輯工具將 Logo 轉為白色 + 透明背景，尺寸 32×32，保存為 `outline.png`

如沒有工具，紫龍可協助用 Python 生成。

---

## 🔧 第二步：部署到 Azure Static Web Apps

### 方法 1：Azure Portal（GUI）
1. 登入 https://portal.azure.com/
2. 搜尋 **Static Web Apps** → **建立**
3. Source: GitHub / Other
4. 區域選擇離您最近的（East Asia）
5. 上傳 `index.html` 文件
6. 部署完成後會得到一個 URL，例如：`https://yonyou-teams-app.azurestaticapps.net`

### 方法 2：Azure CLI
```powershell
# 安裝 Azure CLI（如未安裝）
winget install Microsoft.AzureCLI

# 登入
az login

# 建立 Static Web App
az staticwebapp create \
  --name yonyou-teams-app \
  --resource-group YourResourceGroup \
  --source . \
  --location eastasia \
  --branch main
```

### 方法 3：最簡單 — 直接上傳到 GitHub Pages
1. 建立 GitHub repo
2. 上傳 index.html
3. 設定 GitHub Pages → 得到 `https://yourname.github.io/yonyou-teams-app/`

---

## 🔧 第三步：更新 manifest.json

將部署後的 URL 填入 manifest.json：

1. 生成 App ID：
```powershell
# PowerShell 生成 GUID
[guid]::NewGuid().ToString()
```

2. 替換 manifest.json 中的兩個佔位符：
   - `${TEAMS_APP_ID}` → 替換為上一步生成的 GUID
   - `${TAB_URL}` → 替換為部署後的 URL，例如 `https://yonyou-teams-app.azurestaticapps.net/index.html`

---

## 🔧 第四步：上傳到 Teams

### 方法 1：Teams Developer Portal
1. 打開 Teams → **Apps** → **Manage your apps** → **New app**
2. 上傳 manifest.json 和圖標
3. 點擊 **Preview in Teams** 測試

### 方法 2：Teams Admin Center（組織部署）
1. 登入 https://admin.teams.microsoft.com/
2. **Apps** → **Manage apps** → **Upload an app**
3. 選擇 manifest.json（需打包成 .zip）
4. 部署給全公司或指定用戶

### 打包成 .zip
```powershell
Compress-Archive -Path C:\QClaw_Backup\TeamsApp\* -DestinationPath C:\QClaw_Backup\TeamsApp\yonyou-teams-app.zip
```

---

## ⚠️ 注意事項

1. 用友雲目前未設置 iframe 限制（已驗證），但如果未來用友更新了安全策略，iframe 可能失效
2. 用戶首次使用需要手動登入用友雲帳號
3. 如果用友雲的 Session 過期，iframe 中的頁面可能需要重新登入
4. 建議先部署測試，確認 iframe 正常載入後再推廣到全公司
