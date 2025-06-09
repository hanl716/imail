import { createRouter, createWebHistory } from 'vue-router';
import IMView from '../views/IMView.vue'; // Changed from HomeView to IMView
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import EmailAccountsView from '../views/EmailAccountsView.vue';
import { useAuthStore } from '@/stores/auth';

const routes = [
  {
    path: '/',
    name: 'home', // Or 'inbox' if preferred, but 'home' is fine for default
    component: IMView, // Changed from HomeView
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView
  },
  {
    path: '/about',
    name: 'about',
    component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
    // meta: { requiresAuth: true } // Example if About page needs auth
  },
  {
    path: '/email-accounts',
    name: 'email-accounts',
    component: EmailAccountsView,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

router.beforeEach((to, from, next) => {
  // Ensure Pinia store is initialized before using it,
  // especially if this file is imported before main.js fully sets up Pinia.
  // However, typically by the time beforeEach runs, Pinia is available.
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' });
  } else if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
    // Redirect logged-in users from login/register to home
    next({ name: 'home' });
  }
  else {
    next();
  }
});

export default router;
