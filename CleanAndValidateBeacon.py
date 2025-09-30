import json
import os
from urllib.request import pathname2url
from jsonschema import validate, ValidationError, Draft202012Validator, RefResolver

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
                            for data in dataToValidate:
                                pretty_validate(validator, data)
                        elif isinstance(dataToValidate, dict):
                            pretty_validate(validator, dataToValidate)

                

# Helper
def cleanBeacon(beaconJson):
    if isinstance(beaconJson, dict):
        cleaned = {}
        for key, value in beaconJson.items():
            cleaned[key] = cleanBeacon(value)
        return cleaned

    elif isinstance(beaconJson, list):
        seen = set()
        cleaned = []
        for item in beaconJson:
            if isinstance(item, dict):
                code_id = extractId(item)
                if code_id:
                    if code_id not in seen:
                        seen.add(code_id)
                        cleaned.append(cleanBeacon(item))
                else:
                    cleaned.append(cleanBeacon(item))
            else:
                cleaned.append(item)
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
        print("✅ Beacon valid sesuai schema!")
        return True

    print("❌ Beacon tidak valid:")
    for i, error in enumerate(errors, 1):
        location = " -> ".join(map(str, error.path)) or "root"
        # Buat pesan lebih manusiawi
        if hasattr(error, "validator") and error.validator == "required":
            missing = ", ".join(error.validator_value)
            message = f'Field "{location}" hilang, dibutuhkan: {missing}.'
        elif hasattr(error, "validator") and error.validator == "type":
            message = f'Field "{location}" harus berupa {error.validator_value}, ditemukan: {error.instance}.'
        else:
            message = f'Field "{location}": {error.message}'
        print(f"{i}. {message}")
    return False