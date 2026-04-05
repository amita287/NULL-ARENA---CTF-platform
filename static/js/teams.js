//teamS.js
document.addEventListener("DOMContentLoaded", () => {
  // attach button listeners (if using data-action)
  const createBtn = document.querySelector('[data-action="create"]');
  const joinBtn = document.querySelector('[data-action="join"]');

  if (createBtn) createBtn.addEventListener("click", createTeam);
  if (joinBtn) joinBtn.addEventListener("click", joinTeam);

  // 🔥 optional: auto-load team if already in one
  loadTeamInfo();
});


// ---------------- UI TOGGLE ----------------

function showCreate() {
  document.getElementById("createTeamBox").style.display = "flex";
  document.getElementById("joinTeamBox").style.display = "none";
}

function showJoin() {
  document.getElementById("joinTeamBox").style.display = "flex";
  document.getElementById("createTeamBox").style.display = "none";
}


// ---------------- CREATE TEAM ----------------

function createTeam() {
  fetch("/api/create_team", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: document.getElementById("create_name").value,
      password: document.getElementById("create_pass").value
    })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.msg);

      // 🔥 clear inputs
      document.getElementById("team_name").value = "";
      document.getElementById("team_pass").value = "";

      // 🔥 refresh UI
      loadTeamInfo();
    });
}


// ---------------- JOIN TEAM ----------------

function joinTeam() {
  fetch("/api/join_team", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: document.getElementById("join_name").value,
      password: document.getElementById("join_pass").value
    })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.msg);

      // 🔥 clear inputs
      document.getElementById("join_name").value = "";
      document.getElementById("join_pass").value = "";

      // 🔥 refresh UI
      loadTeamInfo();
    });
}


// ---------------- LOAD TEAM INFO ----------------

function loadTeamInfo() {
  fetch("/api/team")   // ✅ fixed endpoint
    .then(res => res.json())
    .then(data => {
      if (!data.team) return;

      const team = data.team;

      document.getElementById("teamInfo").style.display = "block";
      document.getElementById("teamName").innerText = team.name;

      // 🔥 USE BACKEND TOTAL
      document.getElementById("totalPoints").innerText = team.points || 0;

      let html = "";

      team.members.forEach(member => {
        html += `<div>👤 ${member.name} - ${member.score}</div>`;
      });

      document.getElementById("teamMembers").innerHTML = html;

      document.getElementById("createTeamBox").style.display = "none";
      document.getElementById("joinTeamBox").style.display = "none";
    })
    .catch(() => {});
}

function openTeam() {
  document.getElementById("teamSection").style.display = "flex";
}

document.getElementById("closeTeamBtn")
  ?.addEventListener("click", () => {
    document.getElementById("teamSection").style.display = "none";
  });