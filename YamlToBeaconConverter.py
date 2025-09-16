import requests
import os
import zipfile
import shutil
import pandas as pd

pathBeaconDir = os.path.join(os.getcwd(), 'Beacon')
os.makedirs(pathBeaconDir, exist_ok=True) 

url = "https://github.com/ga4gh-beacon/beacon-v2/archive/refs/tags/v2.2.0.zip"
save_path = os.path.join(pathBeaconDir, 'Beacon_2_2_0.zip')

def download_beacon():
    try:
        if os.path.exists(save_path):
            return True, "File Already Downloaded"
        else:
            r = requests.get(url)
            with open(save_path, "wb") as f:
                f.write(r.content)
            return True, "Beacon File Downloaded"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {e}"
    except OSError as e:
        return False, f"File error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def prepare_beacon():
    is_downloaded, reason = download_beacon()
    if not is_downloaded:
        return False, reason
    
    ExtractFolder = os.path.join(pathBeaconDir, "bin")
    os.makedirs(ExtractFolder, exist_ok=True)
    if os.listdir(ExtractFolder):
        return True, "File Exists"
    
    tempEkstrakFolder = os.path.join(pathBeaconDir, "temp")
    os.makedirs(tempEkstrakFolder, exist_ok=True)
    with zipfile.ZipFile(save_path, "r") as zip_ref:
        zip_ref.extractall(tempEkstrakFolder)

    itemsToMove = os.listdir(tempEkstrakFolder)
    if len(itemsToMove) == 1 and os.path.isdir(os.path.join(tempEkstrakFolder, itemsToMove[0])):
        inner_folder = os.path.join(tempEkstrakFolder, itemsToMove[0])
        inner_folder_bin = os.path.join(inner_folder, "bin")
        for item in os.listdir(inner_folder_bin):
            src = os.path.join(inner_folder_bin, item)
            dst = os.path.join(ExtractFolder, item)
            shutil.move(src, dst)

        shutil.rmtree(inner_folder)

    return True, f"Beacon Ready at : {ExtractFolder}"
    
def processPatient(beacon, fhirObj):
    fhirObjDict = fhirObj.model_dump()
    mapper_path = os.path.join(os.getcwd(), "Mapper.xlsx")
    df = pd.read_excel(mapper_path, sheet_name="Mapper")

    for index, row in df.iterrows():
        if row['Where to Use'] not in beacon:
            beacon[row['Where to Use']] = []
        
        if row['Where to Find'] == "Patient":
            typeDataFind = row["Type of Find Used"]
            if typeDataFind != "array":
                typeDataUse = row["Type of Use Used"]
                if pd.notna(row["What to Use Third"]):
                    # if typeDataUse == "string":
                    beacon[row['Where to Use']][row["What to Use Second"]][row["What to Use Third"]] = getFindValue(row, fhirObjDict)[typeDataUse]
                elif pd.notna(row["What to Use Second"]):
                    # if typeDataUse == "string":
                    beacon[row['Where to Use']][row["What to Use Second"]] = getFindValue(row, fhirObjDict)[typeDataUse]
                elif pd.notna(row["What to Use First"]):
                    # if typeDataUse == "string":
                    beacon[row['Where to Use']] = getFindValue(row, fhirObjDict)[typeDataUse]


def getFindValue(row, fhirObjDict):
    vm = {
        "string": "",
        "number": 0,
        "float": 0.0,
        "object": {},
        "array": []
    }

    typeDataUse = row["Type of Use Used"]
    typeDataFind = row["Type of Find Used"]
    if typeDataFind == typeDataUse:
        if pd.notna(row["What to Find Third"]):
            value = fhirObjDict[row["What to Find First"]][row["What to Find Second"]][row["What to Find Third"]]
            if value is not None:
                vm[typeDataFind] = value
        elif pd.notna(row["What to Find Second"]):
            value = fhirObjDict[row["What to Find First"]][row["What to Find Second"]]
            if value is not None:
                vm[typeDataFind] = value
        elif pd.notna(row["What to Find First"]):
            value = fhirObjDict[row["What to Find First"]]
            if value is not None:
                vm[typeDataFind] = value
    elif typeDataFind != typeDataUse:
        if typeDataUse != "array":
            aaa = ""

    return vm
    