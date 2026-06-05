@echo off
cd /d %~dp0
echo 必要なパッケージをインストール中...
pip install -r requirements.txt
echo.
echo サーバーを起動します...
echo ブラウザで http://localhost:5000 を開いてください
echo.
python app.py
pause
