import request from '@/common/request'

/**
 * 获取审计日志列表
 */
export const getAuditLogs = (params) => {
  return request.get('/audit-logs/', { params })
}

/**
 * 获取审计日志详情
 */
export const getAuditLog = (id) => {
  return request.get(`/audit-logs/${id}`)
}

/**
 * 获取所有模块列表
 */
export const getModules = () => {
  return request.get('/audit-logs/modules')
}

/**
 * 获取所有操作类型
 */
export const getActions = () => {
  return request.get('/audit-logs/actions')
}

/**
 * 获取审计日志统计
 */
export const getStatistics = (days = 7) => {
  return request.get('/audit-logs/statistics', { params: { days } })
}
