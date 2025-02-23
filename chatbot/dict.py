import re

#siglas
abbreviation_dict = {
    "EI": "Engenharia Informática",
    "CBL": "Ciências Biomédicas Laboratoriais",
    "EB": "Educação Básica",
    "EEC": "Engenharia Eletrotécnica e de Computadores",
    "IG": "Informática de Gestão",
}
#Cursos com nomes parecidos ou iguais
course_options = {
    "Educação Ambiental": {
        "licenciatura": ["Educação Ambiental"],
        "mestrado": ["Educação Ambiental"],
        "ctesp": ["Educação Ambiental"]
    },
    "Design de Jogos Digitais": {
        "licenciatura": ["Design de Jogos Digitais"],
        "mestrado": ["Design e Desenvolvimento de Jogos Digitais"],
        "ctesp": ["Design de Jogos Digitais e Gamificação"]
    },
    "Informática": {
        "licenciatura": ["Engenharia Informática", "Informática de Gestão", "Informática e Comunicações"],
        "mestrado": ["Informática",],
        "ctesp": ["Informática"]
    },
    "Gerontologia": {
        "licenciatura": ["Gerontologia"],
        "ctesp": ["Gerontologia"]
    },
    "Enologia": {
        "licenciatura": ["Enologia"],
        "ctesp": ["Viticultura e Enologia"]
    },
    "Contabilidade": {
        "licenciatura": ["Contabilidade"],
        "mestrado": ["Contabilidade e Finanças"],
        "ctesp": ["Contabilidade"]
    },
    "Energias Renováveis": {
        "licenciatura": ["Engenharia de Energias Renováveis"],
        "mestrado": ["Energias Renováveis e Eficiência Energética"],
        "ctesp": ["Energias Renováveis e Instalações Elétricas"]
    },
    "Engenharia Eletrotécnica e de Computadores": {
        "licenciatura": ["Engenharia Eletrotécnica e de Computadores"],
        "mestrado": ["Engenharia Eletrotécnica e de Computadores"]
    },
    "Engenharia Mecânica": {
        "licenciatura": ["Engenharia Mecânica"],
        "mestrado": ["Engenharia Mecânica"]
    },
    "Engenharia Química": {
        "licenciatura": ["Engenharia Química"],
        "mestrado": ["Engenharia Química"]
    }
}

#Substituir siglas no input do user
def replace_abbreviations(text, abbr_dict):
    for abbr, full_form in abbr_dict.items():
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        text = pattern.sub(full_form, text)
    return text
