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
    if os.listdir(ExtractFolder):
        return True, "File Exists"
    
    tempEkstrakFolder = os.path.join(pathBeaconDir, "temp")
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

        os.rmdir(inner_folder)

    return True, f"Beacon Ready at : {ExtractFolder}"
    
def processPatient(beacon, fhirObj):
    mapper_path = os.path.join(os.getcwd(), "Mapper.xlsx")
    df = pd.read_excel(mapper_path, sheet_name="Mapper")

    for row in df.rows:
        if row["Where to Use"] not in beacon:
            beacon[row["Where to Use"]] = []
        
        if row["Where to Find"] == "Patient":
            typeDataFind = row["Type of Find Used"]
            if typeDataFind != "array":
                typeDataUse = row["Type of Use Used"]
                if pd.notna(row["What to Use Third"]):
                    # if typeDataUse == "string":
                    beacon["What to Use First"]["What to Use Second"]["What to Use Third"] = getFindValue(row, fhirObj)[typeDataUse]
                elif pd.notna(row["What to Use Second"]):
                    # if typeDataUse == "string":
                    beacon["What to Use First"]["What to Use Second"] = getFindValue(row, fhirObj)[typeDataUse]
                elif pd.notna(row["What to Use First"]):
                    # if typeDataUse == "string":
                    beacon["What to Use First"] = getFindValue(row, fhirObj)[typeDataUse]


def getFindValue(row, fhirObj):
    vm = {
        "string": "",
        "number": 0,
        "float": 0.0,
    }

    typeDataUse = row["Type of Use Used"]
    typeDataFind = row["Type of Find Used"]
    if typeDataFind == typeDataUse:
        if pd.notna(row["What to Find Third"]):
            value = fhirObj["What to Find First"]["What to Find Second"]["What to Find Third"]
            if value is not None:
                vm[typeDataFind] = value
        elif pd.notna(row["What to Find Second"]):
            value = fhirObj["What to Find First"]["What to Find Second"]
            if value is not None:
                vm[typeDataFind] = value
        elif pd.notna(row["What to Find First"]):
            value = fhirObj["What to Find First"]
            if value is not None:
                vm[typeDataFind] = value
    elif typeDataFind != typeDataUse:
        if typeDataUse != "array":
            aaa = ""

    return vm
    