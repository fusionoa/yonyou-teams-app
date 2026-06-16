# Yonyou Cloud Microsoft Teams App
## 安裝與架構手冊

**版本：** 1.0  
**日期：** 2026-06-14  
**作者：** FusionOA IT Team  
**適用對象：** 技術人員、管理層

---

## 一、專案概述

### 1.1 目的

將公司現有的用友雲（YonSuite）ERP 系統嵌入 Microsoft Teams，讓員工無需開啟額外瀏覽器，直接在 Teams 內使用用友雲的費用報銷、採購、財務等功能。

### 1.2 核心需求

| 需求 | 說明 |
|------|------|
| 嵌入用友雲 | 在 Teams Tab 中顯示用友雲頁面 |
| 多端支援 | PC 版和手機版 Teams 均可使用 |
| 零代碼修改 | 不修改用友雲本身，純前端嵌入 |
| 快速部署 | 一次性安裝，全公司即用 |

### 1.3 技術方案

採用 **iframe 嵌入方案（方案 B）**：

- 用友雲無 `X-Frame-Options` 限制，可直接 iframe 嵌入
- 無需 SSO 整合（用友雲登入態在 iframe 內保持）
- 通過中間頁面（index.html）控制 iframe 顯示參數

---

## 二、系統架構

### 2.1 架構圖（文字版）

```
┌─────────────────────────────────────────────────────────┐
│                    使用者端                               │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  PC Teams     │  │  手機 Teams   │                     │
│  └──────┬───────┘  └──────┬───────┘                     │
└─────────┼─────────────────┼─────────────────────────────┘
          │                 │
          ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│              Microsoft Teams 平台                         │
│  ┌─────────────────────────────────────────┐            │
│  │  Yonyou Cloud App (Custom Tab)           │            │
│  │  contentUrl → fbtimesheet.ddns.net/teams│            │
│  └─────────────────────┬───────────────────┘            │
└────────────────────────┼───────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│           內網伺服器 (192.168.99.126)                     │
│  ┌─────────────────────────────────────────┐            │
│  │  Nginx Web Server                         │            │
│  │  Document Root: /var/www/timesheet/      │            │
│  │                                          │            │
│  │  /teams/ → index.html (中間頁面)         │            │
│  │            └── iframe → 用友雲            │            │
│  └─────────────────────────────────────────┘            │
└────────────────────────┼───────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│              用友雲 (YonSuite)                            │
│  https://c2.yonyoucloud.com/                              │
│  - 費用報銷、採購管理、財務管理                         │
│  - 無 X-Frame-Options 限制，允許 iframe 嵌入            │
│  - 登入態由瀏覽器 Cookie 維持                            │
└─────────────────────────────────────────────────────────┘
```

### 2.2 數據流向

```
1. 使用者在 Teams 開啟 "Yonyou Cloud" Tab
2. Teams 載入 contentUrl: https://fbtimesheet.ddns.net/teams/
3. Nginx 返回 index.html（中間頁面）
4. index.html 內的 iframe 載入 https://c2.yonyoucloud.com/
5. 用友雲頁面顯示在 Teams 內
6. 用戶在 iframe 內操作用友雲（報銷、採購等）
```

### 2.3 關鍵組件說明

| 組件 | 位置 | 說明 |
|------|------|------|
| manifest.json | Teams App 定義檔 | 定義 App 名稱、圖標、Tab 配置、權限 |
| index.html | 內網伺服器 `/teams/` | 中間頁面，控制 iframe 顯示 |
| color.png | Teams App 彩色圖標 | 96×96 px |
| outline.png | Teams App 輪廓圖標 | 32×32 px 透明背景 |
| Nginx | 192.168.99.126 | 反向代理 + 靜態檔案伺服器 |
| Teams SDK | CDN 載入 | Microsoft Teams JS SDK v2.0 |

---

## 三、環境要求

### 3.1 基礎設施

| 項目 | 要求 |
|------|------|
| Microsoft 365 帳號 | E3 或以上（支援自訂 App 上傳） |
| Teams 用戶端 | PC 版 / 手機版均可 |
| 內網 Web 伺服器 | Nginx（已運行，192.168.99.126） |
| 用友雲帳號 | 已有 c2.yonyoucloud.com 的登入權限 |
| DDNS 域名 | fbtimesheet.ddns.net（已配置） |
| SSL 憑證 | HTTPS（Let's Encrypt 或自簽） |

### 3.2 網絡要求

```
Teams 用戶端 ──HTTPS──▶ fbtimesheet.ddns.net ──HTTPS──▶ c2.yonyoucloud.com
                       (內網伺服器)                (用友雲)
```

- 內網伺服器需對外可達（DDNS + Port Forwarding）
- 用友雲需從伺服器可訪問

---

## 四、安裝部署

### 4.1 部署中間頁面（一次性）

在內網伺服器 192.168.99.126 上：

```bash
# SSH 登入伺服器
ssh sysadmin@192.168.99.126

# 建立目錄
mkdir -p /var/www/timesheet/frontend/teams/

# 放入檔案（從本地上傳）
# 需要的檔案：index.html
```

或從本地 Windows 上傳：
```powershell
pscp -P 22 -l sysadmin -pw "密碼" index.html 192.168.99.126:/var/www/timesheet/frontend/teams/
```

### 4.2 安裝 Teams App（管理員一次性）

**方式一：Teams Admin Center（推薦，全公司可用）**

1. 登入 [Teams Admin Center](https://admin.teams.microsoft.com/)
2. 前往 **Teams apps** → **Manage apps** → **Upload new app**
3. 上傳 `yonyou-teams-app.zip`（包含 manifest.json + 圖標）
4. 上傳後狀態為「已上傳」
5. 設定 App 為「允許所有用戶」

**方式二：手動 sideload（個人安裝）**

1. 開啟 Teams
2. 前往 **Apps** → **Manage your apps** → **Upload an app**
3. 選擇 `yonyou-teams-app.zip`
4. 安裝後即可在左側邊欄看到 "Yonyou Cloud"

### 4.3 打包 App 檔案

Zip 檔結構（僅包含以下檔案）：
```
yonyou-teams-app.zip
├── manifest.json    ← App 定義
├── color.png         ← 彩色圖標 (96×96)
└── outline.png       ← 輪廓圖標 (32×32)
```

> ⚠️ **注意：** 不要把 index.html 放入 zip！index.html 部署在伺服器上，不在 App 包內。

---

## 五、用戶使用說明

### 5.1 首次使用

1. 在 Teams 左側邊欄找到 **Yonyou Cloud** 圖標
2. 點擊開啟 Tab
3. 首次會要求登入用友雲（輸入帳號密碼）
4. 登入後，用友雲頁面會顯示在 Teams 內
5. 正常操作費用報銷、採購等功能

### 5.2 手機端使用

- 點擊 Tab 後，用友雲頁面以 1440×900 解析度顯示
- 可**左右滑動**查看完整頁面
- 操作體驗與桌面版相同

### 5.3 常見問題

| 問題 | 解決方法 |
|------|----------|
| 頁面空白/載入中 | 檢查網絡連接，刷新 Tab |
| 用友雲要求重新登入 | Cookie 過期，重新輸入帳號密碼 |
| 手機上字體小 | 左右滑動查看，或使用 PC 版 Teams |
| 頁面顯示異常 | 清除 Teams 緩存後重試 |

---

## 六、技術配置詳情

### 6.1 manifest.json 關鍵配置

```json
{
  "id": "cb53e8fc-9a66-4469-a790-34b6ce1cba75",
  "manifestVersion": "1.16",
  "name": { "short": "Yonyou Cloud" },
  "staticTabs": [{
    "entityId": "yonyou-tab",
    "name": "Yonyou Cloud",
    "contentUrl": "https://fbtimesheet.ddns.net/teams/",
    "websiteUrl": "https://c2.yonyoucloud.com/",
    "scopes": ["personal"]
  }],
  "validDomains": [
    "c2.yonyoucloud.com",
    "*.yonyoucloud.com",
    "*.yonyou.com",
    "fbtimesheet.ddns.net"
  ]
}
```

**欄位說明：**
- `contentUrl`：Teams Tab 載入的頁面地址（中間頁面）
- `websiteUrl`：在瀏覽器中打開時直接跳轉用友雲
- `validDomains`：允許 iframe 載入的域名白名單
- `scopes: ["personal"]`：個人 App（每個用戶獨立安裝）

### 6.2 index.html iframe 配置

```css
iframe {
  width: 1440px;    /* 桌面解析度寬度 */
  height: 900px;    /* 桌面解析度高度 */
  border: none;
}
```

- iframe 以 1440×900 解析度渲染用友雲桌面版
- 手機端可左右滑動查看完整內容
- 如需調整，只需修改 width/height 兩個值

### 6.3 Nginx 配置

中間頁面由現有 Nginx 直接提供靜態檔案服務，無需額外配置：
```
/var/www/timesheet/frontend/teams/
└── index.html
```

---

## 七、安全考量

| 項目 | 現狀 | 建議 |
|------|------|------|
| HTTPS | ✅ 已啟用 | 保持 SSL 憑證有效 |
| iframe 嵌入 | ✅ 用友雲允許 | 無需修改 |
| 身份驗證 | ⚠️ 用友雲帳密 | 建議未來整合 SSO |
| 數據傳輸 | ✅ 全程 HTTPS | — |
| App 權限 | ✅ 僅 identity | 最小權限原則 |
| 跨域限制 | ✅ validDomains 白名單 | 僅允許必要域名 |

### 7.1 限制說明

- **無 SSO 整合**：用戶首次使用需手動登入用友雲
- **iframe 限制**：無法操作用友雲的上傳/下載等彈窗功能
- **手機體驗**：桌面版頁面在手機上需滑動操作

---

## 八、維護與更新

### 8.1 日常維護

| 任務 | 頻率 | 說明 |
|------|------|------|
| SSL 憑證續期 | 每年 | 確保 HTTPS 有效 |
| Nginx 狀態檢查 | 每月 | 確認服務正常 |
| Teams App 版本 | 按需 | 修改 manifest.json 版本號後重新上傳 |

### 8.2 更新流程

**更新 index.html（中間頁面）：**
```powershell
# 1. 修改本地檔案
# 編輯 C:\QClaw_Backup\TeamsApp\index.html

# 2. 上傳到伺服器
pscp -P 22 -l sysadmin -pw "密碼" index.html 192.168.99.126:/var/www/timesheet/frontend/teams/

# 3. 即時生效，無需重啟
```

**更新 Teams App（manifest/圖標）：**
1. 修改 manifest.json（版本號 +1）
2. 重新打包 zip
3. 在 Teams Admin Center 上傳新版本

### 8.3 備份

| 項目 | 位置 |
|------|------|
| 源代碼 | `C:\QClaw_Backup\TeamsApp\` |
| GitHub 倉庫 | `https://github.com/fusionoa/yonyou-teams-app` |
| 伺服器檔案 | `/var/www/timesheet/frontend/teams/` |
| App 安裝包 | `C:\QClaw_Backup\TeamsApp\yonyou-teams-app.zip` |

---

## 九、未來優化方向

### 短期（1-2 個月）
- [ ] 評估 SSO 整合（Azure AD ↔ 用友雲）
- [ ] 優化手機端顯示體驗
- [ ] 添加 Teams 個人 Bot 提醒功能（報銷審批通知）

### 中期（3-6 個月）
- [ ] 開發自適應手機版 UI（與用友雲 API 對接）
- [ ] 整合 Teams 通知（費用報銷審批推播）
- [ ] 多語言支援

### 長期（6 個月+）
- [ ] 開發獨立 Teams App（不依賴 iframe）
- [ ] 與用友雲 API 深度整合
- [ ] 數據分析儀表板

---

## 十、聯絡資訊

| 項目 | 資訊 |
|------|------|
| 開發團隊 | FusionOA IT Team |
| GitHub | https://github.com/fusionoa/yonyou-teams-app |
| 伺服器 | 192.168.99.126 |
| 用友雲 | https://c2.yonyoucloud.com/ |

---

*本文件最後更新：2026-06-14*
