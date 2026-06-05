import dayjs from 'dayjs'

export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''
  return dayjs(date).format(format)
}

export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return ''
  return dayjs(date).format(format)
}

export function parseDate(date, format = 'YYYY-MM-DD') {
  return dayjs(date, format).toDate()
}

export function getPageParams(params = {}) {
  const { page = 1, pageSize = 20, ...rest } = params
  return {
    page: Number(page),
    page_size: Number(pageSize),
    ...rest
  }
}

export function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '0'
  return Number(num).toFixed(decimals)
}

export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

export function debounce(func, wait = 300) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

export function downloadFile(url, filename) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
