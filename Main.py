import os
import FHIRProcess
import YamlToBeaconConverter

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
beacon = {
    "datasetId": "UNQ_1", 
    "dataset": {
        "id": "UNQ_1", 
        "createDateTime": "2021-03-21T02:37:00-08:00",
        "dataUseConditions": { 
            "duoDataUse": [
                {
                    "id": "DUO:0000042",
                    "label": "general research use",
                    "version": "17-07-2016"
                }
            ]
        },
        "description": "Simulation set 1.",
        "externalUrl": "http://example.org/wiki/Main_Page",
        "info": {},
        "name": "Dataset with fake data",
        "updateDateTime": "2022-08-05T17:21:00+01:00",
        "version": "v1.1"
    },
}
for filesTobeacon in valid_files:
    FHIRProcess.process_fhir_resource(beacon, filesTobeacon)