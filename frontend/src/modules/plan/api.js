import request from "@/common/request";

export function getPlans(params) {
  return request({
    url: "/plans/",
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

export function getPlan(id) {
  return request({
    url: `/plans/${id}`,
    method: "get"
  });
}

export function createPlan(data) {
  return request({
    url: "/plans/",
    method: "post",
    data
  });
}

export function updatePlan(id, data) {
  return request({
    url: `/plans/${id}`,
    method: "put",
    data
  });
}

export function deletePlan(id) {
  return request({
    url: `/plans/${id}`,
    method: "delete"
  });
}

export function enablePlan(id) {
  return request({
    url: `/plans/${id}/enable`,
    method: "post"
  });
}

export function disablePlan(id) {
  return request({
    url: `/plans/${id}/disable`,
    method: "post"
  });
}
