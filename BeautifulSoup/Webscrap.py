import requests
from bs4 import BeautifulSoup
import json

# URL for recent Machine Learning topics on arXiv
url = "https://arxiv.org/list/stat.ML/recent"

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all article entries
articles = soup.find_all("dd")

articleInfo = []
for article in articles:
    title_tag = article.find_previous_sibling("dt").find("div", class_="list-title")
    rawTopic = title_tag.text if title_tag else "No title"
    topic = rawTopic.replace("\n", "").strip()

    abstract_tag = article.find("p", class_="mathjax")
    rawFullAbstract = abstract_tag.text if abstract_tag else "No abstract"
    fullAbstract = rawFullAbstract.replace("\n", "").strip()

    pdf_tag = article.find_previous_sibling("dt").find("a", title="Download PDF")
    pdfURL = pdf_tag['href'] if pdf_tag else "No PDF"
    pdfURL = requests.compat.urljoin(url, pdfURL)

    authors_tag = article.find("div", class_="list-authors")
    authors = [a.text for a in authors_tag.find_all("a")] if authors_tag else []

    arxivArticle = {
        "Topic": topic,
        "Abstract": fullAbstract,
        "PDF": pdfURL,
        "Authors": authors
    }

    articleInfo.append(arxivArticle)

# Debugging statements
print(f"Number of articles found: {len(articleInfo)}")
print(f"Article info: {articleInfo}")

with open("arxiv.json", "w") as jsonFile:
    json.dump(articleInfo, jsonFile, indent=4)