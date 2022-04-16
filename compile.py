# Compile application using PyInstaller
# make sure you have UPX in nearby folder to reduce exe file size
import PyInstaller.__main__

# run pyinstaller
PyInstaller.__main__.run([
    'parser.py',
    '--onefile',
    #'--windowed',
    '--console',                    # for debugging
    '--name=ShaftkitParser',
    #'--clean',                     # clean all files periodically
    '--distpath=./dist',
    '--workpath=./build',
    '--log-level=INFO',
    #'--add-data=./data;data',        # include input file folder
    #'--key encryption_key',
    #'--icon=./shaftkit/logo48x48.ico',
    '--noconfirm',                     # overwrite previous compiles without confirmation
    '--upx-dir=C:\\temp\\upx-3.96-win64'
    ])
