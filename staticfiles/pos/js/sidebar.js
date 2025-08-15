const sidebar = document.querySelector('#sidebar');
const sidebar_btn = document.querySelector("#sidebar-btn");
const shop_details = document.querySelector('#shop-details');
const sidebar_header = document.querySelector("#sidebar-header");

const sidebar_items = document.querySelectorAll(".sidebar-item")
const sidebar_item_labels = document.querySelectorAll(".sidebar-item-label")

sidebar_btn.addEventListener('click', () => {

    sidebar.classList.toggle("w-[250px]");
    sidebar.classList.toggle("w-[56px]");

    shop_details.classList.toggle("hidden");

    sidebar_header.classList.toggle("justify-end");
    sidebar_header.classList.toggle("justify-between");

    sidebar_item_labels.forEach((label) => {
        label.classList.toggle("hidden");
    });

    sidebar_items.forEach((item) => {
        item.classList.toggle("h-8");
        item.classList.toggle("h-10");

        item.classList.toggle("justify-start");
        item.classList.toggle("justify-center");

        item.classList.toggle("pl-2");

        item.classList.toggle("gap-1");
    });
});