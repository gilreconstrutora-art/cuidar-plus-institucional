param(
    [ValidateSet('Local','Docker')]
    [string]$Mode = 'Local'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = if ($env:PYTHON_EXE) { $env:PYTHON_EXE } else { 'C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
if (-not (Test-Path -LiteralPath $python)) { throw "Python não encontrado. Defina PYTHON_EXE." }
Set-Location $projectRoot

& $python -m pip install -r requirements.txt --disable-pip-version-check
& $python manage.py migrate --noinput
& $python manage.py collectstatic --noinput
& $python manage.py check
& $python manage.py makemigrations --check --dry-run
& $python -m pytest -q

if ($Mode -eq 'Docker') {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker não está instalado neste computador.' }
    docker compose up -d --build
    Write-Output 'Implantação Docker iniciada. Configure domínio, HTTPS e segredos antes de usar dados reais.'
} else {
    Write-Output 'Validação local concluída. Para iniciar: python manage.py runserver 127.0.0.1:8000'
}
