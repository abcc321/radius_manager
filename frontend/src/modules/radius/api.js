import request from '@/common/request'

export function getServerStatus() {
  return request({
    url: '/radius/server-status',
    method: 'get'
  })
}

export function getRadiusLogs(params) {
  return request({
    url: '/radius/logs',
    method: 'get',
    params
  })
}

export function getLogsStats(params) {
  return request({
    url: '/radius/logs/stats',
    method: 'get',
    params
  })
}

export function deleteLog(logId) {
  return request({
    url: `/radius/logs/${logId}`,
    method: 'delete'
  })
}

export function clearLogs(params) {
  return request({
    url: '/radius/logs',
    method: 'delete',
    params
  })
}

export function exportLogs(params) {
  return request({
    url: '/radius/logs/export',
    method: 'get',
    params
  })
}
