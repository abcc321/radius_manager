<template>
  <el-container class="main-layout">
    <!-- 移动端汉堡菜单按钮 -->
    <div class="mobile-menu-btn hide-on-desktop" @click="drawerVisible = true">
      <el-icon :size="24"><Menu /></el-icon>
    </div>

    <!-- 移动端抽屉菜单 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="70%"
      :show-close="false"
      class="mobile-drawer"
    >
      <template #header>
        <div class="drawer-header">
          <h3>RADIUS</h3>
          <el-button :icon="Close" circle @click="drawerVisible = false" />
        </div>
      </template>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        @select="handleMenuSelect"
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
    </el-drawer>

    <!-- 桌面端侧边栏 -->
    <el-aside width="200px" class="aside hide-on-mobile">
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
                <span class="hide-on-mobile">{{ userName }}</span>
                <el-icon class="hide-on-mobile"><ArrowDown /></el-icon>
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
import { ref, computed } from 'vue'
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
  WarnTriangleFilled,
  Menu,
  Close,
  ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const drawerVisible = ref(false)

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

// 移动端菜单选择后关闭抽屉
const handleMenuSelect = () => {
  if (window.innerWidth < 768) {
    drawerVisible.value = false
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
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.main {
  background-color: #f0f2f5;
  padding: 0;
  overflow-y: auto;
}

/* 移动端样式 */
.mobile-menu-btn {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 1001;
  width: 44px;
  height: 44px;
  background-color: #304156;
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s, box-shadow 0.2s;
}

.mobile-menu-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.mobile-menu-btn:active {
  transform: scale(0.95);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0 10px;
}

.drawer-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
}

/* 响应式断点 */
@media (max-width: 767px) {
  .mobile-menu-btn {
    display: flex !important;
  }

  .header {
    padding-left: 60px;
    padding-right: 15px;
    height: 50px;
    line-height: 50px;
  }

  .header-content {
    padding-right: 0;
  }

  .page-title {
    font-size: 14px;
    font-weight: 600;
  }

  .user-dropdown {
    padding: 6px 10px;
  }

  .main {
    padding: 0;
  }

  .user-dropdown .el-icon {
    font-size: 16px;
  }
}

@media (min-width: 768px) {
  .mobile-menu-btn {
    display: none !important;
  }
}

/* 手机端触摸优化 */
@media (max-width: 767px) {
  .el-menu-item {
    height: 50px;
    line-height: 50px;
  }

  .el-menu-item__icon {
    font-size: 18px;
  }

  .el-dropdown-menu__item {
    padding: 10px 20px;
  }
}
</style>
