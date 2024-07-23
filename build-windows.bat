pyinstaller --noconfirm --log-level=WARN ^
    --onefile --windowed ^
    --additional-hooks-dir='hooks' ^
    --hidden-import="hunspell" ^
    --add-data="README.md:." ^
    --add-data="LICENSE:." ^
    --add-data="images/*:images/" ^
    --add-data="data_files/*:data_files/" ^
    --splash="images/hector-splash.png" ^
    hector.py