<template>
  <div class="fault-container">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span class="title">故障处理</span>
          <!-- 桌面端统计 -->
          <div class="statistics hide-on-mobile">
            <el-tag type="danger" size="large">
              待处理: {{ statistics.pending || 0 }}
            </el-tag>
            <el-tag type="warning" size="large">
              处理中: {{ statistics.processing || 0 }}
            </el-tag>
            <el-tag type="success" size="large">
              已解决: {{ statistics.resolved || 0 }}
            </el-tag>
            <el-tag type="info" size="large">
              已关闭: {{ statistics.closed || 0 }}
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 手机端统计 -->
      <div class="mobile-statistics show-on-mobile">
        <div class="mobile-stat-grid">
          <div class="mobile-stat-item">
            <span class="mobile-stat-value danger">{{ statistics.pending || 0 }}</span>
            <span class="mobile-stat-label">待处理</span>
          </div>
          <div class="mobile-stat-item">
            <span class="mobile-stat-value warning">{{ statistics.processing || 0 }}</span>
            <span class="mobile-stat-label">处理中</span>
          </div>
          <div class="mobile-stat-item">
            <span class="mobile-stat-value success">{{ statistics.resolved || 0 }}</span>
            <span class="mobile-stat-label">已解决</span>
          </div>
          <div class="mobile-stat-item">
            <span class="mobile-stat-value info">{{ statistics.closed || 0 }}</span>
            <span class="mobile-stat-label">已关闭</span>
          </div>
        </div>
      </div>

      <!-- 桌面端搜索表单 -->
      <el-form :inline="true" class="search-form responsive-search-form hide-on-mobile">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.fault_type" placeholder="全部" clearable style="width: 130px">
            <el-option label="全部" value="" />
            <el-option label="不能上网" value="cannot_connect" />
            <el-option label="网络卡顿" value="slow_network" />
            <el-option label="频繁掉线" value="frequent_disconnect" />
          </el-select>
        </el-form-item>
        <el-form-item label="公寓">
          <el-select v-model="searchForm.apartment_id" placeholder="全部" clearable style="width: 130px">
            <el-option label="全部" value="" />
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="账号/报障人"
            clearable
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 手机端简化搜索 -->
      <div class="mobile-search show-on-mobile">
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索账号/报障人"
          clearable
          size="large"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="mobile-search-buttons">
          <el-button type="primary" @click="loadData" size="large">
            搜索
          </el-button>
          <el-button @click="resetSearch" size="large">
            重置
          </el-button>
        </div>
      </div>

      <!-- 桌面端表格 -->
      <div class="table-view hide-on-mobile">
        <el-table :data="tableData" v-loading="loading" stripe>
          <el-table-column prop="id" label="ID" width="50" />
          <el-table-column prop="username" label="账号" width="100" />
          <el-table-column prop="fault_type_text" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getFaultTypeTag(row.fault_type)" size="small">
                {{ row.fault_type_text }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reporter_name" label="报障人" width="80" />
          <el-table-column prop="reporter_phone" label="电话" width="100" />
          <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip />
          <el-table-column prop="fault_time" label="故障时间" width="140">
            <template #default="{ row }">
              {{ formatDateTime(row.fault_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ row.status_text }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="180">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleView(row)">
                详情
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                link
                type="warning"
                size="small"
                @click="handleStartProcessing(row)"
              >
                处理
              </el-button>
              <el-button
                v-if="row.status === 'processing'"
                link
                type="success"
                size="small"
                @click="handleResolve(row)"
              >
                解决
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
          <div v-for="row in tableData" :key="row.id" class="fault-card">
            <div class="fault-card-header">
              <span class="username">{{ row.username }}</span>
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ row.status_text }}
              </el-tag>
            </div>
            <div class="fault-card-body">
              <div class="fault-info-item">
                <span class="label">类型：</span>
                <el-tag :type="getFaultTypeTag(row.fault_type)" size="small">
                  {{ row.fault_type_text }}
                </el-tag>
              </div>
              <div class="fault-info-item">
                <span class="label">报障人：</span>
                <span class="value">{{ row.reporter_name || '-' }}</span>
              </div>
              <div class="fault-info-item">
                <span class="label">电话：</span>
                <span class="value">{{ row.reporter_phone || '-' }}</span>
              </div>
              <div class="fault-info-item description">
                <span class="label">描述：</span>
                <span class="value">{{ row.description || '-' }}</span>
              </div>
              <div class="fault-info-item">
                <span class="label">时间：</span>
                <span class="value">{{ formatDateTime(row.fault_time) }}</span>
              </div>
            </div>
            <div class="fault-card-footer">
              <el-button type="primary" size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                type="warning"
                size="small"
                @click="handleStartProcessing(row)"
              >
                <el-icon><Edit /></el-icon>
                处理
              </el-button>
              <el-button
                v-if="row.status === 'processing'"
                type="success"
                size="small"
                @click="handleResolve(row)"
              >
                <el-icon><CircleCheck /></el-icon>
                解决
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="故障详情"
      width="95%"
      top="5vh"
    >
      <div v-if="detailData" class="detail-content">
        <!-- 桌面端详情 -->
        <el-descriptions :column="2" border v-if="detailData" class="hide-on-mobile">
          <el-descriptions-item label="上网账号">
            <el-tag type="primary" size="small">{{ detailData.username }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="报障人">{{ detailData.reporter_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ detailData.reporter_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="公寓">{{ detailData.apartment_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="房间号">{{ detailData.room || '-' }}</el-descriptions-item>
          <el-descriptions-item label="故障类型">
            <el-tag :type="getFaultTypeTag(detailData.fault_type)">
              {{ detailData.fault_type_text }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="故障时间" :span="2">
            {{ formatDateTime(detailData.fault_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="故障描述" :span="2">
            {{ detailData.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(detailData.status)">
              {{ detailData.status_text }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处理人">{{ detailData.operator_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理时间" :span="2">
            {{ detailData.resolve_time ? formatDateTime(detailData.resolve_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="处理说明" :span="2">
            {{ detailData.resolve_description || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 手机端详情卡片 -->
        <div class="mobile-detail-card show-on-mobile">
          <div class="detail-header">
            <el-tag type="primary" size="large">{{ detailData.username }}</el-tag>
            <el-tag :type="getStatusType(detailData.status)" size="large">
              {{ detailData.status_text }}
            </el-tag>
          </div>
          <div class="detail-body">
            <div class="detail-item">
              <span class="label">报障人：</span>
              <span class="value">{{ detailData.reporter_name || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">电话：</span>
              <span class="value">{{ detailData.reporter_phone || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">公寓：</span>
              <span class="value">{{ detailData.apartment_name || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">房间：</span>
              <span class="value">{{ detailData.room || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">类型：</span>
              <el-tag :type="getFaultTypeTag(detailData.fault_type)" size="small">
                {{ detailData.fault_type_text }}
              </el-tag>
            </div>
            <div class="detail-item">
              <span class="label">时间：</span>
              <span class="value">{{ formatDateTime(detailData.fault_time) }}</span>
            </div>
            <div class="detail-item description">
              <span class="label">描述：</span>
              <span class="value">{{ detailData.description || '-' }}</span>
            </div>
            <div class="detail-divider"></div>
            <div class="detail-item">
              <span class="label">处理人：</span>
              <span class="value">{{ detailData.operator_name || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">处理时间：</span>
              <span class="value">{{ detailData.resolve_time ? formatDateTime(detailData.resolve_time) : '-' }}</span>
            </div>
            <div class="detail-item description">
              <span class="label">处理说明：</span>
              <span class="value">{{ detailData.resolve_description || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer v-if="detailData && detailData.status !== 'closed'">
        <div class="dialog-footer-buttons">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button
            v-if="detailData.status === 'pending'"
            type="warning"
            @click="handleStartProcessing(detailData); detailVisible = false"
          >
            开始处理
          </el-button>
          <el-button
            v-if="detailData.status === 'processing'"
            type="success"
            @click="handleResolve(detailData)"
          >
            标记解决
          </el-button>
          <el-button
            v-if="detailData.status === 'resolved'"
            type="info"
            @click="handleClose(detailData); detailVisible = false"
          >
            关闭
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 处理说明弹窗 -->
    <el-dialog
      v-model="resolveDialogVisible"
      title="处理故障"
      width="95%"
      top="5vh"
    >
      <el-form :model="resolveForm" label-position="top">
        <el-form-item label="故障账号">
          <span>{{ resolveForm.username }}</span>
        </el-form-item>
        <el-form-item label="故障类型">
          <el-tag :type="getFaultTypeTag(resolveForm.fault_type)">
            {{ resolveForm.fault_type_text }}
          </el-tag>
        </el-form-item>
        <el-form-item label="处理说明" prop="resolve_description">
          <el-input
            v-model="resolveForm.resolve_description"
            type="textarea"
            :rows="4"
            placeholder="请输入处理说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer-buttons">
          <el-button @click="resolveDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleResolveSubmit" :loading="submitLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh, View, Edit, CircleCheck, Loading } from '@element-plus/icons-vue';
import {
  getFaultReports,
  updateFaultReport,
  getFaultStatistics,
  getApartments
} from './api';

const loading = ref(false);
const tableData = ref([]);
const statistics = ref({});
const apartments = ref([]);
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
});

const searchForm = reactive({
  keyword: '',
  status: '',
  fault_type: '',
  apartment_id: ''
});

const detailVisible = ref(false);
const detailData = ref(null);

const resolveDialogVisible = ref(false);
const submitLoading = ref(false);
const resolveForm = reactive({
  id: null,
  username: '',
  fault_type: '',
  fault_type_text: '',
  resolve_description: ''
});

const getFaultTypeTag = (type) => {
  const typeMap = {
    'cannot_connect': 'danger',
    'slow_network': 'warning',
    'frequent_disconnect': 'warning'
  };
  return typeMap[type] || 'info';
};

const getStatusType = (status) => {
  const statusMap = {
    'pending': 'danger',
    'processing': 'warning',
    'resolved': 'success',
    'closed': 'info'
  };
  return statusMap[status] || 'info';
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

const loadData = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    };
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key];
      }
    });

    if (!params.status) {
      params.exclude_status = 'resolved,closed';
    }

    const res = await getFaultReports(params);
    if (res.code === 200) {
      tableData.value = res.data || [];
      pagination.total = res.total || 0;
    }
  } catch (error) {
    console.error('加载数据失败:', error);
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

const loadStatistics = async () => {
  try {
    const res = await getFaultStatistics();
    if (res.code === 200) {
      statistics.value = res.data || {};
    }
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
};

const loadApartments = async () => {
  try {
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (isAdmin) {
      const res = await getApartments({ page: 1, page_size: 100, status: 'active' });
      if (res.code === 200) {
        apartments.value = res.data || [];
      }
    } else {
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error);
  }
};

const resetSearch = () => {
  searchForm.keyword = '';
  searchForm.status = '';
  searchForm.fault_type = '';
  searchForm.apartment_id = '';
  pagination.page = 1;
  loadData();
};

const handleView = (row) => {
  detailData.value = row;
  detailVisible.value = true;
};

const handleStartProcessing = async (row) => {
  try {
    await updateFaultReport(row.id, { status: 'processing' });
    ElMessage.success('已开始处理');
    loadData();
    loadStatistics();
    if (detailVisible.value) {
      detailVisible.value = false;
    }
  } catch (error) {
    console.error('处理失败:', error);
    ElMessage.error('操作失败');
  }
};

const handleResolve = (row) => {
  resolveForm.id = row.id;
  resolveForm.username = row.username;
  resolveForm.fault_type = row.fault_type;
  resolveForm.fault_type_text = row.fault_type_text;
  resolveForm.resolve_description = '';
  resolveDialogVisible.value = true;
};

const handleResolveSubmit = async () => {
  try {
    submitLoading.value = true;
    await updateFaultReport(resolveForm.id, {
      status: 'resolved',
      resolve_description: resolveForm.resolve_description
    });
    ElMessage.success('已标记为已解决');
    resolveDialogVisible.value = false;
    loadData();
    loadStatistics();
  } catch (error) {
    console.error('处理失败:', error);
    ElMessage.error('操作失败');
  } finally {
    submitLoading.value = false;
  }
};

const handleClose = async (row) => {
  try {
    await ElMessageBox.confirm('确定要关闭此故障记录吗？', '关闭确认', {
      type: 'info'
    });
    await updateFaultReport(row.id, { status: 'closed' });
    ElMessage.success('已关闭');
    loadData();
    loadStatistics();
    if (detailVisible.value) {
      detailVisible.value = false;
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('关闭失败:', error);
      ElMessage.error('操作失败');
    }
  }
};

onMounted(() => {
  loadData();
  loadStatistics();
  loadApartments();
});
</script>

<style scoped>
.fault-container {
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

.statistics {
  display: flex;
  gap: 10px;
}

.search-form {
  margin-bottom: 20px;
}

/* 手机端视图切换 */
.show-on-mobile {
  display: none;
}

.hide-on-mobile {
  display: block;
}

/* 手机端统计 */
.mobile-statistics {
  display: none;
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.mobile-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  text-align: center;
}

.mobile-stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobile-stat-value {
  font-size: 20px;
  font-weight: bold;
}

.mobile-stat-value.danger {
  color: #f56c6c;
}

.mobile-stat-value.warning {
  color: #e6a23c;
}

.mobile-stat-value.success {
  color: #67c23a;
}

.mobile-stat-value.info {
  color: #909399;
}

.mobile-stat-label {
  font-size: 11px;
  color: #909399;
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

.fault-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
}

.fault-card-header {
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

.fault-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.fault-info-item {
  display: flex;
  align-items: center;
  font-size: 14px;
  line-height: 1.5;
}

.fault-info-item .label {
  color: #909399;
  min-width: 60px;
  flex-shrink: 0;
}

.fault-info-item .value {
  color: #303133;
}

.fault-info-item.description {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.fault-info-item.description .label {
  min-width: auto;
}

.fault-card-footer {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.fault-card-footer .el-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-item {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.detail-item .label {
  color: #909399;
  min-width: 70px;
  flex-shrink: 0;
}

.detail-item .value {
  color: #303133;
}

.detail-item.description {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.detail-item.description .label {
  min-width: auto;
}

.detail-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 5px 0;
}

/* 移动端样式优化 */
@media (max-width: 767px) {
  .fault-container {
    padding: 10px;
  }

  .title {
    font-size: 16px;
  }

  .statistics {
    display: none;
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

  .mobile-statistics {
    display: block;
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

  :deep(.el-form-item) {
    margin-bottom: 16px !important;
  }

  :deep(.el-form-item__label) {
    font-size: 14px !important;
    font-weight: 500 !important;
    margin-bottom: 8px !important;
    display: block !important;
  }

  :deep(.el-input__inner) {
    height: 40px !important;
    font-size: 15px !important;
  }

  :deep(.el-textarea__inner) {
    font-size: 15px !important;
  }

  .dialog-footer-buttons {
    display: flex;
    gap: 10px;
  }

  .dialog-footer-buttons .el-button {
    flex: 1;
    height: 40px;
    font-size: 15px;
  }
}
</style>
