import os
import FHIRProcess

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
# for jsonFile in valid_files:
    