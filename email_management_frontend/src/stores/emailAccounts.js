import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useAuthStore } from './auth'; // Correct path to auth store

export const useEmailAccountsStore = defineStore('emailAccounts', () => {
    const accounts = ref([]);
    const error = ref(null);
    const loading = ref(false);
    const authStore = useAuthStore();

    // Active account state
    const activeAccountId = ref(localStorage.getItem('activeAccountId') ? parseInt(localStorage.getItem('activeAccountId')) : null);

    async function fetchAccounts() {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated.';
            accounts.value = []; // Clear accounts if not authenticated
            activeAccountId.value = null; // Clear active account
            localStorage.removeItem('activeAccountId');
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
            // If no active account is set, or if the stored active account is not in the fetched list,
            // set the first account as active by default, but don't trigger re-fetch from here.
            if (accounts.value.length > 0) {
                const currentActiveExists = accounts.value.some(acc => acc.id === activeAccountId.value);
                if (activeAccountId.value === null || !currentActiveExists) {
                    // Set activeAccountId without triggering a new round of fetches from other stores yet.
                    // IMView's onMounted or watch will handle initial thread fetch.
                    activeAccountId.value = accounts.value[0].id;
                    localStorage.setItem('activeAccountId', accounts.value[0].id.toString());
                }
            } else { // No accounts found
                activeAccountId.value = null;
                localStorage.removeItem('activeAccountId');
            }
        } catch (err) {
            console.error('Fetch accounts error:', err);
            error.value = err.message;
            accounts.value = [];
            activeAccountId.value = null;
            localStorage.removeItem('activeAccountId');
        } finally {
            loading.value = false;
        }
    }

    async function addAccount(newAccountData) {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated.';
            throw new Error('User not authenticated.'); // Re-throw for component
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
            const addedAccount = await response.json();
            await fetchAccounts(); // Re-fetch to update the main list and default active account logic
            setActiveAccountId(addedAccount.id); // Set new account as active, triggering other store updates
            return addedAccount;
        } catch (err) {
            console.error('Add account error:', err);
            error.value = err.message;
            throw err;
        } finally {
            loading.value = false;
        }
    }

    function setActiveAccountId(accountId, triggerRefetch = true) { // triggerRefetch is less used now, IMView watches activeAccountId
        const newActiveId = accountId !== null ? Number(accountId) : null;
        if (activeAccountId.value !== newActiveId) {
            activeAccountId.value = newActiveId;
            if (newActiveId !== null) {
                localStorage.setItem('activeAccountId', newActiveId.toString());
            } else {
                localStorage.removeItem('activeAccountId');
            }
            // No direct fetch call here; dependent components/stores should watch activeAccountId.
            console.log(`Active account ID in store set to: ${newActiveId}`);
        }
    }

    const getActiveAccountDetails = computed(() => {
        if (activeAccountId.value === null || !accounts.value || accounts.value.length === 0) {
            return null;
        }
        return accounts.value.find(acc => acc.id === activeAccountId.value) || null;
    });

    // Initial fetch if authenticated and accounts list is empty.
    // This helps ensure activeAccountId is set early if possible.
    if (authStore.isAuthenticated && (!accounts.value || accounts.value.length === 0)) {
        fetchAccounts();
    }

    return {
        accounts,
        error,
        loading,
        fetchAccounts,
        addAccount,
        activeAccountId,
        setActiveAccountId,
        getActiveAccountDetails
    };
});
