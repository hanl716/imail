<template>
  <div id="app-container"> <!-- Changed id to avoid conflict if #app is used by Vue internally for mounting -->
    <nav>
      <router-link to="/">Home</router-link> |
      <router-link to="/about">About</router-link>
      <span v-if="!authStore.isAuthenticated">
        | <router-link to="/login">Login</router-link>
        | <router-link to="/register">Register</router-link>
      </span>
      <span v-if="authStore.isAuthenticated">
        | <router-link to="/email-accounts">Manage Accounts</router-link>
        | <router-link to="/complaints-suggestions">Complaints/Suggestions</router-link> <!-- New Link -->
        <span v-if="authStore.user"> | Welcome, {{ authStore.user.email }}</span>
        | <button @click="handleLogout">Logout</button>
      </span>
    </nav>
    <div class="router-view-wrapper"> <!-- Ensure this wrapper is present -->
      <router-view/>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import router from '@/router'; // Import router for programmatic navigation if needed

const authStore = useAuthStore();

const handleLogout = () => {
  authStore.logout();
  // router.push('/login'); // This is already handled by the store's logout method
};
</script>

<style>
/* Global styles for full height app layout */
html, body {
  height: 100%;
  margin: 0;
  overflow: hidden; /* Prevents body scrollbars when IMView handles its own scroll */
}

#app-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /* text-align: center; Removed for IM layout */
  color: #2c3e50;
}

nav {
  padding: 15px 30px; /* Adjusted padding */
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  height: 60px; /* Fixed height for nav */
  box-sizing: border-box;
  text-align: center; /* Keep nav items centered */
  flex-shrink: 0; /* Prevent nav from shrinking */
}

/* Router view should take remaining height */
.router-view-wrapper {
  flex-grow: 1;
  overflow: hidden; /* IMView will handle its internal scrolling */
}

nav a {
  font-weight: bold;
  color: #2c3e50;
  margin: 0 10px; /* Added margin for links */
}

nav a.router-link-exact-active {
  color: #42b983;
}

button {
  margin-left: 8px;
  padding: 5px 10px;
  cursor: pointer;
  border: 1px solid #ccc;
  background-color: #fff;
  border-radius: 4px;
}
button:hover {
  background-color: #f0f0f0;
}
</style>
