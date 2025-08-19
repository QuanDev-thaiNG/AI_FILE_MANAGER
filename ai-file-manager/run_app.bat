@echo off
echo ===== AI File Manager =====
echo.

REM Kich hoat moi truong ao
echo Dang kich hoat moi truong ao...
call .venv\Scripts\activate.bat 2>nul
if %ERRORLEVEL% neq 0 (
    echo Khong the kich hoat moi truong ao. Thu kich hoat lai...
    call .venv\Scripts\activate 2>nul
    if %ERRORLEVEL% neq 0 (
        echo Khong the kich hoat moi truong ao. Tiep tuc ma khong co moi truong ao.
    )
)

REM Hien thi menu
:menu
cls
echo ===== AI File Manager - Menu =====
echo 1. Khoi tao co so du lieu
echo 2. Quet va dang ky file
echo 3. Sap xep file theo quy tac
echo 4. Tim kiem file
echo 5. Quan ly the
echo 6. Lap chi muc noi dung
echo 7. Chay kiem thu
echo 8. Thoat
echo.

set /p choice=Chon tuy chon (1-8) 

if "%choice%"=="1" goto init
if "%choice%"=="2" goto ingest
if "%choice%"=="3" goto organize
if "%choice%"=="4" goto search
if "%choice%"=="5" goto tag
if "%choice%"=="6" goto index
if "%choice%"=="7" goto test
if "%choice%"=="8" goto end

echo Tuy chon khong hop le. Vui long chon lai.
pause
goto menu

:end
echo Cam on ban da su dung AI File Manager!
pause
exit /b 0

:error
echo Da xay ra loi: %ERROR_MSG%
pause
exit /b 1

:init
cls
echo ===== Khoi tao co so du lieu =====
set /p db_path=Duong dan co so du lieu (mac dinh ./filemanager.db) 
if "%db_path%"=="" set db_path=./filemanager.db

python main.py init --db-path="%db_path%"
if %ERRORLEVEL% neq 0 (
    set ERROR_MSG=Loi khi khoi tao co so du lieu.
    goto error
)
pause
goto menu

:ingest
cls
echo ===== Quet va dang ky file =====
set /p directory=Duong dan thu muc can quet 
set /p recursive=Quet de quy? (y/n, mac dinh y) 
set /p dry_run=Che do thu nghiem? (y/n, mac dinh n) 
set /p db_path=Duong dan co so du lieu (mac dinh ./filemanager.db) 

if "%db_path%"=="" set db_path=./filemanager.db
if "%recursive%"=="" set recursive=y
if "%dry_run%"=="" set dry_run=n

set cmd=python main.py ingest --db-path="%db_path%" "%directory%"

if /i "%recursive%"=="y" set cmd=%cmd% --recursive
if /i "%dry_run%"=="y" set cmd=%cmd% --dry-run

%cmd%
if %ERRORLEVEL% neq 0 (
    set ERROR_MSG=Loi khi quet va dang ky file.
    goto error
)
pause
goto menu

:organize
cls
echo ===== Sap xep file theo quy tac =====
set /p rules_file=Duong dan file quy tac (mac dinh ./rules/example_rules.yaml): 
set /p source=Duong dan thu muc nguon (de trong neu khong can) 
set /p dry_run=Che do thu nghiem? (y/n, mac dinh n): 
set /p db_path=Duong dan co so du lieu (mac dinh ./filemanager.db): 

if "%rules_file%"=="" set rules_file=./rules/example_rules.yaml
if "%db_path%"=="" set db_path=./filemanager.db
if "%dry_run%"=="" set dry_run=n

set cmd=python main.py organize --db-path="%db_path%" --rules="%rules_file%"

if not "%source%"=="" set cmd=%cmd% --source="%source%"
if /i "%dry_run%"=="y" set cmd=%cmd% --dry-run

%cmd%
pause
goto menu

:search
cls
echo ===== Tim kiem file =====
echo 1. Tim kiem theo ten file
echo 2. Tim kiem theo loai MIME
echo 3. Tim kiem theo the
echo 4. Tim kiem file trung lap
echo 5. Tim kiem nang cao
echo 6. Quay lai
echo.

set /p search_choice=Chon tuy chon (1-6) 
set /p db_path=Duong dan co so du lieu (mac dinh ./filemanager.db): 
if "%db_path%"=="" set db_path=./filemanager.db

if "%search_choice%"=="1" (
    set /p filename=Ten file can tim 
    python main.py search --db-path="%db_path%" --filename="%filename%"
) else if "%search_choice%"=="2" (
    set /p mime_type=Loai MIME can tim 
    python main.py search --db-path="%db_path%" --mime-type="%mime_type%"
) else if "%search_choice%"=="3" (
    set /p tags=Cac the can tim (phan cach bang dau phay) 
    python main.py search --db-path="%db_path%" --tags="%tags%"
) else if "%search_choice%"=="4" (
    python main.py search --db-path="%db_path%" --duplicates
) else if "%search_choice%"=="5" (
    set /p filename=Ten file (de trong neu khong can) 
    set /p extension=Phan mo rong (de trong neu khong can) 
    set /p mime_type=Loai MIME (de trong neu khong can) 
    set /p tags=Cac the (phan cach bang dau phay, de trong neu khong can) 
    set /p min_size=Kich thuoc toi thieu (byte, de trong neu khong can) 
    set /p max_size=Kich thuoc toi da (byte, de trong neu khong can) 
    set /p created_after=Tao sau ngay (YYYY-MM-DD, de trong neu khong can) 
    set /p created_before=Tao truoc ngay (YYYY-MM-DD, de trong neu khong can) 
    
    set cmd=python main.py search --db-path="%db_path%"
    
    if not "%filename%"=="" set cmd=%cmd% --filename="%filename%"
    if not "%extension%"=="" set cmd=%cmd% --extension="%extension%"
    if not "%mime_type%"=="" set cmd=%cmd% --mime-type="%mime_type%"
    if not "%tags%"=="" set cmd=%cmd% --tags="%tags%"
    if not "%min_size%"=="" set cmd=%cmd% --min-size="%min_size%"
    if not "%max_size%"=="" set cmd=%cmd% --max-size="%max_size%"
    if not "%created_after%"=="" set cmd=%cmd% --created-after="%created_after%"
    if not "%created_before%"=="" set cmd=%cmd% --created-before="%created_before%"
    
    %cmd%
) else if "%search_choice%"=="6" (
    goto menu
) else (
    echo Tuy chon khong hop le. Vui long chon lai.
)

pause
goto menu

:tag
cls
echo ===== Quan ly the =====
echo 1. Them the
echo 2. Xoa the
echo 3. Liet ke the
echo 4. Quay lai
echo.

set /p tag_choice=Chon tuy chon (1-4) 
set /p db_path=Duong dan co so du lieu (mac dinh ./filemanager.db): 
if "%db_path%"=="" set db_path=./filemanager.db

if "%tag_choice%"=="1" (
    set /p file_path=Duong dan file 
    set /p tags=Cac the can them (phan cach bang dau phay) 
    python main.py tag --db-path="%db_path%" --add="%tags%" --file="%file_path%"
) else if "%tag_choice%"=="2" (
    set /p file_path=Duong dan file 
    set /p tags=Cac the can xoa (phan cach bang dau phay) 
    python main.py tag --db-path="%db_path%" --remove="%tags%" --file="%file_path%"
) else if "%tag_choice%"=="3" (
    set /p file_path=Duong dan file (de trong de liet ke tat ca) 
    if "%file_path%"=="" (
        python main.py tag --db-path="%db_path%" --list-all
    ) else (
        python main.py tag --db-path="%db_path%" --list --file="%file_path%"
    )
) else if "%tag_choice%"=="4" (
    goto menu
) else (
    echo Tuy chon khong hop le. Vui long chon lai.
)

pause
goto menu

:index
cls
echo ===== Lap chi muc noi dung =====
set /p mime_type=Loai MIME can lap chi muc (de trong cho tat ca) 
set /p rebuild=Xay dung lai chi muc? (y/n, mac dinh n): 
set /p db_path=Duong dan co so du lieu (mac dinh ./filemanager.db): 

if "%db_path%"=="" set db_path=./filemanager.db
if "%rebuild%"=="" set rebuild=n

set cmd=python main.py index --db-path="%db_path%"

if not "%mime_type%"=="" set cmd=%cmd% --mime-type="%mime_type%"
if /i "%rebuild%"=="y" set cmd=%cmd% --rebuild

%cmd%
pause
goto menu

:test
cls
echo ===== Chay kiem thu =====
echo 1. Chay tat ca cac kiem thu
echo 2. Chay kiem thu cho module core
echo 3. Chay kiem thu cho module extractors
echo 4. Chay kiem thu cho module rules
echo 5. Chay kiem thu cho module actions
echo 6. Chay kiem thu cho module search
echo 7. Chay kiem thu cho module cli
echo 8. Quay lai
echo.

set /p test_choice=Chon tuy chon (1-8) 

if "%test_choice%"=="1" (
    python tests/run_tests.py
) else if "%test_choice%"=="2" (
    python tests/run_tests.py test_core
) else if "%test_choice%"=="3" (
    python tests/run_tests.py test_extractors
) else if "%test_choice%"=="4" (
    python tests/run_tests.py test_rules
) else if "%test_choice%"=="5" (
    python tests/run_tests.py test_actions
) else if "%test_choice%"=="6" (
    python tests/run_tests.py test_search
) else if "%test_choice%"=="7" (
    python tests/run_tests.py test_cli
) else if "%test_choice%"=="8" (
    goto menu
) else (
    echo Tuy chon khong hop le. Vui long chon lai.
)

pause
goto menu
