<template>
  <div class="audit-log-container">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span class="title">操作日志</span>
          <el-tag type="info" size="small" class="hide-on-mobile">
            共 {{ statistics.total || 0 }} 条记录
          </el-tag>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" style="margin-bottom: 20px">
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.total || 0 }}</div>
              <div class="stat-label">总操作数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" class="hide-on-mobile">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.by_action?.CREATE || 0 }}</div>
              <div class="stat-label">创建操作</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" class="hide-on-mobile">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.by_action?.UPDATE || 0 }}</div>
              <div class="stat-label">更新操作</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="6" class="hide-on-mobile">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ statistics.by_action?.DELETE || 0 }}</div>
              <div class="stat-label">删除操作</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 桌面端搜索表单 -->
      <el-form :inline="true" class="search-form responsive-search-form hide-on-mobile">
        <el-form-item label="模块">
          <el-select v-model="searchForm.module" placeholder="全部模块" clearable style="width: 120px">
            <el-option
              v-for="mod in modules"
              :key="mod"
              :label="mod"
              :value="mod"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.action" placeholder="全部类型" clearable style="width: 100px">
            <el-option label="创建" value="CREATE" />
            <el-option label="更新" value="UPDATE" />
            <el-option label="删除" value="DELETE" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="searchForm.operator_name" placeholder="用户名" clearable style="width: 120px" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="关键词" clearable style="width: 150px" />
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

      <!-- 手机端简化搜索 -->
      <div class="mobile-search show-on-mobile">
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索关键词"
          clearable
          size="large"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="mobile-search-buttons">
          <el-button type="primary" @click="handleSearch" size="large">
            查询
          </el-button>
          <el-button @click="handleReset" size="large">
            重置
          </el-button>
        </div>
      </div>

      <!-- 桌面端日志表格 -->
      <div class="table-view hide-on-mobile">
        <el-table :data="tableData" v-loading="loading" stripe>
          <el-table-column prop="created_at" label="操作时间" width="140">
            <template #default="{ row }">
              <el-tag type="info" size="small">
                {{ formatTime(row.created_at) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="module" label="模块" width="100">
            <template #default="{ row }">
              <el-tag type="primary" size="small">{{ row.module }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="action" label="类型" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="getActionType(row.action)" size="small">
                {{ getActionText(row.action) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="operator_name" label="用户名" width="80" align="center" />
          <el-table-column prop="description" label="操作描述" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <div>{{ row.description || '-' }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP" width="100" align="center">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.ip_address || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="60" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 手机端卡片视图 -->
      <div class="card-view show-on-mobile">
        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div v-else-if="tableData.length === 0" class="empty-container">
          <el-empty description="暂无数据" />
        </div>
        <div v-else class="card-list">
          <div v-for="row in tableData" :key="row.id" class="log-card">
            <div class="log-card-header">
              <div class="log-info">
                <el-tag type="primary" size="small">{{ row.module }}</el-tag>
                <el-tag :type="getActionType(row.action)" size="small">
                  {{ getActionText(row.action) }}
                </el-tag>
              </div>
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
            <div class="log-card-body">
              <div class="log-info-row">
                <span class="label">用户：</span>
                <span class="value">{{ row.operator_name || '系统' }}</span>
              </div>
              <div class="log-info-row">
                <span class="label">时间：</span>
                <span class="value">{{ formatTime(row.created_at) }}</span>
              </div>
              <div class="log-info-row description">
                <span class="label">描述：</span>
                <span class="value">{{ row.description || '-' }}</span>
              </div>
              <div class="log-info-row">
                <span class="label">IP：</span>
                <span class="value">{{ row.ip_address || '-' }}</span>
              </div>
            </div>
            <div class="log-card-footer">
              <el-button type="primary" size="small" @click="showDetail(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
            </div>
          </div>
        </div>
      </div>

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
      width="95%"
      top="5vh"
    >
      <div v-if="currentLog" class="detail-content">
        <!-- 桌面端详情 -->
        <el-descriptions :column="2" border class="hide-on-mobile">
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
          <el-descriptions-item label="用户名">
            {{ currentLog.operator_name || '系统' }}
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

        <!-- 手机端详情卡片 -->
        <div class="mobile-detail-card show-on-mobile">
          <div class="detail-header">
            <div class="detail-tags">
              <el-tag type="primary">{{ currentLog.module }}</el-tag>
              <el-tag :type="getActionType(currentLog.action)">
                {{ getActionText(currentLog.action) }}
              </el-tag>
              <el-tag :type="currentLog.status === 'success' ? 'success' : 'danger'">
                {{ currentLog.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
          </div>
          <div class="detail-body">
            <div class="detail-item">
              <span class="label">用户名：</span>
              <span class="value">{{ currentLog.operator_name || '系统' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">时间：</span>
              <span class="value">{{ currentLog.created_at }}</span>
            </div>
            <div class="detail-item">
              <span class="label">IP：</span>
              <span class="value">{{ currentLog.ip_address || '-' }}</span>
            </div>
            <div class="detail-item description">
              <span class="label">描述：</span>
              <span class="value">{{ currentLog.description || '-' }}</span>
            </div>
            <div v-if="currentLog.error_message" class="detail-item description error">
              <span class="label">错误：</span>
              <span class="value">{{ currentLog.error_message }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, View, Loading } from '@element-plus/icons-vue'
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

/* 手机端视图切换 */
.show-on-mobile {
  display: none;
}

.hide-on-mobile {
  display: block;
}

/* 手机端简化搜索 */
.mobile-search {
  display: none;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.mobile-search .el-input {
  width: 100%;
}

.mobile-search-buttons {
  display: flex;
  gap: 10px;
}

.mobile-search-buttons .el-button {
  flex: 1;
  height: 42px;
  font-size: 15px;
}

/* 手机端卡片视图 */
.card-view {
  width: 100%;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
}

.log-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.log-info {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.log-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.log-info-row {
  display: flex;
  align-items: baseline;
  font-size: 14px;
  line-height: 1.5;
}

.log-info-row .label {
  color: #909399;
  min-width: 50px;
  flex-shrink: 0;
}

.log-info-row .value {
  color: #303133;
}

.log-info-row.description {
  flex-direction: column;
  gap: 4px;
}

.log-info-row.description .label {
  min-width: auto;
}

.log-card-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.log-card-footer .el-button {
  font-size: 13px;
}

.loading-container,
.empty-container {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.loading-container .el-icon {
  font-size: 32px;
}

/* 手机端详情卡片 */
.mobile-detail-card {
  display: none;
  flex-direction: column;
  gap: 15px;
}

.detail-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-item {
  display: flex;
  align-items: baseline;
  font-size: 14px;
}

.detail-item .label {
  color: #909399;
  min-width: 60px;
  flex-shrink: 0;
}

.detail-item .value {
  color: #303133;
}

.detail-item.description {
  flex-direction: column;
  gap: 4px;
}

.detail-item.description .label {
  min-width: auto;
}

.detail-item.error .value {
  color: #f56c6c;
}

/* 移动端样式优化 */
@media (max-width: 767px) {
  .audit-log-container {
    padding: 10px;
  }

  .header-actions {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .title {
    font-size: 16px;
  }

  .search-form {
    padding: 12px;
    margin-bottom: 15px;
  }

  .stat-value {
    font-size: 22px;
  }

  .stat-label {
    font-size: 12px;
  }

  /* 显示手机端视图 */
  .show-on-mobile {
    display: flex;
  }

  .hide-on-mobile {
    display: none;
  }

  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table__header) {
    font-size: 12px;
  }

  :deep(.el-tag) {
    font-size: 11px;
    padding: 0 4px;
  }

  :deep(.el-button--small) {
    padding: 4px 8px;
    font-size: 12px;
  }

  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }

  :deep(.el-pagination__total) {
    width: 100%;
    text-align: center;
    margin-bottom: 8px;
  }

  :deep(.el-descriptions) {
    font-size: 12px;
  }

  :deep(.el-descriptions__label) {
    width: 100px;
  }
}

/* 手机端对话框样式 */
@media (max-width: 767px) {
  :deep(.el-dialog) {
    width: 95% !important;
    max-width: 95%;
    margin: 5vh auto !important;
    max-height: 90vh !important;
  }

  :deep(.el-dialog__body) {
    padding: 15px !important;
    max-height: 70vh !important;
    overflow-y: auto !important;
  }

  .mobile-detail-card {
    display: flex;
  }

  .detail-item {
    flex-wrap: wrap;
    gap: 5px;
  }

  .detail-item .label {
    min-width: auto;
  }
}
</style>
