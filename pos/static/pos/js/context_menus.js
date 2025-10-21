const context_menu_btns = document.querySelectorAll(".context-menu-btn");
const context_menus = document.querySelectorAll(".context-menu");

hideAllMenus();

context_menu_btns.forEach((btn) => {
    const product_id = btn.dataset.productId;
    btn.addEventListener("click", () => {
        context_menus.forEach((menu) => {
            if (menu.dataset.productId !== product_id){
                menu.classList.add("hidden");
            }
        });
        context_menus.forEach((menu) => {
            if (menu.dataset.productId === product_id){
                menu.classList.toggle("hidden");
            }
        });
    });
});

function hideAllMenus(){
    context_menus.forEach((menu) => {
        menu.classList.add("hidden");
    });
}