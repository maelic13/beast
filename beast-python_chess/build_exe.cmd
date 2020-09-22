cd venv/scripts
pyinstaller --onefile ../../src/main.py --workpath ../../ --distpath ../../build --name beast
cd ../..
rmdir /q/s beast
