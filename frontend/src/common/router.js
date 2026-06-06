import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/home',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('../views/Home.vue'),
        meta: { requiresAuth: true, title: '首页' }
      },
      {
        path: 'operators',
        name: 'Operators',
        component: () => import('../modules/operator/List.vue'),
        meta: { requiresAuth: true, title: '操作员管理' }
      },
      {
        path: 'apartments',
        name: 'Apartments',
        component: () => import('../modules/apartment/List.vue'),
        meta: { requiresAuth: true, title: '公寓管理' }
      },
      {
        path: 'nas',
        name: 'Nas',
        component: () => import('../modules/nas/List.vue'),
        meta: { requiresAuth: true, title: 'NAS设备管理' }
      },
      {
        path: 'radius',
        name: 'Radius',
        component: () => import('../modules/radius/List.vue'),
        meta: { requiresAuth: true, title: 'RADIUS服务器配置' }
      },
      {
        path: 'radius/logs',
        name: 'RadiusLogs',
        component: () => import('../modules/radius/RadiusLogs.vue'),
        meta: { requiresAuth: true, title: 'RADIUS事件日志' }
      },
      {
        path: 'plans',
        name: 'Plans',
        component: () => import('../modules/plan/List.vue'),
        meta: { requiresAuth: true, title: '套餐管理' }
      },
      {
        path: 'network_users',
        name: 'NetworkUsers',
        component: () => import('../modules/network_user/views/List.vue'),
        meta: { requiresAuth: true, title: '网络用户管理' }
      },
      {
        path: 'online_users',
        name: 'OnlineUsers',
        component: () => import('../modules/online_user/List.vue'),
        meta: { requiresAuth: true, title: '在线用户' }
      },
      {
        path: 'billing',
        name: 'GenerateBill',
        component: () => import('../modules/billing/views/GenerateBill.vue'),
        meta: { requiresAuth: true, title: '生成帐单' }
      },
      {
        path: 'warnings',
        name: 'Warnings',
        component: () => import('../modules/warning/List.vue'),
        meta: { requiresAuth: true, title: '预警管理' }
      },
      {
        path: 'audit-logs',
        name: 'AuditLogs',
        component: () => import('../modules/audit_log/List.vue'),
        meta: { requiresAuth: true, title: '操作日志' }
      },
      {
        path: 'fault',
        name: 'Fault',
        component: () => import('../modules/fault/List.vue'),
        meta: { requiresAuth: true, title: '故障处理' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user')

  if (to.meta.requiresAuth !== false && !user) {
    next('/login')
  } else if (to.path === '/login' && user) {
    next('/')
  } else {
    next()
  }
})

export default router
