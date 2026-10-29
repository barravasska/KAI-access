
const API = "/api";

function getToken() {
    return sessionStorage.getItem("access_token");
}

function saveToken(token) {
    sessionStorage.setItem("access_token", token);
}

function logout() {
    sessionStorage.removeItem("access_token");
    window.location.href = "/login.html";
}

async function apiRequest(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    if (
        options.body &&
        !(options.body instanceof FormData)
    ) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(API + path, {
        ...options,
        headers
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(data.detail)
        );
    }

    return data;
}

function requireLogin() {
    if (!getToken()) {
        window.location.href = "/login.html";
    }
}

function showMessage(id, message, success = false) {
    const element = document.getElementById(id);

    element.textContent = message;
    element.className =
        "message " + (success ? "success" : "error");
}
