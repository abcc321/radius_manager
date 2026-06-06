"""
RADIUS网络计费管理系统
启动自检功能已模块化到 startup_check.py
"""

import os
import sys
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from common import init_db
from modules import auth_router, operator_router, apartment_router, nas_router, config_router, radius_router, plan_router, network_user_router, online_user_router, billing_router, warning_router, audit_log_router, fault_router
from startup_check import run_startup_checks
from websocket_manager import manager

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="公寓网络用户管理、计费、监控和分析平台"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix="/api")
app.include_router(operator_router, prefix="/api")
app.include_router(apartment_router, prefix="/api")
app.include_router(nas_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(radius_router, prefix="/api")
app.include_router(plan_router, prefix="/api")
app.include_router(network_user_router, prefix="/api")
app.include_router(online_user_router, prefix="/api")
app.include_router(billing_router, prefix="/api")
app.include_router(warning_router, prefix="/api")
app.include_router(audit_log_router, prefix="/api")
app.include_router(fault_router, prefix="/api")

@app.on_event("startup")
async def startup():
    init_db()
    from startup_check import p_success, p_info, Colors

    from nas_monitor import start_monitor
    import threading

    monitor_thread = threading.Thread(target=start_monitor, daemon=True)
    monitor_thread.start()
    print("[OK] NAS设备监控服务已启动")

    from radius_server import start_radius_server, get_radius_server
    radius_thread = threading.Thread(target=start_radius_server, daemon=True)
    radius_thread.start()
    time.sleep(0.5)

    radius_server = get_radius_server()
    if radius_server and radius_server.is_running():
        print("[OK] RADIUS服务器已启动 (监听 1812/1813 端口)")

        await manager.broadcast_radius_status({
            "is_running": True,
            "host": radius_server.host,
            "auth_port": radius_server.auth_port,
            "acct_port": radius_server.acct_port
        })
    else:
        print("[ERROR] RADIUS服务器启动失败")
        await manager.broadcast_radius_status({
            "is_running": False,
            "host": "0.0.0.0",
            "auth_port": 1812,
            "acct_port": 1813
        })

    p_success(f"{settings.APP_NAME} v{settings.VERSION} 启动成功")
    p_info("API文档: http://localhost:8000/docs")


@app.websocket("/ws/radius")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "radius")
    try:
        radius_server = None
        try:
            from radius_server import get_radius_server
            radius_server = get_radius_server()
        except:
            pass

        if radius_server:
            await websocket.send_json({
                "type": "radius_status",
                "data": {
                    "is_running": radius_server.is_running(),
                    "host": radius_server.host,
                    "auth_port": radius_server.auth_port,
                    "acct_port": radius_server.acct_port
                }
            })

        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    finally:
        manager.disconnect(websocket, "radius")

@app.get("/")
async def root():
    return {"message": "欢迎使用RADIUS网络计费管理系统API", "version": settings.VERSION}

@app.get("/health")
async def health():
    return {"status": "healthy"}

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    success = run_startup_checks(port)
    
    if not success:
        print("⚠️  警告：部分检查未通过，继续启动...")
    
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
