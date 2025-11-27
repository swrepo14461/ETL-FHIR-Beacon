import os
import FHIRProcess
import json
import CleanAndValidateBeacon
from collections import OrderedDict
from datetime import datetime

jsonFiles = []
pathFhirJsonDir = os.path.join(os.getcwd(), 'FHIR Json')
for file in os.listdir(pathFhirJsonDir):
    if file.endswith('.json'):
        jsonFiles.append(file)

print(f"Found {len(jsonFiles)} JSON files in '{pathFhirJsonDir}'")

print(f"Check JSON files...")
valid_count = 0
invalid_count = 0

valid_files = []
for jsonFile in jsonFiles:
    is_valid, file_path = FHIRProcess.validate_fhir_resource(jsonFile)

    if is_valid:
        valid_count += 1
        valid_files.append(file_path)
    else:
        invalid_count += 1

print(f"Validation complete. Valid files: {valid_count}, Invalid files: {invalid_count}")
print(f"Start processing JSON files...")

pathHeader = os.path.join(os.getcwd(), 'HeaderBeacon.json')
with open(pathHeader, "r", encoding="utf-8") as f:
    beacon = json.load(f) 

for idx, filesTobeacon in enumerate(valid_files):
    print(f"Processing {filesTobeacon}...")
    newIdx = FHIRProcess.getIndex(beacon, filesTobeacon, idx)
    beacon = FHIRProcess.process_fhir_resource(beacon, filesTobeacon, newIdx)
    
pathResult = os.path.join(os.getcwd(), 'Result')
os.makedirs(pathResult, exist_ok=True)

print(f"Start Cleaning Beacon...")
cleanedBeacon = CleanAndValidateBeacon.doCleanBeaconJson(beacon)

print(f"Start Validate Beacon...")
CleanAndValidateBeacon.doValidate(cleanedBeacon)

print(f"Start Convert To String...")
convertedBeacon = CleanAndValidateBeacon.doConvertToString(cleanedBeacon)

print(f"Generate Beacon File...")
filename = f"Beacon_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}.json"
result_file = os.path.join(pathResult, filename)
with open(result_file, 'w') as out_f:
    out_f.write(json.dumps(OrderedDict(convertedBeacon), indent=4, sort_keys=True, default=str))

print(f"Generated to {result_file}...")