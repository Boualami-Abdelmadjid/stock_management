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
    show_error(res.message);
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
    show_error(res.message);
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
    show_success("Store created successfully", () => {
      window.location.href = "/";
    });
  } else {
    show_error(res.message);
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
    show_success("Category created successfully", () => {
      window.location.href = "/";
    });
  } else {
    show_error(res.message);
  }
};

const create_router = async (e, elem) => {
  e.preventDefault();
  const category = elem.querySelector("select[name=category]")?.value;
  const serial_number = elem.querySelector("input[name=serial_number]")?.value;
  const emei = elem.querySelector("input[name=emei]")?.value?.trim();

  const body = JSON.stringify({ category, serial_number, emei });
  const res = await fetch("/create-router/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success(
      "Router created successfully",
      () => {
        window.location.reload();
      },
      true
    );
  } else {
    show_error(res.message);
  }
};

const edit_router = async (e, elem) => {
  e.preventDefault();
  const { id } = elem.closest(".edit_form.router").dataset;
  const category = elem.querySelector("select[name=category]")?.value;
  const serial_number = elem.querySelector("input[name=serial_number]")?.value;
  const emei = elem.querySelector("input[name=emei]")?.value?.trim();

  const body = JSON.stringify({ id, category, serial_number, emei });
  const res = await fetch("/router/", {
    method: "PUT",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success("Router edited successfully", () => {
      window.location.reload();
    });
  } else {
    show_error(res.message);
  }
};

const delete_router = async (id) => {
  const body = JSON.stringify({ id });
  const res = await fetch("/router/", {
    method: "DELETE",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success("Router deleted successfully", () => {
      window.location.reload();
    });
  } else {
    show_error(res.message);
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
        create_sugestion(suggestions_container, router.emei);
      });
    } else {
      hide_suggestion(suggestions_container);
    }
  } else {
    hide_suggestion(suggestions_container);
  }
};

const categories_suggestions = async (e, elem) => {
  const { value } = e.target;
  const suggestions_container = elem.nextElementSibling;
  if (value) {
    const res = await fetch(`/categories-suggestions/?value=${value}`).then(
      (res) => res.json()
    );
    if (res.status == 200 && res?.categories.length) {
      const suggestions_container = elem.nextElementSibling;
      suggestions_container.innerHTML = "";
      suggestions_container.classList.add("grid");
      suggestions_container.classList.remove("hidden");
      res.categories.forEach((category) => {
        create_sugestion(suggestions_container, category.name);
      });
    } else {
      hide_suggestion(suggestions_container);
    }
  } else {
    hide_suggestion(suggestions_container);
  }
};

const edit_category = async (e, elem) => {
  e.preventDefault();
  const { id } = elem.closest(".edit_form").dataset;
  const type = elem.querySelector("select[name=type]")?.value;
  const name = elem.querySelector("input[name=name]")?.value;

  const body = JSON.stringify({ id, name, type });
  const res = await fetch("/category/", {
    method: "PUT",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success("Category edited successfully", () => {
      window.location.reload();
    });
  } else {
    console.error(res.message);
  }
};

const create_sugestion = (container, content, link = "#") => {
  const suggestion = document.createElement("a");
  suggestion.innerHTML = content;
  suggestion.href = link;
  container.appendChild(suggestion);
};

const hide_suggestion = (suggestions_container) => {
  suggestions_container.innerHTML = "";
  suggestions_container.classList.remove("grid");
  suggestions_container.classList.add("hidden");
};

const open_edit_router = (elem) => {
  const form = document.querySelector(".edit_form.router");
  const container = elem.closest("tr");
  const { id, sn, emei, category } = container.dataset;

  form.dataset.id = id;
  const sn_container = form.querySelector("[name=serial_number]");
  const emei_container = form.querySelector("[name=emei]")?.trim();
  const category_container = form.querySelector("[name=category]");
  sn_container.value = sn;
  emei_container.value = emei;
  const selected_category = Array.from(category_container.options).find(
    (option) => option.value == category
  );

  if (selected_category) {
    selected_category.selected = true;
  }
  form.classList.remove("hidden");
};

const open_edit_category = (elem) => {
  const form = document.querySelector(".edit_form.category");
  const container = elem.closest("tr");
  const { id, name, type } = container.dataset;

  form.dataset.id = id;
  const name_container = form.querySelector("[name=name]");
  const type_container = form.querySelector("[name=type]");
  name_container.value = name;
  const selected_category = Array.from(type_container.options).find(
    (option) => option.value == type
  );
  selected_category.selected = true;
  form.classList.remove("hidden");
};

const delete_category = async (id) => {
  const body = JSON.stringify({ id });
  const res = await fetch("/category/", {
    method: "DELETE",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success("Category deleted successfully", () => {
      window.location.reload();
    });
  } else {
    show_error(res.message);
  }
};

const close_edit_form = (elem) => {
  const form = elem.closest(".edit_form");
  form.classList.add("hidden");
};

const show_user_form = (elem, action) => {
  const form = document.querySelector(".edit_form");
  if (action == "edit") {
    const { id, username, role } = elem.closest(".user_container").dataset;
    form.querySelector("[name=username]").value = username;
    form.querySelector("[name=username]").disabled = true;
    form.querySelector("button").innerHTML = "Edit";
    form.querySelector("h1").innerHTML = "Edit a user";
    const selected_category = Array.from(
      document.querySelector("select").options
    ).find((option) => option.value == role);

    if (selected_category) {
      selected_category.selected = true;
    }
  } else {
    form.querySelector("button").innerHTML = "Edit";
    form.querySelector("h1").innerHTML = "Edit a user";
  }

  form.classList.remove("hidden");
};

const add_user_to_store = async (e, elem) => {
  e.preventDefault();
  const username = elem.querySelector("input[name=username]").value;
  const role = elem.querySelector("select").value;
  const body = JSON.stringify({ username, role });
  const res = await fetch("/profile/", {
    method: "POST",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success(res.message, () => {
      window.location.reload();
    });
  } else {
    show_error(res.message);
  }
};

const delete_user_from_group = async (elem) => {
  const { id } = elem.closest(".user_container").dataset;
  const body = JSON.stringify({ id });
  const res = await fetch("/profile/", {
    method: "DELETE",
    body,
    headers: {
      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
    },
  }).then((res) => res.json());
  if (res.status == 200) {
    show_success("User deleted successfully", () => {
      window.location.reload();
    });
  } else {
    show_error(res.message);
  }
};

const switch_pages_handler = (e) => {
  const { target } = e;
  const name = target.getAttribute("name");

  Array.from(target.parentElement.children).forEach((span) => {
    span == target
      ? span.classList.add("page_active")
      : span.classList.remove("page_active");
  });
  Array.from(document.querySelectorAll("section")).forEach((section) => {
    section.classList.contains(name)
      ? section.classList.remove("hidden")
      : section.classList.add("hidden");
  });
};

const export_routers = async (e) => {
  e.preventDefault();
  const res = await fetch("/router/").then((res) => res.json());
  if (res.status == 200) {
    const routers = res.routers;
    let excel_data = ["id,category,emei,serial_number,created_at"];
    routers.forEach((router) => {
      excel_data.push(
        `${router.id},${router.category__name},${router.emei},${
          router.serial_number
        },${new Date(router.created_at).getDate()}-${
          new Date(router.created_at).getMonth() + 1
        }`
      );
    });
    const data = "sep=," + "\r\n\n" + excel_data.join("\n");
    const blob = new Blob([data], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.setAttribute("href", url);
    const now = new Date();
    a.setAttribute(
      "download",
      `Routers-${now.getDate()}-${now.getMonth() + 1}-${now.getFullYear()}`
    );
    a.click();
  } else {
    show_error(res.message);
  }
};
