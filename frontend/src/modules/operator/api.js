import request from '@/common/request'

export function getOperators(params) {
  return request.get('/operators/', { params })
}

export function getOperator(id) {
  return request.get(`/operators/${id}`)
}

export function createOperator(data) {
  return request.post('/operators/', data)
}

export function updateOperator(id, data) {
  return request.put(`/operators/${id}`, data)
}

export function deleteOperator(id) {
  return request.delete(`/operators/${id}`)
}

export function changePassword(id, data) {
  return request.put(`/operators/${id}/password`, data)
}

export function assignApartments(id, data) {
  return request.put(`/operators/${id}/apartments`, data)
}

export function getApartments(params) {
  return request.get('/apartments/', { params })
}
