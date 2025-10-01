import os
import pandas as pd
import json

def convertFhirToBeacon(beacon, fhirJson, index, typeFhir, dict = []):
    mapper_path = os.path.join(os.getcwd(), "Mapper.xlsx")
    df = pd.read_excel(mapper_path, sheet_name="Mapper")
    df_filtered = df[df["Where to Find"].str.contains(typeFhir, na=False)]

    groupsMapper = df_filtered.groupby("Where to Use")

    for key, group in groupsMapper:
        if key not in beacon:
            beacon[key] = []

        target = {}
        # get first object if exists
        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            target = beacon[key][index]

        for _, row in group.iterrows():            
            target = mapFhirToBeacon(row, target, fhirJson, df_filtered, dict)

        if key in beacon and len(beacon[key]) > index and beacon[key][index] is not None:
            beacon[key][index] = target
        else:
            beacon[key].append(target)

    return beacon

#Beacon
def mapFhirToBeacon(row, target, fhirObjDict, df, dict = []):
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

                    if 'OR' in valToFind:
                        arrValToFind = valToFind.split('OR')
                    elif 'AND' in valToFind:
                        arrValToFind = valToFind.split('AND')
                    else:
                        arrValToFind = [valToFind]

                    resultValidate = False
                    for val in arrValToFind:
                        root_val = fhirObjDict.get(arrToFind[0].split('-')[0])
                        
                        if root_val is not None and validate_nested(root_val, arrToFind[1:], val):
                            resultValidate = True
                            if 'OR' in valToFind:
                                break
                        else:
                            if 'AND' in valToFind:
                                resultValidate = False
                                break

                    if not resultValidate:
                        isValid = False
                        break
                elif "COMBINENEXT" in toDo:
                    firstCommand = toDo
                    arrCommand = firstCommand.split('-')
                    if len(arrCommand) > 2:
                        if arrCommand[2] != fhirObjDict["resourceType"]:
                            continue

                    totalRowToCombined = arrCommand[1]
                    for i in range(1, int(totalRowToCombined) + 1):
                        nextRow = df.iloc[df.index.get_loc(row.name) + i]
                        nextValue = getFhirValue(fhirObjDict, nextRow)
                        currToDo = nextRow["What to Do"]
                        if '|' in currToDo:
                            firstCommand = currToDo.split('|')[0]
                            arrToFind = currToDo.split('|')[1].split('-')
                            if arrToFind[0] == "GET":
                                if arrToFind[1] == "dosageInstruction":
                                    text = ""

                                if (nextValue is not None):
                                    # valFind = [
                                    #     coding
                                    #     for obj in nextValue if arrToFind[1] in obj
                                    #     for coding in obj[arrToFind[1]][arrToFind[2]]
                                    # ]
                                    valFind = []
                                    for obj in nextValue:
                                        valFind = extractValues(valFind, obj, arrToFind[1:])

                                    valueToInput.append({
                                        "row": nextRow,
                                        "value": valFind
                                    })
                            elif arrToFind[0] == "GETREF":
                                if nextValue is not None:
                                    arrNextVal = nextValue.split('/')
                                    for dictData in dict:
                                        if dictData['resourceType'] == arrNextVal[0] and dictData['id'] == arrNextVal[1]:
                                            valToFind = getDynamicData(dictData, arrToFind)                                            
                                            valueToInput.append({
                                                "row": nextRow,
                                                "value": valToFind
                                            })
                        else:
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
            
            if len(valueToInput) > 0:
                setBeaconArrayValue(target, valueToInput)

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
                            defVal = json.loads(row["Default Value"])

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
                            defVal = json.loads(row["Default Value"])

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
    if len(arrValue) > 1:
        if any(isinstance(row.get("value"), list) for row in arrValue):
            arrValueToInput = []
            dictValueToInput = {}
            for item in arrValue[1:]:
                row = item["row"]
                value = item["value"]
                if isinstance(value, list):
                    if (row["Type of Use Used"] == "array"):
                        arrTempVal = []
                        for val in value:
                            tempDictValueToInput = {}
                            setBeaconValue({
                                "What to Use Third": row["What to Use Third"],
                                "What to Use Second": "root",
                                "Type of Use Used": "object",
                                "What Must Be Done": row["What Must Be Done"],
                                "Default Value": row["Default Value"]
                            }, tempDictValueToInput, val, True)
                            arrTempVal.append(tempDictValueToInput["root"])
                        
                        if pd.notna(row["What to Use Third"]):
                            setNested(dictValueToInput, [row["What to Use Second"]], arrTempVal, as_list=True, doExtend=True)
                        elif pd.notna(row["What to Use Second"]):
                            setNested(dictValueToInput, [row["What to Use Second"]], arrTempVal)
                    else:
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

def extractValues(valFind, data, keys):
    if not keys:
        # level terakhir, pastikan hasilnya array
        if isinstance(data, list):
            valFind.extend(data)
        else:
            valFind.append(data)
        return valFind

    key = keys[0]

    # jika key adalah list (multiple possible keys), ambil semua yang match
    possible_keys = [key] if not isinstance(key, list) else [k for k in key if (isinstance(data, dict) and k in data)]

    for k in possible_keys:
        if isinstance(data, dict) and k in data:
            valFind = extractValues(valFind, data[k], keys[1:])
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and k in item:
                    valFind = extractValues(valFind, item[k], keys[1:])
    
    return valFind

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
    
def getDynamicData(data: dict, arrToFind: list):
    # navigasi sesuai panjang arrToFind
    val = data
    for key in arrToFind[1:]:  # skip index 0 (GETREF dsb)
        if isinstance(val, dict):
            val = val.get(key, None)
        else:
            val = None
        if val is None:
            break

    # Normalisasi hasil jadi list
    if val is None:
        return []
    elif isinstance(val, list):
        return val
    else:
        return [val]
