import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useAuthStore } from './auth'; // Correct path to auth store

export const useEmailAccountsStore = defineStore('emailAccounts', () => {
    const accounts = ref([]);
    const error = ref(null);
    const loading = ref(false);
    const authStore = useAuthStore();

    async function fetchAccounts() {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated.';
            return;
        }
        loading.value = true;
        error.value = null;
        try {
            const response = await fetch('/api/v1/email-accounts/', {
                method: 'GET',
                headers: {
                    ...authStore.authHeader, // Spread the auth header
                    'Content-Type': 'application/json' // Though GET might not need Content-Type
                }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch accounts' }));
                throw new Error(errorData.detail || 'Failed to fetch accounts');
            }
            accounts.value = await response.json();
        } catch (err) {
            console.error('Fetch accounts error:', err);
            error.value = err.message;
            accounts.value = []; // Clear accounts on error
        } finally {
            loading.value = false;
        }
    }

    async function addAccount(newAccountData) {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated.';
            return;
        }
        loading.value = true;
        error.value = null;
        try {
            const response = await fetch('/api/v1/email-accounts/', {
                method: 'POST',
                headers: {
                    ...authStore.authHeader,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newAccountData)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to add account' }));
                throw new Error(errorData.detail || 'Failed to add account');
            }
            // const addedAccount = await response.json(); // The new account from server
            // accounts.value.push(addedAccount); // Optimistically add or refetch
            await fetchAccounts(); // Re-fetch all accounts to get the updated list
        } catch (err) {
            console.error('Add account error:', err);
            error.value = err.message;
            throw err; // Re-throw to be caught by component if needed
        } finally {
            loading.value = false;
        }
    }

    return { accounts, error, loading, fetchAccounts, addAccount };
});
