project_name="Names By Culture"
venv_path=`realpath ".venv"`
src_path=`realpath "src"`

echo "$project_name: Setting up venv at $venv_path"
python_path="python3"
$python_path -m venv $venv_path || exit 1

python_path="$venv_path/bin/python"
echo "$project_name: Upgrading pip at $python_path"
$python_path -m pip install --upgrade pip || exit 1

echo "$project_name: Installing project at $src_path"
if $python_path -c "import os, subprocess; os.chdir('$src_path'); exit(subprocess.call(['$python_path', 'setup.py', 'install']));"
then
    echo "$project_name: Make sure to activate your virtual environment: source $venv_path/bin/activate"
else
    echo "$project_name: Failed to install $src_path"
fi
