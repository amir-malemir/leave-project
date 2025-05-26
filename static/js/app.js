document.addEventListener("DOMContentLoaded", function () {

    // تابع نمایش پیام هشدار
    function showAlert(message, type = "success") {
        const alertContainer = document.getElementById("alert-container");
        if (!alertContainer) return;

        const alertDiv = document.createElement("div");
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = "alert";
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        alertContainer.appendChild(alertDiv);

        // حذف خودکار پیام بعد از 5 ثانیه
        setTimeout(() => {
            alertDiv.classList.remove("show");
            alertDiv.classList.add("hide");
            alertDiv.addEventListener("transitionend", () => alertDiv.remove());
        }, 5000);
    }
    // مدیریت نمایش یا مخفی کردن رمز عبور
    const togglePasswordButton = document.getElementById("toggle-password");
    if (togglePasswordButton) {
        togglePasswordButton.addEventListener("click", function () {
            const passwordInput = document.getElementById("password");
            const passwordIcon = document.getElementById("password-icon");
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                passwordIcon.classList.remove("bi-eye");
                passwordIcon.classList.add("bi-eye-slash");
            } else {
                passwordInput.type = "password";
                passwordIcon.classList.remove("bi-eye-slash");
                passwordIcon.classList.add("bi-eye");
            }
        });
    }

    const convertPersianDigitsToEnglish = (str) => {
        const persian = "۰۱۲۳۴۵۶۷۸۹";
        const english = "0123456789";
        return str.replace(/[۰-۹]/g, (d) => english[persian.indexOf(d)]);
    };

    // دسترسی به فیلدهای فرم ثبت‌نام
    if (document.getElementById("register-unit") &&
    document.getElementById("register-team") &&
    document.getElementById("register-level")) {

    const unitSelect = document.getElementById("register-unit");
    const teamSelect = document.getElementById("register-team");
    const teamContainer = teamSelect.parentElement;
    const levelSelect = document.getElementById("register-level");

    const levelOptions = {
        callcenter: {
            Zitel: ["inbound", "outbound", "ahd"],
            Tornado: ["inbound"]
        },
        noc: {
            Zitel: ["ecs", "fo", "ops"]
        }
    };

    function updateLevels() {
        const unit = unitSelect.value;
        const team = teamSelect.value;
        levelSelect.innerHTML = "";

        const levels = levelOptions[unit]?.[team] || [];
        levels.forEach(level => {
            const opt = document.createElement("option");
            opt.value = level;
            opt.textContent = level.toUpperCase();
            levelSelect.appendChild(opt);
        });
    }

    unitSelect.addEventListener("change", () => {
        const selectedUnit = unitSelect.value;
        if (selectedUnit === "noc") {
            teamContainer.style.display = "none";
            teamSelect.value = "Zitel";
        } else {
            teamContainer.style.display = "block";
        }
        updateLevels();
    });

    teamSelect.addEventListener("change", updateLevels);

    unitSelect.dispatchEvent(new Event("change"));
}

    // تابع نمایش آلارم
    function showAlert(message, type = "success") {
        const alertContainer = document.getElementById("alert-container");
        if (!alertContainer) return;

        const alert = document.createElement("div");
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = "alert";
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        alertContainer.appendChild(alert);

        setTimeout(() => {
            alert.classList.remove("show");
            alert.classList.add("hide");
            alert.addEventListener("transitionend", () => alert.remove());
        }, 5000);
    }
    // دریافت داده‌ها از API
    fetch("/all-leave-requests")
        .then(response => response.json())
        .then(data => {
            const table = document.getElementById("leave-requests-table");
            data.forEach(item => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${item.id}</td>
                    <td>${item.user?.username}</td>
                    <td>${item.startDate || "-"}</td>
                    <td>${item.endDate || "-"}</td>
                    <td>${item.status}</td>
                    <td>${item.reason || ""}</td>
                    <td>
                        <button class="btn btn-sm btn-warning edit-btn" data-id="${item.id}">ویرایش</button>
                    </td>
                `;
                table.appendChild(row);
            });
        })
        .catch(err => {
            console.error("Error fetching leave requests:", err);
        });
    // اکسل
    document.getElementById("export-excel-btn").addEventListener("click", async function () {
        try {
            const token = localStorage.getItem("token");
            const response = await fetch("/all-leave-requests", {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
    
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || "خطا در دریافت داده‌ها");
            }
    
            // تبدیل داده‌ها به فرمت اکسل
            const excelData = data.map((req, index) => ({
                "#": index + 1,
                "نام کاربر": req.user?.username || "بدون نام",
                "تاریخ شروع": req.startDate,
                "تاریخ پایان": req.endDate,
                "نوع مرخصی": req.leaveType,
                "توضیحات": req.reason,
                "وضعیت": req.status,
            }));
    
            const worksheet = XLSX.utils.json_to_sheet(excelData);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, "درخواست‌ها");
    
            // خروجی فایل
            XLSX.writeFile(workbook, "leave-requests.xlsx");
        } catch (error) {
            console.error(error);
            showAlert("خطا در گرفتن خروجی اکسل", "error");
        }
    });

});