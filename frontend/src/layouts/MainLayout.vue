<template>
  <el-container class="main-layout">
    <el-aside width="200px" class="aside">
      <div class="logo">
        <h3>RADIUS</h3>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/operators">
          <el-icon><UserFilled /></el-icon>
          <span>操作员管理</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/apartments">
          <el-icon><OfficeBuilding /></el-icon>
          <span>公寓管理</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/nas">
          <el-icon><Connection /></el-icon>
          <span>NAS设备管理</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/radius">
          <el-icon><Setting /></el-icon>
          <span>RADIUS日志</span>
        </el-menu-item>
        <el-menu-item index="/plans">
          <el-icon><Tickets /></el-icon>
          <span>套餐管理</span>
        </el-menu-item>
        <el-menu-item index="/network_users">
          <el-icon><User /></el-icon>
          <span>网络用户管理</span>
        </el-menu-item>
        <el-menu-item index="/online_users">
          <el-icon><Monitor /></el-icon>
          <span>在线用户</span>
        </el-menu-item>
        <el-menu-item index="/billing">
          <el-icon><Wallet /></el-icon>
          <span>生成帐单</span>
        </el-menu-item>
        <el-menu-item index="/warnings">
          <el-icon><Warning /></el-icon>
          <span>预警分析</span>
        </el-menu-item>
        <el-menu-item index="/fault">
          <el-icon><WarnTriangleFilled /></el-icon>
          <span>故障处理</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/audit-logs">
          <el-icon><Document /></el-icon>
          <span>操作日志</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-content">
          <div class="left-info">
            <span class="page-title">{{ pageTitle }}</span>
            <el-tag v-if="apartmentName" type="success" size="small" style="margin-left: 10px">
              {{ apartmentName }}
            </el-tag>
          </div>
          <div class="user-info">
            <el-dropdown @command="handleCommand">
              <span class="user-dropdown">
                <el-icon><User /></el-icon>
                {{ userName }}
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="switch">切换公寓</el-dropdown-item>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  HomeFilled,
  UserFilled,
  OfficeBuilding,
  Connection,
  Setting,
  Tickets,
  User,
  Monitor,
  Wallet,
  Warning,
  Document,
  WarnTriangleFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const userName = computed(() => localStorage.getItem('name') || localStorage.getItem('username') || '')
const apartmentName = computed(() => localStorage.getItem('apartment_name') || '')
const apartments = computed(() => {
  const data = localStorage.getItem('apartments')
  return data ? JSON.parse(data) : []
})

// 判断是否为管理员
const isAdmin = computed(() => {
  const role = localStorage.getItem('role')
  return role === 'admin'
})

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  return route.meta.title || '首页'
})

const handleCommand = (command) => {
  if (command === 'logout') {
    localStorage.clear()
    router.push('/login')
  } else if (command === 'switch') {
    if (apartments.value.length > 1) {
      ElMessage.info('暂不支持切换公寓')
    } else {
      ElMessage.info('当前只管理一个公寓')
    }
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.aside {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #4a5564;
}

.logo h3 {
  margin: 0;
  font-size: 18px;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-info {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.main {
  background-color: #f0f2f5;
  padding: 0;
}
</style>
