PERMISSION_LABELS = {
    # Products
    "can_view_products": "View Products",
    "can_edit_products": "Edit Products",
    "can_create_products": "Create Products",
    "can_delete_products": "Delete Products",

    # Sales
    "can_view_sales": "View Sales",
    "can_edit_sales": "Edit Sales",
    "can_create_sales": "Create Sales",
    "can_delete_sales": "Delete Sales",

    # Managers
    "can_view_managers": "View Managers",
    "can_edit_managers": "Edit Managers(permissions)",
    "can_create_managers": "Add Managers",
    "can_delete_managers": "Remove Managers",

    # Analytics / Dashboard
    "can_view_dashboard": "View Dashboard",

    # Shop Settings
    "can_view_shop_settings": "View Shop Settings",
    "can_edit_shop_settings": "Edit Shop Settings",

    # Terminals
    "can_view_terminals": "View POS Terminals",
    "can_create_terminals": "Create POS Terminals",
    "can_delete_terminals": "Delete POS Terminals",
}
def default_permissions():
    """Returns a fresh dict of default permissions."""
    return {perm: False for perm in PERMISSION_LABELS.keys()}