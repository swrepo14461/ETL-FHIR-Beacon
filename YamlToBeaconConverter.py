import requests
import os
import zipfile
import shutil
import pandas as pd

target = {}
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
    df_patient = df[df["a"] == "Patient"]
    groupsMapper = df_patient.groupby("b")

    for key, group in groupsMapper:
        if key not in beacon:
            beacon[key] = []

        target = {}
        # get first object if exists
        if beacon[key]:
            target = beacon[key][0]

        for _, row in group.iterrows():
            # temp value
            value = {
                "object": {},
                "array": [],
                "string": "",
                "number": 0,
                "float": 0,
                "boolean": False,
                "null": None
            }

            # get value from fhir
            typeFind = row["Type of Find Used"]
            if pd.notna(row["What to Find Third"]):
                value[typeFind] = fhirObjDict[row["What to Find First"]][row["What to Find Second"]][row["What to Find Third"]]
            elif pd.notna(row["What to Find Second"]):
                value[typeFind] = fhirObjDict[row["What to Find First"]][row["What to Find Second"]]
            elif pd.notna(row["What to Find First"]):
                value[typeFind] = fhirObjDict[row["What to Find First"]]

            # get instruction and set value
            whatToDoFind = row["What to Do"]
            if not whatToDoFind:
                setBeaconValue(row, target, value[typeFind])
            else:
                arrToDo = whatToDoFind.split('|')
            # typeDataFind = row["Type of Find Used"]
            # if typeDataFind == "string":


            # ambil type data yang ingin di cari
            # typeDataFind = row["Type of Find Used"]
            # if typeDataFind != "array":
            #     if pd.notna(row["What to Use Third"]):
            #         # if typeDataUse == "string":
            #         target[row["What to Use First"]][row["What to Use Second"]][row["What to Use Third"]] = getFindValue(row, fhirObjDict)[typeDataUse]
            #     elif pd.notna(row["What to Use Second"]):
            #         # if typeDataUse == "string":
            #         target[row["What to Use First"]][row["What to Use Second"]] = getFindValue(row, fhirObjDict)[typeDataUse]
            #     elif pd.notna(row["What to Use First"]):
            #         # if typeDataUse == "string":
            #         target[row["What to Use First"]] = getFindValue(row, fhirObjDict)[typeDataUse]


def setBeaconValue(row, target, value):
    if pd.notna(row["What to Use Third"]):
        # if typeDataUse == "string":
        setNested(target, [row["What to Use First"], [row["What to Use Second"]], [row["What to Use Third"]]], value)
    elif pd.notna(row["What to Use Second"]):
        # if typeDataUse == "string":
        setNested(target, [row["What to Use First"], [row["What to Use Second"]]], value)
    elif pd.notna(row["What to Use First"]):
        # if typeDataUse == "string":
        setNested(target, [row["What to Use First"]], value)
    

def setNested(target, keys, value, as_list=False):
    d = target
    for key in keys[:-1]:
        # pastikan level dict ada
        d = d.setdefault(key, {})
    
    last_key = keys[-1]
    if as_list:
        # jika level terakhir adalah list
        d.setdefault(last_key, []).append(value)
    else:
        # level terakhir adalah dict/object atau value biasa
        d[last_key] = value