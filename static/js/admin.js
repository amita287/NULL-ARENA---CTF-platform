// admin.js

// 🔥 INIT IMMEDIATELY (no DOMContentLoaded issues)
initAdmin();

function initAdmin() {
  // DEFAULT VIEW
  showView();

  // 🔥 NAVBAR CLICK HANDLER (EVENT DELEGATION - BEST FIX)
  document.addEventListener("click", (e) => {
    const action = e.target.dataset.action;
    if (!action) return;

    switch (action) {
      case "users":
        loadUsers();
        break;

      case "teams":
        loadTeams();
        break;

      case "scoreboard":
        loadScoreboard();
        break;

      case "view":
        showView();
        break;

      case "add":
        showAdd();
        break;

      case "logs":
        showLogs();
        break;

      case "addChallenge":
        addChallenge();
        break;

      case "dashboard":
        window.location.href = "/dashboard";
        break;

      case "logout":
        window.location.href = "/logout";
        break;
    }
  });
}


// ---------------- TOGGLE ----------------

function toggle(section) {
  ["addSection", "viewSection", "logsSection"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.style.display = (id === section) ? "block" : "none";
    }
  });
}

function showAdd() {
  toggle("addSection");
}

function showView() {
  toggle("viewSection");

  // ✅ SHOW button only here
  document.getElementById("addBtnContainer").style.display = "block";

  loadChallenges();
}

function showLogs() {
  toggle("logsSection");

  // ❌ HIDE button
  document.getElementById("addBtnContainer").style.display = "none";

  loadLogs();
}


// ---------------- USERS ----------------

function loadUsers() {
  toggle("viewSection");

  // ❌ HIDE button
  document.getElementById("addBtnContainer").style.display = "none";

  fetch("/api/users", { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      let html = "<h2>Users</h2>";

      data.users.forEach((u, i) => {
        html += `
          <div class="score-row">
            <span>${i + 1}. ${u.name}</span>
            <span>${u.score}</span>
          </div>
        `;
      });

      document.getElementById("challengeContainer").innerHTML = html;
    });
}


// ---------------- TEAMS ----------------

function loadTeams() {
  toggle("viewSection");

  // ❌ HIDE button
  document.getElementById("addBtnContainer").style.display = "none";

  fetch("/api/scoreboard", { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      let html = "<h2>Teams</h2>";

      data.teams.forEach((t, i) => {
        html += `
          <div class="score-row">
            <span>${i + 1}. ${t.name}</span>
            <span>${t.score}</span>
          </div>
        `;
      });

      document.getElementById("challengeContainer").innerHTML = html;
    });
}


// ---------------- SCOREBOARD ----------------

function loadScoreboard() {
  loadTeams(); // same API
}


// ---------------- ADD ----------------

function addChallenge() {
  fetch("/api/add_challenge", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: document.getElementById("title").value,
      description: document.getElementById("description").value,
      category: document.getElementById("category").value,
      author: document.getElementById("author").value,
      points: parseInt(document.getElementById("points").value),
      file_link: document.getElementById("file_link").value,
      flag: document.getElementById("flag").value,
    })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.msg);

    // CLEAR FORM
    document.getElementById("title").value = "";
    document.getElementById("description").value = "";
    document.getElementById("category").value = "";
    document.getElementById("author").value = "";
    document.getElementById("points").value = "";
    document.getElementById("file_link").value = "";
    document.getElementById("flag").value = "";

    showView();
  });
}


// ---------------- LOAD CHALLENGES ----------------

function loadChallenges() {
  fetch("/api/challenges", {
    credentials: "include"
  })
    .then(res => res.json())
    .then(data => {

      window.challengeData = data.challenges;

      const grouped = {};

      data.challenges.forEach(c => {
        if (!grouped[c.category]) grouped[c.category] = [];
        grouped[c.category].push(c);
      });

      const container = document.getElementById("challengeContainer");
      container.innerHTML = "";

      for (let cat in grouped) {

        const heading = document.createElement("h2");
        heading.textContent = cat;
        heading.style.color = "#00ff88";
        heading.style.marginTop = "20px";

        const grid = document.createElement("div");
        grid.className = "grid";

        grouped[cat].forEach(ch => {
          const card = document.createElement("div");
          card.className = "card";

          card.innerHTML = `
            <div>${ch.title}</div>
            <div class="points">${ch.points}</div>
          `;

          card.addEventListener("click", () => openAdminModal(ch.id));

          grid.appendChild(card);
        });

        container.appendChild(heading);
        container.appendChild(grid);
      }
    });
}


// ---------------- MODAL ----------------

function openAdminModal(id) {
  const chal = window.challengeData.find(c => c.id === id);
  if (!chal) return;

  document.getElementById("modalTitle").innerText = chal.title;
  document.getElementById("modalAuthor").innerText = chal.author;
  document.getElementById("modalPoints").innerText = chal.points;
  document.getElementById("modalDesc").innerText = chal.description;

  document.getElementById("challengeModal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("challengeModal").classList.add("hidden");
}


// ---------------- LOAD LOGS ----------------

function loadLogs() {
  fetch("/api/logs", {
    credentials: "include"
  })
    .then(res => res.json())
    .then(data => {

      let html = "<h2>System Logs</h2>";

      data.logs.forEach(log => {
        html += `
          <div class="log">
            <div><b>${log.email}</b></div>
            <div>${log.action}</div>
            <div style="font-size:12px;">${log.time}</div>
          </div>
        `;
      });

      document.getElementById("logsContainer").innerHTML = html;
    });
}