import request from '@/common/request'

export function getBillingSummary(params) {
  return request.get('/billing/bills/', { params })
}

export function getBillingDetails(apartment_id, params) {
  return request.get(`/billing/bills/${apartment_id}/details/`, { params })
}

export function exportBillingExcel(params) {
  return request.get('/billing/bills/export/', {
    params,
    responseType: 'blob'
  })
}

export function getBillingApartments() {
  return request.get('/billing/apartments/')
}
