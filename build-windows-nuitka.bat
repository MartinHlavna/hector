python.exe -m nuitka hector.py  ^
  --standalone ^
  --onefile ^
  --enable-plugin=tk-inter ^
  --include-package=ttkthemes ^
  --include-package-data=ttkthemes ^
  --include-package=cacheman ^
  --include-package=hunspell ^
  --include-package-data=hunspell ^
  --include-module=spacy.lexeme ^
  --include-data-dir=images=images ^
  --include-data-dir=fonts=fonts ^
  --include-data-dir=data_files=data_files ^