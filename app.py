from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd
import requests
from selenium import webdriver
from datetime import date
import time
import dateutil.relativedelta


def getDownloadLink(data):
    link = []
    cont = 0
    while (not link or cont == 10):
        #Iniciando driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("--window-size=800,800")
        driver = webdriver.Chrome(options=options)
        driver.get("https://portalibre.fgv.br/press-releases")
        
        #Selecionando Indice Geral de Preco
        select_element = driver.find_element(By.ID, 'edit-term-node-tid-depth-shs-0-0')
        select = Select(select_element)
        select.select_by_visible_text('Índice Geral de Preço')
        time.sleep(1)

        select_element = driver.find_element(By.ID, 'edit-term-node-tid-depth-shs-0-1')
        select = Select(select_element)
        select.select_by_visible_text('IGP-M')
        time.sleep(1)
        driver.find_element(By.ID, 'edit-submit-press-release').click()
        #button = driver.find_element(By.ID, 'edit-submit-press-release')
        #driver.execute_script("arguments[0].click();", button)
        time.sleep(2)
        elems = driver.find_elements(By.XPATH, '//a[contains(@href,".xls")]')
        links = []
        for elem in elems:
            links.append(elem.get_attribute("href"))
        mes_ano = str(data.strftime("%Y-%m"))
        link = [x for x in links if f'{mes_ano}' in x]
        cont+=1
        if not link:
            data = data - dateutil.relativedelta.relativedelta(months=1)
    return link[0]


def download_file(file_url,file_name):
    #Baixando o arquivo
    print(f"Downloading {file_url}")
    try:
        r = requests.get(file_url)
        open("bases_originais/"+file_name, 'wb').write(r.content)
    except Exception as e:
        print('Downloading file error: ', e)

def clean_df(file_name):
    print("Generating dataframe...")
    #Lendo dataframe
    df = pd.read_excel("bases_originais/"+file_name,header=[1])
    
    #Selecionando e renomeando colunas
    df = df[['Data', 'IGP-M', 'IGP-M.1']]\
    .rename(columns={"Data": "data", "IGP-M": "igp-mMensal", "IGP-M.1": "igp-m12m"})
    
    #formatando o dataframe
    df = df.drop(df[df["igp-mMensal"].str.contains('% mês', na=False)].index)\
    .drop(df[df["data"].str.contains('Fonte', na=False)].index)\
    .drop(df[df["data"].str.contains('Inicio da série', na=False)].index)
	
    #Arrumando tipagem dos dados
    df.data = df.data.astype(str)
    df["igp-mMensal"] = df["igp-mMensal"].astype(float)
    df["igp-m12m"] = df["igp-m12m"].astype(float)
    
    #Arrumando formato de data
    df['data'] = df['data'].apply(lambda x: r"1989-06-01 00:00:00" if x == r"jun/89 (*)" else x)
    
    return df

if __name__ == '__main__':
    file_name = "igpm.xls"
    file_url = getDownloadLink(date.today())
    download_file(file_url, file_name)
    df = clean_df(file_name)
    df.to_csv("bases_tratadas/igpm.csv", sep=";")