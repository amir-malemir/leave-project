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
    const startDateElement = document.getElementById("start-date");
    if (startDateElement) {
        $("#start-date").persianDatepicker({
            format: "YYYY/MM/DD",
            onSelect: function () {
                const jalaliDate = $("#start-date").val();
                const gregorianDate = moment(jalaliDate, "jYYYY/jMM/jDD").startOf("day").format("YYYY-MM-DD");
                console.log("تاریخ میلادی:", gregorianDate);
            }
        });
    }

    // فعال کردن Persian Datepicker برای فیلد تاریخ پایان
    const endDateElement = document.getElementById("end-date");
    if (endDateElement) {
        $("#end-date").persianDatepicker({
            format: "YYYY/MM/DD",
            onSelect: function () {
                const jalaliDate = $("#end-date").val();
                const gregorianDate = moment(jalaliDate, "jYYYY/jMM/jDD").startOf("day").format("YYYY-MM-DD");
                console.log("تاریخ میلادی:", gregorianDate);
            }
        });
    }

    // مدیریت فرم لاگین


    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            try {
                const response = await fetch("/token", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: new URLSearchParams({
                        username: username,
                        password: password
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log("توکن دریافت شد:", data.access_token);

                    // ذخیره توکن در localStorage
                    localStorage.setItem("token", data.access_token);

                    // هدایت به صفحه داشبورد
                    window.location.href = "/dashboard";
                } else {
                    const errorData = await response.json();
                    alert(errorData.detail || "نام کاربری یا رمز عبور اشتباه است!");
                }
            } catch (error) {
                console.error("خطا در ارسال درخواست ورود:", error);
                alert("خطایی رخ داد!");
            }
        });
        }

    // مدیریت فرم ثبت‌نام
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        // مدیریت تغییر سطح‌ها بر اساس واحد
        const unitSelect = document.getElementById("register-unit");
        const levelSelect = document.getElementById("register-level");

        const levels = {
            callcenter: ["Inbound", "Outbound", "AHD"],
            noc: ["ECS", "FO"]
        };

        unitSelect.addEventListener("change", function () {
            const selectedUnit = unitSelect.value;
            levelSelect.innerHTML = ""; // پاک کردن گزینه‌های قبلی

            levels[selectedUnit]?.forEach(level => {
                const option = document.createElement("option");
                option.value = level.toLowerCase();
                option.textContent = level;
                levelSelect.appendChild(option);
            });
        });

        // مقدار پیش‌فرض برای سطح‌ها
        unitSelect.dispatchEvent(new Event("change"));

        registerForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            console.log("فرم ثبت‌نام ارسال شد!");

            const username = document.getElementById("register-username").value;
            const email = document.getElementById("register-email").value;
            const fullName = document.getElementById("register-full-name").value;
            const phoneNumber = document.getElementById("register-phone-number").value;
            const unit = document.getElementById("register-unit").value;
            const level = document.getElementById("register-level").value;
            const password = document.getElementById("register-password").value;
            const confirmPassword = document.getElementById("register-confirm-password").value;

            const role = "employee"; // مقدار پیش‌فرض برای role

            if (password !== confirmPassword) {
                showAlert("رمز عبور و تأیید آن مطابقت ندارند!", "danger"); // پیام هشدار
                return;
            }

            try {
                const response = await fetch("http://127.0.0.1:8000/users", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username,
                        email,
                        full_name: fullName,
                        phone_number: phoneNumber,
                        unit,
                        level,
                        role,
                        password
                    })
                });

                if (response.ok) {
                    showAlert("ثبت‌نام موفقیت‌آمیز بود!", "success"); // پیام موفقیت
                    window.location.href = "/login";
                } else {
                    const errorData = await response.json();
                    console.error("خطای ثبت‌نام:", errorData.detail);
                    showAlert(errorData.detail || "ثبت‌نام ناموفق بود!", "danger"); // پیام خطا
                }
            } catch (error) {
                console.error("خطای درخواست:", error);
                showAlert("خطایی رخ داد!", "danger"); // پیام خطای عمومی
            }
        });
    }
    // دریافت اطلاعات داشبورد
    async function loadDashboardData() {
        console.log("در حال بارگذاری اطلاعات داشبورد...");
        try {
            const token = localStorage.getItem("token");
            if (!token) {
                console.error("توکن یافت نشد!");
                showAlert("لطفاً وارد شوید!", "warning");
                window.location.href = "/login";
                return;
            }

            const response = await fetch("/dashboard-data", {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log("اطلاعات دریافت شد:", data);
                document.getElementById("total-requests").textContent = data.total_requests || 0;
                document.getElementById("approved-requests").textContent = data.approved_requests || 0;
                document.getElementById("rejected-requests").textContent = data.rejected_requests || 0;
                document.getElementById("pending-requests").textContent = data.pending_requests || 0;
            } else if (response.status === 401) {
                console.error("توکن نامعتبر است یا منقضی شده!");
                showAlert("توکن نامعتبر است یا منقضی شده!", "danger");
                window.location.href = "/login";
            }
        } catch (error) {
            console.error("خطا در دریافت اطلاعات داشبورد:", error);
            showAlert("خطا در دریافت اطلاعات داشبورد!", "danger");
        }
    }
    if (window.location.pathname === "/leave-requests-page") {
        loadUserLeaveRequests();
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

    // دریافت لیست کاربران
    async function loadUsers() {
        console.log("در حال بارگذاری لیست کاربران...");
        try {
            const token = localStorage.getItem("token");
            if (!token) {
                console.error("توکن یافت نشد!");
                window.location.href = "/login";
                return;
            }

            const response = await fetch("/user-management", {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (response.ok) {
                const users = await response.json();
                console.log("لیست کاربران دریافت شد:", users);
                renderUsers(users);
            } else {
                console.error("خطا در دریافت لیست کاربران!");
            }
        } catch (error) {
            console.error("خطا در دریافت لیست کاربران:", error);
        }
    }

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
    
    // اتصال تابع خروج به دکمه خروج
    function logoutUser() {
        console.log("در حال خروج...");
        // ارسال درخواست به سرور برای حذف کوکی
        fetch("/logout", {
            method: "POST",
            credentials: "include" // ارسال کوکی‌ها با درخواست
        })
            .then(response => {
                if (response.ok) {
                    console.log("خروج موفقیت‌آمیز بود!");
                    window.location.href = "/login"; // هدایت به صفحه ورود
                } else {
                    console.error("خطا در خروج:", response.statusText);
                    alert("خطا در خروج!");
                }
            })
            .catch(error => {
                console.error("خطا در ارسال درخواست خروج:", error);
                alert("خطایی رخ داد!");
            });
    }
    
    // اتصال تابع خروج به دکمه‌های خروج
    const logoutButtons = document.querySelectorAll(".nav-link.text-danger, .desktop-logout");
    logoutButtons.forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            logoutUser();
        });
    });
    // اگر در صفحه داشبورد هستیم
    if (window.location.pathname.startsWith("/dashboard")) {
        loadDashboardData();
    }

    // اگر در صفحه مشاهده درخواست‌ها هستیم
    if (window.location.pathname.startsWith("/user-leave-requests")) {
        loadLeaveRequests();
    }

    // اگر در صفحه مدیریت کاربران هستیم
    if (window.location.pathname.startsWith("/user-management")) {
        loadUsers();
    }
    

    const leaveRequestForm = document.getElementById("leave-request-form");
    if (leaveRequestForm) {
        leaveRequestForm.addEventListener("submit", async function (e) {
            e.preventDefault(); // جلوگیری از ارسال پیش‌فرض فرم

            // تابع تبدیل اعداد فارسی به انگلیسی
            function convertToEnglishDigits(input) {
                const persianDigits = "۰۱۲۳۴۵۶۷۸۹";
                const englishDigits = "0123456789";
                return input.replace(/[۰-۹]/g, (char) => englishDigits[persianDigits.indexOf(char)]);
            }

            // دریافت تاریخ‌های شمسی از فیلدهای ورودی
            const jalaliStartDate = convertToEnglishDigits(document.getElementById("start-date").value); // تاریخ شمسی
            const jalaliEndDate = convertToEnglishDigits(document.getElementById("end-date").value);     // تاریخ شمسی
            const reason = document.getElementById("reason").value;

            // بررسی فرمت تاریخ‌های ورودی
            console.log("Jalali Start Date:", jalaliStartDate);
            console.log("Jalali End Date:", jalaliEndDate);

            // تبدیل تاریخ‌های شمسی به میلادی با فرمت خط تیره
            const startDate = moment(jalaliStartDate, "jYYYY/jMM/jDD").locale("fa").format("YYYY-MM-DD");
            const endDate = moment(jalaliEndDate, "jYYYY/jMM/jDD").locale("fa").format("YYYY-MM-DD");

            // بررسی تاریخ‌های تبدیل‌شده
            console.log("Start Date (Gregorian):", startDate);
            console.log("End Date (Gregorian):", endDate);
            
            // بررسی اینکه تاریخ پایان نباید کوچکتر از تاریخ شروع باشد
            if (new Date(endDate) < new Date(startDate)) {
                alert("تاریخ پایان نمی‌تواند کوچکتر از تاریخ شروع باشد.");
                return;
            }

            try {
                const token = localStorage.getItem("token");
                if (!token) {
                    alert("لطفاً وارد شوید!");
                    window.location.href = "/login";
                    return;
                }

                // ارسال درخواست به API
                const response = await fetch("/leave_request", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        start_date: startDate, // ارسال تاریخ میلادی
                        end_date: endDate,     // ارسال تاریخ میلادی
                        reason: reason
                    })
                });

                if (response.ok) {
                    alert("درخواست مرخصی با موفقیت ثبت شد!");
                    window.location.href = "/leave-requests-page";
                } else {
                    const errorData = await response.json();
                    alert(errorData.detail || "خطا در ثبت درخواست مرخصی!");
                }
            } catch (error) {
                console.error("خطا در ارسال درخواست مرخصی:", error);
                alert("خطایی رخ داد!");
            }
        });
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