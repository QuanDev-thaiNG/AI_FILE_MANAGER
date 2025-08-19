@echo off
echo Dang khoi dong AI File Manager Web...

REM Kiem tra Python da duoc cai dat chua
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Loi: Python chua duoc cai dat. Vui long cai dat Python 3.8 tro len.
    pause
    exit /b 1
)

REM Di chuyen den thu muc web
cd %~dp0\ui\web

REM Kiem tra va cai dat cac thu vien can thiet
echo Dang kiem tra cac thu vien can thiet...
pip install -r requirements.txt

REM Khoi dong ung dung web
echo Dang khoi dong may chu web...
echo.
echo AI File Manager Web se chay tai dia chi: http://localhost:5000
echo.
echo Ban co the truy cap ung dung bang cach mo trinh duyet va nhap dia chi tren.
echo Nhan Ctrl+C de dung ung dung.
echo.

python app.py

pause