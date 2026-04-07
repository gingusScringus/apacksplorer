Write-Host "setting up virtual env"

python -m venv .venv

.\.venv\Scripts\Activate.ps1

Write-Host "installing dependencies"
pip install -r requirements.txt

Write-Host "run '.\.venv\Scripts\Activate.ps1' to activate again later"