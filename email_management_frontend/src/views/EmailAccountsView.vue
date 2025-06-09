<template>
  <div class="email-accounts-view">
    <h2>Manage Email Accounts</h2>

    <div class="add-account-form">
      <h3>Link New Email Account</h3>
      <form @submit.prevent="handleAddAccount">
        <div>
          <label for="new-email">Email Address:</label>
          <input type="email" id="new-email" v-model="newEmailAddress" required />
        </div>
        <button type="submit" :disabled="emailAccountsStore.loading || !newEmailAddress.trim()">
          {{ emailAccountsStore.loading ? 'Linking...' : 'Link Account' }}
        </button>
        <p v-if="addAccountError" class="error">{{ addAccountError }}</p>
      </form>
    </div>

    <div class="accounts-list">
      <h3>Your Linked Accounts</h3>
      <p v-if="emailAccountsStore.loading && !emailAccountsStore.accounts.length">Loading accounts...</p>
      <p v-if="emailAccountsStore.error && !addAccountError && !emailAccountsStore.loading" class="error">{{ emailAccountsStore.error }}</p>
      <ul v-if="emailAccountsStore.accounts.length">
        <li v-for="account in emailAccountsStore.accounts" :key="account.id" :class="{ 'active-account': account.id === emailAccountsStore.activeAccountId }">
          <span>{{ account.email_address }}</span>
          <span v-if="account.id === emailAccountsStore.activeAccountId" class="active-badge">(Active)</span>
          <button
            v-else
            @click="handleSetActiveAccount(account.id)"
            class="set-active-button"
            :disabled="emailAccountsStore.loading">
            Set Active
          </button>
          <!-- Add more details or actions (e.g., delete) here later -->
        </li>
      </ul>
      <p v-if="!emailAccountsStore.loading && !emailAccountsStore.accounts.length && !emailAccountsStore.error">
        You have no email accounts linked yet.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useEmailAccountsStore } from '@/stores/emailAccounts';
// import { useAuthStore } from '@/stores/auth'; // Not directly needed here if authStore usage is encapsulated in emailAccountsStore

const emailAccountsStore = useEmailAccountsStore();
// const authStore = useAuthStore(); // For direct access if needed

const newEmailAddress = ref('');
const addAccountError = ref(null);


onMounted(() => {
  // Fetch accounts only if user is authenticated, though store should also guard this
  // if (authStore.isAuthenticated) {
  // Fetch accounts if not already loaded by the store itself
  if (emailAccountsStore.accounts.length === 0) {
    emailAccountsStore.fetchAccounts();
  }
});

const handleAddAccount = async () => {
  addAccountError.value = null;
  if (!newEmailAddress.value.trim()) {
    addAccountError.value = 'Email address cannot be empty.';
    return;
  }
  try {
    // The addAccount action in store now also sets the new account as active
    await emailAccountsStore.addAccount({
        email_address: newEmailAddress.value,
        // Prompt for other details if schema requires, or use placeholders
        email_user: newEmailAddress.value, // Assuming same as email for now
        imap_server: "placeholder.imap.com", // Placeholder until form is expanded
        imap_port: 993,
        smtp_server: "placeholder.smtp.com",
        smtp_port: 465,
        // password or token fields should be collected securely if needed at this stage
    });
    newEmailAddress.value = ''; // Clear input on success
  } catch (err) {
    addAccountError.value = err.message || 'Failed to link account.';
  }
};

const handleSetActiveAccount = (accountId) => {
  emailAccountsStore.setActiveAccountId(accountId);
  // Potentially add visual feedback or route change if needed,
  // but store change should trigger reactivity in IMView.
};
</script>

<style scoped>
.email-accounts-view {
  max-width: 700px; /* Slightly wider for buttons */
  margin: auto;
  padding: 20px;
}
.add-account-form, .accounts-list {
  margin-bottom: 30px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 5px;
}
.add-account-form div {
  margin-bottom: 10px;
}
.error {
  color: red;
  margin-top: 10px;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  padding: 10px 12px; /* Consistent padding */
  margin-bottom: 8px;
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 4px; /* Slightly more modern radius */
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.active-account {
  background-color: #e7f3ff; /* Light blue for active account */
  border-left: 3px solid #007bff;
}
.active-badge {
  font-weight: bold;
  color: #007bff;
  margin-left: 10px;
}
.set-active-button {
  padding: 5px 10px;
  font-size: 0.85em;
  background-color: #28a745; /* Green */
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}
.set-active-button:hover {
  background-color: #218838;
}
.set-active-button:disabled {
  background-color: #aaa;
}
</style>
