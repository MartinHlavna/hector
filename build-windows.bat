pyinstaller --noconfirm --log-level=WARN ^
    --onefile --windowed ^
    --additional-hooks-dir='hooks' ^
    --add-data="README.md:." ^
    --add-data="LICENSE:." ^
    --add-data="images/*:images/" ^
    --splash="images/hector-splash.png" ^
    hector.py