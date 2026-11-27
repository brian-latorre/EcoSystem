(function () {
  const PUBLIC_PAGES = ["index.html", "acceso-personal.html"];

  const ROLE_HOME = {
    CIUDADANO: "ciudadano.html",
    CONDUCTOR: "conductor.html",
    OPERARIO: "operario.html",
    ADMIN: "admin.html",
    COORDINADOR: "admin.html",
    SUPERVISOR: "admin.html"
  };

  const PAGES = [
    { file: "ciudadano.html", label: "Mapa y Reciclaje", roles: ["CIUDADANO"] },
    { file: "denuncias.html", label: "Denuncias", roles: ["CIUDADANO", "ADMIN", "COORDINADOR", "SUPERVISOR"] },
    { file: "conductor.html", label: "Hoja de Ruta", roles: ["CONDUCTOR", "ADMIN", "COORDINADOR", "SUPERVISOR"] },
    { file: "operario.html", label: "Planta", roles: ["OPERARIO", "ADMIN", "COORDINADOR", "SUPERVISOR"] },
    { file: "admin.html", label: "Panel Municipal", roles: ["ADMIN", "COORDINADOR", "SUPERVISOR"] }
  ];

  const current = window.location.pathname.split("/").pop() || "index.html";
  const baseUrl = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

  function readSession() {
    try {
      return JSON.parse(localStorage.getItem("ecosystem_user") || "null");
    } catch (error) {
      return null;
    }
  }

  function loginUrlFor(page) {
    const citizenPages = ["ciudadano.html", "denuncias.html"];
    return citizenPages.includes(page) ? "index.html" : "acceso-personal.html";
  }

  function redirectToLogin(page) {
    const target = loginUrlFor(page) + "?next=" + encodeURIComponent(current);
    window.location.replace(target);
  }

  function isAllowed(pageFile, role) {
    const entry = PAGES.find((p) => p.file === pageFile);
    return Boolean(entry && entry.roles.includes(role));
  }

  function createBrand(user) {
    const brand = document.createElement("a");
    brand.className = "eco-nav-brand";
    brand.href = ROLE_HOME[user.role] || "index.html";
    brand.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-14 14z"></path>' +
      '<path d="M5 19c2-4 5-7 9-9"></path></svg>';
    const label = document.createElement("span");
    label.textContent = "EcoSystem";
    brand.appendChild(label);
    return brand;
  }

  function createLinks(user) {
    const wrapper = document.createElement("div");
    wrapper.className = "eco-nav-links";
    PAGES.filter((page) => page.roles.includes(user.role)).forEach((page) => {
      const link = document.createElement("a");
      link.className = "eco-nav-link" + (page.file === current ? " is-active" : "");
      link.href = page.file;
      link.textContent = page.label;
      wrapper.appendChild(link);
    });
    return wrapper;
  }

  function createSide(user) {
    const side = document.createElement("div");
    side.className = "eco-nav-side";

    const chip = document.createElement("span");
    chip.className = "eco-nav-session";
    chip.textContent = user.role === "CIUDADANO"
      ? user.full_name
      : user.full_name + " · " + user.role;
    side.appendChild(chip);

    const logout = document.createElement("button");
    logout.type = "button";
    logout.className = "eco-nav-action";
    logout.textContent = "Cerrar sesión";
    logout.addEventListener("click", () => {
      const exitUrl = user.role === "CIUDADANO" ? "index.html" : "acceso-personal.html";
      localStorage.removeItem("ecosystem_user");
      window.location.href = exitUrl;
    });
    side.appendChild(logout);

    return side;
  }

  function mountNav(user) {
    if (document.querySelector(".eco-nav")) return;
    const nav = document.createElement("nav");
    nav.className = "eco-nav";
    nav.setAttribute("aria-label", "Navegación principal");
    nav.appendChild(createBrand(user));
    nav.appendChild(createLinks(user));
    nav.appendChild(createSide(user));
    document.body.insertBefore(nav, document.body.firstChild);
  }

  if (PUBLIC_PAGES.includes(current)) return;

  const user = readSession();
  if (!user || !user.access_token) {
    redirectToLogin(current);
    return;
  }

  if (!isAllowed(current, user.role)) {
    window.location.replace(ROLE_HOME[user.role] || "index.html");
    return;
  }

  fetch(baseUrl + "/api/v1/auth/me", {
    headers: { Authorization: "Bearer " + user.access_token }
  })
    .then((res) => {
      if (res.status === 401) {
        localStorage.removeItem("ecosystem_user");
        redirectToLogin(current);
      }
    })
    .catch(() => {});

  mountNav(user);
})();
