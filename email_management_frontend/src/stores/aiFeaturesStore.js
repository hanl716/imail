import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useAuthStore } from './auth'; // For auth headers

export const useAiFeaturesStore = defineStore('aiFeatures', () => {
    const suggestions = ref([]);
    const isLoadingSuggestions = ref(false);
    const suggestionError = ref(null);
    const authStore = useAuthStore();

    async function fetchReplySuggestions(messageId) {
        if (!messageId) {
            suggestionError.value = "Message ID is required to fetch suggestions.";
            return;
        }
        if (!authStore.isAuthenticated) {
            suggestionError.value = 'User not authenticated.';
            return;
        }

        isLoadingSuggestions.value = true;
        suggestionError.value = null;
        suggestions.value = []; // Clear previous suggestions

        try {
            const response = await fetch(`/api/v1/ai/suggest-reply/${messageId}`, {
                method: 'POST', // As defined in backend
                headers: {
                    ...authStore.authHeader,
                    'Content-Type': 'application/json' // Though body is empty, POST might expect it
                },
                // body: JSON.stringify({}) // Empty body for POST if required by server/FastAPI
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ detail: 'Failed to fetch suggestions.' }));
                throw new Error(errData.detail || `HTTP error ${response.status}`);
            }
            const data = await response.json();
            suggestions.value = data.suggestions || [];
            if (suggestions.value.length === 0) {
                // If API returns success but no suggestions, treat as "no suggestions found" rather than error
                // suggestionError.value = "No suggestions available for this message.";
            }
        } catch (error) {
            console.error('Error fetching reply suggestions:', error);
            suggestionError.value = error.message;
            suggestions.value = []; // Ensure suggestions are cleared on error
        } finally {
            isLoadingSuggestions.value = false;
        }
    }

    function clearSuggestions() {
        suggestions.value = [];
        suggestionError.value = null;
        // isLoadingSuggestions.value = false; // Optionally reset loading state too
    }

    return {
        suggestions,
        isLoadingSuggestions,
        suggestionError,
        fetchReplySuggestions,
        clearSuggestions
    };
});
