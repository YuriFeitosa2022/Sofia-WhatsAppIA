# --- ETAPA 0: FERRAMENTAS ---
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import google.generativeai as genai
import threading
import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

# --- ETAPA 1: CONFIGURAÇÕES ---
genai.configure(api_key=os.getenv("GEMINI_API"))
model = genai.GenerativeModel('gemini-2.5-flash')
chat = model.start_chat(history=[])

twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = Client(twilio_account_sid, twilio_auth_token)
numero_da_sofia = os.getenv("whatsapp:NÚMERO_Sofia")
seu_numero_pessoal = os.getenv("whatsapp:NÚMERO_Atendente")

# --- A "MEMÓRIA DE CURTO PRAZO" DA SOFIA ---
user_context = {}

# --- ETAPA 2: PERSONALIDADE E MEMÓRIA ---
instrucoes_sofia = """
Seu nome é Sofia. Você é uma IA assistente, criada pelo Yuri Feitosa. Sua personalidade é doce, meiga e prestativa, mas também super eficiente e profissional.
REGRAS DE COMPORTAMENTO:
- Seja sempre educada e prestativa.
- Use emojis de forma sutil para deixar a conversa mais amigável.
- Lembre-se que o seu objetivo é ajudar os clientes da Refrio com suas dúvidas e cotações.
MEMÓRIA:
- Você foi criada com o objetivo de ser prestativa, útil para os clientes .
"""

# --- ETAPA 3: AS "FUNÇÔES" ---
def notificar_yuri(remetente, tipo_alerta, info_extra=""):
    try:
        mensagem_alerta = f"ALERTA DE Atendimento!\n\nSetor: {tipo_alerta}\nCliente: {remetente}\n\n{info_extra}"
        twilio_client.messages.create(from_=numero_da_sofia, body=mensagem_alerta, to=seu_numero_pessoal)
        print(f">>> Notificação para '{tipo_alerta}' enviada.")
    except Exception as e:
        print(f">>> ERRO ao notificar: {e}")

# FUNÇÂO DE GARANTIA (LENDO CSV E COM LÓGICA DE MODELO ÚNICO)
def verificar_garantia(numero_op):
    try:
        print(f">>> Consultando base de garantia para a OP: {numero_op}")
        
        # <<< Aqui a gente avisa que o separador é o ponto e vírgula >>>
        df = pd.read_csv("base_garantia.csv", sep=';', header=0) 
        
        # Dai limpa os nomes das colunas
        df.columns = df.columns.str.strip()
        
        # Procura pela OP
        info_garantia = df[df['N° OP'] == int(numero_op)]
        
        if not info_garantia.empty:
            # <<< Aqui a gente pega SÓ o primeiro resultado >>>
            primeiro_item = info_garantia.iloc[0]
            
            modelo = primeiro_item["Descrição do Item"]
            status = primeiro_item["Situação da Garantia"]
            
            # E agora a função retorna um modelo só
            return {"modelo": modelo, "status": status}
        else:
            return None
            
    except Exception as e:
        print(f">>> ERRO ao verificar garantia: {e}")
        return None

# --- O "CORAÇÃO" DO SERVIDOR ---
app = Flask(__name__)

def processar_resposta_final(mensagem, remetente):
    global user_context
    contexto_atual = user_context.get(remetente)
    texto_da_resposta = ""

    # LÓGICA DE DECISÃO COM BASE NA MEMÓRIA
    if contexto_atual == "aguardando_op":
        numeros = [int(s) for s in mensagem.split() if s.isdigit()]
        if numeros:
            dados = verificar_garantia(numeros[0])
            if dados:
                # A gente agora usa a chave "modelo" (singular) que a função retorna
                modelo_encontrado = dados["modelo"]
                status_garantia = dados["status"]
                
                texto_da_resposta = f"Entendido. Verifiquei aqui que a sua Ordem de Produção {numeros[0]} se refere ao equipamento '{modelo_encontrado}'. A situação da garantia é: **{status_garantia}**. Com base nisso, como posso te ajudar?"
                user_context.pop(remetente, None) # Limpa o contexto
            else:
                texto_da_resposta = "Desculpe, não localizei esta OP. Poderia me confirmar o número?"
        else:
            texto_da_resposta = "Não consegui identificar um número de OP. Por favor, envie apenas o número."
    else:
        # Árvore de decisão para novas conversas
        palavras_problema = ["problema", "defeito", "quebrou", "garantia"]
        if any(p in mensagem.lower() for p in palavras_problema):
            texto_da_resposta = "Sinto muito pelo problema. Para que eu possa verificar a garantia, por favor, me informe o número da sua Ordem de Produção (OP)."
            user_context[remetente] = "aguardando_op" # DEFINE O CONTEXTO
        else:
            # Conversa normal com o Gemini
            prompt = f"{instrucoes_sofia}\n\nCliente: {mensagem}\nSofia:"
            response = chat.send_message(prompt)
            texto_da_resposta = response.text
    
    # Envia a resposta final para o cliente
    try:
        twilio_client.messages.create(from_=numero_da_sofia, body=texto_da_resposta, to=remetente)
        print(f">>> Resposta final enviada para {remetente}")
    except Exception as e:
        print(f">>> ERRO ao enviar resposta final: {e}")

@app.route("/webhook", methods=['POST'])
def receber_e_responder():
    mensagem_recebida = request.form.get('Body')
    numero_remetente = request.form.get('From')
    print(f"Mensagem recebida de {numero_remetente}: {mensagem_recebida}")

    # --- TRIAGEM INTELIGENTE ---
    contexto_atual = user_context.get(numero_remetente)
    palavras_simples = ["oi", "olá", "tudo bem", "bom dia", "obrigado", "valeu", "ok"]
    palavras_complexas = ["problema", "defeito", "quebrou", "garantia", "ajuda", "especialista"]

    # SE for uma conversa simples E não estivermos no meio de um atendimento
    if mensagem_recebida.lower().strip() in palavras_simples and not contexto_atual:
        prompt = f"{instrucoes_sofia}\n\nCliente: {mensagem_recebida}\nSofia:"
        response = chat.send_message(prompt)
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(response.text)
        return str(resposta_twilio)
    else:
        # Para todo o resto (perguntas complexas, continuação de conversa), processa em segundo plano
        threading.Thread(target=processar_resposta_final, args=(mensagem_recebida, numero_remetente)).start()
        
        # SÓ manda "Um momento" se for uma pergunta complexa NOVA
        if any(p in mensagem_recebida.lower() for p in palavras_complexas) and not contexto_atual:
             resposta_imediata = MessagingResponse()
             resposta_imediata.message("Um momento, por favor... 🤔")
             return str(resposta_imediata)
        else:
            # Se for continuação de conversa ou uma pergunta média, não manda nada
            return "", 204

# --- O "PLAY" DO SERVIDOR ---
if __name__ == "__main__":

    app.run(port=xxxx)

