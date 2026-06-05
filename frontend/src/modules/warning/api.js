import request from '@/common/request'

export const getInactiveUsers = (params) => {
  return request.get('/warnings/inactive-users', { params })
}

export const getFrequentDialingUsers = (params) => {
  return request.get('/warnings/frequent-dialing', { params })
}

export const getWarningStatistics = (params) => {
  return request.get('/warnings/statistics', { params })
}
