import request from '@/common/request'

export function getOnlineUsers(params) {
  return request({
    url: '/online-users/list',
    method: 'get',
    params
  })
}

export function getOnlineStatistics(params) {
  return request({
    url: '/online-users/statistics',
    method: 'get',
    params
  })
}

export function getUserDetail(sessionId) {
  return request({
    url: `/online-users/${sessionId}`,
    method: 'get'
  })
}

export function kickUser(data) {
  return request({
    url: '/online-users/kick',
    method: 'post',
    data
  })
}
