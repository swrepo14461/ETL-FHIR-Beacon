import json
import os
from datetime import datetime
from urllib.request import pathname2url
from jsonschema import validate, ValidationError, Draft202012Validator, RefResolver
from decimal import Decimal

beaconSchemaDir = os.path.join(os.getcwd(), "BeaconSchema")
def doCleanBeaconJson(beacon):
    cleanedBeacon = {}
    beaconConf = None
    beaconConfSchema = os.path.join(beaconSchemaDir, "beaconConfiguration.json")
    with open(beaconConfSchema) as r:
        beaconConf = json.load(r)

    if beaconConf is not None:
        entry_types = list(beaconConf.get("entryTypes", {}).keys())
        for entryType in entry_types:
            # if entryType not in cleanedBeacon:
            #     cleanedBeacon[entryType] = []

            if entryType in beacon:
                cleanedBeacon[entryType] = cleanBeacon(beacon[entryType])

    return cleanedBeacon

def doValidate(beacon):
    summary = []
    beaconConf = None
    beaconConfSchema = os.path.join(beaconSchemaDir, "beaconConfiguration.json")
    with open(beaconConfSchema) as r:
        beaconConf = json.load(r)

    if beaconConf is not None:
        entry_types = list(beaconConf.get("entryTypes", {}).keys())
        for entryType in entry_types:
            if entryType in beacon:
                schemaFolder = None
                match entryType:
                    case "analysis":
                        schemaFolder = os.path.join(beaconSchemaDir, "analyses")
                    case "biosample":
                        schemaFolder = os.path.join(beaconSchemaDir, "biosamples")
                    case "cohort":
                        schemaFolder = os.path.join(beaconSchemaDir, "cohorts")
                    case "dataset":
                        schemaFolder = os.path.join(beaconSchemaDir, "datasets")
                    case "genomicVariant":
                        schemaFolder = os.path.join(beaconSchemaDir, "genomicVariations")
                    case "individual":
                        schemaFolder = os.path.join(beaconSchemaDir, "individuals")
                    case "run":
                        schemaFolder = os.path.join(beaconSchemaDir, "runs")
                
                if schemaFolder is not None:
                    jsonPathSchema = os.path.join(schemaFolder, "defaultSchema.json")
                    if jsonPathSchema is not None:
                        with open(jsonPathSchema, "r", encoding="utf-8") as r:
                            schema = json.load(r)

                        base_uri = f"file://{pathname2url(schemaFolder)}/"
                        resolver = RefResolver(base_uri=base_uri, referrer=schema)
                        validator = Draft202012Validator(schema, resolver=resolver)

                        dataToValidate = beacon[entryType]
                        if isinstance(dataToValidate, list):
                            for idx, data in enumerate(dataToValidate):
                                resultValidate, errMessage = pretty_validate(validator, data)
                                if resultValidate is True:
                                    summary.append(f"{entryType} -> Index [{idx}] is Valid")
                                else:
                                    summary.append(f"{entryType} -> Index [{idx}] is Not Valid, Reason : ")
                                    for i, error in enumerate(errMessage, 1):
                                        location = " -> ".join(map(str, error.path)) or "root"                                        
                                        if hasattr(error, "validator") and error.validator == "required":
                                            message = f'In field "{location}" something is missing, reason: {error.message}.'
                                        elif hasattr(error, "validator") and error.validator == "type":
                                            message = f'In field "{location}" must be of type {error.validator_value}, but found: {error.instance}.'
                                        else:
                                            message = f'Field "{location}": {error.message}'

                                        summary.append(f"{i}. {message}")

                        elif isinstance(dataToValidate, dict):
                            resultValidate, errMessage = pretty_validate(validator, dataToValidate)
                            if resultValidate is True:
                                summary.append(f"{entryType} is Valid")
                            else:
                                summary.append(f"{entryType} is Not Valid, Reason : ")
                                for i, error in enumerate(errMessage, 1):
                                    location = " -> ".join(map(str, error.path)) or "root"                                        
                                    if hasattr(error, "validator") and error.validator == "required":
                                        message = f'In field "{location}" something is missing, reason: {error.message}.'
                                    elif hasattr(error, "validator") and error.validator == "type":
                                        message = f'In field "{location}" must be of type {error.validator_value}, but found: {error.instance}.'
                                    else:
                                        message = f'Field "{location}": {error.message}'

                                    summary.append(f"{i}. {message}")

            else:
                summary.append(f"{entryType} Not Found in beacon")
    
    if len(summary) > 0:
        summaryText = "\n".join(summary)
        print(summaryText)
        
        pathResult = os.path.join(os.getcwd(), 'Result')
        os.makedirs(pathResult, exist_ok=True)
        filename = f"Beacon_Summary_Validate_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}.txt"
        result_file = os.path.join(pathResult, filename)
        with open(result_file, "a", encoding="utf-8") as f:
            f.write(summaryText)

def doConvertToString(beacon):
    if isinstance(beacon, list):
        return [doConvertToString(i) for i in beacon]
    elif isinstance(beacon, dict):
        return {k: doConvertToString(v) for k, v in beacon.items()}
    elif isinstance(beacon, (Decimal, float, int)):
        return str(beacon)
    
    return beacon


# Helper
def cleanBeacon(beaconJson):
    if isinstance(beaconJson, dict):
        cleaned = {}
        for key, value in beaconJson.items():
            cleaned[key] = cleanBeacon(value)
        return cleaned

    elif isinstance(beaconJson, list):
        cleaned = []
        for item in beaconJson:
            if isinstance(item, (dict, list)):
                cleaned.append(cleanBeacon(item))
            else:
                cleaned.append(item)
                
        # Hapus Duplikat dihilangkan karena semua id nya sama
        # seen = set()
        # cleaned = []
        # for item in beaconJson:
        #     if isinstance(item, dict):
        #         code_id = extractId(item)
        #         if code_id:
        #             if code_id not in seen:
        #                 seen.add(code_id)
        #                 cleaned.append(cleanBeacon(item))
        #         else:
        #             cleaned.append(cleanBeacon(item))
        #     else:
        #         cleaned.append(item)
        return cleaned

    else:
        return beaconJson

def extractId(item):
    if isinstance(item, dict):
        if "id" in item and isinstance(item["id"], str):
            return item["id"]
        for v in item.values():
            found = extractId(v)
            if found:
                return found
    elif isinstance(item, list):
        for v in item:
            found = extractId(v)
            if found:
                return found
    return None

def pretty_validate(validator, data):
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if not errors:
        return True, []

    return False, errors