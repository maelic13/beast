cd venv/scripts
pyinstaller --onefile ../../src/beast.py --workpath ../../ --distpath ../../build
cd ../..
rmdir /q/s beast
