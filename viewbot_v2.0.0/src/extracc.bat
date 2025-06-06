@echo off
REM Proper Windows-compatible script to extract keys using extract_key.py

python extract_key.py --service webhook --output key_output_1.key
python extract_key.py --service webhook --output key_output_2.key

pause
