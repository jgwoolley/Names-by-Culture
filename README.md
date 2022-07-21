# Names-by-Culture
A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language

Current categories linked with gender/language at [wikicategories.csv](wikicategories.csv)

- Running from PyPi is not quite working
- Only Categories are done, not pages
- I would like build files to be cleared after creating and importing PyPi package
- Possibly categories should go back to requiring uniqueness, wheras pages (names themselves) can be linked to multiple language/gender pairs

```console
foo@bar:~$ sh setup.sh
Names By Culture: Make sure to activate your virtual environment: source .venv/bin/activate
foo@bar:~$ source .venv/bin/activate
foo@bar:~$ .venv/bin/python -m jgwoolley_names
Category:Abkhaz surnames [surnames]
Please provide one of the following: [u]pdate, [s]plit, [i]gnore
```