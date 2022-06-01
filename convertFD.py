from math import floor
import requests
import pandas as pd 
import json
import streamlit as st
import datetime
import sys
from streamlit_lottie import st_lottie
from streamlit_lottie import st_lottie_spinner
import io
import xlsxwriter
def check_password():
    """Returns `True` if the user had a correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        
        st.text_input("Username", key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username",  key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    pd.set_option('display.max_rows', None)
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
    valErr = False
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

    @st.experimental_memo(show_spinner=False)#Fetch AC datas of selected plant in selected dates
    def fetch_AC_Data(siteID, startDate,endDate):
        url = f"{baseURL}dc_points?plant={siteID}&timestamp={startDate} 08:00:00&end={endDate} 21:00:00&devices=338"
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}' }
        response = requests.request("GET", url, headers=headers, ).json()
        response = json.dumps(response)
        response = pd.read_json(response)
        response.fillna(0, inplace=True)
        response = response [['device', 'timestamp','index','p','u','i']]
        response["device"] = response["device"].str.partition("phoenixinverter/")[2] #id comes after this 
        #response["device"] = response["device"].astype(int)
        response = response.set_index("timestamp")
        response=response.between_time("08:30" , "19:00")
        response=response.reset_index()
        response = response.groupby(["timestamp","device","index"]).mean()
        #response['timestamp'] = response["timestamp"].apply(lambda x: pd.to_datetime(x))
        return  response
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
    @st.experimental_memo(show_spinner=False)
    def fetchPlantDetails(siteID):
        urlSD = f"{baseURL}plant/{siteID}"
        ulrADRS=f"{baseURL}address/{siteID}"
        headers = {'Authorization': f'Bearer {key}'}
        responseSD = requests.request("GET", urlSD, headers=headers, ).json()
        responseADRS= requests.request("GET", ulrADRS, headers=headers,).json()
        responseADRS  = json.dumps(responseADRS)
        responseADRS = pd.read_json(responseADRS,lines=True)
        responseADRS = responseADRS[["city","street1","street2"]]
        print(responseADRS)
        responseWiring = responseSD["wiringInformation"]
        
        responseSD  = json.dumps(responseSD)
        responseSD = pd.read_json(responseSD, lines=True)
        responseSD=responseSD[["label","inverterCount","firstData","wp","latestData"]]
       
        return responseSD,responseADRS,responseWiring
    
    def fetchInverterDetailsData(siteID):
        url = f"{baseURL}plant/{siteID}"
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}' }
        response = requests.request("GET", url, headers=headers,).json()
        print(type(response))
        #wiringData =  pd.json_normalize(response["devices"],"wiring",)
        devicesTable = pd.DataFrame()
        deviceNo=0
        for device in response["devices"]:
            print(deviceNo)
            try:
                wiringData = pd.json_normalize(response["devices"][deviceNo]["wiring"],)  
                wiringData = wiringData[["id","dcInputNumber","quantity","orientation","inclination","module"]]
                devicesTable= pd.concat([devicesTable, wiringData])
            except:
                pass
            deviceNo +=1 
        module = response["devices"][0]["wiring"][0]["module"]
        response = pd.json_normalize(response["devices"],)
        inverterDetails = response[["id","label",]]
        #inverterDetails["lastConnection"] = datetime.datetime.fromtimestamp(inverterDetails["lastConnection"])
        return inverterDetails,devicesTable,module
    @st.experimental_memo(show_spinner=False)
    def fetchModuleData(moduleNo):
            url = f"{baseURL}solarmodule/{moduleNo}"
            headers = {
            'Authorization': f'Bearer {key}'
            }

            response = requests.request("GET", url, headers=headers, ).json()
            response = json.dumps(response)
            response = pd.read_json(response,lines=True)
            response = response[["id","label","output","size","coeff","coeffScc"]]
            return response

    lottie_url_hamster = "https://assets9.lottiefiles.com/packages/lf20_xktjqpi6.json"
    lottie_hamster = load_lottieurl(lottie_url_hamster)

    st.title("Convert Control Data Sihirbazı 🧙")
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
        if endDate-startDate < datetime.timedelta(days=1):
            startDate = startDate-datetime.timedelta(days=1)

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
        key = login(user_name,password)
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
                try: #if bloğu ile girilip yalnızca auth hatası alınan durumlarda tekrar giriş yapılacak
                    data = fetch_AC_Data(siteID, startDate,endDate,)
                    frameList.append(data)
                    mixed = pd.concat(frameList)       
                except ValueError:
                    key = login(user_name,password)
                    data = fetch_AC_Data(siteID, startDate,endDate,)
                    frameList.append(data)
                    mixed = pd.concat(frameList)                    
                    print("Key Refreshed")
                    pass
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
            with st.spinner("Tablo Oluşturuluyor.."):
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
                    try:
                        buffer =excelCreator(selectedPlant=selectedPlant)
                        st.download_button(
                                        label="Download as XLSX",
                                        data=buffer,
                                        file_name=f"{selectedPlant}.xlsx",
                                        mime="application/vnd.ms-excel"
                                        )
                    except ValueError:
                        valErr = True
            if valErr:
                st.error("Satır Sayısı Excel Tarafından Belirlenen Limitin Üstünde Olduğundan Excel Dosyası Oluşturulamıyor.")
                        
    if sitedetails:
        try:
            key = login(user_name,password)
        except :
            sys.exit("API Erişimi Sağlanamadı")
        siteDetails = fetchPlantDetails(siteID)[0]
        siteAddress = fetchPlantDetails(siteID)[1]
        label = siteDetails["label"].str.cat()
        inverterCount = siteDetails["inverterCount"]
        inverterCount = pd.to_numeric(inverterCount)
        lastData = siteDetails["latestData"].str.cat()[:16].replace("T"," ")
        firstData = siteDetails["firstData"].str.cat()[:16].replace("T"," ")
        city = siteAddress["city"].str.cat()
        street_1 = siteAddress["street1"].str.cat()
        street_2 = siteAddress["street2"].str.cat()
        address = street_1 + street_2
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Plant Name", label)
        with col2:
            st.metric("City", city)
        st.metric("Address",address)
        st.metric("INV COUNT", inverterCount)
        col1,col2=st.columns(2)
        with col1:
            st.metric("First Connection Date", firstData)
        with  col2:
            st.metric("Last Connection Date", lastData)
        try:   
            inverterDetailsDict = fetchInverterDetailsData(siteID)[0]
            with st.expander("Inverter ID-Label Table"):
                st.write(inverterDetailsDict)
        except:
            pass
        try:
            responseWiring = fetchPlantDetails(siteID)[2]
            with st.expander("Orientation Info"):
                st.write(responseWiring)
        except:
            pass
            
        try:
            with st.expander("Detailed Orientation Info"):
                wiringData = fetchInverterDetailsData(siteID)[1]
                st.write(wiringData)
        except:
            pass
        try:
            with st.expander("Module Info"):
                module = fetchInverterDetailsData(siteID)[2]
                module = module.partition("solarmodule/")[2]
                moduleInfo = fetchModuleData(module)
                st.table(moduleInfo)
        except:
            pass