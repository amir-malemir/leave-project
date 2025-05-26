$(function() {
    // چک کن که المنت‌ها وجود دارن
    const startInput = document.getElementById("start-date");
    const endInput = document.getElementById("end-date");

    if (!startInput || !endInput) return;  // اگر نبودند، کد رو اجرا نکن

    // فعال کردن Persian Datepicker
    $("#start-date").persianDatepicker({
        format: "YYYY/MM/DD"
    });

    $("#end-date").persianDatepicker({
        format: "YYYY/MM/DD"
    });

    // هندل کردن فرم
    const form = document.querySelector("form");
    if (!form) return;

    form.addEventListener("submit", function (e) {
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
});
