<template>
  <div class="billing-container">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span class="title">账单管理</span>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="账单月份">
          <el-date-picker
            v-model="searchForm.billMonth"
            type="month"
            placeholder="选择月份"
            format="YYYY-MM"
            value-format="YYYY-MM"
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item label="公寓">
          <el-select v-model="searchForm.apartment_id" placeholder="全部公寓" clearable style="width: 200px">
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadBills" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="success" @click="exportExcel" :loading="exporting">
            <el-icon><Download /></el-icon>
            导出Excel
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="summary" class="summary-info">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="公寓数量" :value="summary.total_apartments" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="总账号数" :value="summary.total_accounts" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="总费用" :value="summary.total_amount" prefix="¥" :precision="2" />
          </el-col>
        </el-row>
      </div>

      <el-table :data="billSummary" v-loading="loading" stripe style="margin-top: 20px">
        <el-table-column prop="apartment_code" label="公寓编号" width="120" />
        <el-table-column prop="apartment_name" label="公寓名称" min-width="150" />
        <el-table-column prop="total_accounts" label="总账号数" width="100" align="center" />
        <el-table-column prop="active_accounts" label="开通账号" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.active_accounts }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="inactive_accounts" label="未开通账号" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.inactive_accounts }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="总费用" width="120" align="right">
          <template #default="{ row }">
            <span style="color: #409eff; font-weight: bold;">¥{{ row.total_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetails(row)">
              查看明细
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="detailsVisible"
      :title="`账单明细 - ${currentBill?.apartment_name || ''}`"
      width="95%"
      top="5vh"
    >
      <div v-if="currentBill" class="bill-details">
        <el-descriptions :column="3" border style="margin-bottom: 20px">
          <el-descriptions-item label="账单月份">{{ currentBill.bill_month }}</el-descriptions-item>
          <el-descriptions-item label="公寓编号">{{ currentBill.apartment_code }}</el-descriptions-item>
          <el-descriptions-item label="公寓名称">{{ currentBill.apartment_name }}</el-descriptions-item>
          <el-descriptions-item label="总账号数">{{ currentBill.total_accounts }}</el-descriptions-item>
          <el-descriptions-item label="开通账号">
            <el-tag type="success">{{ currentBill.active_accounts }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="未开通账号">
            <el-tag type="info">{{ currentBill.inactive_accounts }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总费用" :span="3">
            <span style="color: #409eff; font-size: 18px; font-weight: bold;">
              ¥{{ currentBill.total_amount }}
            </span>
          </el-descriptions-item>
        </el-descriptions>

        <el-table :data="currentBill.bill_details" stripe max-height="500">
          <el-table-column prop="username" label="宽带账号" width="150" fixed />
          <el-table-column prop="room" label="房间号" width="100" align="center" />
          <el-table-column prop="plan_name" label="套餐名称" min-width="180" />
          <el-table-column prop="plan_price" label="月费" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.plan_price }}
            </template>
          </el-table-column>
          <el-table-column prop="activate_date" label="开通时间" width="120" />
          <el-table-column prop="expire_date" label="到期时间" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '已开通' : '已停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="monthly_fee" label="本月费用" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.monthly_fee == 0" style="color: #e6a23c;">免费</span>
              <span v-else style="color: #409eff; font-weight: bold;">¥{{ row.monthly_fee }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import {
  getBillingSummary,
  getBillingDetails,
  exportBillingExcel,
  getBillingApartments
} from '../api'

const loading = ref(false)
const exporting = ref(false)
const billSummary = ref([])
const summary = ref(null)
const apartments = ref([])

const searchForm = reactive({
  billMonth: '',
  apartment_id: null
})

const detailsVisible = ref(false)
const currentBill = ref(null)

onMounted(() => {
  const now = new Date()
  searchForm.billMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  loadApartments()
  loadBills()
})

const loadApartments = async () => {
  try {
    const res = await getBillingApartments()
    if (res.code === 200) {
      apartments.value = res.data || []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error)
  }
}

const loadBills = async () => {
  if (!searchForm.billMonth) {
    ElMessage.warning('请选择账单月份')
    return
  }

  loading.value = true
  try {
    const [year, month] = searchForm.billMonth.split('-')
    const params = {
      year: parseInt(year),
      month: parseInt(month)
    }

    if (searchForm.apartment_id) {
      params.apartment_id = searchForm.apartment_id
    }

    const res = await getBillingSummary(params)
    if (res.code === 200) {
      billSummary.value = res.data || []
      summary.value = res.summary || null
    }
  } catch (error) {
    console.error('加载账单失败:', error)
    ElMessage.error('加载账单失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  const now = new Date()
  searchForm.billMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  searchForm.apartment_id = null
  loadBills()
}

const showDetails = async (row) => {
  if (!searchForm.billMonth) {
    ElMessage.warning('请先选择账单月份')
    return
  }

  try {
    const [year, month] = searchForm.billMonth.split('-')
    const res = await getBillingDetails(row.apartment_id, {
      year: parseInt(year),
      month: parseInt(month)
    })

    if (res.code === 200) {
      currentBill.value = res.data
      detailsVisible.value = true
    } else {
      ElMessage.error(res.message || '获取账单明细失败')
    }
  } catch (error) {
    console.error('获取账单明细失败:', error)
    ElMessage.error('获取账单明细失败')
  }
}

const exportExcel = async () => {
  if (!searchForm.billMonth) {
    ElMessage.warning('请选择账单月份')
    return
  }

  exporting.value = true
  try {
    const [year, month] = searchForm.billMonth.split('-')
    const params = {
      year: parseInt(year),
      month: parseInt(month)
    }

    if (searchForm.apartment_id) {
      params.apartment_id = searchForm.apartment_id
    }

    const res = await exportBillingExcel(params)

    const blob = new Blob([res], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `账单_${year}年${month}月.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.billing-container {
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
}

.search-form {
  margin-bottom: 20px;
}

.summary-info {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.bill-details {
  padding: 10px;
}
</style>
