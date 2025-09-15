import os
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

pathFhirJsonDir = os.path.join(os.getcwd(), 'FHIR Json')

def validate_fhir_resource(json_file):
    file_path = os.path.join(pathFhirJsonDir, json_file)
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = f.read()

    resource_type = json_data.split('"resourceType": "')[1].split('"')[0]

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
        "Bundle": Bundle
    }

    resource_class = resource_class_map.get(resource_type)
    if not resource_class:
        return False, file_path
    try:
        resource_instance = resource_class.parse_raw(json_data)
        return True, file_path
    except Exception as e:
        return False, file_path