# Names-by-Culture
A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language

Current categories linked with gender/language at [wikicategories.csv](wikicategories.csv)

- Running from PyPi is not quite working
- Only Categories are done, not pages
- I would like build files to be cleared after creating and importing PyPi package
- Possibly categories should go back to requiring uniqueness, wheras pages (names themselves) can be linked to multiple language/gender pairs
- some categories are marked as pages incorrectly. Probably Given Names by language
- remove leading row id from pandas

```console
foo@bar:~$ sh setup.sh
Names By Culture: Make sure to activate your virtual environment: source .venv/bin/activate
foo@bar:~$ .venv/bin/python -m jgwoolley_names
usage: A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language
       [-h] [--cache_name c] [--backend b] [--sqlite_database s] [--categories c]
       {wikicategories,wikipages,out,in,wikicategories_redo} ...
A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language
```

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names in --in wikicategories.csv --model WikiRecord
```

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names out --out wikicategories2.csv --model WikiRecord
```