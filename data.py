import scrapy
import os
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin
import fitz  # PyMuPDF
import io


class DiarioSpider(scrapy.Spider):
    name = "diario_avare"

    custom_settings = {
        "FEEDS": {
            "diarios.json": {
                "format": "json",
                "encoding": "utf8",
                "indent": 4,
                "overwrite": True
            }
        },

        "USER_AGENT": "Mozilla/5.0"
    }

    start_urls = [
        "https://imprensaoficialmunicipal.com.br/listaatos.php?c=Avar%C3%A9&s=Decretos"
    ]

    def parse(self, response):

        diarios = []
        links_processados = set()

        # pega todos os links dos diários
        links = response.xpath(
            '//a[contains(@href,"exibe_do.php?i=")]'
        )

        for link in links:

            href = link.xpath("./@href").get()

            if not href:
                continue

            if "exibe_do.php?i=" not in href:
                continue

            link_completo = urljoin(response.url, href)

            # remove repetidos
            if link_completo in links_processados:
                continue

            links_processados.add(link_completo)

            # pega o título do h3 relacionado
            # pega o elemento li completo
            item = link.xpath("./ancestor::li[@class='lista'][1]")

            # pega o h3 dentro do li
            titulo = item.xpath(".//h3/text()").get()

            if not titulo:
                titulo = f"Diário {len(diarios)+1}"

            titulo = titulo.strip()

            diarios.append({
                "titulo": titulo,
                "link": link_completo
            })

            print("ADICIONADO:", titulo)

            
            if len(diarios) >= 20:
                break

        print(f"TOTAL: {len(diarios)}")

        for diario in diarios:

            yield scrapy.Request(
                diario["link"],
                callback=self.parse_diario,
                dont_filter=True,
                meta={
                    "diario": diario
                }
            )

    def parse_diario(self, response):

        diario = response.meta["diario"]

        conteudo = ""

        content_type = response.headers.get(
            "Content-Type",
            b""
        ).decode()

        # Se for PDF
        if "pdf" in content_type.lower():

            pdf = fitz.open(
                stream=response.body,
                filetype="pdf"
            )

            textos = []

            for pagina in pdf:
                textos.append(
                    pagina.get_text()
                )

            conteudo = "\n".join(textos)

        else:

            textos = response.xpath("//body//text()").getall()

            textos = [
                t.strip()
                for t in textos
                if t.strip()
            ]

            conteudo = " ".join(textos)

        yield {
            "titulo": diario["titulo"],
            "link": diario["link"],
            "conteudo": conteudo
        }


# remove json antigo
if os.path.exists("diarios.json"):
    os.remove("diarios.json")


process = CrawlerProcess()

process.crawl(DiarioSpider)

process.start()