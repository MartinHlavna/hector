rm -rf ./build && pyinstaller --noconfirm --log-level=WARN \
    --onefile --windowed \
    --hidden-import='PIL._tkinter_finder' \
    --hidden-import='hunspell' \
    --additional-hooks-dir='hooks' \
    --add-data="README.md:." \
    --add-data="LICENSE:." \
    --add-data="images/*:images/" \
    --splash="images/hector-splash.png" \
    hector.py