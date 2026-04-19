import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import DashboardLayout from './views/DashboardLayout.vue'
import UsersView from './views/UsersView.vue'
import ReportsView from './views/ReportsView.vue'
import RemindersView from './views/RemindersView.vue'
import AuditView from './views/AuditView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    {
      path: '/',
      component: DashboardLayout,
      children: [
        { path: '', redirect: '/reminders' },
        { path: 'users', component: UsersView },
        { path: 'reports', component: ReportsView },
        { path: 'reminders', component: RemindersView },
        { path: 'audit', component: AuditView },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('eh_admin_token')
  if (to.path !== '/login' && !token) {
    next('/login')
    return
  }
  if (to.path === '/login' && token) {
    next('/reminders')
    return
  }
  next()
})

export default router
