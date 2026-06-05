<template>
  <div class="warning-container">
    <el-card class="statistics-card">
      <div class="statistics">
        <div class="stat-item">
          <el-icon class="stat-icon" color="#E6A23C"><Warning /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.inactive_users || 0 }}</div>
            <div class="stat-label">开通未在线用户分析</div>
          </div>
        </div>
        <div class="stat-item">
          <el-icon class="stat-icon" color="#F56C6C"><WarningFilled /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.frequent_dialing_users || 0 }}</div>
            <div class="stat-label">频繁拨号用户</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="开通未在线用户分析" name="inactive">
          <el-form :inline="true" class="search-form">
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

          <template v-if="hasSearched">
            <el-table
              :data="tableData"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
            >
              <el-table-column prop="username" label="用户名" width="120" fixed />
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="phone" label="电话" width="120" />
              <el-table-column prop="room" label="房间号" width="100" />
              <el-table-column prop="apartment_name" label="公寓" width="150" />
              <el-table-column prop="plan_id" label="套餐ID" width="80" />
              <el-table-column prop="activate_date" label="开通日期" width="120" />
              <el-table-column prop="expire_date" label="到期日期" width="120" />
              <el-table-column prop="updated_at" label="最后更新" width="160" />
            </el-table>

            <el-empty v-if="tableData.length === 0 && !loading" description="暂无未在线用户" />
          </template>

          <el-empty v-else description="请选择公寓后点击分析" />
        </el-tab-pane>

        <el-tab-pane label="频繁拨号用户分析" name="frequent">
          <el-form :inline="true" class="search-form">
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

          <template v-if="hasSearched">
            <el-table
              :data="tableData"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
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
    // 如果是管理员，加载所有公寓；否则只加载自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'

    if (isAdmin) {
      const res = await getAllApartments()
      console.log('公寓数据:', res)
      if (res.code === 200) {
        // 适配返回格式：data 可能是数组或 {items: []}
        apartments.value = Array.isArray(res.data) ? res.data : (res.data.items || [])
        console.log('公寓列表:', apartments.value)
      }
    } else {
      // 非管理员只能看到自己关联的公寓
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
      console.log('公寓列表（当前用户）:', apartments.value)
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
    console.log('未在线用户查询参数:', params)
    const res = await getInactiveUsers(params)
    console.log('未在线用户返回结果:', res)
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
    // 如果已经点击过分析，切换标签时也刷新统计数据
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
    // 如果是非管理员，自动选择自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (!isAdmin && apartments.value.length > 0) {
      searchForm.value.apartment_id = apartments.value[0].id
    }
  })
  // 不自动加载统计数据，等待用户点击分析按钮
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
</style>
