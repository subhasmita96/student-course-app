const API = ""; // same origin

let currentStudent = JSON.parse(localStorage.getItem("student") || "null");

// --- Tab switching ---
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab + "Form").classList.add("active");
  });
});

// --- Register ---
document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fullName = document.getElementById("regName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPassword").value;
  const msg = document.getElementById("registerMsg");
  msg.textContent = "";
  try {
    const res = await fetch(`${API}/api/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fullName, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    msg.textContent = "Account created! You can now log in.";
    msg.className = "msg success";
    e.target.reset();
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "msg error";
  }
});

// --- Login ---
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  const msg = document.getElementById("loginMsg");
  msg.textContent = "";
  try {
    const res = await fetch(`${API}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    currentStudent = data.student;
    localStorage.setItem("student", JSON.stringify(currentStudent));
    enterApp();
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "msg error";
  }
});

// --- Logout ---
document.getElementById("logoutBtn").addEventListener("click", () => {
  currentStudent = null;
  localStorage.removeItem("student");
  document.getElementById("authSection").classList.remove("hidden");
  document.getElementById("appSection").classList.add("hidden");
  document.getElementById("userBadge").classList.add("hidden");
});

// --- Enter app after login ---
function enterApp() {
  document.getElementById("authSection").classList.add("hidden");
  document.getElementById("appSection").classList.remove("hidden");
  document.getElementById("userBadge").classList.remove("hidden");
  document.getElementById("userName").textContent = currentStudent.fullName;
  loadCourses();
  loadEnrollments();
}

// --- Load courses ---
async function loadCourses() {
  const res = await fetch(`${API}/api/courses`);
  const data = await res.json();
  const enrolledRes = await fetch(`${API}/api/enrollments/${currentStudent.id}`);
  const enrolledData = await enrolledRes.json();
  const enrolledIds = new Set(enrolledData.enrollments.map((e) => e.id));

  const grid = document.getElementById("courseList");
  grid.innerHTML = "";
  data.courses.forEach((course) => {
    const div = document.createElement("div");
    div.className = "course-card";
    const isEnrolled = enrolledIds.has(course.id);
    div.innerHTML = `
      <h3>${course.course_code} — ${course.title}</h3>
      <p>${course.description || ""}</p>
      <p>Credits: ${course.credits}</p>
      <button ${isEnrolled ? "disabled" : ""} data-id="${course.id}">
        ${isEnrolled ? "Enrolled" : "Enroll"}
      </button>
    `;
    div.querySelector("button").addEventListener("click", (e) => enroll(course.id, e.target));
    grid.appendChild(div);
  });
}

// --- Enroll ---
async function enroll(courseId, btn) {
  try {
    const res = await fetch(`${API}/api/enroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ studentId: currentStudent.id, courseId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Enroll failed");
    btn.disabled = true;
    btn.textContent = "Enrolled";
    loadEnrollments();
  } catch (err) {
    alert(err.message);
  }
}

// --- Load my enrollments ---
async function loadEnrollments() {
  const res = await fetch(`${API}/api/enrollments/${currentStudent.id}`);
  const data = await res.json();
  const list = document.getElementById("enrollmentList");
  list.innerHTML = "";
  if (data.enrollments.length === 0) {
    list.innerHTML = "<li>No enrollments yet.</li>";
    return;
  }
  data.enrollments.forEach((e) => {
    const li = document.createElement("li");
    li.textContent = `${e.course_code} — ${e.title} (${e.credits} credits)`;
    list.appendChild(li);
  });
}

// --- Auto-login if already logged in ---
if (currentStudent) {
  enterApp();
}
