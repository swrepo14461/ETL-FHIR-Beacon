import os
import json
import YamlToBeaconConverter
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.observation import Observation
from fhir.resources.encounter import Encounter
from fhir.resources.servicerequest import ServiceRequest
from fhir.resources.specimen import Specimen
from fhir.resources.immunization import Immunization
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.medication import Medication
from fhir.resources.procedure import Procedure
from fhir.resources.bundle import Bundle
from fhir.resources.composition import Composition

pathFhirJsonDir = os.path.join(os.getcwd(), 'FHIR Json')

def validate_fhir_resource(json_file):
    file_path = os.path.join(pathFhirJsonDir, json_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = f.read()

    try:
        resource_type = json_data.split('"resourceType": "')[1].split('"')[0]
    except Exception as e:
        return False, file_path

    resource_class_map = {
        "Patient": Patient,
        "Condition": Condition,
        "Observation": Observation,
        "Encounter": Encounter,
        "ServiceRequest": ServiceRequest,
        "Specimen": Specimen,
        "Immunization": Immunization,
        "AllergyIntolerance": AllergyIntolerance,
        "MedicationRequest": MedicationRequest,
        "Medication": Medication,
        "Procedure": Procedure,
        "Bundle": Bundle,
        "Composition": Composition
    }

    if resource_type == "Bundle":
        print(f"{file_path} is a Bundle")
        result = True, file_path
    else:
        resource_class = resource_class_map.get(resource_type)
        if not resource_class:
            print(f"{file_path}: Unsupported resourceType {resource_type}")
            result = False, file_path
        else:
            try: 
                # resource_instance = resource_class.model_validate_json(json_data)
                result = True, file_path
            except Exception as e:
                print(f"{file_path}: Failed to parse {resource_type}: {e}")
                result = False, file_path
    return result

def process_fhir_resource(beacon, file_path, index):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    invalid_count = 0
    entries = json_data.get("entry", [])
    for i, entry in enumerate(entries):
        resource_json = entry.get("resource")
        if not resource_json:
            continue

        resource_type = resource_json.get("resourceType")
        if resource_type == "Patient":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "Procedure":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "Condition":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "Observation":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "AllergyIntolerance":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "Medication":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "MedicationDispense":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        elif resource_type == "FamilyMemberHistory":
            beacon = YamlToBeaconConverter.convertFhirToBeacon(beacon, resource_json, index, resource_type)
        else:
            invalid_count += 1
            
    return beacon

def getIndex(beacon, file_path, index):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    entries = json_data.get("entry", [])
    for i, entry in enumerate(entries):
        
        resource_json = entry.get("resource")
        if not resource_json:
            continue

        resource_type = resource_json.get("resourceType")
        if resource_type == "Patient":
            if "individuals" in beacon:
                lsIndividuals = beacon["individuals"]
                for idx, indv in enumerate(lsIndividuals):
                    if indv["id"] == resource_json["id"]:
                        index = idx
                        break
    
    return index
