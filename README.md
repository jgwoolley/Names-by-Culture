# Names-by-Culture
A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language from [MediaWiki](https://en.wikipedia.org/wiki/MediaWiki) ([Wiktionary](https://en.wikipedia.org/wiki/Wiktionary) or [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia))

- Current pages are located in [pages](pages). See name counts here: [metadata.csv](pages/metadata.csv)
- These pages were collected from the following file: [wikicategories.csv](wikicategories.csv)


# Motivation

When searching for Surname / Given Name databases, the only structured databases I found were either paid for or were from census data and did not include languages of origin. After attempting to pull data from [Wikipedia](https://en.wikipedia.org/wiki/Category:Surnames_by_language), however I found that [Wikitionary](https://en.wiktionary.org/wiki/Category:Given_names_by_language)'s list of names were structured a bit better.

I realized that the subcategories would need some manual review to match them with languages. I found the [ISO 639-3](https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab) specification was extremly close to the list of languages found on Wikitionary.

Later on I also discovered that the [English](https://en.wiktionary.org/wiki/Category:English_given_names) pages had many examples of categories like [Category:English_given_names_from_Japanese](https://en.wiktionary.org/wiki/Category:English_given_names_from_Japanese) which in, my perspective, are not English names but rather Japanese.

I also saw a mix of Latin/Cyrillic names in some languages, and thus sought to identify the script as well. I used this [Unicode](http://unicode.org/Public/UNIDATA/Scripts.txt) specification.

# How to run

1. I have created a [setup script](setup.sh) that can be run to create a [virtual environment (venv)](https://docs.python.org/3/library/venv.html), and downloads the relevant dependencies. This setup guide is written to work on Linux, however, consult the venv documentation to get it working on the operating system of your choice.

```console
foo@bar:~$ sh setup.sh
Names By Culture: Make sure to activate your virtual environment: source .venv/bin/activate
```

2. Run the [CLI](https://en.wikipedia.org/wiki/Command-line_interface).

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names
usage: A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language
       [-h] [--cache_name c] [--backend b] [--sqlite_database s] [--categories c]
       {wikicategories,wikipages,out,in,wikipages_out} ...
A Python library to pull down Surnames, Given Names, and Place Names by Culture/Language
```

3. You can import the [default records](wikicategories.csv) with the following:

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names read_csv --in wikicategories.csv --model WikiRecord
```

4. You can then run the interactive script which identifies languages/scripts for each given category:

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names wikicategories
```

5. You can output all of the categories/pages you have identified into a single file:

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names write_csv --out wikicategories2.csv --model WikiRecord
```

6. You then can find all of the pages referenced by the categories you specified in this way:

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names wikipages
```

7. You can output all of the pages (not categories) you have created into a single file:

```console
foo@bar:~$ .venv/bin/python -m jgwoolley_names wikipages_out --out pages
```

# Libraries used
- [pydantic](https://github.com/pydantic/pydantic): Data validation and settings management using Python type annotations.
- [sqlmodel](https://github.com/tiangolo/sqlmodel): SQLModel is a library for interacting with SQL databases from Python code, with Python objects. It is designed to be intuitive, easy to use, highly compatible, and robust.
- [requests-cache](https://github.com/requests-cache/requests-cache): requests-cache is a persistent HTTP cache that provides an easy way to get better performance with the python requests library.
- [tqdm](https://github.com/tqdm/tqdm): Instantly make your loops show a smart progress meter - just wrap any iterable with tqdm(iterable), and you're done!

# TODO

- Running from PyPi is not quite working
- Add Redo Functionality
- Possibly categories should go back to requiring uniqueness, wheras pages (names themselves) can be linked to multiple language/gender pairs
- Duplication possible, maybe check if record was inserted
- Put default alt-language names in file
- Support alt-languages and countries that span multiple words [main.py](main.py)