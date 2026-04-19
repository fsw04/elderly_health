<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getReportDetail, getReports, updateReportDoctorSummary } from '../api'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const query = reactive({ q: '', riskLevel: '', page: 1, pageSize: 10 })
const drawerVisible = ref(false)
const reportDetail = ref<any>(null)
const doctorSummarySaving = ref(false)
const doctorSummaryForm = reactive({
  height: '',
  weight: '',
  bmi: '',
  bloodPressure: '',
  fastingBloodGlucose: '',
  ecgFinding: '',
  bUltrasound: '',
  tcmConstitution: '',
})

function hydrateDoctorSummaryForm() {
  const summary = reportDetail.value?.contentJson?.doctorSummary || {}
  doctorSummaryForm.height = summary.height || ''
  doctorSummaryForm.weight = summary.weight || ''
  doctorSummaryForm.bmi = summary.bmi || ''
  doctorSummaryForm.bloodPressure = summary.bloodPressure || ''
  doctorSummaryForm.fastingBloodGlucose = summary.fastingBloodGlucose || ''
  doctorSummaryForm.ecgFinding = summary.ecgFinding || ''
  doctorSummaryForm.bUltrasound = summary.bUltrasound || ''
  doctorSummaryForm.tcmConstitution = summary.tcmConstitution || ''
}

async function loadData() {
  if (query.page < 1) query.page = 1
  loading.value = true
  try {
    const res = await getReports(query)
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

async function openDetail(id: string) {
  const res = await getReportDetail(id)
  reportDetail.value = res.data
  hydrateDoctorSummaryForm()
  drawerVisible.value = true
}

async function saveDoctorSummary() {
  if (!reportDetail.value?.id) return
  doctorSummarySaving.value = true
  try {
    const payload = {
      height: doctorSummaryForm.height,
      weight: doctorSummaryForm.weight,
      bmi: doctorSummaryForm.bmi,
      bloodPressure: doctorSummaryForm.bloodPressure,
      fastingBloodGlucose: doctorSummaryForm.fastingBloodGlucose,
      ecgFinding: doctorSummaryForm.ecgFinding,
      bUltrasound: doctorSummaryForm.bUltrasound,
      tcmConstitution: doctorSummaryForm.tcmConstitution,
    }
    const res = await updateReportDoctorSummary(reportDetail.value.id, payload)
    reportDetail.value = res.data
    hydrateDoctorSummaryForm()
    ElMessage.success('体检信息已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    doctorSummarySaving.value = false
  }
}

function ruleHitRows() {
  return reportDetail.value?.contentJson?.ruleHits || []
}

function sectionRows() {
  const sections = reportDetail.value?.contentJson?.sections
  if (!sections) return []
  if (Array.isArray(sections)) return sections
  if (typeof sections === 'object') {
    return Object.keys(sections).map((key) => ({
      key,
      title: key,
      items: Array.isArray(sections[key]) ? sections[key] : [sections[key]],
    }))
  }
  return []
}

function sectionItems(section: any) {
  if (!section) return []
  if (Array.isArray(section.items)) return section.items
  if (Array.isArray(section.rows)) return section.rows
  if (Array.isArray(section.metrics)) return section.metrics
  return []
}

function levelTagType(level: string) {
  const val = String(level || '').toLowerCase()
  if (val.includes('danger') || val.includes('high') || val === 'h') return 'danger'
  if (val.includes('medium') || val.includes('mid') || val === 'm') return 'warning'
  if (val.includes('low') || val === 'l') return 'info'
  return 'info'
}

function abnormalRows() {
  const items = reportDetail.value?.contentJson?.abnormalities || []
  const score = (level: string) => {
    const val = String(level || '').toLowerCase()
    if (val.includes('danger')) return 0
    if (val.includes('high') || val === 'h') return 1
    if (val.includes('medium') || val === 'm') return 2
    if (val.includes('low') || val === 'l') return 3
    return 9
  }
  return [...items].sort((a, b) => score(a.level) - score(b.level))
}

function suggestionRows() {
  const suggestions = reportDetail.value?.contentJson?.suggestions
  if (!suggestions) return []
  if (Array.isArray(suggestions)) {
    return suggestions.map((item: any, idx: number) =>
      typeof item === 'string' ? { id: idx + 1, text: item } : { id: idx + 1, ...item }
    )
  }
  if (typeof suggestions === 'object') {
    return Object.keys(suggestions).map((key, idx) => ({
      id: idx + 1,
      category: key,
      text: Array.isArray(suggestions[key]) ? suggestions[key].join('；') : String(suggestions[key]),
    }))
  }
  return []
}

function suggestionsText() {
  const rows = suggestionRows()
  return rows
    .map((row: any, idx: number) => {
      const prefix = row.category ? `[${row.category}] ` : ''
      return `${idx + 1}. ${prefix}${row.text || ''}`
    })
    .join('\n')
}

async function copySuggestions() {
  const text = suggestionsText()
  if (!text) {
    ElMessage.warning('暂无建议可复制')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('建议已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

function exportReportJson() {
  if (!reportDetail.value) {
    ElMessage.warning('暂无报告可导出')
    return
  }
  const fileName = `${reportDetail.value.id || 'report'}.json`
  const content = JSON.stringify(reportDetail.value, null, 2)
  const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

function doctorSummaryValue(key: string) {
  const summary = reportDetail.value?.contentJson?.doctorSummary || {}
  const value = summary[key]
  return formatDoctorSummaryValue(key, value)
}

function formatDoctorSummaryValue(key: string, value: any) {
  const raw = String(value || '').trim()
  if (!raw) return '--'
  const lowered = raw.toLowerCase()
  if (key === 'height' && !lowered.includes('cm') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} cm`
  if (key === 'weight' && !lowered.includes('kg') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} kg`
  if (key === 'bmi' && !lowered.includes('kg/m') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} kg/m²`
  if (key === 'bloodPressure' && !lowered.includes('mmhg') && /^\d+\s*\/\s*\d+$/.test(raw)) return `${raw} mmHg`
  if (key === 'fastingBloodGlucose' && !lowered.includes('mmol/l') && /^\d+(\.\d+)?$/.test(raw)) return `${raw} mmol/L`
  return raw
}

function printReport() {
  if (!reportDetail.value) {
    ElMessage.warning('暂无报告可打印')
    return
  }
  const detail = reportDetail.value
  const printTime = new Date().toLocaleString()
  const traceNo = `REP-${detail.id || 'UNKNOWN'}`
  const summary = detail.contentJson?.summary?.text || '--'
  const risk = detail.riskLevel || '--'
  const doctorSummary = detail.contentJson?.doctorSummary || {}
  const ds = (k: string) => formatDoctorSummaryValue(k, doctorSummary[k])
  const doctorSummaryTable = `
    <table border="1" cellspacing="0" cellpadding="6" style="width:100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 8px;">
      <tr>
        <td><b>身高</b></td><td>${ds('height')}</td>
        <td><b>体重</b></td><td>${ds('weight')}</td>
        <td><b>BMI</b></td><td>${ds('bmi')}</td>
      </tr>
      <tr>
        <td><b>血压</b></td><td>${ds('bloodPressure')}</td>
        <td><b>空腹血糖</b></td><td colspan="3">${ds('fastingBloodGlucose')}</td>
      </tr>
      <tr>
        <td><b>心电</b></td><td colspan="5">${ds('ecgFinding')}</td>
      </tr>
      <tr>
        <td><b>B超</b></td><td colspan="5">${ds('bUltrasound')}</td>
      </tr>
      <tr>
        <td><b>中医体质辨识</b></td><td colspan="5">${ds('tcmConstitution')}</td>
      </tr>
    </table>
  `
  const abnormalList = abnormalRows()
    .map((item: any) => `<li>${item.name || item.code || '--'}（${item.level || '--'}）：${item.text || '--'}</li>`)
    .join('')
  const suggestionList = suggestionRows()
    .map((item: any) => `<li>${item.category ? `[${item.category}] ` : ''}${item.text || '--'}</li>`)
    .join('')
  const html = `
    <html>
      <head>
        <meta charset="utf-8" />
        <title>报告打印 - ${detail.id || ''}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 24px; color: #222; line-height: 1.6; }
          .header { border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-bottom: 12px; }
          .footer { border-top: 1px solid #ddd; margin-top: 16px; padding-top: 8px; color: #666; font-size: 12px; display: flex; justify-content: space-between; }
          .page-no::after { content: counter(page); }
          .section { page-break-inside: avoid; break-inside: avoid; }
          ul, li { page-break-inside: avoid; break-inside: avoid; }
          .sign-box { margin-top: 24px; display: flex; justify-content: space-between; gap: 16px; }
          .sign-item { flex: 1; border-top: 1px solid #ccc; padding-top: 8px; min-height: 48px; }
          .note-box { margin-top: 12px; border: 1px dashed #bbb; min-height: 60px; padding: 8px; }
          h2 { margin: 0 0 8px; }
          h3 { margin: 12px 0 8px; }
          .line { margin: 6px 0; }
          @media print {
            body { padding: 12px; }
            .footer { position: fixed; bottom: 8px; left: 12px; right: 12px; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h2>体检报告（医生视图）</h2>
          <div>打印时间：${printTime}</div>
          <div>追踪号：${traceNo}</div>
        </div>
        <div class="line">报告ID：${detail.id || '--'}</div>
        <div class="line">会话ID：${detail.sessionId || '--'}</div>
        <div class="line">风险等级：${risk}</div>
        <div class="line">摘要：${summary}</div>
        <div class="section">
          <h3>基础体检信息</h3>
          ${doctorSummaryTable}
        </div>
        <div class="section">
          <h3>异常项</h3>
          <ul>${abnormalList || '<li>暂无异常项</li>'}</ul>
        </div>
        <div class="section">
          <h3>建议</h3>
          <ul>${suggestionList || '<li>暂无建议</li>'}</ul>
        </div>
        <div class="section">
          <h3>医生备注</h3>
          <div class="note-box"></div>
          <div class="sign-box">
            <div class="sign-item">医生签名：</div>
            <div class="sign-item">家属签名：</div>
          </div>
        </div>
        <div class="footer">
          <span>老人健康管理系统 · 医生端打印件 · ${traceNo}</span>
          <span>第 <span class="page-no"></span> 页</span>
        </div>
      </body>
    </html>
  `
  const win = window.open('', '_blank')
  if (!win) {
    ElMessage.error('浏览器拦截了打印窗口')
    return
  }
  win.document.write(html)
  win.document.close()
  win.focus()
  win.print()
}
</script>

<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>报告管理</span>
        <div class="toolbar-right">
          <el-input v-model="query.q" placeholder="按用户搜索" style="width: 220px" />
          <el-select v-model="query.riskLevel" placeholder="风险等级" clearable style="width: 140px">
            <el-option value="low" label="低风险" />
            <el-option value="medium" label="中风险" />
            <el-option value="high" label="高风险" />
          </el-select>
          <el-button type="primary" @click="doSearch">筛选</el-button>
        </div>
      </div>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="报告ID" />
      <el-table-column prop="userId" label="用户ID" width="100" />
      <el-table-column prop="sessionId" label="会话ID" />
      <el-table-column label="风险等级" width="120">
        <template #default="{ row }">
          <el-tag :type="row.riskLevel === 'high' ? 'danger' : row.riskLevel === 'medium' ? 'warning' : 'info'">
            {{ row.riskLevel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="190" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDetail(row.id)">详情</el-button>
        </template>
      </el-table-column>
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

  <el-drawer v-model="drawerVisible" title="报告详情" size="45%">
    <div v-if="reportDetail">
      <p><b>报告ID：</b>{{ reportDetail.id }}</p>
      <p><b>会话ID：</b>{{ reportDetail.sessionId }}</p>
      <p><b>风险等级：</b>{{ reportDetail.riskLevel }}</p>
      <div style="margin-top: 8px; margin-bottom: 12px;">
        <el-button size="small" @click="copySuggestions">复制建议</el-button>
        <el-button size="small" @click="exportReportJson">导出JSON</el-button>
        <el-button size="small" @click="printReport">打印简版</el-button>
      </div>
      <p style="margin-top: 12px"><b>摘要：</b>{{ reportDetail.contentJson?.summary?.text || '--' }}</p>
      <p style="margin-top: 12px"><b>基础体检信息：</b></p>
      <el-form label-width="120px" size="small">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="身高">
              <el-input v-model="doctorSummaryForm.height" placeholder="如：153.5 cm" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="体重">
              <el-input v-model="doctorSummaryForm.weight" placeholder="如：43.6 kg" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="BMI">
              <el-input v-model="doctorSummaryForm.bmi" placeholder="如：18.5 kg/m²" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12">
            <el-form-item label="血压">
              <el-input v-model="doctorSummaryForm.bloodPressure" placeholder="如：115/71 mmHg" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="空腹血糖">
              <el-input v-model="doctorSummaryForm.fastingBloodGlucose" placeholder="如：5.23 mmol/L" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="心电">
          <el-input
            v-model="doctorSummaryForm.ecgFinding"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="未收集可留空"
          />
        </el-form-item>
        <el-form-item label="B超">
          <el-input
            v-model="doctorSummaryForm.bUltrasound"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="未收集可留空"
          />
        </el-form-item>
        <el-form-item label="中医体质辨识">
          <el-input
            v-model="doctorSummaryForm.tcmConstitution"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="未收集可留空"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="doctorSummarySaving" @click="saveDoctorSummary">保存基础体检信息</el-button>
        </el-form-item>
      </el-form>
      <el-descriptions :column="3" border size="small" style="margin-bottom: 12px;">
        <el-descriptions-item label="身高">{{ doctorSummaryValue('height') }}</el-descriptions-item>
        <el-descriptions-item label="体重">{{ doctorSummaryValue('weight') }}</el-descriptions-item>
        <el-descriptions-item label="BMI">{{ doctorSummaryValue('bmi') }}</el-descriptions-item>
        <el-descriptions-item label="血压">{{ doctorSummaryValue('bloodPressure') }}</el-descriptions-item>
        <el-descriptions-item label="空腹血糖" :span="2">{{ doctorSummaryValue('fastingBloodGlucose') }}</el-descriptions-item>
        <el-descriptions-item label="心电" :span="3">{{ doctorSummaryValue('ecgFinding') }}</el-descriptions-item>
        <el-descriptions-item label="B超" :span="3">{{ doctorSummaryValue('bUltrasound') }}</el-descriptions-item>
        <el-descriptions-item label="中医体质辨识" :span="3">{{ doctorSummaryValue('tcmConstitution') }}</el-descriptions-item>
      </el-descriptions>
      <p style="margin-top: 12px"><b>异常项：</b></p>
      <el-table :data="abnormalRows()" border size="small" empty-text="暂无异常项">
        <el-table-column prop="name" label="异常项" />
        <el-table-column prop="code" label="编码" width="140" />
        <el-table-column label="等级" width="100">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)">{{ row.level || '--' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="text" label="说明" />
      </el-table>
      <p style="margin-top: 12px"><b>规则命中（医生视角）：</b></p>
      <el-table :data="ruleHitRows()" border size="small" empty-text="暂无规则命中数据">
        <el-table-column prop="ruleCode" label="规则编码" width="160" />
        <el-table-column prop="name" label="规则名称" />
        <el-table-column label="等级" width="100">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)">{{ row.level || '--' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="说明" />
      </el-table>
      <p style="margin-top: 12px"><b>指标分组（sections）：</b></p>
      <el-collapse>
        <el-collapse-item
          v-for="(section, idx) in sectionRows()"
          :key="section.key || idx"
          :name="section.key || idx"
          :title="section.title || section.key || `分组${idx + 1}`"
        >
          <el-table :data="sectionItems(section)" border size="small" empty-text="该分组暂无指标">
            <el-table-column prop="name" label="指标名" />
            <el-table-column prop="code" label="编码" width="140" />
            <el-table-column prop="value" label="数值" width="120" />
            <el-table-column prop="unit" label="单位" width="100" />
            <el-table-column label="等级" width="100">
              <template #default="{ row }">
                <el-tag :type="levelTagType(row.level)">{{ row.level || '--' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
      <p style="margin-top: 12px"><b>建议（suggestions）：</b></p>
      <el-table :data="suggestionRows()" border size="small" empty-text="暂无建议">
        <el-table-column prop="category" label="分类" width="140" />
        <el-table-column prop="text" label="建议内容" />
      </el-table>
    </div>
  </el-drawer>
</template>
