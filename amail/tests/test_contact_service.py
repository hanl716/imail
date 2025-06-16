"""
Tests for the ContactService class.
"""
import pytest
import os
import json
from amail.app.contact_service import ContactService
from flask import current_app # To get app.config for the test contacts file path

# Note: The test_client fixture from conftest.py sets up a test app instance
# and ensures that CONTACTS_FILE_PATH_OVERRIDE is set in app.config.
# It also handles cleaning up this test contacts file before each test.

@pytest.fixture
def contact_service_instance(test_client): # Depends on test_client to ensure app_context and config
    """
    Provides a ContactService instance configured to use a test-specific contacts file.
    The test contacts file is cleaned up by the test_client fixture.
    """
    # Get the overridden path from the app config, which was set by test_client fixture
    test_contacts_file_path = current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE')
    if not test_contacts_file_path:
        raise ValueError("CONTACTS_FILE_PATH_OVERRIDE not set in test app config. Check conftest.py.")

    # Ensure the directory for the test contacts file exists
    test_data_dir = os.path.dirname(test_contacts_file_path)
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)

    # The test_client fixture should already clean up the file,
    # but as an extra measure, ensure it's clean before this service instance is used.
    if os.path.exists(test_contacts_file_path):
        os.remove(test_contacts_file_path)

    return ContactService(contacts_file_path=test_contacts_file_path)

def test_add_new_contact(contact_service_instance):
    """Test adding a completely new contact."""
    contact, msg = contact_service_instance.add_contact("Alice Wonderland", "alice@wonder.land", "Friend from childhood")
    assert contact is not None
    assert contact["name"] == "Alice Wonderland"
    assert "alice@wonder.land" in contact["email_addresses"]
    assert "Friend from childhood" in contact["notes"]
    assert msg == "New contact added successfully."
    assert len(contact_service_instance.contacts) == 1

    # Verify it's saved to file
    loaded_contacts = contact_service_instance.load_contacts() # Should reload from file
    assert len(loaded_contacts) == 1
    assert loaded_contacts[0]["name"] == "Alice Wonderland"

def test_add_contact_existing_email_different_name_alias(contact_service_instance):
    """Test adding a contact whose email exists but with a different name (should become an alias)."""
    contact_service_instance.add_contact("Bob The Builder", "bob@builder.com", "Handyman")

    updated_contact, msg = contact_service_instance.add_contact("Robert Builder", "bob@builder.com", "Formal name")
    assert updated_contact is not None
    assert updated_contact["name"] == "Bob The Builder" # Original name preserved
    assert "bob@builder.com" in updated_contact["email_addresses"]
    assert "Robert Builder" in updated_contact.get("aliases", [])
    assert "Handyman" in updated_contact["notes"] # Original notes
    assert "Formal name" in updated_contact["notes"] # Appended notes
    assert msg == "Contact updated with new information for existing email."
    assert len(contact_service_instance.contacts) == 1 # Still one contact

def test_add_contact_existing_email_same_name_append_notes(contact_service_instance):
    """Test adding a contact whose email and name already exist (should append notes)."""
    contact_service_instance.add_contact("Carol Danvers", "carol@avengers.com", "Met at SHIELD")

    updated_contact, msg = contact_service_instance.add_contact("Carol Danvers", "carol@avengers.com", "Likes cats")
    assert updated_contact is not None
    assert updated_contact["name"] == "Carol Danvers"
    assert "carol@avengers.com" in updated_contact["email_addresses"]
    assert "Met at SHIELD" in updated_contact["notes"]
    assert "Likes cats" in updated_contact["notes"]
    assert msg == "Contact updated with new information for existing email." # Or a more specific "notes updated"
    assert len(contact_service_instance.contacts) == 1

def test_add_contact_same_name_different_email(contact_service_instance):
    """Test adding a contact with the same name as an existing one but a different email (new contact)."""
    contact_service_instance.add_contact("David Copperfield", "david@magic.com")

    new_contact, msg = contact_service_instance.add_contact("David Copperfield", "d.copperfield@illusions.org")
    assert new_contact is not None
    assert new_contact["name"] == "David Copperfield"
    assert "d.copperfield@illusions.org" in new_contact["email_addresses"]
    assert msg == "New contact added successfully."
    assert len(contact_service_instance.contacts) == 2 # Should be two distinct contacts

def test_find_contact_by_email(contact_service_instance):
    """Test finding a contact by their email address."""
    contact_service_instance.add_contact("Eve Polastri", "eve.polastri@mi6.uk")

    found_contact = contact_service_instance.find_contact_by_email("eve.polastri@mi6.uk")
    assert found_contact is not None
    assert found_contact["name"] == "Eve Polastri"

    not_found_contact = contact_service_instance.find_contact_by_email("villanelle@the12.org")
    assert not_found_contact is None

def test_suggest_duplicates_simple(contact_service_instance):
    """Test duplicate suggestion with simple name variations."""
    contact_service_instance.add_contact("John Smith", "john.smith@example.com")
    contact_service_instance.add_contact("Smith John", "jsmith@work.com") # Normalized name should match
    contact_service_instance.add_contact("Jonathan Smith", "jonathan@home.com") # Different normalized
    contact_service_instance.add_contact("Jane Doe", "jane@example.com")

    duplicates = contact_service_instance.suggest_duplicates()
    assert len(duplicates) == 1 # Expecting one group of duplicates ("john smith")
    assert len(duplicates[0]) == 2 # That group should have two contacts

    # Check if the correct contacts are in the duplicate group (names might vary due to normalization)
    names_in_group = sorted([c['name'] for c in duplicates[0]])
    assert names_in_group == ["John Smith", "Smith John"]

def test_suggest_duplicates_no_duplicates(contact_service_instance):
    """Test duplicate suggestion when no obvious duplicates exist."""
    contact_service_instance.add_contact("Unique Name1", "unique1@example.com")
    contact_service_instance.add_contact("Another Unique Name", "unique2@example.com")
    duplicates = contact_service_instance.suggest_duplicates()
    assert len(duplicates) == 0

def test_suggest_duplicates_with_titles_and_middle_names(contact_service_instance):
    """Test duplicate suggestion with names that include titles or middle initials."""
    contact_service_instance.add_contact("Dr. Emily Carter", "emily.carter@university.edu")
    contact_service_instance.add_contact("Carter Emily", "e.carter@research.org") # Normalized: "carter emily"
    contact_service_instance.add_contact("Prof. Emily R Carter", "ercarter@lab.net") # Normalized: "carter emily" (if middle name/initial is handled simply)
                                                                                 # Current _normalize_name_for_matching sorts parts, so "carter emily r" -> "carter emily r"
                                                                                 # This test might need adjustment based on how sophisticated normalization is.
                                                                                 # Current: "carter emily r" -> "carter emily r"
                                                                                 # "carter emily" -> "carter emily"
                                                                                 # This specific case might not group them if "r" is kept.
                                                                                 # Let's adjust test for current normalization:
    contact_service_instance.add_contact("Emily Carter", "ec@personal.com") # Normalized: "carter emily"

    duplicates = contact_service_instance.suggest_duplicates()
    # Expecting "dr. emily carter" (carter dr. emily), "carter emily", "emily carter" (carter emily) to group.
    # "prof. emily r carter" might be separate if "r" is kept and not just first/last.
    # The current normalization sorts all parts:
    # "dr. emily carter" -> "carter dr. emily" (after title removal -> "carter emily")
    # "carter emily" -> "carter emily"
    # "emily carter" -> "carter emily"
    # "prof. emily r carter" -> "carter emily prof. r" (after title removal -> "carter emily r")

    # So, "carter emily" group should have 3. "carter emily prof. r" is separate.
    found_group_of_3 = False
    for group in duplicates:
        if len(group) == 3:
            names = sorted([c['name'] for c in group])
            if "Dr. Emily Carter" in names and "Carter Emily" in names and "Emily Carter" in names:
                found_group_of_3 = True
                break
    assert found_group_of_3, "Expected a group of 3 similar Emily Carter names."

    # Check that "Prof. Emily R Carter" is not in that group of 3, or forms its own singleton (not a duplicate)
    # or is in a group of 1 if we listed all groups. `suggest_duplicates` only returns groups > 1.
    # So, we expect only one group of duplicates here.
    assert len(duplicates) == 1

def test_load_contacts_file_not_found(test_client):
    """Test loading contacts when the JSON file does not exist."""
    # test_client fixture ensures CONTACTS_FILE_PATH_OVERRIDE is set
    # And it cleans up the file before each test.
    contacts_file = current_app.config['CONTACTS_FILE_PATH_OVERRIDE']
    # Ensure it's really gone if a previous test created it (though test_client should handle this)
    if os.path.exists(contacts_file):
        os.remove(contacts_file)

    service = ContactService(contacts_file_path=contacts_file)
    assert service.contacts == [] # Should load an empty list

def test_load_contacts_empty_file(test_client):
    """Test loading contacts from an empty JSON file."""
    contacts_file = current_app.config['CONTACTS_FILE_PATH_OVERRIDE']
    with open(contacts_file, 'w') as f:
        f.write("") # Create an empty file

    service = ContactService(contacts_file_path=contacts_file)
    assert service.contacts == []

def test_load_contacts_malformed_json(test_client):
    """Test loading contacts from a malformed JSON file."""
    contacts_file = current_app.config['CONTACTS_FILE_PATH_OVERRIDE']
    with open(contacts_file, 'w') as f:
        f.write("{[this is not valid json")

    service = ContactService(contacts_file_path=contacts_file)
    assert service.contacts == [] # Should gracefully handle error and return empty
