
def fetchInverterDetailsData(siteID):
    url = f"https://server.convert-control.de/api/plant/{siteID}"

    payload = json.dumps({
    "refresh_token": "6bfa9dae9f2109a94109946478378cf95bfd7549ec4cac1f8e1300597f2cbe889ba6a7ca8ca9931410ae6f703b9deca2f0876341bf121ec8c1cf7a1eb3b826e5"
    })
    headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {key}' }
    response = requests.request("GET", url, headers=headers, data=payload).json()
    response = pd.json_normalize(response,"devices")   
    inverterDetailsDict = response[["id","label"]]
    #inverterDetails["lastConnection"] = datetime.datetime.fromtimestamp(inverterDetails["lastConnection"])
    return inverterDetailsDict


inverterDetailsDict = fetchInverterDetailsData(siteID)
inverterDetailsDict= inverterDetailsDict.set_index("id").to_dict()


ac_data["device"](lambda  x : print (type(x)))
ac_data["device"].rename(lambda x : inverterDetailsDict["label"][convert_to_int(x)] if convert_to_int(x) in inverterDetailsDict["label"] else x, inplace=True)
ac_data.columns = ac_data.columns.str.replace(' ', '')


st.write(ac_data)
st.write(inverterDetailsDict)
print (inverterDetailsDict["label"][223] )

for i in ac_data["device"]:
    if convert_to_int(i) in inverterDetailsDict["label"]:
        print (inverterDetailsDict["label"][convert_to_int(i)])