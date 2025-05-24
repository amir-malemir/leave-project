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
    // فعال کردن Persian Datepicker برای فیلد تاریخ شروع
    // const startDateElement = document.getElementById("start-date");
    // if (startDateElement) {
    //     $("#start-date").persianDatepicker({
    //         format: "YYYY/MM/DD",
    //         onSelect: function () {
    //             const jalaliDate = $("#start-date").val();
    //             const gregorianDate = moment(jalaliDate, "jYYYY/jMM/jDD").startOf("day").format("YYYY-MM-DD");
    //             console.log("تاریخ میلادی:", gregorianDate);
    //         }
    //     });
    // }

    // فعال کردن Persian Datepicker برای فیلد تاریخ پایان
    // const endDateElement = document.getElementById("end-date");
    // if (endDateElement) {
    //     $("#end-date").persianDatepicker({
    //         format: "YYYY/MM/DD",
    //         onSelect: function () {
    //             const jalaliDate = $("#end-date").val();
    //             const gregorianDate = moment(jalaliDate, "jYYYY/jMM/jDD").startOf("day").format("YYYY-MM-DD");
    //             console.log("تاریخ میلادی:", gregorianDate);
    //         }
    //     });
    // }


    const convertPersianDigitsToEnglish = (str) => {
        const persian = "۰۱۲۳۴۵۶۷۸۹";
        const english = "0123456789";
        return str.replace(/[۰-۹]/g, (d) => english[persian.indexOf(d)]);
    };

    // بدون j در خروجی UI
    $("#start-date").persianDatepicker({
        format: "YYYY/MM/DD"
    });

    $("#end-date").persianDatepicker({
        format: "YYYY/MM/DD"
    });

    const form = document.querySelector("form");
    form.addEventListener("submit", function (e) {
        const startInput = document.getElementById("start-date");
        const endInput = document.getElementById("end-date");

        const startValue = convertPersianDigitsToEnglish(startInput.value);
        const endValue = convertPersianDigitsToEnglish(endInput.value);

        const startMoment = moment.from(startValue, "fa", "YYYY/MM/DD");
        const endMoment = moment.from(endValue, "fa", "YYYY/MM/DD");

        if (!startMoment.isValid() || !endMoment.isValid()) {
            e.preventDefault();
            alert("تاریخ‌ها معتبر نیستند");
            return;
        }

        startInput.value = startMoment.format("YYYY-MM-DD");
        endInput.value = endMoment.format("YYYY-MM-DD");
    });



    // مدیریت فرم ثبت‌نام
    const unitSelect = document.getElementById("register-unit");
    const teamSelect = document.getElementById("register-team");
    const teamContainer = teamSelect?.parentElement;
    const levelSelect = document.getElementById("register-level");

    if (!unitSelect || !teamSelect || !levelSelect) return;

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

    // مقدار اولیه
    unitSelect.dispatchEvent(new Event("change"));

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
    // دریافت لیست درخواست‌های مرخصی از سرور
    async function loadUserLeaveRequests() {
        try {
            const response = await fetch("http://127.0.0.1:8000/user-leave-requests", {
                method: "GET",
                credentials: "include" // ارسال کوکی‌ها با درخواست
            });

            if (response.ok) {
                const requests = await response.json();
                console.log("لیست درخواست‌های مرخصی دریافت شد:", requests);
                renderLeaveRequests(requests); // نمایش داده‌ها در جدول
            } else if (response.status === 401) {
                alert("توکن منقضی شده یا نامعتبر است!");
                window.location.href = "/login";
            } else {
                console.error("خطا در دریافت اطلاعات:", response.statusText);
            }
        } catch (error) {
            console.error("خطا در فراخوانی API:", error);
        }
    }

    // نمایش لیست درخواست‌ها در جدول
    function renderLeaveRequests(requests) {
        const requestsTable = document.getElementById("requests-table");
        requestsTable.innerHTML = ""; // پاک کردن محتوای قبلی جدول

        requests.forEach(request => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${request.id}</td>
                <td>${request.username || "?"}</td>
                <td>${request.start_date}</td>
                <td>${request.end_date}</td>
                <td>
                    <span class="badge ${
                        request.status === "approved" ? "bg-success" :
                        request.status === "rejected" ? "bg-danger" :
                        "bg-warning text-dark"
                    }">
                        ${request.status}
                    </span>
                </td>
                <td>${request.reason}</td>
            `;
            requestsTable.appendChild(row);
        });
    }

    // فراخوانی تابع هنگام بارگذاری صفحه
    document.addEventListener("DOMContentLoaded", loadUserLeaveRequests);

    // نمایش لیست کاربران
    function renderUsers(users) {
        const usersTable = document.getElementById("users-table");
        usersTable.innerHTML = "";

        users.forEach(user => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.unit}</td>
                <td>${user.role}</td>
                <td>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            عملیات
                        </button>
                        <ul class="dropdown-menu">
                            <li>
                                <a class="dropdown-item" href="#" onclick="editUser(${user.id})">
                                    <i class="bi bi-pencil"></i> ویرایش
                                </a>
                            </li>
                            <li>
                                <a class="dropdown-item text-danger" href="#" onclick="deleteUser(${user.id})">
                                    <i class="bi bi-trash"></i> حذف
                                </a>
                            </li>
                        </ul>
                    </div>
                </td>
            `;
            usersTable.appendChild(row);
        });
    }
    
    
   
    // اگر در صفحه داشبورد هستیم
    if (window.location.pathname.startsWith("/dashboard")) {
        loadDashboardData();
    }

    // اگر در صفحه مشاهده درخواست‌ها هستیم
    if (window.location.pathname.startsWith("/user-leave-requests")) {
        loadLeaveRequests();
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