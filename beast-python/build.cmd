cd venv/scripts
pyinstaller --onefile ../../beast.py --workpath ../../ --distpath ../../build
cd ../..
rmdir /q/s beast
