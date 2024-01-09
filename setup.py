"""
A simple setup script to create an executable using PySide6.
"""
# python setup.py bdist_msi    # to build a Windows installer
# Ensure pdf2image.py has Popen creation flags set to: creationflags=0x08000000

from cx_Freeze import Executable, setup
from main_view import __version__ as VERSION

# Additional options
build_exe_options = {
    "bin_excludes": ["libqpdf.so", "libqpdf.dylib"],
    "excludes": [],
    "include_files": [("style/styles.qss", "style/styles.qss"), ("assets/", "assets/"), ("Tesseract/", "Tesseract/"), ("poppler/", "poppler/")],
    "zip_include_packages": ["PySide6", "shiboken6", "pysocks"],
}

# Executable configuration
executables = [Executable("main_view.py", base="Win32GUI", icon="assets/icons/icon.ico", shortcut_name="PDF Flow", shortcut_dir="DesktopFolder", target_name="PDF Flow.exe")]

# Setup configuration
setup(
    name="PDF Flow",
    version=VERSION,
    description="PDF Processing Tool",
    options={"build_exe": build_exe_options},
    executables=executables,
)