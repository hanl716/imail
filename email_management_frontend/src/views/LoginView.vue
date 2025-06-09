<template>
  <div class="login-view">
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <div>
        <label for="email">Email:</label>
        <input type="email" v-model="email" required />
      </div>
      <div>
        <label for="password">Password:</label>
        <input type="password" v-model="password" required />
      </div>
      <button type="submit" :disabled="loading">Login</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
    <p>No account? <router-link to="/register">Register here</router-link></p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';

const email = ref('');
const password = ref('');
const error = ref(null);
const loading = ref(false);
const authStore = useAuthStore();

const handleLogin = async () => {
  error.value = null;
  loading.value = true;
  try {
    await authStore.login(email.value, password.value);
  } catch (err) {
    error.value = err.message || 'Failed to login.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-view {
  max-width: 400px;
  margin: auto;
  padding: 20px;
}
.login-view div {
  margin-bottom: 10px;
}
.error {
  color: red;
  margin-top: 10px;
}
</style>
