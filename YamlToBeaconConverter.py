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
    
def processPatient(beacon, fhirObj, index):
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
        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            target = beacon[key][index]

        for _, row in group.iterrows():
            mapFhirToBeacon(row, target, fhirObjDict, df_filtered)

        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            beacon[key][index] = target
        else:
            beacon[key].append(target)

    return beacon

def processObservation(beacon, fhirObj, index):
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
        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            target = beacon[key][index]

        for _, row in group.iterrows():            
            target = mapFhirToBeacon(row, target, fhirObjDict, df_filtered)

        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            beacon[key][index] = target
        else:
            beacon[key].append(target)

    return beacon

def processCondition(beacon, fhirObj, index):
    fhirObjDict = fhirObj.model_dump()
    mapper_path = os.path.join(os.getcwd(), "Mapper.xlsx")
    df = pd.read_excel(mapper_path, sheet_name="Mapper")
    df_filtered = df[df["Where to Find"] == "Condition"]
    groupsMapper = df_filtered.groupby("Where to Use")

    for key, group in groupsMapper:
        if key not in beacon:
            beacon[key] = []

        target = {}
        # get first object if exists
        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            target = beacon[key][index]

        for _, row in group.iterrows():            
            target = mapFhirToBeacon(row, target, fhirObjDict, df_filtered)

        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            beacon[key][index] = target
        else:
            beacon[key].append(target)

    return beacon

def processProcedure(beacon, fhirJson, index):
    fhirObjDict = fhirJson
    mapper_path = os.path.join(os.getcwd(), "Mapper.xlsx")
    df = pd.read_excel(mapper_path, sheet_name="Mapper")
    df_filtered = df[df["Where to Find"] == "Procedure"]
    groupsMapper = df_filtered.groupby("Where to Use")

    for key, group in groupsMapper:
        if key not in beacon:
            beacon[key] = []

        target = {}
        # get first object if exists
        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            target = beacon[key][index]

        for _, row in group.iterrows():            
            target = mapFhirToBeacon(row, target, fhirObjDict, df_filtered)

        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            beacon[key][index] = target
        else:
            beacon[key].append(target)

    return beacon

#Beacon
def mapFhirToBeacon(row, target, fhirObjDict, df):
    # get instruction and set value
    whatToDoFind = row["What to Do"]
    if pd.isna(whatToDoFind):
        value = getFhirValue(fhirObjDict, row)
        if value is not None:
            setBeaconValue(row, target, value, False)
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
                    for i in range(1, int(totalRowToCombined) + 1):
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
            if value is not None:
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

def setBeaconValue(row, target, value, skipFirst: False):
    defVal = [{"system":"http://snomed.info/sct","code":"SNOMED"},{"system":"http://loinc.org","code":"LOINC"},{"system":"http://unitsofmeasure.org","code":"UCUM"},{"system":"http://terminology.hl7.org/CodeSystem/condition-category","code":"HL7"},{"system":"http://hl7.org/fhir/sid/icd-10","code":"ICD10"},{"system":"http://www.whocc.no/atc","code":"WHO"},{"system":"http://terminology.kemkes.go.id/CodeSystem/clinical-term","code":"KEMKES"},{"system":"http://sys-ids.kemkes.go.id/kfa","code":"KFA"},{"system":"http://hl7.org/fhir/sid/icd-9-cm","code":"ICD9CM"},{"system":"http://terminology.kemkes.go.id/CodeSystem/icd-o-topography","code":"KEMKES"},{"system":"http://terminology.kemkes.go.id/CodeSystem/icd-o-morphology","code":"KEMKES"},{"system":"http://terminology.kemkes.go.id/CodeSystem/cancer-t-category","code":"KEMKES"},{"system":"http://terminology.kemkes.go.id/CodeSystem/cancer-n-category","code":"KEMKES"},{"system":"http://terminology.kemkes.go.id/CodeSystem/cancer-m-category","code":"KEMKES"},{"system":"http://terminology.kemkes.go.id/CodeSystem/examination","code":"KEMKES"}]

    valueToInput = {}
    typeUsed = row["Type of Use Used"]
    if typeUsed == "object":
        toDo = row["What Must Be Done"]
        if toDo and not pd.isna(toDo):
            arrToDo = toDo.split('|')
            if "TRANSFORM" in arrToDo[0]:
                    arrValTransform = arrToDo[0].split('-')
                    arrTransformKey = arrValTransform[1].split(',')

                    newArrTfKey = []
                    for tfKey in arrTransformKey:
                        if "[" in tfKey and "]" in tfKey:
                            newTfKey = getIdAndLabel(tfKey)
                            newArrTfKey.append(newTfKey)
                        else:
                            newArrTfKey.append(tfKey)

                    arrActionDetail = arrToDo[1].split('-')
                    if "Default Value" in arrActionDetail[0]:
                        keyCol = arrActionDetail[0]
                        keyToFind = arrActionDetail[1]
                        
                        jsonData = json.loads(row[keyCol])
                        matched = next((item for item in jsonData if item[keyToFind] == value), None)

                        colGet = arrActionDetail[2].split(',')
                        valueToInput = {}
                        for idx, item in enumerate(newArrTfKey):
                            if isinstance(item, dict):
                                for parentKey, subKeys in item.items():
                                    valueToInput[parentKey] = {k: matched.get(k) for k in subKeys}
                            elif isinstance(item, str):
                                valueToInput[item] = matched.get(colGet[idx])
                            else:
                                raise TypeError(f"Unsupported type in parsed for {parentKey}: {type(subKeys)}")
                    elif "Coding" in arrActionDetail[0]:
                        keyToFind = arrActionDetail[1].split(',')[0]
                        keyToGet = arrActionDetail[1].split(',')[1]

                        if pd.notna(row["Default Value"]):
                            defVal = row["Default Value"]

                        codeUnit = next((item[keyToGet] for item in defVal if item[keyToFind] == value[keyToFind]), None)
                        
                        colGet = arrActionDetail[2].split(',')
                        for idx, item in enumerate(newArrTfKey):
                            if isinstance(item, dict):
                                for parentKey, subKeys in item.items():
                                    valueToInput[parentKey] = f"{codeUnit}:{target['code']}" # {k: matched.get(k) for k in subKeys}
                            elif isinstance(item, str):
                                if colGet[idx] == "unitcode":
                                    valueToInput[item] = f"{codeUnit}:{value["code"]}"
                                else:
                                    valueToInput[item] = value[colGet[idx]]
                    elif "Value" in arrActionDetail[0]:
                        keyToFind = arrActionDetail[1].split(',')[0]
                        keyToGet = arrActionDetail[1].split(',')[1]

                        if pd.notna(row["Default Value"]):
                            defVal = row["Default Value"]

                        codeUnit = next((item[keyToGet] for item in defVal if item[keyToFind] == value[keyToFind]), None)

                        colGet = arrActionDetail[2].split(',')
                        for idx, item in enumerate(newArrTfKey):
                            if isinstance(item, dict):
                                # kalau list → mapping banyak key
                                for parentKey, subKeys in item.items():
                                    val = {}
                                    colGet2 = []

                                    tempColGet2 = getIdAndLabel(colGet[idx])
                                    if tempColGet2:
                                        if "root" in tempColGet2:
                                            colGet2 = tempColGet2["root"]
                                        else:
                                            colGet2 = tempColGet2
                                    else:
                                        colGet2 = None

                                    for idx2, item2 in enumerate(subKeys):
                                        if colGet2[idx2] == "unitcode":
                                            val[item2] = f"{codeUnit}:{value["code"]}"
                                        else:
                                            val[item2] = value[colGet2[idx2]]
                                    valueToInput[parentKey] = val
                            elif isinstance(item, str):
                                valueToInput[item] = value[colGet[idx]]
    else:
        valueToInput = value
    
    if skipFirst:
        if pd.notna(row["What to Use Third"]):
            setNested(target, [row["What to Use Second"], row["What to Use Third"]], valueToInput)
        elif pd.notna(row["What to Use Second"]):
            setNested(target, [row["What to Use Second"]], valueToInput)
    else:
        if pd.notna(row["What to Use Third"]):
            setNested(target, [row["What to Use First"], [row["What to Use Second"]], [row["What to Use Third"]]], valueToInput)
        elif pd.notna(row["What to Use Second"]):
            setNested(target, [row["What to Use First"], [row["What to Use Second"]]], valueToInput)
        elif pd.notna(row["What to Use First"]):
            setNested(target, [row["What to Use First"]], valueToInput)
    
def setBeaconArrayValue(target, arrValue):
    firstRow = arrValue[0]
    secondRow = arrValue[1]
    if isinstance(secondRow["value"], list):
        arrValueToInput = []
        dictValueToInput = {}
        for item in arrValue[1:]:
            row = item["row"]
            value = item["value"]
            if isinstance(value, list):
                for val in value:
                    tempDictValueToInput = {}
                    setBeaconValue(row, tempDictValueToInput, val, True)
                    arrValueToInput.append(tempDictValueToInput)
            else:
                setBeaconValue(row, dictValueToInput, value, True)

        if len(arrValueToInput) > 0:
            for dictItem in arrValueToInput:
                dictItem.update(dictValueToInput)
            setNested(target, [firstRow["row"]["What to Use First"]], arrValueToInput, as_list=True, doExtend=True)
        else:
            setNested(target, [firstRow["row"]["What to Use First"]], dictValueToInput, as_list=True, doExtend=False)
    else:
        arrValueToInput = {}
        for item in arrValue[1:]:
            row = item["row"]
            value = item["value"]
            setBeaconValue(row, arrValueToInput, value, True)

        setNested(target, [firstRow["row"]["What to Use First"]], arrValueToInput, as_list=True, doExtend=False)

#Helper
def setNested(target, keys, value, as_list=False, doExtend=False):
    d = target
    for key in keys[:-1]:
        # pastikan level dict ada
        d = d.setdefault(key, {})
    
    last_key = keys[-1]
    if as_list:
        # jika level terakhir adalah list
        if doExtend and isinstance(value, list):
            d.setdefault(last_key, []).extend(value)
        else:
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

def getIdAndLabel(data: str) -> list:
    try:
        start = data.find('[') + 1
        end = data.find(']')
        
        # Pastikan formatnya valid
        if start == 0 or end == -1:
            return {}
        
        before = data[:start].rstrip('[:')   
        arrContent = data[start:end].split(':')
        
        return {before if before else "root": arrContent}
    except Exception:
        return {}