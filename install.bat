IF NOT EXIST env python3 -m venv env ELSE CALL .\env\Scripts\activate

python3 -m pip install -r requirements.txt