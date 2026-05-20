<template>
  <div class="dashboard">
    <h2 class="page-title">{{ $t('dashboard.title') }}</h2>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>{{ $t('dashboard.totalTasks') }}</template>
          <div class="stat-value">{{ overview.total_tasks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>DAG Nodes</template>
          <div class="stat-value">{{ overview.total_dag_nodes }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>Total Tokens</template>
          <div class="stat-value">{{ formatNumber(overview.total_tokens) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>Total Cost</template>
          <div class="stat-value">${{ overview.total_cost_usd.toFixed(4) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row -->
    <el-row :gutter="20" class="chart-row">
      <!-- Agent Stats -->
      <el-col :span="12">
        <el-card>
          <template #header>Agent Performance</template>
          <div class="chart-container">
            <v-chart :option="agentChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <!-- Cost Trend -->
      <el-col :span="12">
        <el-card>
          <template #header>Token Trend (7d)</template>
          <div class="chart-container">
            <v-chart :option="costChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Agent Table -->
    <el-card class="table-card">
      <template #header>Agent Statistics</template>
      <el-table :data="agentStats" stripe>
        <el-table-column prop="agent" label="Agent" width="150" />
        <el-table-column prop="executions" label="Executions" width="120" />
        <el-table-column prop="total_tokens" label="Tokens" width="120">
          <template #default="{ row }">{{ formatNumber(row.total_tokens) }}</template>
        </el-table-column>
        <el-table-column prop="total_cost_usd" label="Cost (USD)" width="120">
          <template #default="{ row }">${{ row.total_cost_usd.toFixed(4) }}</template>
        </el-table-column>
        <el-table-column prop="avg_latency_ms" label="Avg Latency" width="120">
          <template #default="{ row }">{{ row.avg_latency_ms }}ms</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getMetricsOverview, getAgentStats, getCostTrend } from '@/api/metrics'
import type { MetricsOverview, AgentStat, CostTrendItem } from '@/api/metrics'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const overview = ref<MetricsOverview>({
  total_tasks: 0,
  status_counts: {},
  total_tokens: 0,
  total_cost_usd: 0,
  total_dag_nodes: 0,
})
const agentStats = ref<AgentStat[]>([])
const costTrend = ref<CostTrendItem[]>([])

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return String(num)
}

const agentChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: agentStats.value.map(a => a.agent),
  },
  yAxis: [
    { type: 'value', name: 'Latency (ms)' },
  ],
  series: [
    {
      name: 'Avg Latency',
      type: 'bar',
      data: agentStats.value.map(a => a.avg_latency_ms),
      itemStyle: { color: '#409eff' },
    },
  ],
}))

const costChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: costTrend.value.map(c => c.date),
  },
  yAxis: { type: 'value', name: 'Tokens' },
  series: [
    {
      name: 'Tokens',
      type: 'line',
      data: costTrend.value.map(c => c.tokens),
      smooth: true,
      areaStyle: { opacity: 0.2 },
      itemStyle: { color: '#67c23a' },
    },
  ],
}))

async function fetchData() {
  try {
    overview.value = await getMetricsOverview()
  } catch {}
  try {
    agentStats.value = await getAgentStats()
  } catch {}
  try {
    costTrend.value = await getCostTrend(7)
  } catch {}
}

onMounted(fetchData)
</script>

<style scoped>
.dashboard { padding: 0; }
.page-title { margin-bottom: 20px; font-size: 22px; color: #303133; }
.stats-row { margin-bottom: 20px; }
.stat-value { font-size: 28px; font-weight: bold; color: #409eff; text-align: center; }
.chart-row { margin-bottom: 20px; }
.chart-container { height: 280px; }
.table-card { margin-top: 10px; }
</style>
