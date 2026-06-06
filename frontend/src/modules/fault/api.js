import request from '@/common/request'

// 创建故障报告
export function createFaultReport(data) {
  return request({
    url: '/fault/reports',
    method: 'post',
    data
  })
}

// 获取故障报告列表
export function getFaultReports(params) {
  return request({
    url: '/fault/reports',
    method: 'get',
    params
  })
}

// 获取故障报告详情
export function getFaultReportDetail(id) {
  return request({
    url: `/fault/reports/${id}`,
    method: 'get'
  })
}

// 更新故障报告
export function updateFaultReport(id, data) {
  return request({
    url: `/fault/reports/${id}`,
    method: 'put',
    data
  })
}

// 删除故障报告
export function deleteFaultReport(id) {
  return request({
    url: `/fault/reports/${id}`,
    method: 'delete'
  })
}

// 获取故障统计
export function getFaultStatistics() {
  return request({
    url: '/fault/statistics',
    method: 'get'
  })
}

// 获取公寓列表
export function getApartments(params) {
  return request({
    url: '/apartments/',
    method: 'get',
    params
  })
}
