from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
import sys
import re

def validar_codigo(codigo):
    """Valida se o código fornecido é um UUID (padrão SIGEF)."""
    if codigo is None:
        return False
    codigo = codigo.strip()
    # Padrão UUID v4
    padrao_uuid = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return re.match(padrao_uuid, codigo.lower()) is not None

# === Obtem código por argumento ou input ===
# Cria a instância principal do Tkinter (oculta) para uso com simpledialog/messagebox
root = tk.Tk()
root.withdraw()

if len(sys.argv) > 1:
    codigo = sys.argv[1]
else:
    codigo = simpledialog.askstring("Código SIGEF", "Digite o código SIGEF (ex: 4c5b03c8-e43a-4f22-a10e-0dc33ad20044):")

if not validar_codigo(codigo):
    print("⚠️ Código inválido ou vazio. Encerrando o script.")
    root.destroy()
    sys.exit(1)

# === CONFIGURAÇÕES FIXAS ===
url = 'https://mapa.onr.org.br/'
data_camada = 'sigef_parcela'
grupo_nome = 'Imóveis Rurais'

# === OPÇÕES DO CHROME ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# Opções para evitar que o site detecte o Selenium/automação
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--disable-blink-features=AutomationControlled")
# Mantém a janela do Chrome aberta após a conclusão do script
options.add_experimental_option("detach", True)

# === INICIA O CHROME COM O DRIVER MANAGER PADRÃO (Compatível com versões antigas) ===
try:
    # Removido 'force_install=True' para resolver o erro 'unexpected keyword argument'.
    # O ChromeDriverManager() agora usará o método padrão para verificar e instalar o driver.
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Executa script anti-automação após o driver iniciar
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

except Exception as e:
    print(f"❌ Erro fatal ao iniciar o navegador Chrome. Detalhes: {e}")
    messagebox.showerror(
        "Erro de Inicialização", 
        "Falha ao iniciar o navegador Chrome.\nVerifique se o Google Chrome está instalado e atualizado.\nDetalhes técnicos: " + str(e)
    )
    root.destroy()
    sys.exit(1)

wait = WebDriverWait(driver, 30)
driver.get(url)
time.sleep(9) # Tempo para carregamento inicial da página e do mapa

# === ABRE DROPDOWN DE CAMADAS ===
try:
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-busca-camada'))).click()
    time.sleep(1)

    # === EXPANDE O GRUPO DE CAMADAS ===
    for grupo in driver.find_elements(By.CLASS_NAME, 'toggle-subnivel'):
        if grupo_nome.lower() in grupo.text.lower():
            driver.execute_script("arguments[0].click();", grupo)
            time.sleep(1)
            break

    # === CLICA NA CAMADA DO SIGEF ===
    camadas = wait.until(EC.presence_of_all_elements_located(
        (By.XPATH, f"//div[@class='dropdown-item' and @data-camada='{data_camada}']")))

    for camada in camadas:
        if camada.is_displayed():
            driver.execute_script("arguments[0].scrollIntoView(true);", camada)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", camada)
            break
except Exception as e:
    print(f"Erro ao interagir com as camadas do mapa:", e)

# === BUSCA O CÓDIGO ===
try:
    input_codigo = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geocoder-control-input')))
    input_codigo.clear()
    input_codigo.send_keys(codigo)
    input_codigo.send_keys(Keys.ENTER)
    time.sleep(2)
except Exception as e:
    print("Erro ao inserir o código de busca:", e)

# === CLICA NA SUGESTÃO ===
try:
    sugestao = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".geocoder-control-suggestions div"))
    )
    sugestao.click()
except:
    # Não é um erro crítico se a sugestão não aparecer ou for clicada
    print("Sugestão de busca não encontrada ou não clicada, prosseguindo...")
    pass

# === CLICA NO CENTRO DA TELA PARA ATIVAR O POPUP DE INFORMAÇÃO ===
time.sleep(8)
try:
    width = driver.execute_script("return window.innerWidth")
    height = driver.execute_script("return window.innerHeight")
    center_x = width // 2
    center_y = height // 2
    
    # Clica no centro
    ActionChains(driver).move_by_offset(center_x, center_y).click().perform()
    # Retorna o cursor para evitar interferência na tela
    ActionChains(driver).move_by_offset(-center_x, -center_y).perform()
    
    time.sleep(3) # Tempo para o popup aparecer
    
except Exception as e:
    print("Erro ao clicar no centro da tela:", e)

# === Janela popup final ===
# Reutilizando a instância 'root' já criada e oculta
root.attributes("-topmost", True)
messagebox.showinfo("Concluído", "Consulta Finalizada\nO mapa com o código SIGEF foi carregado e o popup de informações deve estar visível.\nVocê pode fechar o navegador quando quiser.")
root.destroy()

# === Mantém navegador aberto ===
# O navegador permanecerá aberto devido à opção "detach", mas este loop garante que o script não morra imediatamente
try:
    while driver.window_handles:
        time.sleep(1)
except:
    pass

sys.exit(0)