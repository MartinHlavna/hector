pyinstaller --noconfirm --log-level=WARN \
    --onedir --nowindow \
    --hidden-import='PIL._tkinter_finder' \
    --add-data="README.md:." \
    --add-data="LICENSE:." \
    --add-data="images/*:images/" \
    hector.py