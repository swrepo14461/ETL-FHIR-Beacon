import requests
import os
import zipfile
import shutil
import pandas as pd
import json

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
    df_filtered = df[df["Where to Find"] == "Patient"]
    groupsMapper = df_filtered.groupby("Where to Use")

    for key, group in groupsMapper:
        if key not in beacon:
            beacon[key] = []

        target = {}
        # get first object if exists
        if beacon[key]:
            target = beacon[key][0]

        for _, row in group.iterrows():
            mapFhirToBeacon(row, target, fhirObjDict, df_filtered)

        beacon[key].append(target)

    return beacon

def processObservation(beacon, fhirObj):
    fhirObjDict = fhirObj.model_dump()
    mapper_path = os.path.join(os.getcwd(), "Mapper.xlsx")
    df = pd.read_excel(mapper_path, sheet_name="Mapper")
    df_filtered = df[df["Where to Find"] == "Observation"]
    groupsMapper = df_filtered.groupby("Where to Use")

    for key, group in groupsMapper:
        if key not in beacon:
            beacon[key] = []

        target = {}
        # get first object if exists
        if beacon[key]:
            target = beacon[key][0]

        for _, row in group.iterrows():            
            target = mapFhirToBeacon(row, target, fhirObjDict, df_filtered)

        if beacon[key]:
            beacon[key][0] = target
        else:
            beacon[key].append(target)

    return beacon

def mapFhirToBeacon(row, target, fhirObjDict, df):
    # get instruction and set value
    whatToDoFind = row["What to Do"]
    if pd.isna(whatToDoFind):
        value = getFhirValue(fhirObjDict, row)
        setBeaconValue(row, target, value)
    else:
        isValid = True
        valueToInput = []
        arrToDo = whatToDoFind.split('||')
        for toDo in arrToDo:
            if isValid:
                if "VALIDATE" in toDo:
                    arrToFind = toDo.split('|')[1].split(',') # category-array, coding-array
                    valToFind = toDo.split('|')[2]

                    resultValidate = False
                    if validate_nested(fhirObjDict[arrToFind[0].split('-')[0]], arrToFind[1:], valToFind):
                            resultValidate = True

                    if not resultValidate:
                        print("Data Not Valid")
                        isValid = False
                        break
                elif "COMBINENEXT" in toDo:
                    totalRowToCombined = toDo.split('-')[1]
                    for i in range(1, int(totalRowToCombined)):
                        nextRow = df.iloc[df.index.get_loc(row.name) + i]
                        nextValue = getFhirValue(fhirObjDict, nextRow)
                        if (nextValue is not None):
                            valueToInput.append({
                                "row": nextRow,
                                "value": nextValue
                            })
                elif "COMBINED" in toDo:
                    isValid = False
                    break
        if isValid:
            value = getFhirValue(fhirObjDict, row)
            valueToInput.insert(0, {
                "row": row,
                "value": value
            })
            setBeaconArrayValue(target, valueToInput)
            # for item in valueToInput:
            #     setBeaconValue(item["row"], target, item["value"])

    return target
        
def getFhirValue(fhirObjDict, row):
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
    typeFind = row["Type of Find Used"]

    # get value from fhir
    first = row["What to Find First"]
    second = row["What to Find Second"]
    third = row["What to Find Third"]

    if pd.notna(third):
        value[typeFind] = fhirObjDict.get(first, {}).get(second, {}).get(third)
    elif pd.notna(second):
        value[typeFind] = fhirObjDict.get(first, {}).get(second)
    elif pd.notna(first):
        value[typeFind] = fhirObjDict.get(first)

    return value[typeFind]

def setBeaconValue(row, target, value):
    valueToInput = value
    typeUsed = row["Type of Use Used"]
    if typeUsed == "object":
        toDo = row["What Must Be Done"]
        if toDo and not pd.isna(toDo):
            arrToDo = toDo.split('|')
            if "TRANSFORM" in arrToDo[0]:
                arrValTransform = arrToDo[0].split('-')
                arrTransformKey = arrValTransform[1].split(',')

                arrActionDetail = arrToDo[1].split('-')
                if "Default Value" in arrActionDetail[0]:
                    keyCol = arrActionDetail[0].split(',')[0]
                    keyToFind = arrActionDetail[1].split(',')[1]
                    
                    jsonData = json.loads(row[keyCol])
                    matched = next((item for item in jsonData if item[keyToFind] == value), None)

                    colGet = arrActionDetail[1].split(',')
                    valueToInput = {k: matched[c] for k, c in zip(arrTransformKey, colGet)}
                elif "Coding" in arrActionDetail[0]:
                    defVal = [{"system":"http://snomed.info/sct","value":"SNOMED"},{"system":"http://hl7.org/fhir/sid/icd-10","value":"ICD-10"},{"system":"http://loinc.org","value":"LOINC"},{"system":"http://unitsofmeasure.org","value":"UCUM"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","value":"ICD-9-CM"}]
                    codeUnit = next((item["value"] for item in defVal if item["system"] == value["system"]), None)
                    valueToInput = {arrTransformKey[0]: f"{codeUnit}:{value["code"]}", arrTransformKey[1]: value["display"]}
                elif "Value" in arrActionDetail[0]:
                    defVal = [{"system":"http://snomed.info/sct","value":"SNOMED"},{"system":"http://hl7.org/fhir/sid/icd-10","value":"ICD-10"},{"system":"http://loinc.org","value":"LOINC"},{"system":"http://unitsofmeasure.org","value":"UCUM"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","value":"ICD-9-CM"}]
                    codeUnit = next((item["value"] for item in defVal if item["system"] == value["system"]), None)
                    valueToInput = {arrTransformKey[0]: f"{codeUnit}:{value["code"]}", arrTransformKey[1]: value["value"]}
    elif typeUsed == "array":
        valueToInput = []
        toDo = row["What Must Be Done"]
        if toDo and not pd.isna(toDo):
            arrToDo = toDo.split('|')
            if "TRANSFORM" in arrToDo[0]:
                arrValTransform = arrToDo[0].split('-')
                arrTransformKey = arrValTransform[1].split(',')

                arrActionDetail = arrToDo[1].split('-')
                if "Default Value" in arrActionDetail[0]:
                    keyCol = arrActionDetail[0].split(',')[0]
                    keyToFind = arrActionDetail[1].split(',')[1]
                    
                    jsonData = json.loads(row[keyCol])
                    matched = next((item for item in jsonData if item[keyToFind] == value), None)

                    colGet = arrActionDetail[1].split(',')
                    valueToInput.append({k: matched[c] for k, c in zip(arrTransformKey, colGet)})
                elif "Coding" in arrActionDetail[0]:
                    defVal = [{"system":"http://snomed.info/sct","value":"SNOMED"},{"system":"http://hl7.org/fhir/sid/icd-10","value":"ICD-10"},{"system":"http://loinc.org","value":"LOINC"},{"system":"http://unitsofmeasure.org","value":"UCUM"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","value":"ICD-9-CM"}]
                    for arrVal in value:
                        codeUnit = next((item["value"] for item in defVal if item["system"] == arrVal["system"]), None)
                        valueToInput.append({arrTransformKey[0]: f"{codeUnit}:{arrVal["code"]}", arrTransformKey[1]: arrVal["display"]})
                elif "Value" in arrActionDetail[0]:
                    defVal = [{"system":"http://snomed.info/sct","value":"SNOMED"},{"system":"http://hl7.org/fhir/sid/icd-10","value":"ICD-10"},{"system":"http://loinc.org","value":"LOINC"},{"system":"http://unitsofmeasure.org","value":"UCUM"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","value":"ICD-9-CM"}]
                    codeUnit = next((item["value"] for item in defVal if item["system"] == value["system"]), None)
                    valueToInput.append({arrTransformKey[0]: f"{codeUnit}:{value["code"]}", arrTransformKey[1]: value["value"]})
    
    if pd.notna(row["What to Use Third"]):
        setNested(target, [row["What to Use First"], [row["What to Use Second"]], [row["What to Use Third"]]], valueToInput, as_list=(typeUsed == "array"))
    elif pd.notna(row["What to Use Second"]):
        setNested(target, [row["What to Use First"], [row["What to Use Second"]]], valueToInput, as_list=(typeUsed == "array"))
    elif pd.notna(row["What to Use First"]):
        setNested(target, [row["What to Use First"]], valueToInput, as_list=(typeUsed == "array"))
    
def setBeaconArrayValue(target, arrValue):
    arrValueToInput = {}
    firstRow = arrValue[0]
    for item in arrValue[1:]:
        row = item["row"]
        value = item["value"]

        valueToInput = value
        typeUsed = row["Type of Use Used"]
        if typeUsed == "object":
            toDo = row["What Must Be Done"]
            if toDo and not pd.isna(toDo):
                arrToDo = toDo.split('|')
                if "TRANSFORM" in arrToDo[0]:
                    arrValTransform = arrToDo[0].split('-')
                    arrTransformKey = arrValTransform[1].split(',')

                    arrActionDetail = arrToDo[1].split('-')
                    if "Default Value" in arrActionDetail[0]:
                        keyCol = arrActionDetail[0].split(',')[0]
                        keyToFind = arrActionDetail[1].split(',')[1]
                        
                        jsonData = json.loads(row[keyCol])
                        matched = next((item for item in jsonData if item[keyToFind] == value), None)

                        colGet = arrActionDetail[1].split(',')
                        valueToInput = {k: matched[c] for k, c in zip(arrTransformKey, colGet)}
                    elif "Coding" in arrActionDetail[0]:
                        defVal = [{"system":"http://snomed.info/sct","value":"SNOMED"},{"system":"http://hl7.org/fhir/sid/icd-10","value":"ICD-10"},{"system":"http://loinc.org","value":"LOINC"},{"system":"http://unitsofmeasure.org","value":"UCUM"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","value":"ICD-9-CM"}]
                        if len(value) > 0:
                            codeUnit = next((item["value"] for item in defVal if item["system"] == value[0]["system"]), None)
                            valueToInput = {arrTransformKey[0]: f"{codeUnit}:{value[0]["code"]}", arrTransformKey[1]: value[0]["display"]}
                        else:
                            codeUnit = next((item["value"] for item in defVal if item["system"] == value["system"]), None)
                            valueToInput = {arrTransformKey[0]: f"{codeUnit}:{value["code"]}", arrTransformKey[1]: value["display"]}
                    elif "Value" in arrActionDetail[0]:
                        defVal = [{"system":"http://snomed.info/sct","value":"SNOMED"},{"system":"http://hl7.org/fhir/sid/icd-10","value":"ICD-10"},{"system":"http://loinc.org","value":"LOINC"},{"system":"http://unitsofmeasure.org","value":"UCUM"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","value":"ICD-9-CM"}]
                        codeUnit = next((item["value"] for item in defVal if item["system"] == value["system"]), None)
                        valueToInput = {arrTransformKey[0]: f"{codeUnit}:{value["code"]}", arrTransformKey[1]: value["value"]}

        if pd.notna(row["What to Use Third"]):
            setNested(arrValueToInput, [row["What to Use Second"], row["What to Use Third"]], valueToInput)
        elif pd.notna(row["What to Use Second"]):
            setNested(arrValueToInput, [row["What to Use Second"]], valueToInput)
        # elif pd.notna(row["What to Use First"]):
        #     setNested(arrValueToInput, [row["What to Use First"]], valueToInput)

    setNested(target, [firstRow["row"]["What to Use First"]], arrValueToInput, as_list=True)

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

def validate_nested(val, keyPaths, target):
    if not keyPaths:
        # sudah sampai key terakhir, cek apakah val sama dengan target
        return val == target
    
    for path in keyPaths:
        keyPath = path.split('-')
        key = keyPath[0]
        subtype = keyPath[1] if len(keyPath) > 1 else None

        if isinstance(val, dict):
            next_val = val.get(key)
            if next_val is None:
                return False
            if subtype == "array" and isinstance(next_val, list):
                for item in next_val:
                    if validate_nested(item, keyPaths[1:], target):
                        return True
            else:
                return validate_nested(next_val, keyPaths[1:], target)
        elif isinstance(val, list):
            for item in val:
                if validate_nested(item, keyPaths, target):
                    return True

    return False

def validate_todo(toDo, val, row):
    toDoList = toDo.split('|')
    if "VALIDATE" in toDoList[0]:
        arrToFind = toDoList[1].split(',')
        valToFind = toDoList[2]

        for path in arrToFind:
            if not validate_nested(val, path, valToFind):
                return "Data Not Valid"
    elif "COMBINENEXT" in toDoList[0]:
        totalRowToCombined = toDoList[1].split('-')[1]
        for i in range(1, int(totalRowToCombined)):
            row[i]