python.exe -m nuitka hector.py  ^
  --standalone --onefile ^
  --enable-plugin=tk-inter ^
  --include-package=ttkthemes ^
  --include-package=ttkthemes ^
  --include-package-data=ttkthemes ^
  --include-package=cacheman ^
  --include-package=hunspell ^
  --include-package-data=hunspell ^
  --include-module=fsspec.implementations.github ^
  --include-data-dir=images=images