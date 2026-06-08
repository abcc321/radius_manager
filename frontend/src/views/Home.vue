<template>
  <div class="home-container">
    <el-card class="welcome-card">
      <div class="welcome-content">
        <h1 class="welcome-title">欢迎使用RADIUS网络计费管理系统</h1>
        <p class="welcome-version">版本：1.1.0</p>
      </div>
    </el-card>

    <el-row :gutter="20" class="info-cards">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <div class="info-icon" style="background-color: #409eff;">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="info-text">
              <div class="info-number">{{ stats.totalUsers || 0 }}</div>
              <div class="info-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <div class="info-icon" style="background-color: #67c23a;">
              <el-icon :size="32"><UserFilled /></el-icon>
            </div>
            <div class="info-text">
              <div class="info-number">{{ stats.activeUsers || 0 }}</div>
              <div class="info-label">在线用户</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <div class="info-icon" style="background-color: #e6a23c;">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="info-text">
              <div class="info-number">{{ stats.expiringUsers || 0 }}</div>
              <div class="info-label">即将到期</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <div class="info-icon" style="background-color: #f56c6c;">
              <el-icon :size="32"><CircleClose /></el-icon>
            </div>
            <div class="info-text">
              <div class="info-number">{{ stats.expiredUsers || 0 }}</div>
              <div class="info-label">已过期</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <div class="info-icon" style="background-color: #909399;">
              <el-icon :size="32"><OfficeBuilding /></el-icon>
            </div>
            <div class="info-text">
              <div class="info-number">{{ stats.totalApartments || 0 }}</div>
              <div class="info-label">公寓数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <div class="info-icon" style="background-color: #909399;">
              <el-icon :size="32"><Connection /></el-icon>
            </div>
            <div class="info-text">
              <div class="info-number">{{ stats.totalNasDevices || 0 }}</div>
              <div class="info-label">NAS设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { User, UserFilled, Warning, CircleClose, OfficeBuilding, Connection } from '@element-plus/icons-vue'

const stats = ref({
  totalUsers: 0,
  activeUsers: 0,
  expiringUsers: 0,
  expiredUsers: 0,
  totalApartments: 0,
  totalNasDevices: 0
})

onMounted(() => {
  // 统计数据加载逻辑可以在这里实现
  // 目前是占位符，后续可以添加API调用
})
</script>

<style scoped>
.home-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 767px) {
  .home-container {
    padding: 15px;
  }
}

.welcome-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.welcome-card :deep(.el-card__body) {
  padding: 30px;
}

@media (max-width: 767px) {
  .welcome-card :deep(.el-card__body) {
    padding: 20px;
  }
}

.welcome-content {
  text-align: center;
}

.welcome-title {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: bold;
  color: white;
}

@media (max-width: 767px) {
  .welcome-title {
    font-size: 20px;
  }
}

.welcome-version {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.info-cards {
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.info-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.info-card-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

@media (max-width: 767px) {
  .info-card-content {
    gap: 15px;
  }
}

.info-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .info-icon {
    width: 50px;
    height: 50px;
    border-radius: 10px;
  }

  .info-icon .el-icon {
    font-size: 24px !important;
  }
}

.info-text {
  flex: 1;
}

.info-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

@media (max-width: 767px) {
  .info-number {
    font-size: 24px;
  }
}

.info-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

@media (max-width: 767px) {
  .info-label {
    font-size: 12px;
  }
}

/* 卡片样式优化 */
@media (max-width: 767px) {
  :deep(.el-card) {
    border-radius: 8px;
  }

  :deep(.el-card__body) {
    padding: 15px;
  }
}
</style>
