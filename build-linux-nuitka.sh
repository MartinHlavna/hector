rm -rf build.hector && python3 -m nuitka hector.py  \
  --standalone --onefile \
  --enable-plugin=tk-inter \
  --include-package=ttkthemes \
  --include-package-data=ttkthemes \
  --include-package=cacheman \
  --include-package=hunspell \
  --include-package-data=hunspell \
  --include-module=fsspec.implementations.github \
  --include-data-dir=images=images


#--user-package-configuration-file=nuitka-config.yaml