# Compile application using PyInstaller
# make sure you have UPX in nearby folder to reduce exe file size
import PyInstaller.__main__

# run pyinstaller
PyInstaller.__main__.run([
    'parser.py',
    #'--onefile',
    #'--windowed',
    '--console',                    # for debugging
    '--name=ShaftkitParser',
    #'--clean',                     # clean all files periodically
    '--distpath=./dist/',
    '--workpath=./build',
    '--log-level=INFO',
    '--add-data=parser-settings.ini;.',        # include data file
    '--add-data=README.MD;.',        # include data file
    #'--key encryption_key',
    #'--icon=./shaftkit/logo48x48.ico',
    '--noconfirm',                     # overwrite previous compiles without confirmation
    '--upx-dir=C:\\temp\\upx-4.0.1-win64'
    ])
