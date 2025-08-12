PERMISSION_LABELS = {
    "can_manage_products": "Manage Products",
    "can_manage_sales": "Manage Sales",
    "can_manage_managers": "Manage Managers",
    "can_view_analytics": "View Analytics",
    "can_manage_shop_settings": "Manage Shop Settings",
}

def default_permissions():
    """Returns a fresh dict of default permissions."""
    return {perm: False for perm in PERMISSION_LABELS.keys()}