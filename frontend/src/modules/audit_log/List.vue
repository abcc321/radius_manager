<template>
  <div class="audit-log-container">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span class="title">操作日志</span>
          <el-tag type="info" size="small">
            共 {{ statistics.total || 0 }} 条记录
          </el-tag>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" style="margin-bottom: 20px">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.total || 0 }}</div>
              <div class="stat-label">总操作数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.by_action?.CREATE || 0 }}</div>
              <div class="stat-label">创建操作</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.by_action?.UPDATE || 0 }}</div>
              <div class="stat-label">更新操作</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.by_action?.DELETE || 0 }}</div>
              <div class="stat-label">删除操作</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 搜索表单 -->
      <el-form :inline="true" class="search-form">
        <el-form-item label="模块">
          <el-select v-model="searchForm.module" placeholder="全部模块" clearable style="width: 150px">
            <el-option
              v-for="mod in modules"
              :key="mod"
              :label="mod"
              :value="mod"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="searchForm.action" placeholder="全部类型" clearable style="width: 120px">
            <el-option label="创建" value="CREATE" />
            <el-option label="更新" value="UPDATE" />
            <el-option label="删除" value="DELETE" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作员">
          <el-input v-model="searchForm.operator_name" placeholder="操作员名称" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="目标名称/描述" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 日志表格 -->
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            <el-tag type="info" size="small">
              {{ formatTime(row.created_at) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.module }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作员" width="120" align="center" />
        <el-table-column prop="target_name" label="操作对象" min-width="200">
          <template #default="{ row }">
            <div>
              <strong>{{ row.target_name || '未知' }}</strong>
              <div style="color: #909399; font-size: 12px;">
                {{ row.description }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="130" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.ip_address || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="pagination.total > 0"
        style="margin-top: 20px; text-align: right"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="操作详情"
      width="800px"
      top="5vh"
    >
      <div v-if="currentLog" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="操作时间" :span="2">
            <el-tag type="info">{{ currentLog.created_at }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作模块">
            <el-tag type="primary">{{ currentLog.module }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getActionType(currentLog.action)">
              {{ getActionText(currentLog.action) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="操作员">
            {{ currentLog.operator_name || '系统' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作员ID">
            {{ currentLog.operator_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作对象" :span="2">
            {{ currentLog.target_name }}
          </el-descriptions-item>
          <el-descriptions-item label="操作描述" :span="2">
            {{ currentLog.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ currentLog.ip_address || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentLog.status === 'success' ? 'success' : 'danger'">
              {{ currentLog.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="currentLog.error_message" label="错误信息" :span="2">
            <el-alert type="error" :closable="false">
              {{ currentLog.error_message }}
            </el-alert>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 数据对比 -->
        <el-divider content-position="left">数据变更</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover" class="data-card">
              <template #header>
                <span class="card-title">操作前数据</span>
              </template>
              <pre v-if="currentLog.old_data" class="data-pre">{{ formatJson(currentLog.old_data) }}</pre>
              <el-empty v-else description="无" :image-size="60" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover" class="data-card">
              <template #header>
                <span class="card-title">操作后数据</span>
              </template>
              <pre v-if="currentLog.new_data" class="data-pre">{{ formatJson(currentLog.new_data) }}</pre>
              <el-empty v-else description="无" :image-size="60" />
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getAuditLogs, getModules, getStatistics } from './api'

const loading = ref(false)
const tableData = ref([])
const modules = ref([])
const statistics = ref({})
const detailVisible = ref(false)
const currentLog = ref(null)
const dateRange = ref([])

const searchForm = reactive({
  module: null,
  action: null,
  operator_name: '',
  keyword: '',
  start_date: '',
  end_date: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

onMounted(() => {
  loadModules()
  loadStatistics()
  loadData()
})

const loadModules = async () => {
  try {
    const res = await getModules()
    if (res.code === 200) {
      modules.value = res.data || []
    }
  } catch (error) {
    console.error('加载模块列表失败:', error)
  }
}

const loadStatistics = async () => {
  try {
    const res = await getStatistics(7)
    if (res.code === 200) {
      statistics.value = res.data || {}
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (searchForm.module) params.module = searchForm.module
    if (searchForm.action) params.action = searchForm.action
    if (searchForm.operator_name) params.operator_name = searchForm.operator_name
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await getAuditLogs(params)

    if (res.code === 200) {
      tableData.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载审计日志失败:', error)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.module = null
  searchForm.action = null
  searchForm.operator_name = ''
  searchForm.keyword = ''
  dateRange.value = []
  pagination.page = 1
  loadData()
}

const showDetail = (row) => {
  currentLog.value = row
  detailVisible.value = true
}

const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getActionType = (action) => {
  const typeMap = {
    'CREATE': 'success',
    'UPDATE': 'warning',
    'DELETE': 'danger'
  }
  return typeMap[action] || 'info'
}

const getActionText = (action) => {
  const textMap = {
    'CREATE': '创建',
    'UPDATE': '更新',
    'DELETE': '删除'
  }
  return textMap[action] || action
}

const formatJson = (data) => {
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch (e) {
      return data
    }
  }
  return JSON.stringify(data, null, 2)
}
</script>

<style scoped>
.audit-log-container {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.detail-content {
  padding: 10px;
}

.data-card {
  margin-bottom: 10px;
}

.card-title {
  font-weight: bold;
  font-size: 14px;
}

.data-pre {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
