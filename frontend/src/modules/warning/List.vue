<template>
  <div class="warning-container">
    <!-- 统计卡片 - 桌面端 -->
    <el-card class="statistics-card hide-on-mobile">
      <div class="statistics">
        <div class="stat-item">
          <el-icon class="stat-icon" color="#E6A23C"><Warning /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.inactive_users || 0 }}</div>
            <div class="stat-label">未在线用户</div>
          </div>
        </div>
        <div class="stat-item">
          <el-icon class="stat-icon" color="#F56C6C"><WarningFilled /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.frequent_dialing_users || 0 }}</div>
            <div class="stat-label">频繁拨号</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 统计卡片 - 手机端 -->
    <el-card class="statistics-card show-on-mobile">
      <div class="mobile-stats">
        <div class="mobile-stat-item">
          <el-icon class="stat-icon" color="#E6A23C" size="32"><Warning /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.inactive_users || 0 }}</div>
            <div class="stat-label">未在线用户</div>
          </div>
        </div>
        <div class="mobile-stat-item">
          <el-icon class="stat-icon" color="#F56C6C" size="32"><WarningFilled /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.frequent_dialing_users || 0 }}</div>
            <div class="stat-label">频繁拨号</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="未在线用户分析" name="inactive">
          <!-- 桌面端搜索表单 -->
          <el-form :inline="true" class="search-form responsive-search-form hide-on-mobile">
            <el-form-item label="公寓">
              <el-select
                v-model="searchForm.apartment_id"
                placeholder="选择公寓"
                clearable
                class="apartment-select"
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
                <el-icon><DataAnalysis /></el-icon>
                分析
              </el-button>
              <el-button @click="handleReset">
                <el-icon><RefreshLeft /></el-icon>
                重置
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 手机端简化搜索 -->
          <div class="mobile-search show-on-mobile">
            <el-select v-model="searchForm.apartment_id" placeholder="选择公寓" clearable style="width: 100%; margin-bottom: 10px;">
              <el-option
                v-for="apt in apartments"
                :key="apt.id"
                :label="apt.name"
                :value="apt.id"
              />
            </el-select>
            <div class="mobile-search-buttons">
              <el-button type="primary" @click="handleSearch" size="large">
                分析
              </el-button>
              <el-button @click="handleReset" size="large">
                重置
              </el-button>
            </div>
          </div>

          <template v-if="hasSearched">
            <!-- 桌面端表格 -->
            <div class="table-view hide-on-mobile">
              <el-table
                :data="tableData"
                v-loading="loading"
                stripe
                border
                style="width: 100%"
              >
                <el-table-column prop="username" label="用户" width="100" fixed />
                <el-table-column prop="name" label="姓名" width="80" />
                <el-table-column prop="phone" label="电话" width="100" />
                <el-table-column prop="room" label="房间" width="70" />
                <el-table-column prop="apartment_name" label="公寓" width="120" />
                <el-table-column prop="activate_date" label="开通日" width="100" />
                <el-table-column prop="expire_date" label="到期日" width="100" />
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
                <div v-for="row in tableData" :key="row.username" class="user-card">
                  <div class="user-card-header">
                    <span class="username">{{ row.username }}</span>
                    <span class="name">{{ row.name || '-' }}</span>
                  </div>
                  <div class="user-card-body">
                    <div class="user-info-item">
                      <span class="label">电话：</span>
                      <span class="value">{{ row.phone || '-' }}</span>
                    </div>
                    <div class="user-info-item">
                      <span class="label">房间：</span>
                      <span class="value">{{ row.room || '-' }}</span>
                    </div>
                    <div class="user-info-item">
                      <span class="label">公寓：</span>
                      <span class="value">{{ row.apartment_name }}</span>
                    </div>
                    <div class="user-info-item">
                      <span class="label">开通日：</span>
                      <span class="value">{{ row.activate_date || '-' }}</span>
                    </div>
                    <div class="user-info-item">
                      <span class="label">到期日：</span>
                      <span class="value">{{ row.expire_date || '-' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <el-empty v-if="tableData.length === 0 && !loading" description="暂无未在线用户" />
          </template>

          <el-empty v-else description="请选择公寓后点击分析" />
        </el-tab-pane>

        <el-tab-pane label="频繁拨号用户分析" name="frequent">
          <!-- 桌面端搜索表单 -->
          <el-form :inline="true" class="search-form hide-on-mobile">
            <el-form-item label="公寓">
              <el-select
                v-model="searchForm.apartment_id"
                placeholder="选择公寓"
                clearable
                class="apartment-select"
              >
                <el-option
                  v-for="apt in apartments"
                  :key="apt.id"
                  :label="apt.name"
                  :value="apt.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="阈值（次/天）">
              <el-input-number
                v-model="searchForm.threshold"
                :min="1"
                :max="100"
              />
            </el-form-item>
            <el-form-item label="天数">
              <el-input-number
                v-model="searchForm.days"
                :min="1"
                :max="30"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">
                <el-icon><DataAnalysis /></el-icon>
                分析
              </el-button>
              <el-button @click="handleReset">
                <el-icon><RefreshLeft /></el-icon>
                重置
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 手机端简化搜索 -->
          <div class="mobile-search show-on-mobile">
            <el-select v-model="searchForm.apartment_id" placeholder="选择公寓" clearable style="width: 100%; margin-bottom: 10px;">
              <el-option
                v-for="apt in apartments"
                :key="apt.id"
                :label="apt.name"
                :value="apt.id"
              />
            </el-select>
            <div class="mobile-form-row">
              <div class="mobile-form-item">
                <span class="mobile-form-label">阈值(次/天)</span>
                <el-input-number v-model="searchForm.threshold" :min="1" :max="100" size="large" style="width: 100%;" />
              </div>
              <div class="mobile-form-item">
                <span class="mobile-form-label">天数</span>
                <el-input-number v-model="searchForm.days" :min="1" :max="30" size="large" style="width: 100%;" />
              </div>
            </div>
            <div class="mobile-search-buttons">
              <el-button type="primary" @click="handleSearch" size="large">
                分析
              </el-button>
              <el-button @click="handleReset" size="large">
                重置
              </el-button>
            </div>
          </div>

          <template v-if="hasSearched">
            <!-- 桌面端表格 -->
            <el-table
              :data="tableData"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
              class="hide-on-mobile"
            >
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="dial_count" label="拨号次数" width="120">
                <template #default="{ row }">
                  <el-tag type="danger">{{ row.dial_count }} 次</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="用户信息" width="300">
                <template #default="{ row }">
                  <div v-if="row.user_info">
                    <div>姓名: {{ row.user_info.name || '-' }}</div>
                    <div>电话: {{ row.user_info.phone || '-' }}</div>
                    <div>房间: {{ row.user_info.room || '-' }}</div>
                    <div>公寓: {{ row.user_info.apartment_name }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="first_dial_time" label="首次拨号" width="160" />
              <el-table-column prop="last_dial_time" label="最后拨号" width="160" />
            </el-table>

            <!-- 手机端卡片视图 -->
            <div class="card-view show-on-mobile">
              <div v-if="loading" class="loading-container">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>加载中...</span>
              </div>
              <div v-else-if="tableData.length === 0" class="empty-container">
                <el-empty description="暂无频繁拨号用户" />
              </div>
              <div v-else class="card-list">
                <div v-for="row in tableData" :key="row.username" class="dial-card">
                  <div class="dial-card-header">
                    <span class="username">{{ row.username }}</span>
                    <el-tag type="danger" size="small">{{ row.dial_count }} 次</el-tag>
                  </div>
                  <div class="dial-card-body">
                    <div class="dial-info" v-if="row.user_info">
                      <div class="dial-info-item">
                        <span class="label">姓名：</span>
                        <span class="value">{{ row.user_info.name || '-' }}</span>
                      </div>
                      <div class="dial-info-item">
                        <span class="label">电话：</span>
                        <span class="value">{{ row.user_info.phone || '-' }}</span>
                      </div>
                      <div class="dial-info-item">
                        <span class="label">房间：</span>
                        <span class="value">{{ row.user_info.room || '-' }}</span>
                      </div>
                      <div class="dial-info-item">
                        <span class="label">公寓：</span>
                        <span class="value">{{ row.user_info.apartment_name }}</span>
                      </div>
                    </div>
                    <div class="dial-time">
                      <div class="time-item">
                        <span class="time-label">首次：</span>
                        <span class="time-value">{{ row.first_dial_time || '-' }}</span>
                      </div>
                      <div class="time-item">
                        <span class="time-label">最后：</span>
                        <span class="time-value">{{ row.last_dial_time || '-' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <el-empty v-if="tableData.length === 0 && !loading" description="暂无频繁拨号用户" />
          </template>

          <el-empty v-else description="请选择公寓后点击分析" />
        </el-tab-pane>
      </el-tabs>

      <div class="pagination" v-if="hasSearched">
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { getInactiveUsers, getFrequentDialingUsers, getWarningStatistics } from './api'
import { getAllApartments } from '@/modules/apartment/api'

const loading = ref(false)
const tableData = ref([])
const statistics = ref({})
const apartments = ref([])
const activeTab = ref('inactive')
const hasSearched = ref(false)

const searchForm = ref({
  apartment_id: null,
  threshold: 10,
  days: 1
})

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

let refreshTimer = null

const loadStatistics = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await getWarningStatistics({
      apartment_id: searchForm.value.apartment_id,
      operator_id: user.id,
      threshold: searchForm.value.threshold,
      days: searchForm.value.days
    })
    if (res.code === 200) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadApartments = async () => {
  try {
    const isAdmin = localStorage.getItem('role') === 'admin'

    if (isAdmin) {
      const res = await getAllApartments()
      if (res.code === 200) {
        apartments.value = Array.isArray(res.data) ? res.data : (res.data.items || [])
      }
    } else {
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error)
  }
}

const loadInactiveUsers = async () => {
  loading.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const params = {
      ...searchForm.value,
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      operator_id: user.id
    }
    const res = await getInactiveUsers(params)
    if (res.code === 200) {
      tableData.value = res.data.items || []
      pagination.value.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载未在线用户失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadFrequentDialingUsers = async () => {
  loading.value = true
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const res = await getFrequentDialingUsers({
      apartment_id: searchForm.value.apartment_id,
      threshold: searchForm.value.threshold,
      days: searchForm.value.days,
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      operator_id: user.id
    })
    if (res.code === 200) {
      tableData.value = res.data.items || []
      pagination.value.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载频繁拨号用户失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  if (activeTab.value === 'inactive') {
    loadInactiveUsers()
  } else if (activeTab.value === 'frequent') {
    loadFrequentDialingUsers()
  }
}

const handleSearch = () => {
  hasSearched.value = true
  pagination.value.page = 1
  loadStatistics()
  loadData()
}

const handleReset = () => {
  hasSearched.value = false
  tableData.value = []
  searchForm.value = {
    apartment_id: null,
    threshold: 10,
    days: 1
  }
  pagination.value.page = 1
  pagination.value.total = 0
}

const handleTabChange = () => {
  pagination.value.page = 1
  if (hasSearched.value) {
    loadStatistics()
  }
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

onMounted(() => {
  loadApartments().then(() => {
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (!isAdmin && apartments.value.length > 0) {
      searchForm.value.apartment_id = apartments.value[0].id
    }
  })
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.warning-container {
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

.mobile-stats {
  display: flex;
  justify-content: space-around;
}

.mobile-stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
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

.search-form {
  margin-bottom: 20px;
}

.apartment-select {
  width: 200px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
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

.mobile-search-buttons {
  display: flex;
  gap: 10px;
}

.mobile-search-buttons .el-button {
  flex: 1;
  height: 42px;
  font-size: 15px;
}

.mobile-form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.mobile-form-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.mobile-form-label {
  font-size: 13px;
  color: #606266;
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

.user-card,
.dial-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
}

.user-card-header,
.dial-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.username {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.name {
  font-size: 13px;
  color: #909399;
}

.user-card-body,
.dial-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-info-item,
.dial-info-item {
  display: flex;
  align-items: baseline;
  font-size: 14px;
  line-height: 1.5;
}

.user-info-item .label,
.dial-info-item .label {
  color: #909399;
  min-width: 60px;
  flex-shrink: 0;
}

.user-info-item .value,
.dial-info-item .value {
  color: #303133;
}

.dial-time {
  display: flex;
  gap: 15px;
  margin-top: 5px;
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}

.time-item {
  display: flex;
  align-items: baseline;
  font-size: 12px;
}

.time-label {
  color: #909399;
}

.time-value {
  color: #606266;
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

/* 移动端样式优化 */
@media (max-width: 767px) {
  .warning-container {
    padding: 10px;
  }

  .statistics {
    justify-content: center;
    gap: 20px;
  }

  .stat-item {
    padding: 10px 15px;
  }

  .stat-icon {
    font-size: 30px;
    margin-right: 10px;
  }

  .stat-value {
    font-size: 20px;
  }

  .search-form {
    margin-bottom: 15px;
  }

  /* 显示手机端视图 */
  .show-on-mobile {
    display: flex;
  }

  .hide-on-mobile {
    display: none;
  }

  :deep(.el-tabs__nav-wrap) {
    padding: 0 10px;
  }

  :deep(.el-tabs__item) {
    font-size: 14px;
    padding: 0 12px;
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
}
</style>
