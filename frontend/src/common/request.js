import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from './router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(
  config => {
    const url = config.url || ''
    const role = localStorage.getItem('role')
    const operator_id = localStorage.getItem('operator_id')
    const username = localStorage.getItem('username')
    const apartment_id = localStorage.getItem('apartment_id')

    // 设置请求头，传递操作员信息
    if (role) {
      config.headers['X-Operator-Role'] = role
    }
    if (operator_id) {
      config.headers['X-Operator-Id'] = operator_id
    }
    if (username) {
      config.headers['X-Operator-Username'] = username
    }

    // 根据角色自动过滤数据
    // 非管理员（operator）只能看到自己关联公寓的数据
    if (role !== 'admin' && apartment_id) {
      // 套餐、网络用户、在线用户、预警等接口自动带上 apartment_id
      const filteredUrls = [
        '/plans',
        '/network_users',
        '/online-users',
        '/warnings',
        '/billing'
      ]

      const shouldFilter = filteredUrls.some(filteredUrl => url.includes(filteredUrl))

      if (shouldFilter) {
        config.params = config.params || {}
        config.params.apartment_id = parseInt(apartment_id)
      }
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        ElMessage.error('未登录或登录已过期')
        localStorage.clear()
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error('权限不足')
      } else if (status === 404) {
        ElMessage.error('资源不存在')
      } else {
        ElMessage.error(data.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
