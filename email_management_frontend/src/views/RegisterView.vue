<template>
  <div class="register-view">
    <h2>Register</h2>
    <form @submit.prevent="handleRegister">
      <div>
        <label for="email">Email:</label>
        <input type="email" v-model="email" required />
      </div>
      <div>
        <label for="password">Password:</label>
        <input type="password" v-model="password" required />
      </div>
      <button type="submit" :disabled="loading">Register</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
    <p>Already have an account? <router-link to="/login">Login here</router-link></p>
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

const handleRegister = async () => {
  error.value = null;
  loading.value = true;
  try {
    await authStore.register(email.value, password.value);
  } catch (err) {
    error.value = err.message || 'Failed to register.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-view {
  max-width: 400px;
  margin: auto;
  padding: 20px;
}
.register-view div {
  margin-bottom: 10px;
}
.error {
  color: red;
  margin-top: 10px;
}
</style>
