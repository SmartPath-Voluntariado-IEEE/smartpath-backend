import httpx
from bs4 import BeautifulSoup


class WebScraperService:

    @staticmethod
    def scrape_course_page(url: str, max_chars: int = 15000) -> str:
        """
        Descarga el HTML de la página del curso y extrae el texto visible,
        limitado a max_chars para no exceder el contexto del modelo.
        """
        if not url or url.strip() == "#" or not url.startswith("http"):
            return ""

        try:
            response = httpx.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
                follow_redirects=True,
            )
            response.raise_for_status()
        except Exception as error:
            print(f"⚠️ [SCRAPER] No se pudo descargar {url}: {error}")
            return ""

        soup = BeautifulSoup(response.text, "html.parser")

        # Quita scripts, estilos y navegación, que no aportan contenido real
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Colapsa líneas vacías repetidas
        lines = [line for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        return clean_text[:max_chars]