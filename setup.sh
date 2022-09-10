project_name="Names By Culture"
venv_path=`realpath ".venv"`

echo "$project_name: Setting up venv at $venv_path"
python_path="python3"
$python_path -m venv $venv_path || exit 1

python_path="$venv_path/bin/python"
echo "$project_name: Upgrading pip at $python_path"
$python_path -m pip install --upgrade pip || exit 1

echo "$project_name: Creating requires.txt"
$python_path setup.py egg_info || exit 1
echo "$project_name: Installing requires.txt"
$python_path -m pip install -r *.egg-info/requires.txt || exit 1
echo "$project_name: Cleanup egg-info"
rm -rf *.egg-info/ || exit 1
echo "$project_name: Make sure to activate your virtual environment: source $venv_path/bin/activate"