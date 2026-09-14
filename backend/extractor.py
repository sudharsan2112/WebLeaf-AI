from bs4 import BeautifulSoup
from typing import Dict, Any
from .utils import clean_text

class Extractor:
    def __init__(self, html_content: str, url: str):
        self.soup = BeautifulSoup(html_content, "lxml")
        self.url = url

    def remove_unwanted_tags(self):
        unwanted_tags = [
            "nav", "footer", "header", "script", "style", "noscript", 
            "aside", "iframe", "form"
        ]
        for tag in unwanted_tags:
            for el in self.soup.find_all(tag):
                el.decompose()
        
        noise_selectors = [
            {"class_": lambda c: c and any(x in c.lower() for x in ["cookie", "popup", "ad", "banner", "menu", "sidebar", "nav"])}
        ]
        for selector in noise_selectors:
            for el in self.soup.find_all(**selector):
                el.decompose()

    def extract_content(self) -> Dict[str, Any]:
        self.remove_unwanted_tags()
        
        title = self.soup.title.string if self.soup.title else ""
        
        content_parts = []
        for element in self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'pre', 'code', 'table']):
            text = clean_text(element.get_text(separator=" "))
            if text:
                if element.name in ['h1', 'h2', 'h3']:
                    content_parts.append(f"\n\n# {text}\n")
                elif element.name in ['pre', 'code']:
                    content_parts.append(f"\n```\n{text}\n```\n")
                else:
                    content_parts.append(f"{text}\n")

        full_text = "".join(content_parts)
        
        return {
            "url": self.url,
            "title": clean_text(title),
            "text": full_text.strip()
        }
