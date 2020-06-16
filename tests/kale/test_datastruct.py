import pytest

from kale.constants import Disease, TreatmentCost
from kale.datastruct import Patient, PatientCollection


@pytest.fixture
def pat1():
    return Patient(name="John", delta_dict={Disease.healthy: 0, Disease.cold: 3},
                   confidence_dict={Disease.healthy: 0.3, Disease.cold: 0.7}, disease=Disease.cold)


@pytest.fixture
def pat2():
    return Patient(name="Jane", delta_dict={Disease.healthy: 0, Disease.lung_cancer: 10},
                   confidence_dict={Disease.healthy: 0.2, Disease.lung_cancer: 0.8}, disease=Disease.healthy)


@pytest.fixture
def pat3():
    return Patient(name="Jackson", delta_dict={Disease.healthy: 0, Disease.lung_cancer: 10},
                   confidence_dict={Disease.healthy: 0.8, Disease.lung_cancer: 0.2}, disease=Disease.healthy)


@pytest.fixture
def patient_collection1(pat1, pat2):
    return PatientCollection(patients=[pat1, pat2], identifier=0)


@pytest.fixture
def patient_collection2(pat1, pat3):
    return PatientCollection(patients=[pat1, pat3], identifier=0)


def test_Patient(pat1, pat2):
    assert pat1.name == "John"
    assert pat1.disease == "cold"
    assert pat1.true_life_gain(Disease.healthy) == 0.0
    assert pat1.true_life_gain(Disease.lung_cancer) == 0.0
    assert pat1.true_life_gain(Disease.cold) == 3.0
    assert pat1.expected_life_gain(Disease.healthy) == 0.0
    assert pat1.expected_life_gain(Disease.lung_cancer) == 0.0
    assert pat1.expected_life_gain(Disease.cold) == 0.7 * 3
    assert pat1.uuid != pat2.uuid
    assert hash(pat1) != hash(pat2)
    with pytest.raises(TypeError):
        pat1.name = "New Name"


def test_PatientCollection_basics(patient_collection1):
    assert patient_collection1.identifier == 0

    # with unbounded costs we just heal the disease
    treatments_dict, expected_life_gain, cost = patient_collection1.optimal_treatment()
    assert sorted(treatments_dict.values()) == ["cold", "lung_cancer"]
    assert expected_life_gain == 0.7*3 + 0.8*10
    assert cost == TreatmentCost.cold + TreatmentCost.lung_cancer

    # checking the treatment-evaluating methods
    assert patient_collection1.true_life_gain(treatments_dict) == 3.0
    assert patient_collection1.treatment_cost(treatments_dict) == cost
    assert patient_collection1.expected_life_gain(treatments_dict) == expected_life_gain


def test_PatientCollection_bounded_cost(patient_collection1):
    # adding a hard cost boundary - here we can only heal cold, so we do it
    treatments_dict, expected_life_gain, cost = patient_collection1.optimal_treatment(max_cost=2)
    assert sorted(treatments_dict.values()) == ["cold", "healthy"]
    assert expected_life_gain == 0.7 * 3
    assert cost == TreatmentCost.cold

    # if possible, it is more beneficial to heal lung cancer for these patients
    treatments_dict, expected_life_gain, cost = patient_collection1.optimal_treatment(max_cost=3)
    assert sorted(treatments_dict.values()) == ["healthy", "lung_cancer"]
    assert expected_life_gain == 0.8 * 10
    assert cost == TreatmentCost.lung_cancer


def test_PatientCollection_nontrivial_optimization(patient_collection2):
    # although cost-wise it would be possible to heal the cancer,
    # in expectation it is more beneficial to heal the cold since 0.7 * 3 > 0.2 * 10
    treatments_dict, expected_life_gain, cost = patient_collection2.optimal_treatment(max_cost=3)
    assert sorted(treatments_dict.values()) == ["cold", "healthy"]
    assert expected_life_gain == 0.7 * 3
    assert cost == TreatmentCost.cold

# TODO: multiple important cases are missing
