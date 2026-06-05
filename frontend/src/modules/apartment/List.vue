<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">公寓管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增公寓
          </el-button>
        </div>
      </template>

      <div class="search-form">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input
              v-model="searchForm.keyword"
              placeholder="编号/名称/地址"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="code" label="公寓编号" width="120" />
        <el-table-column prop="name" label="公寓名称" min-width="150" />
        <el-table-column prop="contact" label="联系人" width="100" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
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
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'active'"
              link
              type="warning"
              size="small"
              @click="handleDisable(row)"
            >
              停用
            </el-button>
            <el-button
              v-else-if="row.status === 'inactive'"
              link
              type="success"
              size="small"
              @click="handleEnable(row)"
            >
              启用
            </el-button>
            <el-button
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
      width="500px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
        <el-form-item label="公寓编号" prop="code">
          <el-input
            v-model="formData.code"
            :disabled="isEdit"
            placeholder="请输入公寓编号"
          />
        </el-form-item>
        <el-form-item label="公寓名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入公寓名称"
          />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input
            v-model="formData.contact"
            placeholder="请输入联系人"
          />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input
            v-model="formData.phone"
            placeholder="请输入联系电话"
          />
        </el-form-item>
        <el-form-item label="地址">
          <el-input
            v-model="formData.address"
            type="textarea"
            placeholder="请输入地址"
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
import { getApartments, createApartment, updateApartment, deleteApartment, disableApartment, enableApartment } from "./api";

const loading = ref(false);
const tableData = ref([]);
const dialogVisible = ref(false);
const submitLoading = ref(false);
const formRef = ref();
const currentId = ref(null);

const isEdit = computed(() => !!currentId.value);
const dialogTitle = computed(() => isEdit.value ? "编辑公寓" : "新增公寓");

const searchForm = reactive({
  keyword: ""
});

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
});

const formData = reactive({
  code: "",
  name: "",
  contact: "",
  phone: "",
  address: ""
});

const rules = {
  code: [{ required: true, message: "请输入公寓编号", trigger: "blur" }],
  name: [{ required: true, message: "请输入公寓名称", trigger: "blur" }]
};

const loadData = async () => {
  loading.value = true;
  try {
    const res = await getApartments({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: searchForm.keyword
    });
    tableData.value = res.data || [];
    pagination.total = res.total || 0;
  } catch (error) {
    console.error("加载数据失败:", error);
    ElMessage.error("加载公寓列表失败");
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
  loadData();
};

const handleCreate = () => {
  currentId.value = null;
  formData.code = "";
  formData.name = "";
  formData.contact = "";
  formData.phone = "";
  formData.address = "";
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  currentId.value = row.id;
  formData.code = row.code;
  formData.name = row.name;
  formData.contact = row.contact || "";
  formData.phone = row.phone || "";
  formData.address = row.address || "";
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
          await updateApartment(currentId.value, formData);
          ElMessage.success("更新成功");
        } else {
          await createApartment(formData);
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

const handleDisable = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要停用公寓"${row.name}"吗？`,
      "提示",
      { type: "warning" }
    );
    await disableApartment(row.id);
    ElMessage.success("停用成功");
    loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("停用失败:", error);
      ElMessage.error(error.response?.data?.detail || "停用失败");
    }
  }
};

const handleEnable = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要启用公寓"${row.name}"吗？`,
      "提示",
      { type: "warning" }
    );
    await enableApartment(row.id);
    ElMessage.success("启用成功");
    loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("启用失败:", error);
      ElMessage.error(error.response?.data?.detail || "启用失败");
    }
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除公寓"${row.name}"吗？删除后将不再显示在列表中。`,
      "删除确认",
      { type: "warning" }
    );
    await deleteApartment(row.id);
    ElMessage.success(`公寓"${row.name}"已成功删除`);
    loadData();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
      ElMessage.error(error.response?.data?.detail || "删除失败");
    }
  }
};

onMounted(() => {
  loadData();
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
