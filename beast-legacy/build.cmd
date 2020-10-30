cd venv/scripts
pyinstaller --onefile ../../src/main.py --workpath ../../ --distpath ../../build --paths ../../ --name beast
cd ../..
rmdir /q/s beast
