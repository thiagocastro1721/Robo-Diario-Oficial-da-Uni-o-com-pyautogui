#Leia as dicas abaixo!
"""
Caso o script não funcione, copie as duas linhas abaixo e cole no terminal, as duas de um vez. execute e tente novamente.
touch ~/.Xauthority
xauth generate :0 . trusted
"""
"""
Não esqueça de configurar o crond:
crontab -e
Abaixo segue um exemplo de terminal que permanece aberto. Bom para ver erros.
0 9 * * * DISPLAY=:0 qterminal -e bash -c '/usr/bin/python3 /home/thiago/Desktop/diarioOficial.py; exec bash'
Abaixo segue um exemplo de terminal que fecha após a execução.
0 9 * * * DISPLAY=:0 qterminal -e /usr/bin/python3 /home/thiago/Desktop/diarioOficial.py  
"""
import pyautogui
import time
import subprocess
import smtplib
from email.message import EmailMessage
import os
import glob
from datetime import datetime
import re

screenWidth, screenHeight = pyautogui.size()

print(pyautogui.size())
time.sleep(4)

#Abrir navegador Firefox
pyautogui.moveTo(210,751)
time.sleep(2)
pyautogui.click()
time.sleep(80)

def sendEmail(nome, novidade, erro, texto, screenshot_path=None):
    """
    Envia email com as informações do script
    novidade: 0 = sem novidades, 1 = há novidades
    erro: 0 = sem erro, 1 = houve erro
    """
    remetente = 'txhxfx@gmail.com'
    destinatario = 'txhxfx@gmail.com'
    mensagem = ''

    if erro == 1:
        assunto = f"""Erro no script FUB 25 do {nome}."""
        mensagem = f"""
        Segue texto copiado:
        {texto}
        """         
    elif novidade == 0:
        assunto = 'FUB 25 sem novidades.'
        mensagem = f"""
        {nome}, continue acreditando! 
        Deus é fiel!
        """  
    elif novidade == 1:
        assunto = 'ATENÇÃO! NOVIDADE FUB 25! VEJA O DOU!'
        mensagem = f"""
        Novidade para {nome}!
        Verifique o screenshot anexo.
        """   
    #Habilite a autenticação em duas etapas
    #Obtenha a senha do aplicativo em https://myaccount.google.com/apppasswords
    senha = 'dqwy mmsz mqos zcvc'  

    msg = EmailMessage()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.set_content(mensagem) 

    # Anexar screenshot se houver
    if screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, 'rb') as f:
            img_data = f.read()
            filename = 'novidade_screenshot.png' if novidade == 1 else 'erro_screenshot.png'
            msg.add_attachment(img_data, maintype='image', subtype='png', filename=filename)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as email:
            email.login(remetente, senha)
            email.send_message(msg)
        print(f"Email enviado com sucesso para {nome}!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def capturar_screenshot(pasta, prefixo=''):
    """
    Captura screenshot e salva na pasta especificada
    Retorna o caminho do arquivo salvo
    """
    # Cria pasta se não existir
    os.makedirs(pasta, exist_ok=True)
    
    # Captura screenshot com nome no formato anomesdiahoraminuto
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    screenshot_path = f'{pasta}/{prefixo}{timestamp}.png'
    pyautogui.screenshot(screenshot_path)
    
    print(f"Screenshot salvo em: {screenshot_path}")
    return screenshot_path

def limpar_screenshots_antigos(pasta, limite=10):
    """
    Remove screenshots antigos se houver mais que o limite especificado
    """
    arquivos = sorted(glob.glob(f'{pasta}/*.png'), key=os.path.getmtime)
    while len(arquivos) > limite:
        arquivo_remover = arquivos.pop(0)
        try:
            os.remove(arquivo_remover)
            print(f"Screenshot antigo removido: {arquivo_remover}")
        except Exception as e:
            print(f"Erro ao remover arquivo {arquivo_remover}: {e}")

#Análise do texto copiado
#A função analizeDOU recebe como parâmetro as coordenadas x e y do favorito do navegador ao qual deseja-se conectar.
def analizeDOU(nome, favX, favY):
    """
    Analisa o DOU para verificar novidades sobre o concurso FUB 25
    """
    # Limpa a área de transferência
    subprocess.run(['xclip', '-selection', 'clipboard', '-i'], input=b'', check=False)
    time.sleep(1)
    print(f"Área de transferência limpa para {nome}")
    
    #Nova aba
    pyautogui.hotkey('ctrl', 't')
    time.sleep(20)

    #Favorito DOU
    pyautogui.moveTo(favX, favY)
    time.sleep(60)
    pyautogui.click()
    time.sleep(60)

    #Scroll
    pyautogui.scroll(-5)
    time.sleep(6)

    #Selecionar texto
    pyautogui.moveTo(400, 161)
    time.sleep(2)
    pyautogui.mouseDown()
    time.sleep(2)
    pyautogui.moveTo(541, 330, duration=4)
    time.sleep(2)
    pyautogui.mouseUp()
    time.sleep(2)

    #Copia texto
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(6)

    #Pega o texto copiado
    texto = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True).stdout

    #Extrai números
    numeros = re.findall(r'\d+', texto) 

    #Análise do texto copiado
    # Definir quantidade esperada de editais por pessoa
    editais_esperados = {
        'Thiago': 9,
        'Italo': 13
    }
    
    edital_referencia = "EDITAL Nº 8 - FUB, DE 19 DE SETEMBRO DE 2025"

    if numeros and "resultado" in texto:
        primeiro_numero = int(numeros[0])
        quantidade_esperada = editais_esperados.get(nome, 0)
        
        # Verifica se está tudo conforme esperado
        if primeiro_numero == quantidade_esperada and edital_referencia in texto:
            print(f"FUB 25 SEM NOVIDADE para {nome}!")
            print(f"{primeiro_numero} editais foram encontrados.")
            print(f"O {edital_referencia} AINDA É O ÚLTIMO.")
            sendEmail(nome, 0, 0, '')
        else:
            # HÁ NOVIDADE!
            print(f"ATENÇÃO! HÁ NOVIDADE DO CONCURSO FUB 25 PARA {nome}!")
            print(f"Número de editais encontrados: {primeiro_numero}")
            print(f"Esperado: {quantidade_esperada}")
            
            # Captura screenshot da novidade
            pasta_novidades = '/home/thiago/Desktop/FUB_2025_novidades'
            screenshot_path = capturar_screenshot(pasta_novidades, f'{nome}_')
            
            # Limpa screenshots antigos (mantém últimos 20)
            limpar_screenshots_antigos(pasta_novidades, 20)
            
            # Envia email com screenshot
            sendEmail(nome, 1, 0, '', screenshot_path)
    else:
        print(f"Ocorreu algum Erro para {nome}! Verifique!")
        
        # Captura screenshot do erro
        pasta_erros = '/home/thiago/Desktop/prints_dos_erros_do_script'
        screenshot_path = capturar_screenshot(pasta_erros, f'{nome}_erro_')
        
        # Limpa screenshots antigos de erro (mantém últimos 10)
        limpar_screenshots_antigos(pasta_erros, 10)
        
        # Envia email com screenshot do erro
        sendEmail(nome, 0, 1, texto, screenshot_path)


# Executa análise para cada pessoa
analizeDOU('Thiago', 59, 121)
analizeDOU('Italo', 157, 121)

#Fecha abas abertas
time.sleep(20)
pyautogui.hotkey('ctrl', 'w')
time.sleep(20)
pyautogui.hotkey('ctrl', 'w')
time.sleep(20)
pyautogui.hotkey('ctrl', 'w')
