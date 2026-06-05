<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">套餐管理</span>
          <el-button v-if="isAdmin" type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增套餐
          </el-button>
        </div>
      </template>

      <div class="search-form">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="名称/描述"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="公寓">
            <el-select
              v-model="searchForm.apartment_id"
              placeholder="全部公寓"
              clearable
              @change="handleSearch"
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
            <el-select v-model="searchForm.status" placeholder="全部状态" clearable @change="handleSearch">
              <el-option label="全部" :value="null" />
              <el-option label="正常" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="套餐名称" min-width="120" />
        <el-table-column prop="price" label="套餐费用" width="120">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: bold;">¥{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column label="上行速率" width="120">
          <template #default="{ row }">
            {{ row.upload_speed }} M
          </template>
        </el-table-column>
        <el-table-column label="下行速率" width="120">
          <template #default="{ row }">
            {{ row.download_speed }} M
          </template>
        </el-table-column>
        <el-table-column label="所属公寓" width="150">
          <template #default="{ row }">
            {{ row.apartment ? row.apartment.name : '通用' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'active' ? 'success' : 'danger'"
              size="small"
            >
              {{ row.status === "active" ? "正常" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="isAdmin"
              link
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="isAdmin"
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
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
            placeholder="请输入上行速率（单位：M）"
            type="number"
          >
            <template #append>M</template>
          </el-input>
        </el-form-item>
        <el-form-item label="下行速率" prop="download_speed">
          <el-input
            v-model.number="formData.download_speed"
            placeholder="请输入下行速率（单位：M）"
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitLoading"
          @click="handleSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { getPlans, createPlan, updatePlan, deletePlan } from "./api";
import { getApartments } from "@/modules/apartment/api";

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
    const isAdmin = localStorage.getItem('role') === 'admin'

    if (isAdmin) {
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
  formRef.value?.resetFields();
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
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (!isAdmin && apartments.value.length > 0) {
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
</style>
