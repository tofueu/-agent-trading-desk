# -agent-trading-desk (Agent Desk — General AI & Trading Operations Console)

本專案為雙視圖控制台原型，包含「通用 AI 控制中心」與原有的「交易回測 Console」，支援跨桌面與手機裝置的響應式操作。

---

## 🌟 主要功能與架構

### 1. 通用 AI 控制中心 (General AI Control Center)
- **頂部導覽切換 (Tab Navigation)**：支援在「通用 AI 控制中心」與「交易回測 Console」間自由切換。
- **AI 模型與團隊人員管理 (AI & Team Roster)**：
  - AI 模型列表：GPT-4o、Claude 3.5 Sonnet、Gemini 1.5 Pro、DeepSeek V3，如實標明「未連接 API / 離線示範模式」。
  - 團隊人員清單：專案經理 (PM)、量化研究員 (RA)、系統工程師 (SE)，顯示當前在線狀態與職責。
- **跨類型專案管理 (5 Project Portfolio Types)**：
  - 金融交易類、軟體開發類、行銷內容類、數據分析類、多 Agent 協同研究類。
- **動態任務佇列 (Task Dispatch & Queue System)**：
  - 支援線上填寫與新增任務、指派 AI 模型或人員。
  - 點擊派送時會如實提示「示範佇列 · API 未連接」，並同步更新任務佇列與活動紀錄。
  - 支援手動標記任務完成狀態。
- **活動紀錄 (Activity Log)**：即時紀錄 AI 控制中心之任務指派、系統事件與狀態變更。

### 2. 交易回測控制台 (Trading Research Console - 保留原有功能)
- 完全保留原有的交易回測原型介面，包含 Paper Account Equity 資金曲線圖、Tail Probability Ridge 示意曲面圖、Handoff Chord 流程圖與 5D Strategy Lattice 參數網格圖。

---

## 📱 響應式支援 (Responsive Design)
- **桌面端 (Desktop)**：提供寬螢幕多欄位併排佈局 (1200px+)。
- **行動端 (Mobile)**：優化 780px 及 390px 以下的手機版佈局，頁籤自動適應全寬，表單與任務佇列單欄呈現，確保良好操作體驗。

---

## 🧪 驗證與測試 (Verification)

本專案提供 DOM 與邏輯結構測試腳本 `test_ui.py`：

```bash
python3 test_ui.py
```

測試涵蓋：
1. 頂部頁籤切換結構與事件綁定
2. 通用 AI 控制中心 View 與交易回測 Console View 的隔離與顯隱
3. AI 模型與團隊人員清單完整度與連線狀態標示
4. 5 大類別專案卡片呈現
5. 任務派送表單與佇列 DOM 綁定
6. 活動紀錄與原交易控制台結構無失真驗證

---

## ⚠️ 連線與安全聲明
- **示範模式 (DEMO MODE)**：本控制台目前為原型示範介面，**未連接任何實際 AI API、行情資料庫、加密貨幣錢包或交易所**。
- **真實訂單防護**：安全模式預設固定開啟，無法進行任何真實下單或付費 API 調用。
