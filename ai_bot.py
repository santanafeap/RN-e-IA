import os
import json

from decouple import config

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq


os.environ['GROQ_API_KEY'] = config('GROQ_API_KEY')


class DiarioBot:

    def __init__(self):

        self.__chat = ChatGroq(
            model='meta-llama/llama-4-scout-17b-16e-instruct',
            temperature=0
        )

    def resumir_diario(self, titulo, conteudo):

        prompt = PromptTemplate(
            input_variables=['titulo', 'conteudo'],
            template='''
Você é um analisador especializado em diários oficiais municipais.

Sua função é:
- analisar o conteúdo do diário
- identificar informações relevantes
- resumir de forma objetiva
- remover textos repetitivos, jurídicos e irrelevantes
- identificar automaticamente edição e data no conteúdo

IMPORTANTE:
- Retorne APENAS JSON válido
- NÃO use markdown
- NÃO use ```json
- NÃO escreva comentários
- NÃO escreva texto fora do JSON
- NÃO invente informações

REGRAS:
- Cada item deve possuir no máximo 2 linhas
- Não coloque "Diário x - " antes do título dos itens do json
- Evite repetir informações
- Use linguagem curta e objetiva
- Se não houver conteúdo em uma categoria, deixe []
- Ignore:
  - assinaturas
  - rodapés
  - autenticações
  - cabeçalhos repetidos
  - publicações duplicadas
  - textos legais sem ação prática

PRIORIZE:
- licitações
- valores
- contratos
- nomeações
- exonerações
- decretos
- leis
- compras públicas
- concursos
- processos seletivos
- alterações administrativas
- avisos importantes

Extraia do conteúdo:
- número/edição do diário
- data oficial publicada

FORMATO OBRIGATÓRIO:

{{
    "titulo": "",
    "data": "",
    "resumo": {{
        "licitacoes": [],
        "contratos": [],
        "nomeacoes": [],
        "leis_e_decretos": [],
        "outros": []
    }}
}}

EXEMPLO:

{{
    "titulo": "Edição nº 1452",
    "data": "Sexta-feira, 08 de maio de 2026",
    "resumo": {{
        "licitacoes": [
            "Pregão eletrônico para compra de medicamentos"
        ],
        "contratos": [
            "Renovação de contrato de coleta de lixo"
        ],
        "nomeacoes": [
            "Nomeação de servidor para Secretaria da Saúde"
        ],
        "leis_e_decretos": [
            "Decreto altera horário de funcionamento das repartições"
        ],
        "outros": [
            "Aviso de processo seletivo simplificado"
        ]
    }}
}}

TÍTULO ORIGINAL:
{titulo}

CONTEÚDO DO DIÁRIO:
{conteudo}
'''
        )

        chain = prompt | self.__chat | StrOutputParser()

        response = chain.invoke({
            'titulo': titulo,
            'conteudo': conteudo[:15000]
        })

        return response


def processar_diarios(
    arquivo_entrada='diarios.json',
    arquivo_saida='diarios_resumidos.json'
):

    bot = DiarioBot()

    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        diarios = json.load(f)

    resultado_final = []

    for diario in diarios:

        titulo = diario.get('titulo', '')
        link = diario.get('link', '')
        conteudo = diario.get('conteudo', '')

        try:

            resumo = bot.resumir_diario(
                titulo=titulo,
                conteudo=conteudo
            )

            resumo_json = json.loads(resumo)

            resumo_json['link'] = link

            resultado_final.append(resumo_json)

            print(f'[OK] {titulo}')

        except Exception as e:

            print(f'[ERRO] {titulo}')
            print(e)

    with open(arquivo_saida, 'w', encoding='utf-8') as f:

        json.dump(
            resultado_final,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(f'\nArquivo gerado: {arquivo_saida}')


if __name__ == '__main__':

    processar_diarios()