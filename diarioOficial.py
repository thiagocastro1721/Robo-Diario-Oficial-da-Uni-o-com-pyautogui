#!/usr/bin/env python3
"""
Monitor de Editais DOU - FUB 25
Versão otimizada que usa requisições HTTP e só abre navegador quando necessário

AGENDAMENTOS DE TAREFAS

AGENDAR PARA LIGAR COMPUTADOR:

sudo nano /usr/local/bin/agendar_boot.sh

#!/bin/bash
#Agenda o próximo boot para amanhã às 08:00
#rtcwake -m no -t $(date +%s -d 'tomorrow 08:00')
#rtcwake -m off --date "tomorrow 08:00"
DATA=$(date -d "tomorrow 08:00" "+%Y-%m-%d %H:%M:%S")
rtcwake -m off --date "$DATA"



sudo nano /etc/systemd/system/agendar-boot.service

[Unit]
Description=Agenda boot RTC para o dia seguinte
DefaultDependencies=no
Before=poweroff.target reboot.target halt.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/agendar_boot.sh

[Install]
WantedBy=poweroff.target reboot.target halt.target


sudo chmod +x /usr/local/bin/agendar_boot.sh

sudo systemctl enable agendar-boot.service
sudo systemctl daemon-reload
sudo rtcwake -m off --date "2026-01-10 08:00"


EXECUTAR SCRIPT E AGENDAR DESLIGAMENTO:
Configuração do crontab para ligar o computador, executar o script e depois desligar computador todos os dias:
O comando shutdown, para deligar o computador, requer  acesso root.
A configuração abaixo fará com que não seja solicidata a senha ao usuário quando usar o shotdown.

Edite o sudoers:
sudo visudo
adicione ao fim do arquivo visudo:
thiago ALL=(ALL) NOPASSWD: /sbin/shutdown

A configuração a seguir irá executar o script todos os dias as 9h e depois iŕá deligar o computador ás 10h.

crontab -e
0 9 * * * DISPLAY=:0 /usr/bin/python3 /home/thiago/Desktop/diarioOficial.py
0 10 * * * /sbin/shutdown -h now
"""

import requests
import pyautogui
import time
import subprocess
import smtplib
from email.message import EmailMessage
import os
import glob
from datetime import datetime
import re

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

PESSOAS = {
    'Fulano': {
        'url': 'https://www.in.gov.br/consulta/-/buscar/dou?q=%22FULANO+DE+TALS%22&s=todos&exactDate=all&sortType=0',
        'numero_de_editais_com_o_padrao_de_data_no_titulo': 3,
        'numero_de_editais_encontrados_na_pesquisa_do_site': 9,
        'fav_x': 59,
        'fav_y': 121
    },
    'Beltrano': {
        'url': 'https://www.in.gov.br/consulta/-/buscar/dou?q=%22BELTRANO+DE+TALS%22&s=todos&exactDate=all&sortType=0',
        'numero_de_editais_com_o_padrao_de_data_no_titulo': 5,
        'numero_de_editais_encontrados_na_pesquisa_do_site': 7,
        'fav_x': 157,
        'fav_y': 121
    }
}
#print(PESSOAS['Thiago']['url'])


EDITAL_REFERENCIA = "EDITAL Nº 8 - FUB, DE 19 DE SETEMBRO DE 2025"
DATA_REFERENCIA = datetime(2025, 9, 19)

EMAIL_CONFIG = {
    'remetente': 'email@gmail.com',
    'destinatario': 'email@gmail.com',
    'senha': 'xxxx xxxx xxxx xxxx'
}

# ============================================================================
# FUNÇÕES DE CAPTURA WEB
# ============================================================================

def capturar_html(url, max_tentativas=10):
    """Captura o HTML de uma URL com múltiplas tentativas"""
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"  Tentativa {tentativa}/{max_tentativas}: Buscando dados...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            resposta = requests.get(url, headers=headers, timeout=180)
            resposta.raise_for_status()
            
            print(f"  ✓ Sucesso! Status: {resposta.status_code}")
            return resposta.text
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Erro na tentativa {tentativa}: {e}")
            if tentativa < max_tentativas:
                time.sleep(4)
            else:
                print("  ✗ Todas as tentativas falharam.")
                return None
        except Exception as e:
            print(f"  ✗ Erro inesperado: {e}")
            return None


def extrair_numero_resultados(html, nome):
    """Extrai o número de resultados da busca do padrão 'X resultados para <strong>\"Nome\"</strong>'"""
    
    # Tenta vários padrões possíveis, do mais específico ao mais genérico
    padroes = [
        # Padrão 1: Com aspas duplas literais no HTML
        r'(\d+)\s+resultados?\s+para\s+<strong>"[^"]*"</strong>',
        
        # Padrão 2: Com aspas simples
        r"(\d+)\s+resultados?\s+para\s+<strong>'[^']*'</strong>",
        
        # Padrão 3: Sem aspas
        r'(\d+)\s+resultados?\s+para\s+<strong>[^<]+</strong>',
        
        # Padrão 4: Mais genérico, captura qualquer coisa depois de "resultados para"
        r'(\d+)\s+resultados?\s+para\s+<strong>',
        
        # Padrão 5: Versão HTML escapada
        r'(\d+)\s+resultados?\s+para\s+&lt;strong&gt;',
    ]
    
    for i, padrao in enumerate(padroes, 1):
        match = re.search(padrao, html, re.IGNORECASE)
        if match:
            numero = int(match.group(1))
            print(f"  Número de resultados encontrados: {numero} (padrão {i})")
            return numero
    
    # Se nenhum padrão funcionou, tenta buscar especificamente pelo nome
    # Escapa caracteres especiais do nome para uso em regex
    nome_escapado = re.escape(nome)
    padrao_com_nome = rf'(\d+)\s+resultados?\s+para.*?{nome_escapado}'
    match = re.search(padrao_com_nome, html, re.IGNORECASE | re.DOTALL)
    if match:
        numero = int(match.group(1))
        print(f"  Número de resultados encontrados: {numero} (busca por nome)")
        return numero
    
    # Debug: Mostra trechos do HTML que contêm "resultados para"
    print(f"  ⚠️  Não foi possível encontrar o número de resultados no HTML")
    print(f"  Debug: Procurando por 'resultados para' no HTML...")
    
    # Busca ocorrências de "resultados para" para debug
    debug_matches = re.finditer(r'.{0,50}resultados?\s+para.{0,100}', html, re.IGNORECASE)
    for idx, match in enumerate(debug_matches, 1):
        if idx <= 3:  # Mostra apenas as 3 primeiras ocorrências
            trecho = match.group(0).replace('\n', ' ').strip()
            print(f"  Ocorrência {idx}: ...{trecho}...")
    
    return None


def extrair_data_edital(texto):
    """Extrai a data do edital no formato 'DE DD DE MMMM DE AAAA'"""
    padrao = r'DE\s+(\d{1,2})\s+DE\s+([A-ZÇÃÕ]+)\s+DE\s+(\d{4})'
    match = re.search(padrao, texto, re.IGNORECASE)
    
    if match:
        dia = match.group(1)
        mes_nome = match.group(2).upper()
        ano = match.group(3)
        
        meses = {
            'JANEIRO': 1, 'FEVEREIRO': 2, 'MARÇO': 3, 'ABRIL': 4,
            'MAIO': 5, 'JUNHO': 6, 'JULHO': 7, 'AGOSTO': 8,
            'SETEMBRO': 9, 'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
        }
        
        mes = meses.get(mes_nome)
        if mes:
            try:
                data_obj = datetime(int(ano), mes, int(dia))
                return texto, data_obj
            except:
                pass
    
    return None, None


def analisar_editais_html(html, nome):
    """Analisa o HTML e retorna informações sobre os editais"""
    if not html:
        return None
    
    # Extrai o número de resultados da busca
    num_resultados = extrair_numero_resultados(html, nome)
    
    # Procura por títulos de editais no JSON
    #padrao_titulo = r'"title":"([^"]*EDITAL[^"]*FUB[^"]*)"'
    padrao_titulo = r'"title":"([^"]*DE \d{1,2} DE [A-ZÇÃÕ]+ DE \d{4}[^"]*)"'
    titulos = re.findall(padrao_titulo, html, re.IGNORECASE)
    
    total_editais = len(titulos)
    editais_com_data = []
    
    # Extrai datas dos editais
    for titulo in titulos:
        data_str, data_obj = extrair_data_edital(titulo)
        if data_str and data_obj:
            editais_com_data.append({
                'titulo': titulo,
                'data_obj': data_obj
            })
    
    # Ordena por data (mais recente primeiro)
    editais_com_data.sort(key=lambda x: x['data_obj'], reverse=True)
    
    edital_mais_recente = editais_com_data[0] if editais_com_data else None
    
    return {
        'total_editais': total_editais,
        'num_resultados': num_resultados,
        'edital_mais_recente': edital_mais_recente,
        'todos_editais': editais_com_data
    }

# ============================================================================
# FUNÇÕES DE SCREENSHOT E EMAIL
# ============================================================================

def obter_caminho_desktop():
    """Retorna o caminho para a pasta Desktop"""
    return os.path.join(os.path.expanduser('~'), 'Desktop')


def capturar_screenshot(pasta, prefixo=''):
    """Captura screenshot e salva na pasta especificada"""
    try:
        os.makedirs(pasta, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        screenshot_path = os.path.join(pasta, f'{prefixo}{timestamp}.png')
        pyautogui.screenshot(screenshot_path)
        print(f"  ✓ Screenshot salvo em: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"  ✗ Erro ao capturar screenshot: {e}")
        return None


def limpar_screenshots_antigos(pasta, limite=10):
    """Remove screenshots antigos se houver mais que o limite"""
    arquivos = sorted(glob.glob(f'{pasta}/*.png'), key=os.path.getmtime)
    while len(arquivos) > limite:
        arquivo_remover = arquivos.pop(0)
        try:
            os.remove(arquivo_remover)
            print(f"  ✓ Screenshot antigo removido: {os.path.basename(arquivo_remover)}")
        except Exception as e:
            print(f"  ✗ Erro ao remover arquivo: {e}")


def sendEmail(nome, novidade, erro, detalhes='', screenshot_path=None):
    """Envia email com as informações do script"""
    cfg = EMAIL_CONFIG
    
    if erro == 1:
        assunto = f"Erro no script FUB 25 do {nome}"
        mensagem = f"Ocorreu um erro ao verificar os editais.\n\nDetalhes:\n{detalhes}\n\nAcesse o DOU:\n{PESSOAS[nome]['url']}"
        
    elif novidade == 0:
        assunto = 'FUB 25 sem novidades'
        mensagem = f"{nome}, continue acreditando!\nDeus é fiel!\n\n{detalhes}\n\nAcesse o DOU:\n{PESSOAS[nome]['url']}"
    elif novidade == 1:
        assunto = 'ATENÇÃO! NOVIDADE FUB 25! VEJA O DOU!'
        assunto = f'⚠️ {assunto} ⚠️'
        mensagem = f"Novidade para {nome}!\n\n{detalhes}\n\nAcesse o DOU:\n{PESSOAS[nome]['url']}\n\nVerifique o screenshot anexo."
    
    msg = EmailMessage()
    msg['From'] = cfg['remetente']
    msg['To'] = cfg['destinatario']
    msg['Subject'] = assunto
    msg.set_content(mensagem)
    
    # Anexar screenshot se houver
    if screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, 'rb') as f:
            img_data = f.read()
            filename = f'{nome}_{"novidade" if novidade == 1 else "erro"}.png'
            msg.add_attachment(img_data, maintype='image', subtype='png', filename=filename)
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as email:
            email.login(cfg['remetente'], cfg['senha'])
            email.send_message(msg)
        print(f"  ✓ Email enviado com sucesso!")
    except Exception as e:
        print(f"  ✗ Erro ao enviar email: {e}")

# ============================================================================
# FUNÇÕES DE NAVEGADOR (BACKUP)
# ============================================================================

def abrir_navegador_e_capturar(nome, fav_x, fav_y):
    """Abre o navegador e captura screenshot (usado quando há novidade)"""
    print(f"  → Abrindo navegador para capturar screenshot...")
    
    screenWidth, screenHeight = pyautogui.size()
    print(f"  Resolução da tela: {screenWidth}x{screenHeight}")
    
    # Abrir Firefox
    pyautogui.moveTo(210, 751)
    time.sleep(4)
    pyautogui.click()
    time.sleep(60)
    
    # Nova aba
    pyautogui.hotkey('ctrl', 't')
    time.sleep(60)
    
    # Clica no favorito
    pyautogui.moveTo(fav_x, fav_y)
    time.sleep(8)
    pyautogui.click()
    time.sleep(60)
    
    # Scroll para mostrar conteúdo
    pyautogui.scroll(-5)
    time.sleep(60)
    
    # Captura screenshot
    desktop_path = obter_caminho_desktop()
    pasta_novidades = os.path.join(desktop_path, 'FUB_2025_novidades')
    screenshot_path = capturar_screenshot(pasta_novidades, f'{nome}_')
    
    # Fecha a aba
    time.sleep(20)
    pyautogui.hotkey('ctrl', 'w')
    time.sleep(20)
    pyautogui.hotkey('ctrl', 'w')

    
    return screenshot_path

# ============================================================================
# FUNÇÃO PRINCIPAL DE ANÁLISE
# ============================================================================

def verificar_pessoa(nome, config):
    """Verifica os editais de uma pessoa"""
    print("\n" + "="*80)
    print(f"VERIFICANDO EDITAIS PARA: {nome}")
    print("="*80)
    
    # 1. Captura o HTML
    html = capturar_html(config['url'])
    
    if not html:
        print(f"  ✗ Não foi possível acessar o site para {nome}")
        desktop_path = obter_caminho_desktop()
        pasta_erros = os.path.join(desktop_path, 'prints_dos_erros_do_script')
        screenshot_path = capturar_screenshot(pasta_erros, f'{nome}_erro_conexao_')
        sendEmail(nome, 0, 1, "Falha ao acessar o site do DOU", screenshot_path)
        return
    
    # 2. Analisa os editais
    resultado = analisar_editais_html(html, nome)
    
    if not resultado:
        print(f"  ✗ Não foi possível analisar os editais para {nome}")
        desktop_path = obter_caminho_desktop()
        pasta_erros = os.path.join(desktop_path, 'prints_dos_erros_do_script')
        screenshot_path = capturar_screenshot(pasta_erros, f'{nome}_erro_analise_')
        sendEmail(nome, 0, 1, "Erro ao analisar os editais", screenshot_path)
        return
    
    total = resultado['total_editais']
    esperado = config['numero_de_editais_com_o_padrao_de_data_no_titulo']
    num_resultados = resultado['num_resultados']
    numero_de_editais_encontrados_na_pesquisa_do_site = config['numero_de_editais_encontrados_na_pesquisa_do_site']
    mais_recente = resultado['edital_mais_recente']
    
    print(f"\n  Total de editais com data encontrados: {total}")
    print(f"  Total de editais com data esperados: {esperado}")
    
    if num_resultados is not None:
        print(f"  Número de resultados no site: {num_resultados}")
        print(f"  Número de resultados esperados no site : {numero_de_editais_encontrados_na_pesquisa_do_site}")
    
    if mais_recente:
        print(f"  Edital mais recente: {mais_recente['titulo'][:80]}...")
        print(f"  Data: {mais_recente['data_obj'].strftime('%d/%m/%Y')}")
    
    # 3. Verifica se há novidades
    tem_novidade = False
    motivo = []
    
    if total != esperado:
        tem_novidade = True
        motivo.append(f"Número de editais mudou: {esperado} → {total}")
    
    if num_resultados is not None and num_resultados != numero_de_editais_encontrados_na_pesquisa_do_site:
        tem_novidade = True
        motivo.append(f"Número de resultados no site mudou: {numero_de_editais_encontrados_na_pesquisa_do_site} → {num_resultados}")
    
    if mais_recente:
        if mais_recente['data_obj'] > DATA_REFERENCIA:
            tem_novidade = True
            motivo.append(f"Novo edital mais recente: {mais_recente['data_obj'].strftime('%d/%m/%Y')}")
            motivo.append(f"Título: {mais_recente['titulo'][:80]}...")
        elif EDITAL_REFERENCIA not in mais_recente['titulo']:
            tem_novidade = True
            motivo.append("Edital de referência não é o mais recente")
    
    # 4. Age conforme o resultado
    if tem_novidade:
        print(f"\n  ⚠️  NOVIDADE DETECTADA!")
        for m in motivo:
            print(f"      - {m}")
        
        # Abre navegador e captura screenshot
        screenshot_path = abrir_navegador_e_capturar(nome, config['fav_x'], config['fav_y'])
        
        # Limpa screenshots antigos
        desktop_path = obter_caminho_desktop()
        pasta_novidades = os.path.join(desktop_path, 'FUB_2025_novidades')
        limpar_screenshots_antigos(pasta_novidades, 20)
        
        # Envia email
        detalhes = f"Total de títulos com data: {total} (esperado: {esperado})\n"
        if num_resultados is not None:
            detalhes += f"Número de resultados no site: {num_resultados} (esperado: {numero_de_editais_encontrados_na_pesquisa_do_site})\n"
        detalhes += "\n".join(motivo)
        sendEmail(nome, 1, 0, detalhes, screenshot_path)
        
    else:
        print(f"\n  ✓ SEM NOVIDADES")
        print(f"      - {total} editais com data encontrados (conforme esperado)")
        if num_resultados is not None:
            print(f"      - {num_resultados} resultados de editais encontrados no site (conforme esperado)")
        print(f"      - Edital de referência continua o mais recente")
        
        detalhes = f"Editais com data: {total}\n"
        if num_resultados is not None:
            detalhes += f"Número de resultados no site: {num_resultados}\n"
        detalhes += f"Edital mais recente: {EDITAL_REFERENCIA}"
        sendEmail(nome, 0, 0, detalhes,)

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MONITOR DE EDITAIS DOU - FUB 25")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80)
    
    try:
        # Verifica cada pessoa
        for nome, config in PESSOAS.items():
            verificar_pessoa(nome, config)
            time.sleep(10)  # Pausa entre verificações
        
        print("\n" + "="*80)
        print("VERIFICAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n✗ Execução interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
