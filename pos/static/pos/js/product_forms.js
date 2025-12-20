// --------------- Product Variant Section ----------------- //

const total_forms = document.querySelector('#id_product_variants-TOTAL_FORMS');
const min_forms = document.querySelector("#id_product_variants-MIN_NUM_FORMS");
const delete_variant_btns = document.querySelectorAll(".delete-variant-btn");

document.body.addEventListener('htmx:afterSwap', (event) => {
    // Check if the swap target is your variants container
    if (event.target.id === 'variant-forms') {
        // Your custom function
        console.log("A new variant was added!");
        const img_uploads = event.target.querySelectorAll(".image-upload");
        img_uploads.forEach(initImageUpload);
        variantAdded(event.target.lastElementChild);
    }
});
function variantAdded(element){
    total_forms.value = parseInt(total_forms.value) + 1;
    const btn = element.querySelector(".delete-variant-btn");
    btn.addEventListener("click", () => {deleteFunc(btn)});
}

delete_variant_btns.forEach((btn) => {
    btn.addEventListener("click", () => {deleteFunc(btn)});
});

function deleteFunc(btn){
    if (parseInt(total_forms.value) > parseInt(min_forms.value)){
            total_forms.value = parseInt(total_forms.value) - 1;
            btn.parentElement.remove();
    }
    else {
        swal({
            title: "Can't delete",
            text: "You must have at least 1 variant per product.",
            icon: "error",
            });
    }
}

// --------------- Image Upload Section ----------------- //



document.querySelectorAll('.image-upload').forEach(initImageUpload);

function initImageUpload(container) {
    const fileInput = container.querySelector('.image-input');
    const previewBox = container.querySelector('.preview-box');
    const uploadBox = container.querySelector('.upload-box');
    const previewImg = container.querySelector('.preview-img');
    const deleteBtn = container.querySelector('.delete-image-btn');
    const deleteFlag = container.querySelector('.delete-image-flag');

    // Drag over
    uploadBox.addEventListener('dragover', e => {
        e.preventDefault();
        uploadBox.classList.add('border-primary');
    });

    uploadBox.addEventListener('dragleave', e => {
        e.preventDefault();
        uploadBox.classList.remove('border-primary');
    });

    // Drop
    uploadBox.addEventListener('drop', e => {
        e.preventDefault();
        uploadBox.classList.remove('border-primary');

        const file = e.dataTransfer.files[0];
        if (!file) return;

        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;

        previewFile(file);
    });

    // Paste
    container.addEventListener('paste', e => {
        const items = e.clipboardData.items;
        for (let item of items) {
            if (item.type.startsWith('image/')) {
                const file = item.getAsFile();
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
                previewFile(file);
            }
        }
    });

    // File select
    fileInput.addEventListener('change', e => {
        const file = e.target.files[0];
        if (file) previewFile(file);
    });

    // Delete
    deleteBtn?.addEventListener('click', () => {
        fileInput.value = '';
        previewImg.src = '';
        previewBox.classList.add('hidden');
        uploadBox.classList.remove('hidden');
        deleteFlag.value = 'true';
    });

    function previewFile(file) {
        const reader = new FileReader();
        reader.onload = e => {
            previewImg.src = e.target.result;
            previewBox.classList.remove('hidden');
            uploadBox.classList.add('hidden');
            deleteFlag.value = 'false';
        };
        reader.readAsDataURL(file);
    }
}


const form = document.querySelector(".main-form");
// --------------- Fix Form Image names beofore submit ----------------- //
form.addEventListener("submit", (event) => {
    const variant_forms = document.querySelectorAll(".variant-form");

    event.preventDefault();
    for (const [i, variant] of variant_forms.entries()){
        variant.querySelector(".image-input").name = `product_variants-${i}-image`;
        variant.querySelector(".sku-input").name = `product_variants-${i}-sku`;
        variant.querySelector(".price-input").name = `product_variants-${i}-price`;
        variant.querySelector(".discount_percentage-input").name = `product_variants-${i}-discount_percentage`;
        variant.querySelector(".stock_quantity-input").name = `product_variants-${i}-stock_quantity`;
        variant.querySelector(".reorder_point-input").name = `product_variants-${i}-reorder_point`;
        variant.querySelector(".product_attribute_values-input").name = `product_variants-${i}-product_attribute_values`;


    }
    alert("ran")
    form.submit();
});