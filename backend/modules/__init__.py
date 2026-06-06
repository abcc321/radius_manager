from modules.auth.api import router as auth_router
from modules.operator.api import router as operator_router
from modules.apartment.api import router as apartment_router
from modules.nas.api import router as nas_router
from modules.config.api import router as config_router
from modules.radius.api import router as radius_router
from modules.plan.api import router as plan_router
from modules.network_user.api import router as network_user_router
from modules.online_user.api import router as online_user_router
from modules.billing.api_new import router as billing_router
from modules.warning.api import router as warning_router
from modules.audit_log.api import router as audit_log_router
from modules.fault.api import router as fault_router

__all__ = ["auth_router", "operator_router", "apartment_router", "nas_router", "config_router", "radius_router", "plan_router", "network_user_router", "online_user_router", "billing_router", "warning_router", "audit_log_router", "fault_router"]
