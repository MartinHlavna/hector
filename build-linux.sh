rm -rf ./build && pyinstaller --noconfirm --log-level=WARN \
    --onefile --windowed \
    --hidden-import='PIL._tkinter_finder' \
    --hidden-import='svglib' \
    --hidden-import='hunspell' \
    --hidden-import='rlPyCairo' \
    --additional-hooks-dir='hooks' \
    --add-data="README.md:." \
    --add-data="LICENSE:." \
    --add-data="images/*:images/" \
    --add-data="data_files/*:data_files/" \
    --splash="images/hector-splash.png" \
    hector.py