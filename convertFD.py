
from math import floor
import requests
import pandas as pd 
import json
import streamlit as st
import datetime
import sys
from stqdm import stqdm
from streamlit_lottie import st_lottie
from streamlit_lottie import st_lottie_spinner
import io
import xlsxwriter
pd.set_option('display.max_rows', None)
baseURL = "https://server.convert-control.de/"

convertControlPlants = [
    {"id": 37, "name": "Cactus Farm"},
    {"id": 14,"name": "PUTAS Textil" },
    {"id": 12, "name": "Yaylakoy"},
    {"id": 13, "name": "Cena Alasehir"},
    {"id": 87, "name": "Irmak Depoları"},
    {"id": 58, "name": "DOST Madencilik"},
    {"id": 61, "name": "Özçakım Mermer"},
    {"id": 93, "name": "Defne Çatı Ges"},
    {"id": 68, "name": "Hitit"},
    {"id": 59, "name": "ASP"},
    {"id": 40, "name": "Barlas Soğutma"},
    {"id": 32, "name": "Çağlacan"},
    {"id": 33, "name": "Cereyan"},
    {"id": 34, "name": "Chef Seasons"},
    {"id": 31, "name": "ELMAS Lojistik"},
    {"id": 38, "name": "Defne Ges-3"},
    {"id": 42, "name": "Defne Ges-4"},
    {"id": 43, "name": "Defne Ges-5"},
    {"id": 44, "name": "Defne Ges-6"},
    {"id": 45, "name": "Defne Ges-7"},
    {"id": 46, "name": "Defne Ges-8"},
    {"id": 30, "name": "Liva Grup ITOB"},
    {"id": 35, "name": "Kozağaç Karya"},
    {"id": 36, "name": "Kozağaç Medis"},
    {"id": 39, "name": "Özkaramanlar "},
    ]

user_name = st.secrets["user_name"]
password = st.secrets["password"]
mixed = pd.DataFrame()

baseURL = "https://server.convert-control.de/api/"
frameList = list()
buffer = io.BytesIO()

def get_key(val): #get id of selected plant
    for plant in convertControlPlants:
         if plant["name"] == val:
             return plant["id"]
    return "key doesn't exist"
def login(user_name, password): #get API key by login
    url = f"{baseURL}login_check"
    payload = json.dumps({
    "username": user_name,   
    "password": password
    })
    headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload).json()
    key = response["token"]
    return key

@st.experimental_memo(show_spinner=False)
def fetch_AC_Data(siteID, startDate,endDate): #Fetch AC datas of selected plant in selected dates
    url = f"{baseURL}dc_points?plant={siteID}&timestamp={startDate} 08:00:00&end={endDate} 21:00:00&devices=338"
    payload = json.dumps({
    "refresh_token": "6bfa9dae9f2109a94109946478378cf95bfd7549ec4cac1f8e1300597f2cbe889ba6a7ca8ca9931410ae6f703b9deca2f0876341bf121ec8c1cf7a1eb3b826e5"
    })
    headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {key}' }
    response = requests.request("GET", url, headers=headers, data=payload).json()
    response = json.dumps(response)
    response = pd.read_json(response)
    response.fillna(0, inplace=True)
    response = response [['device', 'timestamp','index','p','u','i']]
    response["device"] = response["device"].str[-3:]
    #response["device"] = response["device"].astype(int)
    response = response.set_index("timestamp")
    response=response.between_time("08:30" , "19:00")
    response=response.reset_index()
    response = response.groupby(["timestamp","device","index"]).mean()
    return  response

def convert_to_int(value):
    if value.isdigit():
        value = int(value)
        return value
    else:
        return value

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def excelCreator(selectedPlant):
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        mixed.to_excel(writer, sheet_name=f"{selectedPlant}")
        writer.save()
        return buffer      

def csvCreator():
    csv = mixed.to_csv()
    csv = csv.encode('utf-8')
    return csv
   
lottie_url_hamster = "https://assets9.lottiefiles.com/packages/lf20_xktjqpi6.json"
lottie_hamster = load_lottieurl(lottie_url_hamster)

with st.form(key="Santral Seçim Forumu"):
    selectedPlant= st.selectbox(
                "Santarli Seçiniz",
                ("Cactus Farm", "PUTAS Textil", "Yaylakoy","Cena Alasehir","Irmak Depoları","DOST Madencilik","Özçakım Mermer","Defne Çatı Ges","Hitit","ASP","Barlas Soğutma","Çağlacan","Cereyan","Chef Seasons","ELMAS Lojistik","Defne Ges-3","Defne Ges-4","Defne Ges-5","Defne Ges-6","Defne Ges-7","Defne Ges-8","Liva Grup ITOB","Kozağaç Karya","Kozağaç Medis","Özkaramanlar "))
    siteID = get_key(val = selectedPlant)
    colx, coly = st.columns(2)
    with colx:
        startDate = st.date_input("Başlangıç Tarihi", max_value=datetime.datetime.now())
    with coly:
        endDate = st.date_input("Btiş Tarihi",max_value=datetime.datetime.now())

    col1, mid, col2 = st.columns([10,39,10])
    with col1:
        submitted = st.form_submit_button("Submit")
    with  col2:
        sitedetails = st.form_submit_button("Site Details")

with st.expander("Bilgilendirme"):
    st.info("API'de günlük istek limiti bulunmaktadır, bu limit genel çağrılar için 300, santral numarası ile ile yapılan çağrılar için de ayrıca 300 olarak belirlenmiştir.\n Günlük istek limiti aşıldığıda istek hata döndürecektir.")
    st.warning("API'ın çalışma şekli toplu veri indirmeye uygun olmadığından, veriler her inverter bazında verilen tarih aralığını bir haftalık bloklara bölüp ardından tüm dataları bir araya getirmek suretiyle çalışır, Ornegin 9 inverterli bir tesisten bir aylık data çekmek için her inverter için 4 haftalık data çekilip birleştirilir, seri no'ları çekmek için 1 veriler için 36 olmak üzere toplam 37 istek atılmış olur.")
with st.expander("Bellek Temizliği"):
    st.error("Lütfen yalnızca gerekli olduğu durumlarda kullanınız..")
    st.info("Bellekteki tüm verileri temizler, aynı tesiste yapılacak art arda istekleklerde kullnılması önerilir.")
    colx,coly,colz = st.columns(3)
    with coly:
        if st.button("Belleği Temizle"):
            st.experimental_memo.clear()
if submitted:
    try:
        key = login(user_name,password)
    except :
        sys.exit("API Erişimi Sağlanamadı")

    tarih = pd.date_range(startDate,endDate, freq="1D").to_series() #to create a list from given dates in order to make daily api calls
    tarih = tarih.apply(lambda x: x.strftime("%Y-%m-%d"))
    tarih=tarih.to_list()
    colx,coly = st.columns([8.5,1.5])
    with colx:
        st.write("#")
        my_bar = st.progress(0)
    progress = 0
    with coly:
        placeholder = st.empty()
        with placeholder.container():
            st.metric("Progress", f"{progress}%")
    
    with st_lottie_spinner(lottie_hamster, key="download", height=300, quality="high"):
        for i in range(len(tarih)-1):
            startDate=tarih[i]
            endDate=tarih[i+1]
            try:
                data = fetch_AC_Data(siteID, startDate,endDate,)
                frameList.append(data)
                mixed = pd.concat(frameList)       
            except Exception as e:
                print(e)
                pass
            percent = (100/ (len(tarih)-1))/100
            print("Percent:", percent)
            progress += percent
            if progress > 1 :
                progress=1.0
            my_bar.progress(progress)
            print("progress:", progress)
            progressShown = round(progress*100)
            with placeholder.container():
                st.metric("Progress", f"{progressShown}%")
    
    print ( progress)  
    if not mixed.empty:
        st.dataframe(mixed)

    col1, mid, col2 = st.columns([10,15,7.5])
    if not mixed.empty:
        with col1:
            with st.spinner("CSV Dosyası Hazırlanıyor.."):
                csv = csvCreator()
                st.download_button(
                                "Download as CSV",
                                csv,
                                f"{selectedPlant}.csv",
                                "text/csv",
                                key='download-csv'
                                )
        with col2:
            with st.spinner("Excel Dosyası Hazırlanıyor.."):
                buffer =excelCreator(selectedPlant=selectedPlant)
                st.download_button(
                                label="Download as XLSX",
                                data=buffer,
                                file_name=f"{selectedPlant}.xlsx",
                                mime="application/vnd.ms-excel"
                                )


    