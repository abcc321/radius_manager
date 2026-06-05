<template>
  <div class="radius-logs-container">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>RADIUS日志</span>
          <el-button @click="fetchAuthLogs" :loading="authLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-alert
        title="RADIUS事件日志"
        type="info"
        description="记录所有RADIUS认证和计费事件，便于排查问题和监控账号使用情况。"
        :closable="false"
        show-icon
        class="mb-3"
      />

      <el-tabs v-model="activeTab">
        <el-tab-pane label="认证日志" name="auth">
          <div class="stats-row">
            <el-statistic title="认证总数" :value="authStats.total">
              <template #suffix>
                <el-tag type="primary" size="small">次</el-tag>
              </template>
            </el-statistic>
            <el-statistic title="成功" :value="authStats.success_count">
              <template #suffix>
                <el-tag type="success" size="small">次</el-tag>
              </template>
            </el-statistic>
            <el-statistic title="失败" :value="authStats.reject_count">
              <template #suffix>
                <el-tag type="danger" size="small">次</el-tag>
              </template>
            </el-statistic>
          </div>

          <el-form :inline="true" class="log-filters mt-3">
            <el-form-item label="用户名">
              <el-input v-model="authFilters.username" placeholder="用户名" clearable @keyup.enter="fetchAuthLogs" />
            </el-form-item>
            <el-form-item label="NAS IP">
              <el-input v-model="authFilters.nas_ip" placeholder="NAS IP" clearable @keyup.enter="fetchAuthLogs" />
            </el-form-item>
            <el-form-item label="结果">
              <el-select v-model="authFilters.result" placeholder="全部" clearable>
                <el-option label="成功" value="success" />
                <el-option label="失败" value="rejected" />
              </el-select>
            </el-form-item>
            <el-form-item label="错误类型">
              <el-select v-model="authFilters.error_code" placeholder="全部" clearable>
                <el-option label="用户不存在" value="USER_NOT_FOUND" />
                <el-option label="公寓不匹配" value="APARTMENT_MISMATCH" />
                <el-option label="无CHAP数据" value="NO_CHAP_DATA" />
                <el-option label="无用户名" value="NO_USERNAME" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="fetchAuthLogs">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button @click="resetAuthFilters">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </el-form-item>
          </el-form>

          <el-table :data="authLogs" stripe v-loading="authLoading">
            <el-table-column prop="created_at" label="时间" width="160" sortable />
            <el-table-column prop="event_type" label="事件类型" width="130">
              <template #default="{ row }">
                <el-tag :type="getEventTypeColor(row.event_type)" size="small">
                  {{ row.event_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户名" width="120">
              <template #default="{ row }">
                <el-tag type="primary" size="small">{{ row.username || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="nas_ip" label="NAS IP" width="130" />
            <el-table-column prop="nas_name" label="NAS名称" width="120">
              <template #default="{ row }">
                {{ row.nas_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="result" label="结果" width="80">
              <template #default="{ row }">
                <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.result === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_code" label="错误代码" width="150">
              <template #default="{ row }">
                <span v-if="row.error_code" style="color: #f56c6c; font-size: 12px;">
                  {{ row.error_code }}
                </span>
                <span v-else style="color: #67c23a;">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
            <el-table-column prop="response_time" label="响应时间" width="100">
              <template #default="{ row }">
                {{ row.response_time ? row.response_time + 'ms' : '-' }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="authTotal > 0"
            class="mt-3"
            v-model:current-page="authFilters.page"
            v-model:page-size="authFilters.page_size"
            :total="authTotal"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="fetchAuthLogs"
            @current-change="fetchAuthLogs"
          />

          <el-empty v-if="!authLoading && authLogs.length === 0" description="暂无认证日志" />
        </el-tab-pane>

        <el-tab-pane label="用户行为" name="acct">
          <div class="stats-row">
            <el-statistic title="用户上线" :value="acctStats.start_count">
              <template #suffix>
                <el-tag type="success" size="small">次</el-tag>
              </template>
            </el-statistic>
            <el-statistic title="用户下线" :value="acctStats.user_offline_count">
              <template #suffix>
                <el-tag type="warning" size="small">次</el-tag>
              </template>
            </el-statistic>
          </div>

          <el-form :inline="true" class="log-filters mt-3">
            <el-form-item label="用户名">
              <el-input v-model="acctFilters.username" placeholder="用户名" clearable @keyup.enter="fetchAcctLogs" />
            </el-form-item>
            <el-form-item label="NAS IP">
              <el-input v-model="acctFilters.nas_ip" placeholder="NAS IP" clearable @keyup.enter="fetchAcctLogs" />
            </el-form-item>
            <el-form-item label="行为">
              <el-select v-model="acctFilters.behavior_type" placeholder="全部行为" clearable>
                <el-option label="全部行为" value="" />
                <el-option label="用户上线" value="user_online" />
                <el-option label="用户下线" value="user_offline" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="fetchAcctLogs">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
              <el-button @click="resetAcctFilters">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </el-form-item>
          </el-form>

          <el-table :data="acctLogs" stripe v-loading="acctLoading">
            <el-table-column prop="created_at" label="时间" width="160" sortable />
            <el-table-column label="行为" width="130">
              <template #default="{ row }">
                <el-tag :type="getBehaviorTypeColor(row)" size="small">
                  {{ getBehaviorTypeText(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户名" width="120">
              <template #default="{ row }">
                <el-tag type="primary" size="small">{{ row.username || '-' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="nas_ip" label="NAS IP" width="130" />
            <el-table-column prop="session_time" label="在线时长(秒)" width="120">
              <template #default="{ row }">
                {{ row.session_time || '-' }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="acctTotal > 0"
            class="mt-3"
            v-model:current-page="acctFilters.page"
            v-model:page-size="acctFilters.page_size"
            :total="acctTotal"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="fetchAcctLogs"
            @current-change="fetchAcctLogs"
          />

          <el-empty v-if="!acctLoading && acctLogs.length === 0" description="暂无计费日志" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import request from '@/common/request'

const activeTab = ref('auth')

const authLoading = ref(false)
const authLogs = ref([])
const authTotal = ref(0)
const authStats = reactive({
  total: 0,
  success_count: 0,
  reject_count: 0
})

const authFilters = reactive({
  username: '',
  nas_ip: '',
  result: '',
  error_code: '',
  page: 1,
  page_size: 20
})

const acctLoading = ref(false)
const acctLogs = ref([])
const acctTotal = ref(0)
const acctStats = reactive({
  total: 0,
  start_count: 0,
  stop_count: 0,
  total_upload: 0,
  total_download: 0
})

const acctFilters = reactive({
  username: '',
  nas_ip: '',
  behavior_type: '',
  page: 1,
  page_size: 20
})

const fetchAuthLogs = async () => {
  authLoading.value = true
  try {
    const params = { ...authFilters }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })

    const res = await request.get('/radius/logs/auth', { params })
    if (res.code === 200) {
      authLogs.value = res.data.logs || []
      authTotal.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取认证日志失败:', error)
    ElMessage.error('获取认证日志失败')
  } finally {
    authLoading.value = false
  }
}

const fetchAuthStats = async () => {
  try {
    const params = {}
    if (authFilters.username) params.username = authFilters.username
    if (authFilters.nas_ip) params.nas_ip = authFilters.nas_ip

    const res = await request.get('/radius/logs/auth/stats', { params })
    if (res.code === 200) {
      Object.assign(authStats, res.data)
    }
  } catch (error) {
    console.error('获取认证统计失败:', error)
  }
}

const resetAuthFilters = () => {
  authFilters.username = ''
  authFilters.nas_ip = ''
  authFilters.result = ''
  authFilters.error_code = ''
  authFilters.page = 1
  fetchAuthLogs()
  fetchAuthStats()
}

const fetchAcctLogs = async () => {
  acctLoading.value = true
  try {
    const params = { ...acctFilters }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })

    const res = await request.get('/radius/logs/acct', { params })
    if (res.code === 200) {
      acctLogs.value = res.data.logs || []
      acctTotal.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取计费日志失败:', error)
    ElMessage.error('获取计费日志失败')
  } finally {
    acctLoading.value = false
  }
}

const fetchAcctStats = async () => {
  try {
    const params = {}
    if (acctFilters.username) params.username = acctFilters.username
    if (acctFilters.nas_ip) params.nas_ip = acctFilters.nas_ip

    const res = await request.get('/radius/logs/acct/stats', { params })
    if (res.code === 200) {
      Object.assign(acctStats, res.data)
    }
  } catch (error) {
    console.error('获取计费统计失败:', error)
  }
}

const resetAcctFilters = () => {
  acctFilters.username = ''
  acctFilters.nas_ip = ''
  acctFilters.behavior_type = ''
  acctFilters.page = 1
  fetchAcctLogs()
  fetchAcctStats()
}

const getEventTypeColor = (type) => {
  if (type === 'Access-Accept') return 'success'
  if (type === 'Access-Reject') return 'danger'
  return 'info'
}

const getBehaviorTypeColor = (row) => {
  // Start报文 - 用户上线
  if (row.packet_type && row.packet_type.includes('Start')) {
    return 'success'
  }

  // Stop报文 - 用户下线
  if (row.packet_type && row.packet_type.includes('Stop')) {
    return 'warning'
  }

  return 'info'
}

const getBehaviorTypeText = (row) => {
  // Start报文 - 用户上线
  if (row.packet_type && row.packet_type.includes('Start')) {
    return '用户上线'
  }

  // Stop报文 - 用户下线
  if (row.packet_type && row.packet_type.includes('Stop')) {
    return '用户下线'
  }

  return '未知行为'
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2))
}

onMounted(() => {
  fetchAuthLogs()
  fetchAuthStats()
  fetchAcctLogs()
  fetchAcctStats()
})
</script>

<style scoped>
.radius-logs-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-row {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.log-filters {
  margin-bottom: 15px;
}

.mb-3 {
  margin-bottom: 15px;
}

.mt-3 {
  margin-top: 15px;
}

.mb-4 {
  margin-bottom: 20px;
}
</style>
