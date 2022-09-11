import requests, csv, sqlmodel

from typing import Iterator, List
from .models import Language, LanguageName

DEFAULT_URL = 'https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab'

def query_languages_from_web(session:requests.Session, url:str=DEFAULT_URL) -> str:
    R = session.get(url=url)
    data = R.text
    return data

def parse_languages_from_text(tsv:str) -> Iterator[List[str]]:
    reader = csv.reader(tsv.splitlines(), delimiter='\t')
    header = next(reader)
    for line in reader:
        yield line

def parse_languages_from_web(session:requests.Session, url:str=DEFAULT_URL) -> Iterator[List[str]]:
    result = query_languages_from_web(session=session)
    return parse_languages_from_text(result)

def write_languages_to_sql(session:requests.Session, sql_session:sqlmodel.Session, url:str=DEFAULT_URL):
    for table in [Language, LanguageName]:
        statement = sqlmodel.select(table)
        results = sql_session.exec(statement)
        result = results.first()
        if result is not None:
            return

    for result in parse_languages_from_web(url=url, session=session):
        id, part2b, part2t, part1, scope, language_type, ref_name, comment = result

        statement = sqlmodel.select(Language).where(Language.id == id)
        results = sql_session.exec(statement)
        result = results.first()
        if result is None:
            result = Language(
                id = id,
                part2b = part2b,
                part2t = part2t,
                part1 = part1,
                scope = scope,
                language_type = language_type,
                ref_name = ref_name,
                comment = comment
            )
            sql_session.add(result)

        for ref_dat in result.create_references():
            statement = sqlmodel.select(LanguageName).where(LanguageName.name == ref_dat.name)
            results = sql_session.exec(statement)
            result = results.first()
            if result is not None:
                continue
            
            sql_session.add(ref_dat)

    sql_session.commit()

    #TODO: Put in file
    for name, language_id in [
        ('Chichewa','nya'),
        ('Greek','ell'),
        ('Ilocano','ilo'),
        ('Kapampangan','pam'),
        ('Norman','nrf'),
        ('Occitan','oci'),
        ('Punjabi','pan'),
        # ('Scottish Gaelic','gla'),
        ('Slovene','slv'),
        ('Waray-Waray','war'),
        ('Germanic','deu'),
        ('Hellenic','ell'),
        ('Italic','ita'),
        ('Japonic','jpn'),
        ('Koreanic','kor'),
        ('Malayo-Polynesian','poz'),
        ('Norse','non'),
        ('Frisian','fry'),
        ('Abkhaz', 'abk'),
        ('Aramaic', 'arc'),
        ('Assyrian', 'syr'),
        ('Nahuatl', 'nhe'),
        ('Egyptian', 'egy'),
        # ('Gandhari', 'pdg'),
        ('Gaulish', 'xtg'),
        ('Greenlandic', 'kal'),
        ('Malay', 'ind'),
        # ('Na\'vi', 'mis'),
        ('Sami', 'sme'),
        ('Novgorodian', 'rus'),
        ('Saxon', 'osx'),
        ('Proto-Brythonic', 'xpi'),
        ('Proto-Celtic', 'mga'),
        ('Proto-Germanic', 'deu'),
        ('Proto-Norse', 'non'),
        # ('Proto-Slavic', None),
        ('Swahili', 'swa'),
        # ('Tocharian', None),
        ('Uyghur', 'uig'),
        ('Vilamovian', 'wym'),
        ('Westrobothnian','swe'),
        ('Zazaki', 'zza'),
        ('Aromanian', 'rup'),
        ('Bura', 'bwr'),
        ('Buryat', 'bua'),
        ('Tamazight', 'ber'),
        ('Franconian', 'deu'),
        ('Demotic', 'cop'),
        ('Gandhari', 'pgd'),
        ('Jamtish', 'swe'),
        ('Kaxuyana', 'waw'),
        ('Kom', 'bkm'),
        ('Konkani', 'kok'),
        ('Kyrgyz', 'kir'),
        ('Limburgish', 'lim'),
        ('Lishana', 'lsd'),
        ('Sorbian', 'wen'),
        ('Nepali', 'nep'),
        ('Slavonic', 'chu'),
        # ('Philistine', None),
        ('Prakrit', 'pra'),
        ('Proto-Hellenic', 'ell'),
        ('Proto-Iranian', 'fas'),
        ('Romani', 'rom'),
        ('Rwanda-Rundi', 'kin'),
        ('Sinhalese', 'sin'),
        ('Solon', 'evn'),
        ('Altai', 'tut'),
        ('Tocharian', 'txb'),
        ('Tokelauan', 'tkl'),
        ('Tuvan', 'tyv')
    ]:
        sql_session.add(
            LanguageName(
                name=name,
                language_id=language_id,
                source=__name__
            )
        )

    sql_session.commit()

def find_language_id(sql_session:sqlmodel.Session, name:str) -> str:
    statement = sqlmodel.select(LanguageName).where(LanguageName.name == name)
    results = sql_session.exec(statement)
    result = results.first()
    return result.language_id if result else None