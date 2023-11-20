from fastapi import FastAPI, HTTPException
import pyodbc
from typing import List
from pydantic import BaseModel
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Definindo o modelo das certidões
class Certidao(BaseModel):
    nome: str
    id_ambito: int
    estado: str
    cidade: str
    data_criacao: str
    id_status: int


# Função para criar uma conexão com o banco de dados
def criar_conexao_bd():
    return pyodbc.connect('Driver={SQL Server};'
                          'Server=DESKTOP-K9Q4OE3;'
                          'Database=PythonSQL;'
                          'Trusted_Connection=yes;')


# Rota para buscar todas as certidões no banco de dados
@app.get('/certidao', response_model=List[dict])
async def buscar_todas_certidoes():
    print("Rota /certidao foi chamada")
    conn = None
    try:
        # Criando uma nova conexão com o banco de dados
        conn = criar_conexao_bd()
        cursor = conn.cursor()

        # Comando SQL a ser executado
        cursor.execute('SELECT * FROM Certidoes;')

        # Busque todas as linhas como dicionários
        rows = cursor.fetchall()
        colunas = [coluna[0] for coluna in cursor.description]
        resultado = [dict(zip(colunas, linha)) for linha in rows]

        return resultado

    except pyodbc.Error:
        return []

    finally:
        if conn:
            # Fechando a conexão que foi criada com o banco de dados
            conn.close()


@app.get('/certidao/{cod_certidao}', response_model=Certidao)
async def buscar_certidao_por_cod(cod_certidao: int):
    conn = None
    try:
        # Criando uma nova conexão com o banco de dados
        conn = criar_conexao_bd()
        cursor = conn.cursor()

        # Comando SQL para buscar a certidão pelo ID
        # Comando SQL para buscar a certidão pelo ID e formatar a data
        cursor.execute(
            'SELECT nome, id_ambito, estado, cidade, FORMAT(data_criacao, \'yyyy-MM-dd HH:mm:ss\') AS data_criacao, '
            'id_status FROM Certidoes WHERE cod_certidao = ?;',
            cod_certidao)

        certidao = cursor.fetchone()

        if not certidao:
            raise HTTPException(status_code=404, detail="Certidão não encontrada")

        # Mapeando os resultados para o objeto Certidao
        resultado = Certidao(
            nome=certidao.nome,
            id_ambito=certidao.id_ambito,
            estado=certidao.estado,
            cidade=certidao.cidade,
            data_criacao=certidao.data_criacao,
            id_status=certidao.id_status,
        )

        return resultado

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")

    finally:
        if conn:
            conn.close()


@app.post('/certidao', response_model=Certidao)
async def inserir_certidao(certidao: Certidao):
    conn = None
    try:
        # Criando uma nova conexão com o banco de dados
        conn = criar_conexao_bd()
        cursor = conn.cursor()

        # Comando SQL para inserir uma nova certidão
        cursor.execute(
            'INSERT INTO Certidoes (nome, id_ambito, estado, cidade, data_criacao, id_status) '
            'VALUES (?, ?, ?, ?, ?, ?);',
            certidao.nome,
            certidao.id_ambito,
            certidao.estado,
            certidao.cidade,
            certidao.data_criacao,
            certidao.id_status,
        )

        # Commit para salvar as alterações no banco de dados
        conn.commit()

        # Recuperando o ID da certidão recém-inserida
        cursor.execute('SELECT SCOPE_IDENTITY();')
        new_certidao_id = cursor.fetchone()[0]

        # Criando e retornando um objeto Certidao com os outros campos
        certidao_inserida = Certidao(
            nome=certidao.nome,
            id_ambito=certidao.id_ambito,
            estado=certidao.estado,
            cidade=certidao.cidade,
            data_criacao=certidao.data_criacao,
            id_status=certidao.id_status,
        )

        return certidao_inserida

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")

    finally:
        if conn:
            conn.close()


@app.delete('/certidao/{cod_certidao}', response_model=dict)
async def excluir_certidao(cod_certidao: int):
    conn = None
    try:
        # Criando uma nova conexão com o banco de dados
        conn = criar_conexao_bd()
        cursor = conn.cursor()

        # Verificando se a certidão com o ID especificado existe
        cursor.execute('SELECT * FROM Certidoes WHERE cod_certidao = ?;', cod_certidao)
        certidao = cursor.fetchone()

        if not certidao:
            raise HTTPException(status_code=404, detail="Certidão não encontrada")

        # Comando SQL para excluir a certidão
        cursor.execute('DELETE FROM Certidoes WHERE cod_certidao = ?;', cod_certidao)

        # Commit para salvar as alterações no banco de dados
        conn.commit()

        return {"message": "Certidão excluída com sucesso"}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")

    finally:
        if conn:
            conn.close()


@app.put('/certidao/{cod_certidao}', response_model=Certidao)
async def atualizar_certidao(cod_certidao: int, certidao: Certidao):
    conn = None
    try:
        # Criando uma nova conexão com o banco de dados
        conn = criar_conexao_bd()
        cursor = conn.cursor()

        # Verificando se a certidão com o ID especificado existe
        cursor.execute('SELECT * FROM Certidoes WHERE cod_certidao = ?;', cod_certidao)
        certidao_existente = cursor.fetchone()

        if not certidao_existente:
            raise HTTPException(status_code=404, detail="Certidão não encontrada")

        # Comando SQL para atualizar a certidão
        cursor.execute(
            'UPDATE Certidoes SET nome = ?, id_ambito = ?, estado = ?, cidade = ?, data_criacao = ?, id_status = ? '
            'WHERE cod_certidao = ?;',
            certidao.nome,
            certidao.id_ambito,
            certidao.estado,
            certidao.cidade,
            certidao.data_criacao,
            certidao.id_status,
            cod_certidao
        )

        # Commit para salvar as alterações no banco de dados
        conn.commit()

        # Atualizando o objeto Certidao com os novos valores
        certidao_atualizada = Certidao(
            nome=certidao.nome,
            id_ambito=certidao.id_ambito,
            estado=certidao.estado,
            cidade=certidao.cidade,
            data_criacao=certidao.data_criacao,
            id_status=certidao.id_status,
        )

        return certidao_atualizada

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")

    finally:
        if conn:
            conn.close()


@app.get("/consulta_cnpj/{cnpj}")
def consulta_cnpj(cnpj: str):
    # Removendo caracteres não numéricos
    cnpj = ''.join(filter(str.isdigit, cnpj))

    # Solicitação à API ReceitaWS
    api_url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
    response = requests.get(api_url)

    if response.status_code == 200:
        # Retornando um json caso a solicitação for bem sucedida
        return response.json()
    else:
        # Retornando uma mensagem de erro, caso a solicitação falhe
        return {"error": "Falha na consulta", "status_code": response.status_code}
