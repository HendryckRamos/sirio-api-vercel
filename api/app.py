from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import io
import base64
import sys
from PyPDF2 import PdfReader
import google.generativeai as genai

app = Flask(__name__)
CORS(app) # Libera o HostGator para acessar a Vercel

API_DEFENSORIA = 'https://services.defensoria.pa.def.br/sirio-app-usuarios'
os.environ["GEMINI_API_KEY"] = "COLOQUE_SUA_API_KEY_AQUI" 
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

@app.route('/api/local/login', methods=['POST'])
def proxy_login():
    try:
        dados_front = request.get_json(force=True)
        payload = {"usuario": dados_front.get("cpf"), "senha": dados_front.get("senha")}
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Flutter-App'}
        res = requests.post(f"{API_DEFENSORIA}/enviar-codigo", json=payload, headers=headers)
        try: retorno = res.json()
        except: retorno = {"mensagem": res.text}
        return jsonify(retorno), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/usuario/verificar-login', methods=['POST'])
def proxy_verificar_login():
    try:
        dados_front = request.get_json(force=True)
        payload = {"usuario": dados_front.get("cpf"), "senha": dados_front.get("senha"), "codigo": dados_front.get("codigo")}
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Flutter-App'}
        res = requests.post(f"{API_DEFENSORIA}/access-token", json=payload, headers=headers)
        try: retorno = res.json()
        except: retorno = {"mensagem": res.text}
        return jsonify(retorno), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/usuario', methods=['POST'])
def proxy_cadastro():
    try:
        dados_front = request.get_json(force=True)
        payload = {
            "cpf": dados_front.get("cpf"), "apelido": dados_front.get("apelido"), "nome": dados_front.get("nome"),
            "sobrenome": dados_front.get("sobrenome"), "email": dados_front.get("email"),
            "senha": dados_front.get("senha"), "dataNascimento": dados_front.get("dataNascimento")
        }
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'Flutter-App'}
        res = requests.post(f"{API_DEFENSORIA}/usuario", json=payload, headers=headers)
        try: retorno = res.json()
        except: retorno = {"mensagem": res.text}
        return jsonify(retorno), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/usuario/ativar', methods=['POST'])
def proxy_ativar_conta():
    try:
        dados_front = request.get_json(force=True)
        payload = {
            "cpf": dados_front.get("cpf"),
            "codigo": dados_front.get("codigo") 
        } 
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Flutter-App'}
        
        # LOG DA REQUISIÇÃO ENVIADA
        print(f"👉 [VERCEL PROXY] Enviando ativação para Java. Payload: {payload}", file=sys.stderr)
        
        res = requests.post(f"{API_DEFENSORIA}/usuario/verificar-codigo", json=payload, headers=headers)
        
        # LOG DA RESPOSTA RECEBIDA DO JAVA
        print(f"👈 [VERCEL PROXY] Java respondeu com Status: {res.status_code}", file=sys.stderr)
        print(f"👈 [VERCEL PROXY] Java headers: {dict(res.headers)}", file=sys.stderr)
        print(f"👈 [VERCEL PROXY] Java body raw: {res.text}", file=sys.stderr)
        
        if res.status_code in [200, 202, 204]: 
            return jsonify({"mensagem": "Conta ativada com sucesso!"}), 200
            
        try: 
            retorno = res.json()
        except Exception as e:
            print(f"⚠️ [VERCEL PROXY] Falha ao decodificar JSON do Java: {str(e)}", file=sys.stderr)
            retorno = {"mensagem": res.text}
            
        return jsonify(retorno), res.status_code
    except Exception as e: 
        print(f"❌ [VERCEL PROXY] Exceção geral capturada: {str(e)}", file=sys.stderr)
        return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/usuario/envio-codigo', methods=['POST'])
def proxy_enviar_codigo():
    try:
        dados_front = request.get_json(force=True)
        payload = {"cpf": dados_front.get("cpf")}
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Flutter-App'}
        res = requests.post(f"{API_DEFENSORIA}/usuario/reenviar-codigo", json=payload, headers=headers)
        return jsonify({"mensagem": res.text}), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/integracao/v1/atendimento', methods=['GET'])
def proxy_listar_atendimentos():
    token = request.headers.get('Authorization')
    headers = {'Accept': 'application/json', 'User-Agent': 'Flutter-App', 'Authorization': token if token else ''}
    try:
        res = requests.get(f"{API_DEFENSORIA}/integracao/v1/atendimento?limit=100", headers=headers)
        return jsonify(res.json()), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/integracao/v1/processos', methods=['GET'])
def proxy_listar_processos():
    token = request.headers.get('Authorization')
    sirio_id = request.args.get('sirioId')
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': token if token else '', 'User-Agent': 'Flutter-App'}
    try:
        res = requests.get(f"{API_DEFENSORIA}/integracao/v1/atendimento/{sirio_id}/processo", headers=headers)
        return jsonify(res.json()), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/integracao/v1/processo/detalhes', methods=['GET'])
def proxy_detalhes_processo_completo():
    token = request.headers.get('Authorization')
    sirio_id = request.args.get('sirioId') 
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': token if token else '', 'User-Agent': 'Flutter-App'}
    try:
        res = requests.get(f"{API_DEFENSORIA}/integracao/v1/processo/{sirio_id}", headers=headers)
        return jsonify(res.json()), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/integracao/v1/processo/eventos', methods=['GET'])
def proxy_eventos_processo():
    token = request.headers.get('Authorization')
    sirio_id = request.args.get('sirioId')
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': token if token else '', 'User-Agent': 'Flutter-App'}
    try:
        res = requests.get(f"{API_DEFENSORIA}/integracao/v1/processo/{sirio_id}/evento", headers=headers)
        return jsonify(res.json()), res.status_code
    except Exception as e: return jsonify({"mensagem": str(e)}), 500

@app.route('/api/local/gemini/resumir', methods=['POST'])
def gemini_summary_real():
    try:
        token = request.headers.get('Authorization', '')
        dados_front = request.get_json(force=True)
        sirio_id = dados_front.get('sirioId')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': token, 'User-Agent': 'Flutter-App'}

        res_docs = requests.get(f"{API_DEFENSORIA}/integracao/v1/processo/{sirio_id}/documento", headers=headers)
        if res_docs.status_code != 200: return jsonify({"resumo": "Não foi possível resgatar o documento do tribunal."}), 200
            
        docs_data = res_docs.json().get('results', [])
        if not docs_data: return jsonify({"resumo": "Nenhum documento encontrado neste processo."}), 200

        doc_selecionado = docs_data[0]
        numero_doc = doc_selecionado.get('numero')
        
        res_doc_detail = requests.get(f"{API_DEFENSORIA}/integracao/v1/processo/{sirio_id}/documento/{numero_doc}", headers=headers)
        texto_extraido = ""
        is_pdf = 'application/pdf' in res_doc_detail.headers.get('content-type', '').lower()
        
        if is_pdf:
            reader = PdfReader(io.BytesIO(res_doc_detail.content))
            for page in reader.pages: texto_extraido += page.extract_text() or ""
        else:
            try:
                json_doc = res_doc_detail.json()
                conteudo_raw = json_doc.get('conteudo', '')
                if isinstance(conteudo_raw, str):
                    try:
                        bytes_pdf = base64.b64decode(conteudo_raw)
                        reader = PdfReader(io.BytesIO(bytes_pdf))
                        for page in reader.pages: texto_extraido += page.extract_text() or ""
                    except: texto_extraido = conteudo_raw
            except: texto_extraido = res_doc_detail.text

        if not texto_extraido.strip(): return jsonify({"resumo": "O documento é uma imagem ou scan legível apenas fisicamente."}), 200

        prompt = f"""Extraia as informações do processo abaixo.
Explique a fase atual do processo em texto direto e simples, como se você fosse um atendente humano da defensoria conversando com o cidadão. Não use jargões, não use tópicos, não use asteriscos, não cite que você é IA. Seja direto e tranquilizador.
Texto: {texto_extraido[:100000]}"""
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return jsonify({"resumo": response.text, "pontosChave": ""}), 200
    except Exception as e:
        return jsonify({"resumo": f"Não foi possível processar a leitura neste momento."}), 500
