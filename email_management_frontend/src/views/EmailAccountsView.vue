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
      <p v-if="emailAccountsStore.error && !addAccountError" class="error">{{ emailAccountsStore.error }}</p> <!-- Show general store error if not specific to addAccount -->
      <ul v-if="emailAccountsStore.accounts.length">
        <li v-for="account in emailAccountsStore.accounts" :key="account.id">
          {{ account.email_address }}
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
  emailAccountsStore.fetchAccounts();
  // }
});

const handleAddAccount = async () => {
  addAccountError.value = null; // Clear previous add error
  if (!newEmailAddress.value.trim()) {
    addAccountError.value = 'Email address cannot be empty.';
    return;
  }
  try {
    await emailAccountsStore.addAccount({ email_address: newEmailAddress.value });
    newEmailAddress.value = ''; // Clear input on success
  } catch (err) {
    addAccountError.value = err.message || 'Failed to link account.';
    // The store itself also sets its own error, which could be displayed globally
  }
};
</script>

<style scoped>
.email-accounts-view {
  max-width: 600px;
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
  padding: 8px;
  margin-bottom: 5px;
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 3px;
}
</style>
