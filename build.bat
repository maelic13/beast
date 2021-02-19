cd venv/scripts
pyinstaller --onedir ../../src/main.py --workpath ../../ --distpath ../../build --paths ../../ --name beast
cd ../..
rmdir /q/s beast
