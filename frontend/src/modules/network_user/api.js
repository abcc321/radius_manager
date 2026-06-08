import request from "@/common/request";

export function getNetworkUsers(params) {
  return request({
    url: "/network_users/",
    method: "get",
    params
  });
}

export function getAllNetworkUsers(params) {
  return request({
    url: "/network_users/all",
    method: "get",
    params
  });
}

export function getNetworkUserDetail(id) {
  return request({
    url: `/network_users/${id}`,
    method: "get"
  });
}

export function createNetworkUser(data) {
  return request({
    url: "/network_users/",
    method: "post",
    data
  });
}

export function updateNetworkUser(id, data) {
  return request({
    url: `/network_users/${id}`,
    method: "put",
    data
  });
}

export function updateNetworkUserPassword(id, data) {
  return request({
    url: `/network_users/${id}/password`,
    method: "put",
    data
  });
}

export function activateNetworkUser(id) {
  return request({
    url: `/network_users/${id}/activate`,
    method: "post"
  });
}

export function deactivateNetworkUser(id) {
  return request({
    url: `/network_users/${id}/deactivate`,
    method: "post"
  });
}

export function deleteNetworkUser(id) {
  return request({
    url: `/network_users/${id}`,
    method: "delete"
  });
}

export function exportNetworkUsers(params) {
  return request({
    url: "/network_users/export-users",
    method: "get",
    params,
    responseType: "blob"
  });
}

export function importNetworkUsers(formData) {
  return request({
    url: "/network_users/import-users",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
}

export function getApartments(params) {
  return request({
    url: "/apartments/",
    method: "get",
    params
  });
}

export function getAllPlans(params) {
  return request({
    url: "/plans/all",
    method: "get",
    params
  });
}

export function createFaultReport(data) {
  return request({
    url: "/fault/reports",
    method: "post",
    data
  });
}

export function getCurrentOperator() {
  return request({
    url: "/operators/me",
    method: "get"
  });
}
