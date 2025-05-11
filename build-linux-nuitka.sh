rm -rf build.hector && python3 -m nuitka hector.py  \
  --standalone \
  --enable-plugin=tk-inter \
  --include-package=ttkthemes \
  --include-package-data=ttkthemes \
  --include-package=cacheman \
  --include-package=hunspell \
  --include-package-data=hunspell \
  --include-module=spacy.lexeme \
  --include-data-dir=images=images \
  --include-data-dir=data_files=data_files \
  --include-data-dir=fonts=fonts \
  --onefile


#--user-package-configuration-file=nuitka-config.yaml