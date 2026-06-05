<template>
  <div class="online-users-container">
    <el-card class="statistics-card">
      <div class="statistics">
        <div class="stat-item">
          <el-icon class="stat-icon" color="#409EFF"><User /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_online || 0 }}</div>
            <div class="stat-label">当前在线</div>
          </div>
        </div>
        <div class="stat-item">
          <el-icon class="stat-icon" color="#67C23A"><OfficeBuilding /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_apartments || 0 }}</div>
            <div class="stat-label">活跃公寓</div>
          </div>
        </div>
        <div class="stat-item">
          <el-icon class="stat-icon" color="#E6A23C"><Top /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_traffic?.input_formatted || '0 B' }}</div>
            <div class="stat-label">总上行流量</div>
          </div>
        </div>
        <div class="stat-item">
          <el-icon class="stat-icon" color="#F56C6C"><Bottom /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.total_traffic?.output_formatted || '0 B' }}</div>
            <div class="stat-label">总下行流量</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>在线用户列表</span>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="用户名">
          <el-input
            v-model="searchForm.username"
            placeholder="搜索用户名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="公寓">
          <el-select
            v-model="searchForm.apartment_id"
            placeholder="选择公寓"
            clearable
            @change="handleSearch"
          >
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="120" fixed />
        <el-table-column prop="apartment_name" label="公寓" width="150" />
        <el-table-column prop="room" label="房间号" width="100" />
        <el-table-column prop="nas_name" label="NAS设备" width="150" />
        <el-table-column prop="framed_ip" label="分配IP" width="130" />
        <el-table-column prop="calling_station_id" label="MAC地址" width="150" />
        <el-table-column prop="start_time" label="上线时间" width="160" />
        <el-table-column prop="online_duration" label="在线时长" width="120" />
        <el-table-column prop="session_time_formatted" label="会话时长" width="120">
          <template #default="{ row }">
            {{ row.session_time_formatted || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="流量" width="200">
          <template #default="{ row }">
            <div class="traffic-info">
              <span class="upload">
                <el-icon><Top /></el-icon>
                {{ row.input_formatted }}
              </span>
              <span class="download">
                <el-icon><Bottom /></el-icon>
                {{ row.output_formatted }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleKickUser(row)"
            >
              踢出
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailDialogVisible"
      title="用户详情"
      width="700px"
    >
      <div v-if="currentUser" class="user-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">
            {{ currentUser.username }}
          </el-descriptions-item>
          <el-descriptions-item label="公寓">
            {{ currentUser.apartment_name }}
          </el-descriptions-item>
          <el-descriptions-item label="房间号">
            {{ currentUser.room }}
          </el-descriptions-item>
          <el-descriptions-item label="NAS设备">
            {{ currentUser.nas_name }}
          </el-descriptions-item>
          <el-descriptions-item label="NAS IP">
            {{ currentUser.nas_ip }}
          </el-descriptions-item>
          <el-descriptions-item label="NAS标识符">
            {{ currentUser.nas_identifier || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="分配IP">
            {{ currentUser.framed_ip }}
          </el-descriptions-item>
          <el-descriptions-item label="MAC地址">
            {{ currentUser.calling_station_id }}
          </el-descriptions-item>
          <el-descriptions-item label="会话ID" :span="2">
            {{ currentUser.session_id }}
          </el-descriptions-item>
          <el-descriptions-item label="上线时间">
            {{ currentUser.start_time }}
          </el-descriptions-item>
          <el-descriptions-item label="在线时长">
            {{ currentUser.online_duration }}
          </el-descriptions-item>
          <el-descriptions-item label="上行流量">
            <span style="color: #E6A23C">{{ currentUser.input_formatted }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="下行流量">
            <span style="color: #F56C6C">{{ currentUser.output_formatted }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="总会话时长">
            {{ currentUser.session_time_formatted }}
          </el-descriptions-item>
          <el-descriptions-item label="用户姓名" v-if="currentUser.user_info">
            {{ currentUser.user_info.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户电话" v-if="currentUser.user_info">
            {{ currentUser.user_info.phone || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOnlineUsers, getOnlineStatistics, getUserDetail, kickUser } from './api'
import { getAllApartments } from '@/modules/apartment/api'

const loading = ref(false)
const tableData = ref([])
const statistics = ref({})
const apartments = ref([])

const searchForm = ref({
  username: '',
  apartment_id: null
})

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

const detailDialogVisible = ref(false)
const currentUser = ref(null)

let refreshTimer = null

const loadStatistics = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await getOnlineStatistics({ operator_id: user.id })
    if (res.code === 200) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadApartments = async () => {
  try {
    // 如果是管理员，加载所有公寓；否则只加载自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'

    if (isAdmin) {
      const res = await getAllApartments()
      if (res.code === 200) {
        apartments.value = res.data.items || []
      }
    } else {
      // 非管理员只能看到自己关联的公寓
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await getOnlineUsers({
      ...searchForm.value,
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      operator_id: user.id
    })
    if (res.code === 200) {
      tableData.value = res.data.items || []
      pagination.value.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载在线用户失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.value = {
    username: '',
    apartment_id: null
  }
  pagination.value.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadData()
}

const handleSizeChange = (size) => {
  pagination.value.page_size = size
  pagination.value.page = 1
  loadData()
}

const handleViewDetail = async (row) => {
  try {
    const res = await getUserDetail(row.session_id)
    if (res.code === 200) {
      currentUser.value = res.data
      detailDialogVisible.value = true
    } else {
      ElMessage.error(res.message || '获取详情失败')
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

const handleKickUser = (row) => {
  ElMessageBox.confirm(
    `确定要踢出用户 "${row.username}" 吗？`,
    '踢出用户',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const res = await kickUser({
        session_id: row.session_id,
        reason: 'Admin kick'
      })
      if (res.code === 200) {
        ElMessage.success(res.data.message || '踢出请求已发送')
        setTimeout(() => {
          loadData()
          loadStatistics()
        }, 2000)
      } else {
        ElMessage.error(res.message || '踢出失败')
      }
    } catch (error) {
      console.error('踢出用户失败:', error)
      ElMessage.error('踢出用户失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadApartments().then(() => {
    // 如果是非管理员，自动选择自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (!isAdmin && apartments.value.length > 0) {
      searchForm.value.apartment_id = apartments.value[0].id
    }
  })
  loadData()
  loadStatistics()

  // 自动刷新数据（每5秒刷新一次）
  refreshTimer = setInterval(() => {
    loadData()
    loadStatistics()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.online-users-container {
  padding: 20px;
}

.statistics-card {
  margin-bottom: 20px;
}

.statistics {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 10px 20px;
}

.stat-icon {
  font-size: 40px;
  margin-right: 15px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.traffic-info {
  display: flex;
  flex-direction: column;
  font-size: 13px;
}

.traffic-info .upload {
  color: #E6A23C;
  margin-bottom: 4px;
}

.traffic-info .download {
  color: #F56C6C;
}

.user-detail {
  padding: 10px;
}
</style>
