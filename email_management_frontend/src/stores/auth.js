import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import router from '@/router'; // Assuming router is in src/router

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || null);
    const user = ref(JSON.parse(localStorage.getItem('user')) || null); // Basic user info

    const isAuthenticated = computed(() => !!token.value);

    const authHeader = computed(() => {
        if (token.value) {
            return { 'Authorization': `Bearer ${token.value}` };
        }
        return {};
    });

    async function login(email, password) {
        try {
            const response = await fetch('/api/v1/auth/token/', { // Adjust API endpoint as per backend
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ username: email, password: password })
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
                throw new Error(errorData.detail || 'Login failed');
            }
            const data = await response.json();
            token.value = data.access_token;
            localStorage.setItem('token', data.access_token);

            // Fetch basic user info (optional, or get from token if included)
            // For now, just store email or a placeholder. A real app might decode the token
            // or make another request to /users/me with the token.
            user.value = { email: email }; // Placeholder, adjust as needed
            localStorage.setItem('user', JSON.stringify(user.value));

            router.push('/'); // Redirect to home or dashboard
        } catch (error) {
            console.error('Login error:', error);
            throw error; // Re-throw to be caught by component
        }
    }

    async function register(email, password) {
        try {
            const response = await fetch('/api/v1/auth/users/', { // Adjust API endpoint
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
                throw new Error(errorData.detail || 'Registration failed');
            }
            // Optionally login user directly after registration or redirect to login
            alert('Registration successful! Please login.'); // Or handle differently
            router.push('/login');
        } catch (error) {
            console.error('Registration error:', error);
            throw error; // Re-throw
        }
    }

    function logout() {
        token.value = null;
        user.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/login');
    }

    return { token, user, isAuthenticated, login, register, logout, authHeader };
});
