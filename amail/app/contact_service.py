"""
Manages contacts for the Amail application.

This service provides functionality to load, save, add, and find contacts.
Contacts are stored in a JSON file (`amail/data/contacts.json`).
It also includes a basic mechanism for suggesting potential duplicate contacts
based on name similarity.

Future enhancements could include more robust storage (database), advanced
duplicate detection, and contact merging capabilities.
"""
import json         # For reading and writing contacts data to JSON file
import os           # For path manipulation and directory creation
import uuid         # For generating unique IDs for contacts
from collections import defaultdict # For grouping contacts during duplicate detection
from flask import current_app   # For accessing Flask app context (e.g., logger)

# --- Path Definitions ---
# Assumes this service file is in 'amail/app/'.
# APP_ROOT determines the root directory of the 'amail' package.
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Resolves to 'amail/'
DATA_DIR = os.path.join(APP_ROOT, 'data') # Path to 'amail/data/'
# Default path for the JSON file where contacts are stored.
CONTACTS_FILE_PATH = os.path.join(DATA_DIR, 'contacts.json')
# --- End Path Definitions ---

class ContactService:
    """
    Service class for managing contacts.
    Handles loading from and saving to a JSON file, adding new contacts,
    finding contacts, and suggesting potential duplicates.
    """
    def __init__(self, contacts_file_path=None):
        """
        Initializes the ContactService.

        Args:
            contacts_file_path (str, optional):
                The path to the JSON file used for storing contacts.
                If None, defaults to `CONTACTS_FILE_PATH`.
        """
        self.contacts_file_path = contacts_file_path or CONTACTS_FILE_PATH
        self._ensure_data_dir_exists() # Ensure the data directory exists
        self.contacts = self.load_contacts() # Load contacts into memory on initialization

    def _ensure_data_dir_exists(self):
        """
        Ensures that the data directory (defined by `DATA_DIR`) exists.
        Creates the directory if it's missing.
        Logs errors if directory creation fails.
        """
        if not os.path.exists(DATA_DIR):
            try:
                os.makedirs(DATA_DIR)
            except OSError as e:
                if current_app:
                    current_app.logger.error(f"Error creating data directory {DATA_DIR}: {e}")
                else:
                    print(f"Error creating data directory {DATA_DIR}: {e}")

    def load_contacts(self):
        """
        Loads contacts from the JSON file specified by `self.contacts_file_path`.

        Returns:
            list: A list of contact dictionaries. Returns an empty list if the file
                  doesn't exist, is empty, or an error occurs during loading/parsing.
        """
        logger = current_app.logger if current_app else print
        try:
            if os.path.exists(self.contacts_file_path):
                with open(self.contacts_file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    if not file_content.strip(): # Check if file is empty or just whitespace
                        logger.info(f"Contacts file '{self.contacts_file_path}' is empty. Returning empty list.")
                        return []
                    # Parse JSON content into a list of contacts
                    loaded_contacts = json.loads(file_content)
                    logger.info(f"Successfully loaded {len(loaded_contacts)} contacts from '{self.contacts_file_path}'.")
                    return loaded_contacts
            else: # File does not exist
                logger.info(f"Contacts file '{self.contacts_file_path}' not found. Returning empty list.")
                return []
        except (IOError, json.JSONDecodeError) as e: # Handle file I/O or JSON parsing errors
            logger.error(f"Error loading contacts from '{self.contacts_file_path}': {e}")
            return [] # Return an empty list to ensure the app can continue gracefully

    def save_contacts(self):
        """
        Saves the current list of contacts (`self.contacts`) to the JSON file.
        The JSON is pretty-printed with an indent of 4 for readability.
        """
        self._ensure_data_dir_exists() # Ensure data directory exists before attempting to save
        logger = current_app.logger if current_app else print
        try:
            with open(self.contacts_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.contacts, f, indent=4, ensure_ascii=False) # ensure_ascii=False for non-Latin names
            logger.info(f"Successfully saved {len(self.contacts)} contacts to '{self.contacts_file_path}'.")
        except IOError as e:
            logger.error(f"Error saving contacts to '{self.contacts_file_path}': {e}")

    def add_contact(self, name, email_address, notes=""):
        """
        Adds a new contact or updates an existing one.

        If the provided `email_address` already exists in a contact's `email_addresses` list,
        the existing contact is updated:
        - If the `name` is different from the contact's primary name and not already in `aliases`, it's added.
        - `notes` are appended to existing notes.

        If the `email_address` does not exist, a new contact is created.

        Args:
            name (str): The primary name for the contact.
            email_address (str): The email address to add/associate with the contact.
            notes (str, optional): Additional notes for the contact. Defaults to "".

        Returns:
            tuple: (contact_dict, message_str)
                   - `contact_dict`: The newly created or updated contact dictionary, or `None` on validation failure.
                   - `message_str`: A status message indicating success or failure.
        """
        logger = current_app.logger if current_app else print
        if not name or not email_address: # Basic validation
            logger.warning("Attempted to add contact with missing name or email.")
            return None, "Name and email address are required to add a contact."

        normalized_email = email_address.lower().strip() # Normalize for consistent matching

        # Check if this email already exists for any contact
        for existing_contact in self.contacts:
            # Normalize existing emails for comparison
            normalized_existing_emails = [e.lower().strip() for e in existing_contact.get('email_addresses', [])]
            if normalized_email in normalized_existing_emails:
                # Email found in an existing contact. Update this contact.
                updated = False
                # Add name as an alias if it's different from primary name and not already an alias
                if name != existing_contact.get('name') and name not in existing_contact.get('aliases', []):
                    existing_contact.setdefault('aliases', []).append(name)
                    updated = True
                # Append notes if new notes are provided
                if notes:
                     existing_contact['notes'] = (existing_contact.get('notes', "") + f"\n---\n{notes}").strip()
                     updated = True

                if updated:
                    self.save_contacts()
                    logger.info(f"Updated existing contact (ID: {existing_contact['contact_id']}) for email '{normalized_email}'.")
                    return existing_contact, "Contact updated with new information for existing email."
                else:
                    logger.info(f"Email '{normalized_email}' already exists for contact (ID: {existing_contact['contact_id']}). No changes made.")
                    return existing_contact, "Email already associated with this contact. No new information to add."

        # Email does not exist in any contact; create a new contact entry.
        new_contact_entry = {
            "contact_id": str(uuid.uuid4()), # Generate a unique ID
            "name": name.strip(),
            "email_addresses": [normalized_email],
            "aliases": [], # List to store alternative names
            "notes": notes.strip(),
            "linked_person_id": None # For future explicit merging of duplicate persons
        }
        self.contacts.append(new_contact_entry)
        self.save_contacts()
        logger.info(f"Added new contact: '{name}' with email '{normalized_email}'.")
        return new_contact_entry, "New contact added successfully."

    def find_contact_by_email(self, email_address):
        """
        Finds a contact by a given email address.
        Searches through all contacts and their `email_addresses` list.

        Args:
            email_address (str): The email address to search for.

        Returns:
            dict: The contact dictionary if found, otherwise `None`.
        """
        normalized_target_email = email_address.lower().strip()
        for contact in self.contacts:
            normalized_contact_emails = [e.lower().strip() for e in contact.get('email_addresses', [])]
            if normalized_target_email in normalized_contact_emails:
                return contact # Return the first contact found with this email
        return None # No contact found with this email

    def _normalize_name_for_matching(self, name_str):
        """
        Performs simple normalization on a name string for duplicate detection.
        This includes lowercasing, removing common titles, and basic parsing
        to compare first and last names, and sorting name parts.

        Args:
            name_str (str): The name string to normalize.

        Returns:
            str: The normalized name string. Returns an empty string if input is empty or None.
        """
        if not name_str:
            return ""

        # Lowercase and remove common titles
        normalized_name = name_str.lower()
        titles_to_remove = ["mr.", "ms.", "mrs.", "dr.", "prof."]
        for title in titles_to_remove:
            normalized_name = normalized_name.replace(title, "")
        normalized_name = normalized_name.strip() # Remove leading/trailing spaces

        # Basic attempt to handle "Last, First" by splitting and rejoining if a comma is present
        if ',' in normalized_name:
            parts = [p.strip() for p in normalized_name.split(',')]
            if len(parts) == 2: # e.g., "Doe, John"
                normalized_name = f"{parts[1]} {parts[0]}" # Reorder to "John Doe"

        name_parts = normalized_name.split()

        # If more than two parts (e.g., "First Middle Last"), try to keep first and last.
        # This is a very basic heuristic and might discard important distinctions.
        # if len(name_parts) > 2:
        #     name_parts = [name_parts[0], name_parts[-1]]

        # Sort the remaining parts of the name to handle "John Smith" vs "Smith John" as same.
        # This helps in grouping names that might be entered in different orders.
        return " ".join(sorted(name_parts))

    def suggest_duplicates(self):
        """
        Suggests potential duplicate contacts based on normalized names.

        This method groups contacts by a normalized version of their primary name.
        If a group contains more than one distinct contact (based on `contact_id`),
        it's considered a potential set of duplicates.

        Returns:
            list: A list of groups (lists) of contact dictionaries that are potential duplicates.
                  Example: `[[contact_A, contact_B], [contact_C, contact_D, contact_E]]`
        """
        if not self.contacts or len(self.contacts) < 2: # Need at least two contacts to find duplicates
            return []

        # Group contacts by their normalized primary name.
        # defaultdict(list) creates a list for any new key automatically.
        contacts_by_normalized_name = defaultdict(list)
        for contact_item in self.contacts:
            primary_name = contact_item.get('name')
            normalized_name_key = self._normalize_name_for_matching(primary_name)
            if normalized_name_key: # Only process if a valid normalized name is generated
                contacts_by_normalized_name[normalized_name_key].append(contact_item)

        suggested_duplicate_groups = []
        for normalized_name_key, group_of_contacts in contacts_by_normalized_name.items():
            # A group is a potential duplicate set if it contains more than one contact object.
            if len(group_of_contacts) > 1:
                # Ensure these are truly distinct contact entries (check contact_id uniqueness within the group).
                # This check is somewhat redundant if `add_contact` prevents exact duplicates based on ID,
                # but good as a safeguard or if contacts could be loaded from other sources.
                # The current `add_contact` creates new IDs for new name/email combos if email doesn't match an existing contact.
                # So, if they have the same normalized name but different contact_ids, they are candidates.
                unique_contact_ids_in_group = {c['contact_id'] for c in group_of_contacts}
                if len(unique_contact_ids_in_group) > 1:
                    # This group contains multiple distinct contacts with the same normalized name.
                    suggested_duplicate_groups.append(group_of_contacts)
                    if current_app:
                        current_app.logger.info(f"Potential duplicate group for name '{normalized_name_key}': "
                                                f"{[c['contact_id'] for c in group_of_contacts]}")


        return suggested_duplicate_groups


if __name__ == '__main__':
    # Test the ContactService
    print("Testing ContactService...")
    # Create a temporary contacts file for testing
    temp_contacts_file = os.path.join(DATA_DIR, 'test_contacts.json')
    if os.path.exists(temp_contacts_file):
        os.remove(temp_contacts_file)

    service = ContactService(contacts_file_path=temp_contacts_file)

    # Add some contacts
    c1, msg1 = service.add_contact("John Doe", "john.doe@example.com", "Met at conference")
    print(f"Add c1: {msg1}")
    c2, msg2 = service.add_contact("Jane Doe", "jane.doe@example.com", "Project Alpha lead")
    print(f"Add c2: {msg2}")
    c3, msg3 = service.add_contact("John Doe", "johndoe@work.com", "Work email for John") # Same name, diff email
    print(f"Add c3: {msg3}")
    c4, msg4 = service.add_contact("Jon Dough", "jon.dough@example.net", "Slightly different name") # Similar name
    print(f"Add c4: {msg4}")
    c5, msg5 = service.add_contact("John Doe", "john.doe@example.com", "Updated notes") # Update existing
    print(f"Add c5 (update c1): {msg5}")
    c6, msg6 = service.add_contact("Alice Wonderland", "alice@wonder.land")
    print(f"Add c6: {msg6}")
    c7, msg7 = service.add_contact("Doe John", "john.d@personal.co") # Name variation
    print(f"Add c7: {msg7}")


    print(f"\nTotal contacts: {len(service.contacts)}")
    # for contact in service.contacts:
    #     print(contact)

    # Find contact
    found_john = service.find_contact_by_email("john.doe@example.com")
    print(f"\nFound John Doe by email: {found_john['name'] if found_john else 'Not found'}")

    found_jane = service.find_contact_by_email("jane.doe@example.com")
    print(f"Found Jane Doe by email: {found_jane['name'] if found_jane else 'Not found'}")

    # Suggest duplicates
    duplicates = service.suggest_duplicates()
    print("\nPotential Duplicates:")
    if duplicates:
        for i, group in enumerate(duplicates):
            print(f"  Group {i+1}:")
            for contact in group:
                print(f"    - {contact['name']} ({', '.join(contact['email_addresses'])}) - ID: {contact['contact_id']}")
    else:
        print("  No obvious duplicates found with current basic logic.")

    # Clean up test file
    if os.path.exists(temp_contacts_file):
        os.remove(temp_contacts_file)
    print("\nContactService test finished.")
