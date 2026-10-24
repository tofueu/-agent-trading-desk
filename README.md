# -agent-trading-desk
交易回測控制台原型，用於設定回測條件、監控執行狀態及查看結果；目前為示範介面，尚未連接實際行情資料。

## 執行說明 (Run Instructions)
本專案包含前端 UI 與 Flask 後端 API，以展示實際的回測數據（勝率、報酬率、Max Drawdown、Kelly fraction 等）。

1. 安裝後端相依套件：
   ```bash
   pip install flask flask-cors pandas numpy
   ```
2. 啟動 Flask 後端伺服器：
   ```bash
   python3 backend/app.py
   ```
3. 開啟前端介面：
   在瀏覽器中直接開啟 `index.html`。點擊「Start demo」按鈕即可呼叫後端 API 並載入即時回測數據。可以使用上方的過濾器即時切換策略與時間框架。