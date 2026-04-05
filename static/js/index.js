//index.js
document.addEventListener("DOMContentLoaded", () => {
  const loginBox = document.getElementById("loginBox");
  const signupBox = document.getElementById("signupBox");

  const showSignupBtn = document.querySelector('[data-action="showSignup"]');
  const showLoginBtn = document.querySelector('[data-action="showLogin"]');
  const loginBtn = document.querySelector('[data-action="login"]');
  const signupBtn = document.querySelector('[data-action="signup"]');
  const googleBtn = document.querySelector('[data-action="google"]');

  if (showSignupBtn) {
    showSignupBtn.addEventListener("click", () => {
      loginBox.style.display = "none";
      signupBox.style.display = "block";
    });
  }

  if (showLoginBtn) {
    showLoginBtn.addEventListener("click", () => {
      signupBox.style.display = "none";
      loginBox.style.display = "block";
    });
  }

  if (loginBtn) loginBtn.addEventListener("click", login);
  if (signupBtn) signupBtn.addEventListener("click", signup);

  if (googleBtn) {
    googleBtn.addEventListener("click", () => {
      window.location.href = "/login/google";
    });
  }
});

async function signup() {
  const res = await fetch("/signup", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      password: document.getElementById("signupPassword").value
    })
  });

  const data = await res.json();
  if (data.msg.includes("created")) {
    document.querySelector('[data-action="showLogin"]').click();
  }
}

async function login() {
  const res = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      email: document.getElementById("loginEmail").value,
      password: document.getElementById("loginPassword").value
    })
  });

  const data = await res.json();

  if (!res.ok) {
    alert(data.msg);
    return;
  }

  window.location.href = "/dashboard";
}