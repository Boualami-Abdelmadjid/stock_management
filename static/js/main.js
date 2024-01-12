const create_account = async (e, elem) => {
  e.preventDefault();
  const [email, username, password1, password2] = Array.from(
    elem.querySelectorAll("input")
  ).map((input) => input.value);
  console.log(email, username, password1, password2);
  if (password1 !== password2) {
    console.log("passwords do not match");
    return;
  }
  const body = JSON.stringify({ username, email, password1, password2 });
  console.log(body);
  const res = await fetch("/signup/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    window.location.href = "/";
  } else {
    console.log(res);
  }
};

const login = async (e, elem) => {
  e.preventDefault();
  const [username, password] = Array.from(elem.querySelectorAll("input")).map(
    (input) => input.value
  );

  const body = JSON.stringify({ username, password });
  const res = await fetch("/login/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    window.location.href = "/";
  } else {
    console.log(res);
  }
};

const create_store = async (e, elem) => {
  e.preventDefault();
  const name = elem.querySelector("input[name=name]")?.value;

  const body = JSON.stringify({ name });
  const res = await fetch("/create-store/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    console.log("Store created successfully");
  } else {
    console.error(res.message);
  }
};

const create_category = async (e, elem) => {
  e.preventDefault();
  const name = elem.querySelector("input[name=name]")?.value;
  const type = elem.querySelector("select[name=type]")?.value;

  const body = JSON.stringify({ name, type });
  console.log(name, type);
  const res = await fetch("/create-category/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    console.log("Category created successfully");
  } else {
    console.error(res.message);
  }
};

const create_router = async (e, elem) => {
  e.preventDefault();
  const category = elem.querySelector("select[name=category]")?.value;
  const serial_number = elem.querySelector("input[name=serial_number]")?.value;
  const emei = elem.querySelector("input[name=emei]")?.value;

  const body = JSON.stringify({ category, serial_number, emei });
  const res = await fetch("/create-router/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    window.location.reload();
  } else {
    console.error(res.message);
  }
};

const routers_suggestions = async (e, elem) => {
  const { value } = e.target;
  const suggestions_container = elem.nextElementSibling;
  if (value) {
    const res = await fetch(`/routers-suggestions/?value=${value}`).then(
      (res) => res.json()
    );
    if (res.status == 200 && res?.routers.length) {
      const suggestions_container = elem.nextElementSibling;
      suggestions_container.innerHTML = "";
      suggestions_container.classList.add("grid");
      suggestions_container.classList.remove("hidden");
      res.routers.forEach((router) => {
        create_router_sugestion(suggestions_container, router);
      });
    } else {
      hide_router_suggestion(suggestions_container);
    }
  } else {
    hide_router_suggestion(suggestions_container);
  }
};

const create_router_sugestion = (container, router) => {
  const suggestion = document.createElement("a");
  suggestion.innerHTML = router.emei;
  suggestion.href = "#";
  container.appendChild(suggestion);
};

const hide_router_suggestion = (suggestions_container) => {
  suggestions_container.innerHTML = "";
  suggestions_container.classList.remove("grid");
  suggestions_container.classList.add("hidden");
};
