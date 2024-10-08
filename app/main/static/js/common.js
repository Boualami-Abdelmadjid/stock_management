const show_success = (text, cb, emmidiate = false) => {
    Toastify({
        text: text,
        duration: 3000,
        destination: "https://github.com/apvarun/toastify-js",
        newWindow: true,
        gravity: "bottom",
        position: "center",
        stopOnFocus: true,
        style: {
            color: "white",
            border: "2px",
            background: "#2b9718",
            borderRadius: "5px",
        },
    }).showToast();
    if (cb) {
        if (emmidiate) {
            cb();
        } else {
            setTimeout(cb, 2000);
        }
    }
};

const show_error = (text, cb) => {
    Toastify({
        text: text,
        duration: 3000,
        destination: "https://github.com/apvarun/toastify-js",
        newWindow: true,
        gravity: "bottom",
        position: "center",
        stopOnFocus: true,
        style: {
            color: "white",
            border: "2px",
            background: "#ed4848",
            borderRadius: "5px",
        },
    }).showToast();
    if (cb) {
        if (emmidiate) {
            cb();
        } else {
            setTimeout(cb, 2000);
        }
    }
};

const export_file = (data, name) => {
    const output = "sep=," + "\r\n\n" + data.join("\n");
    const blob = new Blob([output], {type: "text/csv"});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.setAttribute("href", url);

    a.setAttribute("download", name);
    a.click();
};

const isVisible = (elem) => {
    return !elem?.parentElement?.classList?.contains("hidden");
};

const isValidSerialNumber = (value) => {
    return value.length == 17;
};

const scan_change_event = (event, elem) => {
    event.preventDefault();
    const {value} = elem;
    if (event.inputType == "insertText" || event.inputType == "insertFromPaste") {
        console.log(value?.includes(' '));
        if (value?.includes(" ") || value.includes("\n")) {
            if (isValidSerialNumber(value.trim())) {
                focusNextInputOrSubmit(event, elem);
            } else {
                show_error("Please scan a valid serial number");
                elem.focus();
            }
        }
    } else if (value && event.inputType != "deleteContentBackward") {
        if (isValidSerialNumber(value.trim())) {
            focusNextInputOrSubmit(event, elem);
        } else {
            show_error("Please scan a valid serial number");
            elem.focus();

        }
    }
};

const focusNextInputOrSubmit = (event, elem) => {
    const form = elem.closest("form");
    const elemContainer = elem.parentElement;
    const shownInputs = Array.from(
        form.querySelectorAll(":scope>div:not(.hidden)")
    ).splice(1);
    const elemIndex = indexOfElement(elemContainer, shownInputs);
    if (isValidSerialNumber(elem.value.trim())) {
        elemIndex === shownInputs.length - 1
            ? submit_action(event, form)
            : shownInputs[elemIndex + 1]
                .querySelector("input, select, textarea")
                .focus();
    }
};
const indexOfElement = (elem, shownInputs) => {
    return shownInputs.indexOf(elem);
};

const toggleDark = (text) => {
    document.querySelector("html").classList.toggle("dark");
    localStorage.setItem("dark", text);
};

const addToBulkOnScan = (event, elem) => {
    event.preventDefault();
    const {value} = elem;
    if (event.inputType == "insertText" || event.inputType == "insertFromPaste") {
        if (value?.includes(" ") || value.includes("\n")) {
            if (isValidSerialNumber(value.trim())) {
                addToBatch(event);
            } else {
                show_error("Please scan a valid serial number");
                elem.focus();
            }
        }
    }
}