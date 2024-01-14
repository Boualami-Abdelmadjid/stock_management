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
