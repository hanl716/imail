import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useAuthStore } from './auth';

export const useComposeStore = defineStore('compose', () => {
    const loading = ref(false);
    const error = ref(null);
    const successMessage = ref(null);

    const authStore = useAuthStore();

    async function sendEmail(composeData) {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated.';
            throw new Error('User not authenticated.');
        }

        loading.value = true;
        error.value = null;
        successMessage.value = null;

        try {
            const response = await fetch('/api/v1/actions/send-email', {
                method: 'POST',
                headers: {
                    ...authStore.authHeader,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(composeData)
            });

            const responseData = await response.json(); // Try to parse JSON regardless of response.ok for error details

            if (!response.ok) {
                throw new Error(responseData.detail || `Failed to send email (status ${response.status})`);
            }

            successMessage.value = responseData.message || 'Email sent successfully!'; // Assuming backend sends a message
            return responseData; // Return data for potential further use
        } catch (err) {
            console.error('Send email error:', err);
            error.value = err.message;
            throw err; // Re-throw to be caught by component
        } finally {
            loading.value = false;
        }
    }

    function clearStatus() {
        error.value = null;
        successMessage.value = null;
    }

    return {
        loading,
        error,
        successMessage,
        sendEmail,
        clearStatus
    };
});
