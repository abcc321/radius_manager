import request from '@/common/request'

export function getApartments(params) {
  return request.get('/apartments/', { params })
}

export function getAllApartments() {
  return request.get('/apartments/', { page: 1, page_size: 1000 })
}

export function getApartment(id) {
  return request.get(`/apartments/${id}`)
}

export function createApartment(data) {
  return request.post('/apartments/', data)
}

export function updateApartment(id, data) {
  return request.put(`/apartments/${id}`, data)
}

export function deleteApartment(id) {
  return request.delete(`/apartments/${id}`)
}

export function disableApartment(id) {
  return request.post(`/apartments/${id}/disable`)
}

export function enableApartment(id) {
  return request.post(`/apartments/${id}/enable`)
}

export function getApartmentStats(id) {
  return request.get(`/apartments/${id}/stats`)
}

export function getApartmentOnlineUsers(id) {
  return request.get(`/apartments/${id}/online-users`)
}

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

export function getNasOnlineUsers(id) {
  return request.get(`/nas/${id}/online-users`)
}
