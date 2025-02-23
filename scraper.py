import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import html2text

# Suprimir avisos de InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Mapear domínios para códigos
domain_mapping = {
    'portal3.ipb.pt': '3040',
    'estig.ipb.pt': '3043',
    'ese.ipb.pt': '3042',
    'esa.ipb.pt': '3041',
    'essa.ipb.pt': '7015',
    'esact.ipb.pt': '3045',
    'sas.ipb.pt': '0000'
}

# Inicializar o conversor HTML para texto
html_converter = html2text.HTML2Text()
html_converter.ignore_links = False
html_converter.ignore_images = False

# Função para obter o código do domínio com base na URL
def get_domain_code(url):
    domain = urlparse(url).netloc
    return domain_mapping.get(domain, '9999')  # Padrão para 9999 se o domínio não for encontrado

# Função para verificar se o link pertence a um dos domínios especificados
def is_valid_domain(url):
    domain = urlparse(url).netloc
    return domain in domain_mapping

# Função para filtrar links indesejados
def is_valid_link(link):
    invalid_paths = ['/banners/click/', '/atualidades']
    return not any(invalid_path in link for invalid_path in invalid_paths)

# Função para buscar links de uma URL
def get_links_from_url(url):
    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        sublinks = [link['href'] for link in links if link['href'].startswith('/') or link['href'].startswith('https://') or link['href'].startswith('http://')]
        sublinks = [urljoin(url, sublink) for sublink in sublinks]  # Completa links relativos
        sublinks = [sublink for sublink in sublinks if is_valid_domain(sublink) and is_valid_link(sublink)]  # Filtra links fora dos domínios especificados e links inválidos
        return sublinks
    except requests.exceptions.SSLError as e:
        print(f"Erro SSL para {url}: {e}")
        return []
    except Exception as e:
        print(f"Erro ao buscar {url}: {e}")
        return []

# Função para obter todos os sublinks de uma lista de URLs
def get_all_sublinks(urls):
    all_sublinks = set()  
    for url in urls:
        sublinks = get_links_from_url(url)
        all_sublinks.update(sublinks)
    return list(all_sublinks)

# Função para gerar um nome de arquivo baseado na URL
def generate_filename(url, domain_code):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path.strip('/')
    query = parsed_url.query

    # Substituir caracteres inválidos para nomes de arquivo
    filename = re.sub(r'[<>:"/\\|?*]', '_', f"{domain}_{path}")
    
    # Adicionar a query se existir
    if query:
        filename += f"_{query}"

    # Limitar o tamanho do nome do arquivo
    if len(filename) > 180:
        filename = filename[:180]

    return f"{filename}_{domain_code}.md"

# Função para limpar o texto
def clean_text(text):
    # Remove the navigation menu
    text = re.sub(r'\| \[!\[Home\].*?---', '', text, flags=re.DOTALL)
    text = re.sub(r'\| \[!\[Suporte.IPB\].*?---', '', text, flags=re.DOTALL)
    text = re.sub(r'\| \[!\[ESA-IPB\].*?---', '', text, flags=re.DOTALL)
    
    # Remove the list of menu items
    text = re.sub(r'\* \[.*?\].*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove lines with code jQuery
    text = re.sub(r'jQuery\(.*\);', '', text)

    # Remove caracteres &nbsp;
    text = text.replace('&nbsp;', ' ')

    # Remove extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

# Função para remover texto após "### CookiesAccept"
def remove_after_cookies_accept(text):
    index = text.find('### CookiesAccept')
    if index != -1:
        return text[:index]
    return text

# Função para baixar o conteúdo HTML, converter para MD e salvar
def save_as_md(url, processed_urls):
    if url in processed_urls:
        print(f"Já processado: {url}")
        return
    
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            domain_code = get_domain_code(url)
            html_content = response.text
            
            # Converter HTML para Markdown
            markdown_content = html_converter.handle(html_content)
            
            # Limpar o conteúdo Markdown
            markdown_content = clean_text(markdown_content)
            
            # Remover texto após "### CookiesAccept"
            markdown_content = remove_after_cookies_accept(markdown_content)
            
            # Adicionar a URL fonte no topo do arquivo
            markdown_content = f"Source: {url}\n\n{markdown_content}"
            
            # Verificar se o conteúdo inclui "403 Forbidden"
            if "403 Forbidden" not in markdown_content:
                file_name = generate_filename(url, domain_code)
                
                # Salva o conteúdo Markdown em um arquivo
                if not os.path.exists('output'):
                    os.makedirs('output')
                
                file_path = os.path.join('output', file_name)
                with open(file_path, 'w', encoding='utf-8') as md_file:
                    md_file.write(markdown_content)
                
                print(f"Salvo: {file_path}")
                processed_urls.add(url)  # Adiciona a URL ao conjunto de processados
            else:
                print(f"O arquivo {url} será ignorado porque contém o texto '403 Forbidden'.")
        else:
            print(f"Falha ao baixar {url}: Código de status {response.status_code}")
    except requests.exceptions.SSLError as e:
        print(f"Erro SSL para {url}: {e}")
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")

# Execução principal
urls = [
    "https://portal3.ipb.pt/index.php/pt/",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos/licenciaturas",
    "https://portal3.ipb.pt/index.php/pt/guiaects/o-ects-no-ipb",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos/mestrados",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos/cursos-tecnicos-superiores-profissionais",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos/pos-graduacoes",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos/mestrados-profissionais",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos/doutoramentos",
    "https://portal3.ipb.pt/index.php/pt/guiaects/cursos-em-ingles",
    "https://portal3.ipb.pt/index.php/pt/guiaects/unidades-curriculares-em-ingles",
    "https://estig.ipb.pt/",
    "https://estig.ipb.pt/index.php/estig/estudar-na-estig/",
    "https://ese.ipb.pt/",
    "https://esa.ipb.pt/",
    "https://essa.ipb.pt/",
    "https://esact.ipb.pt/",
    "https://sas.ipb.pt/",
    "https://esact.ipb.pt/index.php/esact/alunos",
    "https://www.ese.ipb.pt/index.php/ese/estudar-na-ese",
    "https://essa.ipb.pt/index.php/essa/alunos",
    "https://sas.ipb.pt/index.php/sas/servicos/bolsas",
    "https://sas.ipb.pt/index.php/sas/servicos/alojamento",
    "https://sas.ipb.pt/index.php/sas/servicos/alimentacao",
    "https://www.ese.ipb.pt/index.php/ese/estudar-na-ese/horarios-calendarios",
    "https://portal3.ipb.pt/index.php/pt/portalcandidato/inicio"
]

# Buscar todos os sublinks
all_sublinks = get_all_sublinks(urls)

# Salvar todos os dados de sublinks em um arquivo JSON
with open('sublinks_data.json', 'w', encoding='utf-8') as json_file:
    json.dump(all_sublinks, json_file, indent=4)

print("Dados de sublinks salvos no arquivo sublinks_data.json.")

# Conjunto para armazenar URLs já processadas
processed_urls = set()

# Baixar, converter para MD e salvar cada sublink
for sublink in all_sublinks:
    save_as_md(sublink, processed_urls)