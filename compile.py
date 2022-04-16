# Compile application using PyInstaller
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
    '--upx-dir=C:\\Users\\ZacSchramm\\OneDrive - LamaLo\\scripts\\python\\upx-3.96-win64'
    ])


# # rename to add "__" to beginning of file name for easy finding.  Could also create a link to file??
# import os
# cwd = os.getcwd()
# os.rename(cwd + "\\dist\\Shaftkit\\Shaftkit.exe", cwd + "\\dist\\Shaftkit\\__Shaftkit.exe")

