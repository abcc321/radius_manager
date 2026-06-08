<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">套餐管理</span>
          <el-button v-if="isAdmin" type="primary" @click="handleCreate" size="small">
            <el-icon><Plus /></el-icon>
            <span class="hide-on-mobile">新增套餐</span>
          </el-button>
        </div>
      </template>

      <!-- 桌面端搜索表单 -->
      <div class="search-form responsive-search-form hide-on-mobile">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="名称/描述"
              clearable
              @keyup.enter="handleSearch"
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="公寓">
            <el-select
              v-model="searchForm.apartment_id"
              placeholder="全部公寓"
              clearable
              @change="handleSearch"
              style="width: 150px"
            >
              <el-option label="全部公寓" :value="null" />
              <el-option
                v-for="apt in apartments"
                :key="apt.id"
                :label="apt.name"
                :value="apt.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="全部状态" clearable @change="handleSearch" style="width: 120px">
              <el-option label="全部" :value="null" />
              <el-option label="正常" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch" size="small">
              <el-icon><Search /></el-icon>
              <span>查询</span>
            </el-button>
            <el-button @click="handleReset" size="small">
              <el-icon><Refresh /></el-icon>
              <span>重置</span>
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 手机端简化搜索 -->
      <div class="mobile-search show-on-mobile">
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索套餐名称"
          clearable
          @keyup.enter="handleSearch"
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

      <!-- 桌面端表格视图 -->
      <div class="table-view hide-on-mobile">
        <el-table :data="tableData" v-loading="loading" stripe>
          <el-table-column prop="name" label="套餐名称" min-width="120" />
          <el-table-column prop="price" label="费用" width="90">
            <template #default="{ row }">
              <span style="color: #f56c6c; font-weight: bold;">¥{{ row.price }}</span>
            </template>
          </el-table-column>
          <el-table-column label="上行" width="80">
            <template #default="{ row }">
              {{ row.upload_speed }} M
            </template>
          </el-table-column>
          <el-table-column label="下行" width="80">
            <template #default="{ row }">
              {{ row.download_speed }} M
            </template>
          </el-table-column>
          <el-table-column label="公寓" width="100">
            <template #default="{ row }">
              {{ row.apartment ? row.apartment.name : '通用' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="70">
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'active' ? 'success' : 'danger'"
                size="small"
              >
                {{ row.status === "active" ? "正常" : "禁用" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="isAdmin"
                link
                type="primary"
                size="small"
                @click="handleEdit(row)"
              >
                <el-icon><Edit /></el-icon>
                <span>编辑</span>
              </el-button>
              <el-button
                v-if="isAdmin"
                link
                type="danger"
                size="small"
                @click="handleDelete(row)"
              >
                <el-icon><Delete /></el-icon>
                <span>删除</span>
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
          <div v-for="row in tableData" :key="row.id" class="plan-card">
            <div class="plan-card-header">
              <div class="plan-name">{{ row.name }}</div>
              <el-tag
                :type="row.status === 'active' ? 'success' : 'danger'"
                size="small"
              >
                {{ row.status === "active" ? "正常" : "禁用" }}
              </el-tag>
            </div>
            <div class="plan-card-body">
              <div class="plan-info-item">
                <span class="plan-info-label">费用：</span>
                <span class="plan-info-value price">¥{{ row.price }}</span>
              </div>
              <div class="plan-info-item">
                <span class="plan-info-label">上行：</span>
                <span class="plan-info-value">{{ row.upload_speed }} M</span>
              </div>
              <div class="plan-info-item">
                <span class="plan-info-label">下行：</span>
                <span class="plan-info-value">{{ row.download_speed }} M</span>
              </div>
              <div class="plan-info-item">
                <span class="plan-info-label">公寓：</span>
                <span class="plan-info-value">{{ row.apartment ? row.apartment.name : '通用' }}</span>
              </div>
              <div v-if="row.description" class="plan-info-item plan-description">
                <span class="plan-info-label">描述：</span>
                <span class="plan-info-value">{{ row.description }}</span>
              </div>
            </div>
            <div v-if="isAdmin" class="plan-card-footer">
              <el-button type="primary" size="small" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="95%"
      top="5vh"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top">
        <el-form-item label="套餐名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入套餐名称"
          />
        </el-form-item>
        <el-form-item label="套餐费用" prop="price">
          <el-input
            v-model="formData.price"
            placeholder="请输入套餐费用（元）"
            type="number"
          >
            <template #append>元</template>
          </el-input>
        </el-form-item>
        <el-form-item label="上行速率" prop="upload_speed">
          <el-input
            v-model.number="formData.upload_speed"
            placeholder="上行速率（单位：M）"
            type="number"
          >
            <template #append>M</template>
          </el-input>
        </el-form-item>
        <el-form-item label="下行速率" prop="download_speed">
          <el-input
            v-model.number="formData.download_speed"
            placeholder="下行速率（单位：M）"
            type="number"
          >
            <template #append>M</template>
          </el-input>
        </el-form-item>
        <el-form-item label="所属公寓" prop="apartment_id">
          <el-select
            v-model="formData.apartment_id"
            placeholder="请选择所属公寓（可选）"
            clearable
            style="width: 100%"
          >
            <el-option label="通用（所有公寓）" :value="null" />
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="套餐描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入套餐描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer-buttons">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="handleSubmit"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { getPlans, createPlan, updatePlan, deletePlan } from "./api";
import { getApartments } from "@/modules/apartment/api";
import { Plus, Search, Refresh, Edit, Delete, Loading } from "@element-plus/icons-vue";

const loading = ref(false);
const tableData = ref([]);
const dialogVisible = ref(false);
const submitLoading = ref(false);
const formRef = ref();
const currentId = ref(null);
const apartments = ref([]);

const isEdit = computed(() => !!currentId.value);
const dialogTitle = computed(() => isEdit.value ? "编辑套餐" : "新增套餐");

// 判断是否为管理员
const isAdmin = computed(() => {
  const role = localStorage.getItem('role')
  return role === 'admin'
})

const searchForm = reactive({
  keyword: "",
  status: null,
  apartment_id: null
});

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
});

const formData = reactive({
  name: "",
  price: "",
  upload_speed: null,
  download_speed: null,
  apartment_id: null,
  description: ""
});

const rules = {
  name: [{ required: true, message: "请输入套餐名称", trigger: "blur" }],
  price: [{ required: true, message: "请输入套餐费用", trigger: "blur" }],
  upload_speed: [{ required: true, message: "请输入上行速率", trigger: "blur" }],
  download_speed: [{ required: true, message: "请输入下行速率", trigger: "blur" }]
};

const loadApartments = async () => {
  try {
    // 如果是管理员，加载所有公寓；否则只加载自己关联的公寓
    const isAdminUser = localStorage.getItem('role') === 'admin'

    if (isAdminUser) {
      const res = await getApartments({ page: 1, page_size: 100, status: "active" });
      apartments.value = res.data || []
    } else {
      // 非管理员只能看到自己关联的公寓
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error("加载公寓列表失败:", error);
  }
};

const loadData = async () => {
  loading.value = true;
  try {
    const res = await getPlans({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword,
      status: searchForm.status,
      apartment_id: searchForm.apartment_id
    });
    tableData.value = res.data || [];
    pagination.total = res.total || 0;
  } catch (error) {
    console.error("加载数据失败:", error);
    ElMessage.error("加载套餐列表失败");
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.page = 1;
  loadData();
};

const handleReset = () => {
  searchForm.keyword = "";
  searchForm.status = null;
  searchForm.apartment_id = null;
  handleSearch();
};

const handleCreate = () => {
  currentId.value = null;
  formData.name = "";
  formData.price = "";
  formData.upload_speed = null;
  formData.download_speed = null;
  formData.apartment_id = null;
  formData.description = "";
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  currentId.value = row.id;
  formData.name = row.name;
  formData.price = row.price;
  formData.upload_speed = row.upload_speed;
  formData.download_speed = row.download_speed;
  formData.apartment_id = row.apartment_id;
  formData.description = row.description || "";
  dialogVisible.value = true;
};

const handleDialogClose = () => {
  // 只在创建模式下重置表单，编辑模式下保持数据
  if (!isEdit.value) {
    formRef.value?.resetFields();
  }
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        if (isEdit.value) {
          await updatePlan(currentId.value, formData);
          ElMessage.success("更新成功");
        } else {
          await createPlan(formData);
          ElMessage.success("创建成功");
        }
        dialogVisible.value = false;
        loadData();
      } catch (error) {
        console.error("提交失败:", error);
        ElMessage.error(error.response?.data?.detail || "操作失败，请重试");
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除套餐"${row.name}"吗？此操作不可恢复！`,
      "删除确认",
      { type: "warning" }
    );
    await deletePlan(row.id);
    ElMessage.success(`套餐"${row.name}"已成功删除`);
    loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
      ElMessage.error(error.response?.data?.detail || "删除失败");
    }
  }
};

onMounted(() => {
  loadApartments().then(() => {
    // 如果是非管理员，自动选择自己关联的公寓
    const isAdminUser = localStorage.getItem('role') === 'admin'
    if (!isAdminUser && apartments.value.length > 0) {
      searchForm.apartment_id = apartments.value[0].id
    }
  })
  loadData()
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.pagination-container {
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

.mobile-search .el-input {
  width: 100%;
}

.mobile-search .el-input__wrapper {
  padding: 8px 12px;
}

.mobile-search .el-input__inner {
  font-size: 15px;
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

.card-view {
  width: 100%;
}

.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 0;
}

.plan-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.plan-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.plan-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.plan-info-item {
  display: flex;
  align-items: baseline;
  font-size: 14px;
  line-height: 1.5;
}

.plan-info-label {
  color: #909399;
  min-width: 60px;
  flex-shrink: 0;
}

.plan-info-value {
  color: #303133;
}

.plan-info-value.price {
  color: #f56c6c;
  font-weight: bold;
  font-size: 18px;
}

.plan-description {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.plan-description .plan-info-value {
  color: #606266;
  font-size: 13px;
  padding-left: 0;
}

.plan-card-footer {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.plan-card-footer .el-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
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

/* 手机端样式优化 */
@media (max-width: 767px) {
  .page-container {
    padding: 10px;
  }

  .search-form {
    padding: 12px;
    margin-bottom: 15px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .page-title {
    font-size: 16px;
    font-weight: 600;
  }

  .el-button--small {
    padding: 6px 12px;
  }

  .el-button .el-icon {
    margin-right: 4px;
  }

  /* 手机端显示卡片视图和简化搜索 */
  .show-on-mobile {
    display: flex;
  }

  .hide-on-mobile {
    display: none;
  }

  .pagination-container {
    justify-content: center;
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
    padding: 20px 15px !important;
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
    min-height: 80px !important;
  }

  :deep(.el-select) {
    width: 100% !important;
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
