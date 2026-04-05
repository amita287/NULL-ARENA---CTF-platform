//dashboard.js
document.addEventListener("DOMContentLoaded", () => {

  setTerminalUser();
  // ---------------- ELEMENTS ----------------
  const teamSection = document.getElementById("teamSection");
  const teamOptions = document.getElementById("teamOptions");
  const createBox = document.getElementById("createTeamBox");
  const joinBox = document.getElementById("joinTeamBox");
  const teamInfo = document.getElementById("teamInfo");

  document.getElementById("closeTeamBtn")
  ?.addEventListener("click", () => {
    document.getElementById("teamSection").style.display = "none";
    document.querySelector(".container").style.display = "block";
  });
  
  // ---------------- profile --------------------
  document.querySelector('[data-action="profile"]')
  ?.addEventListener("click", () => window.loadProfile());

  document.getElementById("closeProfileBtn")
  ?.addEventListener("click", () => window.closeProfile());

  function openProfile() {
  document.getElementById("teamSection").style.display = "none"; // 🔥 fix
  document.getElementById("profileBox").classList.remove("hidden");
}
  

  // ---------------- USER ROLE (ADMIN BUTTON) ----------------
  fetch("/api/dashboard", { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      const adminBtn = document.getElementById("admin-btn");
      if (data?.user?.role === "admin") {
        adminBtn.style.setProperty("display", "inline-block", "important");
      }
    })
    .catch(console.error);

  // ----------------users-----------------------
  document.querySelector('[data-action="users"]')
  ?.addEventListener("click", () => {
    document.getElementById("teamSection").style.display = "none";
    document.querySelector(".container").style.display = "block";

    showSection("show users");
    loadUsers();
  });

  // ---------------- scoreboard ---------------
  document.querySelector('[data-action="scoreboard"]')
  ?.addEventListener("click", () => {
    document.getElementById("teamSection").style.display = "none";
    document.querySelector(".container").style.display = "block";

    showSection("show scoreboard");
    loadScoreboard();
  });

  // ---------------- NAVIGATION ----------------

  // LOGOUT
  document.querySelector('[data-action="logout"]')
    ?.addEventListener("click", async () => {
      await fetch("/logout", { method: "GET", credentials: "include" });
      document.cookie = "access_token_cookie=; path=/; expires=Thu, 01 Jan 1970 00:00:00;";
      window.location.href = "/";
    });

  // ADMIN PANEL
  document.querySelector('[data-action="admin"]')
    ?.addEventListener("click", () => {
      window.location.href = "/admin";
    });

  // CHALLENGES VIEW
  document.querySelector('[data-action="challenges"]')
    ?.addEventListener("click", () => {
      teamSection.style.display = "none";
      document.querySelector(".container").style.display = "block";
      loadChallenges();
    });

  // TEAM VIEW
  document.querySelector('[data-action="team"]')
    ?.addEventListener("click", async () => {
      document.querySelector(".container").style.display = "none";
      teamSection.style.display = "flex";

      const res = await fetch("/api/team", { credentials: "include" });
      const data = await res.json();

      if (data.team) {
        showTeamInfo(data.team);
      } else {
        resetUI();
      }
    });

  // ---------------- TEAM UI ----------------

  function loadUsers() {
  fetch("/api/users", {
    credentials: "include"
  })
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("container");
      container.innerHTML = "";

      // Heading
      const heading = document.createElement("h1");
      heading.innerText = "Users";
      heading.style.color = "#00ff88";
      heading.style.marginBottom = "20px";

      container.appendChild(heading);

      // Table container
      const table = document.createElement("div");

      data.users.forEach((user, index) => {
        const row = document.createElement("div");
        row.className = "user-row";

        row.innerHTML = `
          <div>${index + 1}. ${user.name}</div>
          <div>${user.score}</div>
        `;

        table.appendChild(row);
      });

      container.appendChild(table);
    });
}
  function resetUI() {
    teamOptions.style.display = "flex";
    createBox.style.display = "none";
    joinBox.style.display = "none";
    teamInfo.style.display = "none";
  }

  document.getElementById("showCreate").onclick = () => {
    teamOptions.style.display = "none";
    createBox.style.display = "flex";
  };

  document.getElementById("showJoin").onclick = () => {
    teamOptions.style.display = "none";
    joinBox.style.display = "flex";
  };

  // CREATE TEAM
  document.getElementById("createBtn").onclick = async () => {
    const name = document.getElementById("team_name").value;
    const pass = document.getElementById("team_pass").value;

    if (!name || !pass) return alert("Enter all fields");

    const res = await fetch("/api/create_team", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, password: pass })
    });

    const data = await res.json();

    if (data.success) showTeamInfo(data.team);
    else alert(data.error || data.msg);
  };

  // JOIN TEAM
  document.getElementById("joinBtn").onclick = async () => {
    const name = document.getElementById("join_name").value;
    const pass = document.getElementById("join_pass").value;

    const res = await fetch("/api/join_team", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, password: pass })
    });

    const data = await res.json();

    if (data.success) showTeamInfo(data.team);
    else alert(data.error || data.msg);
  };

  function showTeamInfo(team) {
    teamOptions.style.display = "none";
    createBox.style.display = "none";
    joinBox.style.display = "none";
    teamInfo.style.display = "block";

    document.getElementById("teamTitle").innerText = team.name;
    document.getElementById("teamPoints").innerText = team.points;

    let html = "";
    team.members.forEach(m => {
      html += `
        <div class="row">
          <div>${m.name}</div>
          <div>${m.score}</div>
        </div>
      `;
    });

    document.getElementById("teamMembers").innerHTML = html;
  }
  // ---------------- scoreboard ----------------
  function loadScoreboard() {
  fetch("/api/scoreboard", {
    credentials: "include"
  })
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("container");
      container.innerHTML = "";

      // Heading
      const heading = document.createElement("h1");
      heading.innerText = "Scoreboard";
      heading.style.color = "#00ff88";
      heading.style.marginBottom = "20px";

      container.appendChild(heading);

      const table = document.createElement("div");

      data.teams.forEach((team, index) => {
        const row = document.createElement("div");
        row.className = "user-row";

        row.innerHTML = `
          <div>${index + 1}. ${team.name}</div>
          <div>${team.score}</div>
        `;

        table.appendChild(row);
      });

      container.appendChild(table);
    });
}
// ------------------ profile ------------------
window.loadProfile = async function () {

  // hide team if open
  document.getElementById("teamSection").style.display = "none";

  // show main container
  document.querySelector(".container").style.display = "block";

  // switch from welcome → main
  document.getElementById("welcomeScreen").style.display = "none";
  document.getElementById("mainContent").style.display = "block";

  // update terminal
  showSection("show profile");

  try {
    const res = await fetch("/api/profile", {
      credentials: "include"
    });

    const data = await res.json();

    const container = document.getElementById("container");

container.innerHTML = `
  <div class="profile-page">

    <div class="profile-box">
      <span>NAME</span>
      <div>${data.name}</div>
    </div>

    <div class="profile-box">
      <span>EMAIL</span>
      <div>${data.email}</div>
    </div>

    <div class="profile-box">
      <span>TEAM</span>
      <div>${data.team}</div>
    </div>

    <div class="profile-box">
      <span>POINTS</span>
      <div>${data.score}</div>
    </div>

  </div>
`;

  } catch (err) {
    console.error("Profile error:", err);
  }
};
  // ---------------- CHALLENGES ----------------

  function loadChallenges() {
    fetch("/api/challenges", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        const container = document.getElementById("container");
        container.innerHTML = "";

        const grouped = {};

        data.challenges.forEach(c => {
          if (!grouped[c.category]) grouped[c.category] = [];
          grouped[c.category].push(c);
        });

        for (let cat in grouped) {
          const heading = document.createElement("h2");
          heading.innerText = cat;

          const grid = document.createElement("div");
          grid.className = "grid";

          grouped[cat].forEach(ch => {
            const card = document.createElement("div");
            card.className = ch.solved ? "card solved" : "card";

            card.innerHTML = `
              <div>${ch.title}</div>
              <div class="points">${ch.points}</div>
            `;

            // ✅ FIXED CLICK
            card.addEventListener("click", () => openModal(ch));

            grid.appendChild(card);
          });

          container.appendChild(heading);
          container.appendChild(grid);
        }
      });
  }
  window.closeProfile = function () {
  document.getElementById("profileBox").classList.add("hidden");
};

  // ---------------- MODAL ----------------

  function openModal(ch) {
    window.currentChallenge = ch;

    document.getElementById("modalTitle").innerText = ch.title;
    document.getElementById("modalAuthor").innerText = ch.author;
    document.getElementById("modalPoints").innerText = ch.points;
    document.getElementById("modalDesc").innerText = ch.description;

    document.getElementById("challengeModal").classList.remove("hidden");
  }

  function closeModal() {
    document.getElementById("challengeModal").classList.add("hidden");
  }

  document.getElementById("closeModal")
    ?.addEventListener("click", closeModal);

  // ---------------- FLAG SUBMIT ----------------

  document.getElementById("submitFlag")
    ?.addEventListener("click", async () => {
      const flag = document.getElementById("flagInput").value;

      const res = await fetch("/api/submit_flag", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          challenge_id: window.currentChallenge.id,
          flag: flag
        })
      });

      const data = await res.json();
      alert(data.msg);
    });

});

function setTerminalUser() {
  fetch("/api/dashboard", {
    credentials: "include"
  })
    .then(res => res.json())
    .then(data => {
      const role = data.user.role;

      const prefix = role === "admin" ? "admin" : "user";

      document.getElementById("terminalLine").innerText =
        `${prefix}@ctf:~$ show challenges`;
    });
}

function showSection(command) {
  document.getElementById("welcomeScreen").style.display = "none";
  document.getElementById("mainContent").style.display = "block";

  document.getElementById("terminalLine").innerText =
    document.getElementById("terminalLine").innerText.replace(/show .*/, command);
}