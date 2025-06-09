import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useAuthStore } from './auth';

export const useComplaintsStore = defineStore('complaints', () => {
    const complaints = ref([]);
    const isLoading = ref(false);
    const error = ref(null);
    const authStore = useAuthStore();

    async function fetchComplaints() {
        if (!authStore.isAuthenticated) {
            error.value = 'User not authenticated.';
            complaints.value = [];
            return;
        }
        isLoading.value = true;
        error.value = null;
        try {
            // The backend router for complaints is at /api/v1/complaints-suggestions
            const response = await fetch('/api/v1/complaints-suggestions/', {
                method: 'GET',
                headers: { ...authStore.authHeader }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch complaints data' }));
                throw new Error(errorData.detail || 'Failed to fetch complaints data');
            }
            complaints.value = await response.json();
        } catch (err) {
            console.error('Fetch complaints error:', err);
            error.value = err.message;
            complaints.value = []; // Clear on error
        } finally {
            isLoading.value = false;
        }
    }

    return {
        complaints,
        isLoading,
        error,
        fetchComplaints
    };
});
