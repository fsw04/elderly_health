<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { getAudit } from '../api'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const query = reactive({ targetType: '', targetId: '', page: 1, pageSize: 10 })

async function loadData() {
  if (query.page < 1) query.page = 1
  loading.value = true
  try {
    const res = await getAudit(query)
    rows.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

function doSearch() {
  query.page = 1
  loadData()
}

function handlePageChange(page: number) {
  query.page = page > 0 ? page : 1
  loadData()
}
</script>

<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>审计日志</span>
        <div class="toolbar-right">
          <el-input v-model="query.targetType" placeholder="targetType" style="width: 140px" />
          <el-input v-model="query.targetId" placeholder="targetId" style="width: 140px" />
          <el-button type="primary" @click="doSearch">筛选</el-button>
        </div>
      </div>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="adminId" label="医生ID" width="100" />
      <el-table-column prop="action" label="动作" />
      <el-table-column prop="targetType" label="目标类型" />
      <el-table-column prop="targetId" label="目标ID" />
      <el-table-column prop="createdAt" label="时间" width="190" />
    </el-table>
    <el-pagination
      v-model:current-page="query.page"
      :page-size="query.pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="pager"
      @current-change="handlePageChange"
    />
  </el-card>
</template>
