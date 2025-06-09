<template>
  <div v-if="isVisible" class="compose-modal-overlay" @click.self="$emit('close')">
    <div class="compose-modal-content">
      <button class="close-button" @click="$emit('close')">&times;</button>
      <h3>{{ initialData ? 'Reply/Forward Email' : 'Compose New Email' }}</h3>

      <form @submit.prevent="handleSendEmail">
        <div class="form-group">
          <label for="fromAccount">From:</label>
          <select id="fromAccount" v-model="formData.from_account_id" required :disabled="!availableAccounts.length">
            <option v-if="!availableAccounts.length" value="" disabled>No accounts available</option>
            <option v-for="account in availableAccounts" :key="account.id" :value="account.id">
              {{ account.email_address }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="toRecipients">To:</label>
          <input type="text" id="toRecipients" v-model="toRecipientsStr" required placeholder="Comma-separated emails"/>
        </div>
        <div class="form-group">
          <label for="ccRecipients">Cc:</label>
          <input type="text" id="ccRecipients" v-model="ccRecipientsStr" placeholder="Comma-separated emails"/>
        </div>
        <div class="form-group">
          <label for="bccRecipients">Bcc:</label>
          <input type="text" id="bccRecipients" v-model="bccRecipientsStr" placeholder="Comma-separated emails"/>
        </div>
        <div class="form-group">
          <label for="subject">Subject:</label>
          <input type="text" id="subject" v-model="formData.subject" required />
        </div>
        <div class="form-group">
          <label for="bodyText">Body:</label>
          <textarea id="bodyText" v-model="formData.body_text" rows="10" required></textarea>
        </div>

        <div v-if="composeStore.error" class="error-message">{{ composeStore.error }}</div>
        <div v-if="composeStore.successMessage" class="success-message">{{ composeStore.successMessage }}</div>

        <div class="form-actions">
          <button type="button" @click="$emit('close')" :disabled="composeStore.loading">Cancel</button>
          <button type="submit" :disabled="composeStore.loading || !availableAccounts.length">
            {{ composeStore.loading ? 'Sending...' : 'Send' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { useComposeStore } from '@/stores/composeStore';
import { useEmailAccountsStore } from '@/stores/emailAccounts'; // To get list of user's accounts

const props = defineProps({
  isVisible: Boolean,
  initialData: { // For reply/forward
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close']);

const composeStore = useComposeStore();
const emailAccountsStore = useEmailAccountsStore();

const availableAccounts = ref([]);

const formData = ref({
  from_account_id: null,
  to_recipients: [],
  cc_recipients: [],
  bcc_recipients: [],
  subject: '',
  body_text: '',
  // body_html: null, // Can add later if using a rich text editor
});

// For handling comma-separated string inputs for recipients
const toRecipientsStr = ref('');
const ccRecipientsStr = ref('');
const bccRecipientsStr = ref('');

function parseRecipients(str) {
  return str.split(',').map(email => email.trim()).filter(email => email);
}

watch(() => props.isVisible, (newVal) => {
  if (newVal) {
    composeStore.clearStatus(); // Clear previous send status
    // Reset form or populate with initialData
    formData.value = {
      from_account_id: availableAccounts.value.length > 0 ? availableAccounts.value[0].id : null, // Default to first account
      to_recipients: [],
      cc_recipients: [],
      bcc_recipients: [],
      subject: '',
      body_text: '',
    };
    toRecipientsStr.value = '';
    ccRecipientsStr.value = '';
    bccRecipientsStr.value = '';

    if (props.initialData) {
      toRecipientsStr.value = (props.initialData.to_recipients || []).join(', ');
      // ccRecipientsStr.value = (props.initialData.cc_recipients || []).join(', '); // If needed
      formData.value.subject = props.initialData.subject || '';
      formData.value.body_text = props.initialData.quoted_body || '';
      // Set from_account_id if relevant, or let user choose
    }
  }
});

onMounted(async () => {
    if (emailAccountsStore.accounts.length === 0) {
        await emailAccountsStore.fetchAccounts(); // Ensure accounts are loaded
    }
    availableAccounts.value = emailAccountsStore.accounts;
    if (availableAccounts.value.length > 0 && !formData.value.from_account_id) {
        formData.value.from_account_id = availableAccounts.value[0].id;
    }
});


const handleSendEmail = async () => {
  formData.value.to_recipients = parseRecipients(toRecipientsStr.value);
  formData.value.cc_recipients = parseRecipients(ccRecipientsStr.value);
  formData.value.bcc_recipients = parseRecipients(bccRecipientsStr.value);

  if (!formData.value.from_account_id) {
    composeStore.error = "Please select a 'From' account.";
    return;
  }
  if (formData.value.to_recipients.length === 0) {
    composeStore.error = "Please enter at least one 'To' recipient.";
    return;
  }

  try {
    await composeStore.sendEmail(formData.value);
    // Optionally close modal on success after a short delay
    setTimeout(() => {
      if (!composeStore.error) { // Only close if no error occurred during send
        emit('close');
      }
    }, 1500); // Delay to show success message
  } catch (err) {
    // Error is already set in the store, UI will display it
  }
};

</script>

<style scoped>
.compose-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.compose-modal-content {
  background-color: white;
  padding: 20px 30px;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}
.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
.form-group input[type="text"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group textarea {
  resize: vertical;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
.form-actions button {
  margin-left: 10px;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
}
.form-actions button[type="submit"] {
  background-color: #007bff;
  color: white;
  border: none;
}
.form-actions button[type="button"] {
  background-color: #f0f0f0;
  border: 1px solid #ccc;
}
.error-message {
  color: red;
  margin-bottom: 10px;
}
.success-message {
  color: green;
  margin-bottom: 10px;
}
</style>
