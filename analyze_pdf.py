import pdfplumber

with pdfplumber.open("tages_news.pdf") as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    print("--- TEXT ---")
    print(text)
    print("--- TABLES ---")
    for table in page.extract_tables():
        print(table)
