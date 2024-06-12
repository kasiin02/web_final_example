@echo off
rem 切換工作目錄至批次檔所在目錄
cd /d "%~dp0"
if not defined _OLD_VIRTUAL_PROMPT (
    call env\Scripts\activate
)
rem 啟動 Flask 應用
start "" /B cmd /C "flask --debug -A app run -h 0.0.0.0 -p 80"
rem 等待幾秒鐘讓 Flask 應用啟動
timeout /t 2 /nobreak >nul
rem 打開瀏覽器並訪問應用
start "" "http://127.0.0.1"
