<template>
  <div class="radius-container">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>RADIUS服务器</span>
            <el-tag :type="serverStatus.is_running ? 'success' : 'danger'" size="large" class="ml-2">
              {{ serverStatus.is_running ? '运行中' : '已停止' }}
            </el-tag>
            <el-tag :type="isConnected ? 'success' : 'warning'" size="small" class="ml-2">
              {{ isConnected ? '✅ WebSocket已连接' : '⚠️ WebSocket未连接' }}
            </el-tag>
          </div>
          <div class="header-right">
            <el-button type="primary" @click="handleRefresh" :loading="refreshing">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="监听地址">
          {{ serverStatus.host || '0.0.0.0' }}
        </el-descriptions-item>
        <el-descriptions-item label="认证端口">
          <el-tag type="primary">{{ serverStatus.auth_port || 1812 }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="计费端口">
          <el-tag type="primary">{{ serverStatus.acct_port || 1813 }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="服务器时间">
          <el-tag type="success">{{ serverTime }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="服务器状态" :span="2">
          <el-tag :type="serverStatus.is_running ? 'success' : 'danger'" size="large">
            {{ serverStatus.is_running ? '✅ 运行中 - 正在监听 1812/1813 端口' : '❌ 已停止' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        v-if="serverStatus.is_running"
        title="RADIUS服务器正在运行"
        type="success"
        description="服务器已成功启动，正在监听来自NAS设备的RADIUS请求。所有通信内容将自动记录到数据库。"
        :closable="false"
        show-icon
        class="mt-3"
      />
    </el-card>

    <el-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>NAS与RADIUS服务器通信日志</span>
          <div>
            <el-button type="danger" @click="handleClearLogs" :disabled="logTotal === 0">
              <el-icon><Delete /></el-icon>
              清空日志
            </el-button>
            <el-button @click="handleExportLogs" :disabled="logTotal === 0">
              <el-icon><Download /></el-icon>
              导出日志
            </el-button>
          </div>
        </div>
      </template>

      <div class="stats-row">
        <el-statistic title="总通信次数" :value="stats.total" />
        <el-statistic title="成功次数" :value="stats.success_count">
          <template #suffix>
            <el-tag type="success" size="small">次</el-tag>
          </template>
        </el-statistic>
        <el-statistic title="失败次数" :value="stats.fail_count">
          <template #suffix>
            <el-tag type="danger" size="small">次</el-tag>
          </template>
        </el-statistic>
        <el-statistic title="请求次数" :value="stats.request_count">
          <template #suffix>
            <el-tag type="primary" size="small">次</el-tag>
          </template>
        </el-statistic>
        <el-statistic title="响应次数" :value="stats.response_count">
          <template #suffix>
            <el-tag type="warning" size="small">次</el-tag>
          </template>
        </el-statistic>
      </div>

      <el-form :inline="true" class="log-filters">
        <el-form-item label="NAS IP">
          <el-input v-model="logFilters.nas_ip" placeholder="NAS IP地址" clearable @keyup.enter="fetchLogs" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="logFilters.username" placeholder="用户名" clearable @keyup.enter="fetchLogs" />
        </el-form-item>
        <el-form-item label="行为">
          <el-select v-model="logFilters.packet_type" placeholder="全部" clearable>
            <el-option label="用户上线" value="user_online" />
            <el-option label="用户下线" value="user_offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logs" stripe v-loading="logsLoading" :default-sort="{ prop: 'created_at', order: 'descending' }">
        <el-table-column prop="created_at" label="时间" width="160" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="nas_ip" label="NAS IP" width="130" />
        <el-table-column prop="nas_name" label="公寓" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.nas_name || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.port }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="packet_type" label="行为" min-width="150">
          <template #default="{ row }">
            <el-tag :type="getBehaviorTagType(row.packet_type)" size="small">
              {{ getBehaviorText(row.packet_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.username || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_success" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_success ? 'success' : 'danger'" size="small">
              {{ row.is_success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="响应时间" width="100">
          <template #default="{ row }">
            {{ row.response_time ? row.response_time + 'ms' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="session_id" label="Session ID" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="font-family: monospace; font-size: 12px;">{{ row.session_id || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="handleDeleteLog(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="logTotal > 0"
        class="mt-4"
        v-model:current-page="logFilters.page"
        v-model:page-size="logFilters.page_size"
        :total="logTotal"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchLogs"
        @current-change="fetchLogs"
      />

      <el-empty v-if="!logsLoading && logs.length === 0" description="暂无通信日志" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/common/utils'
import * as api from './api.js'
import { useRadiusWebSocket } from '@/common/useWebSocket.js'

const refreshing = ref(false)
const logsLoading = ref(false)
const logs = ref([])
const logTotal = ref(0)

const { isConnected, serverStatus: wsServerStatus, onCommunicationEvent, connect, disconnect } = useRadiusWebSocket()

const serverStatus = reactive({
  is_running: false,
  host: '0.0.0.0',
  auth_port: 1812,
  acct_port: 1813
})

const serverTime = ref('')
let timeInterval = null

const updateServerTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  serverTime.value = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

watch(() => wsServerStatus.value, (newStatus) => {
  if (newStatus) {
    console.log('[List] WebSocket status received:', newStatus)
    serverStatus.is_running = newStatus.is_running
    serverStatus.host = newStatus.host
    serverStatus.auth_port = newStatus.auth_port
    serverStatus.acct_port = newStatus.acct_port
    console.log('[List] Server status updated:', serverStatus)
  } else {
    console.log('[List] WebSocket status is null')
  }
}, { immediate: true })

const stats = reactive({
  total: 0,
  success_count: 0,
  fail_count: 0,
  request_count: 0,
  response_count: 0
})

const logFilters = reactive({
  nas_ip: '',
  username: '',
  packet_type: '',
  page: 1,
  page_size: 20
})

let refreshTimer = null

const fetchServerStatus = async () => {
  try {
    const res = await api.getServerStatus()
    if (res.code === 200) {
      Object.assign(serverStatus, res.data)
    }
  } catch (error) {
    console.error('获取服务器状态失败', error)
  }
}

const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const params = { ...logFilters }
    if (!params.nas_ip) delete params.nas_ip
    if (!params.username) delete params.username
    if (!params.packet_type) delete params.packet_type

    const res = await api.getRadiusLogs(params)
    if (res.code === 200) {
      logs.value = res.data.logs || []
      logTotal.value = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('获取日志失败')
  } finally {
    logsLoading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await api.getLogsStats()
    if (res.code === 200) {
      Object.assign(stats, res.data)
    }
  } catch (error) {
    console.error('获取统计失败', error)
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    await fetchLogs()
    await fetchStats()
    ElMessage.success('状态刷新成功')
  } catch (error) {
    ElMessage.error('状态刷新失败')
  } finally {
    refreshing.value = false
  }
}

const resetFilters = () => {
  logFilters.nas_ip = ''
  logFilters.username = ''
  logFilters.packet_type = ''
  logFilters.page = 1
  fetchLogs()
}

const handleDeleteLog = (row) => {
  ElMessageBox.confirm('确定要删除这条日志吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await api.deleteLog(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        fetchLogs()
        fetchStats()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const handleClearLogs = () => {
  ElMessageBox.confirm('确定要清空所有通信日志吗？此操作不可恢复！', '警告', {
    confirmButtonText: '确定清空',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await api.clearLogs()
      if (res.code === 200) {
        ElMessage.success(res.message)
        fetchLogs()
        fetchStats()
      }
    } catch (error) {
      ElMessage.error('清空失败')
    }
  }).catch(() => {})
}

const handleExportLogs = async () => {
  try {
    const params = { ...logFilters }
    if (!params.nas_ip) delete params.nas_ip
    if (!params.username) delete params.username
    if (!params.packet_type) delete params.packet_type
    delete params.page
    delete params.page_size

    const res = await api.exportLogs(params)
    if (res.code === 200 && res.data.length > 0) {
      const csvContent = convertToCSV(res.data)
      downloadCSV(csvContent, 'radius_communication_logs.csv')
      ElMessage.success('导出成功')
    } else {
      ElMessage.warning('没有可导出的数据')
    }
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const convertToCSV = (data) => {
  const headers = Object.keys(data[0])
  const csvRows = [headers.join(',')]
  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header] || ''
      return `"${String(value).replace(/"/g, '""')}"`
    })
    csvRows.push(values.join(','))
  }
  return csvRows.join('\n')
}

const downloadCSV = (content, filename) => {
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
}

const getBehaviorText = (packetType) => {
  // 用户上线
  if (packetType === 'Access-Request') {
    return '用户上线'
  }

  // 用户下线
  if (packetType && packetType.includes('Accounting-Request (Stop)')) {
    return '用户下线'
  }

  return packetType || '未知'
}

const getBehaviorTagType = (packetType) => {
  // 用户上线 - 绿色
  if (packetType === 'Access-Request') {
    return 'success'
  }

  // 用户下线 - 橙色
  if (packetType && packetType.includes('Accounting-Request (Stop)')) {
    return 'warning'
  }

  return 'info'
}

let wsTimeoutTimer = null

onMounted(() => {
  connect()

  updateServerTime()
  timeInterval = setInterval(updateServerTime, 1000)

  wsTimeoutTimer = setTimeout(() => {
    if (!wsServerStatus.value) {
      console.log('[List] WebSocket timeout, fetching status via API')
      fetchServerStatus()
    }
  }, 5000)

  onCommunicationEvent.value = (eventType, data) => {
    console.log('[List] Communication event received:', eventType)
    if (eventType === 'log_created') {
      fetchLogs()
      fetchStats()
    }
  }

  fetchLogs()
  fetchStats()
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  if (wsTimeoutTimer) {
    clearTimeout(wsTimeoutTimer)
  }
  if (onCommunicationEvent) {
    onCommunicationEvent.value = null
  }
  disconnect()
})
</script>

<style scoped>
.radius-container {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 20px;
}

.mt-4 {
  margin-top: 20px;
}

.mt-3 {
  margin-top: 15px;
}

.ml-2 {
  margin-left: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 10px;
}

.logs-card {
  margin-top: 20px;
}

.stats-row {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.log-filters {
  margin-bottom: 20px;
}

.packet-desc {
  color: #606266;
  font-size: 13px;
}
</style>
