from enum import Enum


class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    API_CLIENT = "api_client"
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"
