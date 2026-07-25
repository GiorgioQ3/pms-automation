from selenium import webdriver

# Avvia il browser Chrome
driver = webdriver.Chrome()

# Apre una pagina di prova
driver.get("https://www.google.com")
print("Titolo della pagina:", driver.title)

# Chiude il browser
driver.quit()