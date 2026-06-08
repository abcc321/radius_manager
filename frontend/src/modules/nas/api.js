import request from '@/common/request'

export function getNasDevices(params) {
  return request.get('/nas/', { params })
}

export function getNasDevice(id) {
  return request.get(`/nas/${id}`)
}

export function createNasDevice(data) {
  return request.post('/nas/', data)
}

export function updateNasDevice(id, data) {
  return request.put(`/nas/${id}`, data)
}

export function deleteNasDevice(id) {
  return request.delete(`/nas/${id}`)
}

export function testNasDevice(id) {
  return request.post(`/nas/${id}/test`)
}
