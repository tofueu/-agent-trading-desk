# Multi-AI Workbench

以 OpenCreator 深色工作台為介面參考的本機多 AI 專案控制台。此版本先處理你要求的核心：專案、主任務、巢狀子任務、AI 分工、執行狀態，以及 GitHub Repository／Issue／PR 連結。

## Windows 啟動

1. 安裝 Node.js 22 或更新版本。
2. 安裝並登入 Google Antigravity CLI（命令為 `agy`）。
3. 解壓縮或 clone 專案後，雙擊 `start.bat`。
4. 工作台會開啟 `http://127.0.0.1:4173`。
5. 輸入主任務、本機專案資料夾路徑和選填的 GitHub 網址，按「建立分工」。

也可以在此資料夾執行 `npm start`，再用瀏覽器開啟上述網址。

## 任務分工

- Gemini／Antigravity：在指定本機工作區執行程式任務；使用已登入的 Google 帳號。
- Perplexity Pro：工作台複製研究任務並開啟官方網站；完成後將回覆貼回任務樹。
- SuperGrok：同樣透過官方網站交辦審查；完成後將回覆貼回任務樹。
- 工作台負責保存主任務與子任務狀態、提示詞和結果；Perplexity 與 Grok 的訂閱不會轉成 API，也不會由工作台代替登入或操作帳號。

## 本機資料與安全

- 任務紀錄保存在 `data/tasks.json`，不會上傳到工作台服務。
- 伺服器只監聽 `127.0.0.1`，不會對外公開。
- Gemini 使用 Antigravity CLI 的 `accept-edits` 模式，會直接修改你指定的專案資料夾。請先備份重要程式碼。
- 本機檢查：`npm run check`。啟動：`npm start`。

## 版本範圍

目前是「多 AI 專案管理」第一版，含主任務／子任務樹、AI 角色卡、交辦、狀態與結果紀錄。它採用 OpenCreator 的深色工作台視覺方向；OpenCreator 的影片翻譯、影像／影片生成、配音等創作工具尚未包含在此版本。
