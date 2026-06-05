import request from '@/common/request'

export function generateBill(params) {
  return request.post('/billing/generate/', null, { params })
}

export function getBillRecords(params) {
  return request.get('/billing/records/', { params })
}

export function getBillRecord(record_id) {
  return request.get(`/billing/records/${record_id}/`)
}

export function getBillDetails(record_id) {
  return request.get(`/billing/records/${record_id}/details/`)
}

export function deleteBill(record_id) {
  return request.delete(`/billing/records/${record_id}/`)
}

export function downloadBill(record_id) {
  return request.get(`/billing/records/${record_id}/download/`, {
    responseType: 'blob'
  })
}

export function getBillingApartments() {
  return request.get('/billing/apartments/')
}
