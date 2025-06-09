import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAuthStore } from './auth'; // Assuming auth.js is in the same directory

export const useThreadStore = defineStore('threads', () => {
    const threads = ref([]);
    const activeThreadId = ref(null);
    const activeThreadMessages = ref([]);

    const loadingThreads = ref(false);
    const loadingMessages = ref(false);
    const error = ref(null); // General error for the store

    const authStore = useAuthStore();

    async function fetchThreads(accountId = null) { // Accept accountId
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated to fetch threads.';
            threads.value = [];
            clearActiveThread(); // Also clear active messages
            return;
        }

        // If accountId is null, and we require an account to be selected,
        // then don't fetch. Or, fetch for "all accounts" if backend supports it.
        // For this implementation, we'll require an accountId to fetch threads.
        if (accountId === null) {
            threads.value = []; // Clear threads if no account is active
            clearActiveThread();
            // error.value = "No active account selected to fetch threads for."; // Optional message
            loadingThreads.value = false; // Not technically loading if we don't fetch
            return;
        }

        loadingThreads.value = true;
        error.value = null;
        // Clear previous thread data when fetching for a new account
        threads.value = [];
        clearActiveThread();

        try {
            const apiUrl = accountId ? `/api/v1/threads/?account_id=${accountId}` : '/api/v1/threads/';
            const response = await fetch(apiUrl, {
                method: 'GET',
                headers: { ...authStore.authHeader }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch threads' }));
                throw new Error(errorData.detail || 'Failed to fetch threads');
            }
            threads.value = await response.json();
        } catch (err) {
            console.error('Fetch threads error:', err);
            error.value = err.message;
            threads.value = []; // Clear on error
        } finally {
            loadingThreads.value = false;
        }
    }

    async function fetchMessagesForThread(threadId) {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated to fetch messages.';
            activeThreadMessages.value = [];
            return;
        }
        if (!threadId) {
            activeThreadId.value = null;
            activeThreadMessages.value = [];
            return;
        }

        loadingMessages.value = true;
        error.value = null; // Clear previous general errors
        try {
            const response = await fetch(`/api/v1/threads/${threadId}/messages`, {
                method: 'GET',
                headers: { ...authStore.authHeader }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch messages for thread' }));
                throw new Error(errorData.detail || `Failed to fetch messages for thread ${threadId}`);
            }
            activeThreadId.value = threadId; // Set active thread ID only on successful fetch
            activeThreadMessages.value = await response.json();
        } catch (err) {
            console.error(`Fetch messages for thread ${threadId} error:`, err);
            error.value = err.message; // Display this error prominently in UI related to message panel
            activeThreadMessages.value = []; // Clear messages on error for this thread
            // Do not nullify activeThreadId here, so UI can know which thread failed to load
        } finally {
            loadingMessages.value = false;
        }
    }

    // Getters
    const getThreadById = computed(() => (id) => {
        return threads.value.find(thread => thread.id === id);
    });

    const getActiveThreadDetails = computed(() => {
        if (activeThreadId.value) {
            return threads.value.find(thread => thread.id === activeThreadId.value);
        }
        return null;
    });

    // Action to clear active thread (e.g., when navigating away or deselecting)
    function clearActiveThread() {
        activeThreadId.value = null;
        activeThreadMessages.value = [];
    }

    return {
        threads,
        activeThreadId,
        activeThreadMessages,
        loadingThreads,
        loadingMessages,
        error,
        fetchThreads,
        fetchMessagesForThread,
        getThreadById,
        getActiveThreadDetails,
        clearActiveThread
    };
});
