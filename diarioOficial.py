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
screenWidth, screenHeight = pyautogui.size()
import smtplib
from email.message import EmailMessage

print(pyautogui.size())
time.sleep(2)

#Abrir navegador Firefox
pyautogui.moveTo(210,751)
time.sleep(1)
pyautogui.click()
time.sleep(40)

#Variaveis Globais
novidade = 0
nome = ''

def sendEmail(name, novidade):
    #Enviar Email
    remetente = 'txhxfx@gmail.com'
    destinatario = 'txhxfx@gmail.com'
    mensagem = ''

    if novidade == 0:
        assunto = 'Sem novidades.'
        mensagem = f"""
        {nome}, continue acreditando! 
        Deus é fiel!
        """  
    else:
        assunto = 'ATENÇÃO! NOVIDADE FUB 25! VEJA O DOU!'
        mensagem = f"""
        Novidade para {nome}!
        """   
    #Habilite a autenticação em duas etapas
    #Obtenha a senha do aplicativo em https://myaccount.google.com/apppasswords
    senha = 'xxxx xxxx xxxx xxxx'  

    msg = EmailMessage()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.set_content(mensagem) 

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as email:
        email.login(remetente, senha)
        email.send_message(msg) 

#Análise do texto copiado
#A função analizeDOU recebe como parâmetro as coordenadas x e y do favorito do navegador ao qual deseja-se conectar.
def analizeDOU(favX, favY):
    #Nova aba
    pyautogui.hotkey('ctrl', 't')
    time.sleep(10)

    #Favorito DOUThiago
    #pyautogui.moveTo(59, 121)
    pyautogui.moveTo(favX, favY)
    time.sleep(30)
    pyautogui.click()
    time.sleep(30)

    #Scroll
    pyautogui.scroll(-5)
    time.sleep(3)

    #Selecionar texto
    pyautogui.moveTo(400, 161)
    time.sleep(1)
    pyautogui.mouseDown()
    time.sleep(1)
    pyautogui.moveTo(541, 330, duration=2)
    time.sleep(1)
    pyautogui.mouseUp()
    time.sleep(1)

    #Copia texto
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(3)

    #Pega o texto copiado
    #texto = pyperclip.paste()
    texto = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True).stdout

    #Extrai números
    import re
    numeros = re.findall(r'\d+', texto)

    #Senha DouBot
    #dqwy mmsz mqos zcvc 

    #Análise do texto copiado

    if numeros:
        primeiro_numero = int(numeros[0])
        if nome == 'Thiago' and primeiro_numero == 9 and "EDITAL Nº 8 - FUB, DE 19 DE SETEMBRO DE 2025" in texto:
            print("SEM NOVIDADE!")
            print("9 editais foram encontrados.")
            print("O EDITAL Nº 8 - FUB, DE 19 DE SETEMBRO DE 2025 AINDA É O ÚLTIMO.")
            sendEmail(nome, 0)
        elif nome == 'Italo' and primeiro_numero == 13 and "EDITAL Nº 8 - FUB, DE 19 DE SETEMBRO DE 2025" in texto:
            print("SEM NOVIDADE!")
            print("13 editais foram encontrados.")
            print("O EDITAL Nº 8 - FUB, DE 19 DE SETEMBRO DE 2025 AINDA É O ÚLTIMO.")
            sendEmail(nome, 0)    
        else:
            print("ATENÇÃO! HÁ ALGUMA NOVIDADE DO CONCURSO FUB 25!")
            sendEmail(nome, 1)
    else:
        print("Ocorreu algum Erro! Verifique!")
    novidade = 0

nome = 'Thiago'
analizeDOU(59, 121)
nome = 'Italo'
analizeDOU(157, 121)

#Fecha abas abertas
time.sleep(10)
pyautogui.hotkey('ctrl', 'w')
time.sleep(10)
pyautogui.hotkey('ctrl', 'w')
time.sleep(10)
pyautogui.hotkey('ctrl', 'w')    

 
        
