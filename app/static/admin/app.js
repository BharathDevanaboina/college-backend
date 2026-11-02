import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.2/firebase-app.js";
import {
  TotpMultiFactorGenerator,
  getAuth,
  getMultiFactorResolver,
  multiFactor,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
} from "https://www.gstatic.com/firebasejs/11.0.2/firebase-auth.js";

const root = document.querySelector("#app");
const toastRegion = document.querySelector("#toast-region");
const state = { auth: null, user: null, page: "dashboard", cache: {}, resolver: null };
const nav = [
  ["dashboard", "◫", "Overview"], ["settings", "⚙", "Contact & settings"],
  ["courses", "◈", "Courses & fees"], ["batches", "◷", "Batches"],
  ["brochures", "▣", "Brochures"], ["banners", "▧", "Banners"],
  ["announcements", "◉", "Announcements"], ["gallery", "▦", "Gallery"],
  ["videos", "▶", "Videos"], ["exam", "✦", "Mock exam"], ["leads", "⌁", "Lead delivery"],
];

const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[c]));
const money = (value) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value || 0);
const date = (value) => value ? new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value)) : "—";
const datetimeLocal = (value) => value ? new Date(value).toISOString().slice(0, 16) : "";
const status = (active, label = active ? "Active" : "Hidden") => `<span class="status ${active ? "good" : "muted"}">${label}</span>`;
const batchPhase = (batch) => { const today = new Date().toISOString().slice(0, 10); if (!batch.is_active) return status(false, "Hidden"); if (batch.end_date < today) return status(false, "Completed"); if (batch.start_date <= today) return status(true, "Running"); return `<span class="status warning">Upcoming</span>`; };

function notice(message, error = false) {
  const item = document.createElement("div"); item.className = `toast ${error ? "error" : ""}`; item.textContent = message;
  toastRegion.append(item); setTimeout(() => item.remove(), 4500);
}

function problem(error) {
  const detail = error?.detail || error?.message || "Something went wrong. Please try again.";
  notice(detail, true);
}

async function token() {
  if (!state.user) throw new Error("Your session has ended. Please sign in again.");
  return state.user.getIdToken();
}

async function api(path, { method = "GET", body, form = false } = {}) {
  const headers = { Authorization: `Bearer ${await token()}` };
  if (body && !form) headers["Content-Type"] = "application/json";
  const response = await fetch(`/api/v1${path}`, { method, headers, body: body ? (form ? body : JSON.stringify(body)) : undefined });
  if (!response.ok) {
    let payload = {}; try { payload = await response.json(); } catch (_) { /* non-json response */ }
    const error = new Error(payload.detail || `Request failed (${response.status})`); Object.assign(error, payload); throw error;
  }
  if (response.status === 204) return null;
  const type = response.headers.get("content-type") || "";
  return type.includes("application/json") ? response.json() : response.blob();
}

async function secureFile(path, filename) {
  const preview = window.open("", "_blank");
  try {
    const blob = await api(path); const url = URL.createObjectURL(blob);
    if (preview) preview.location = url;
    else Object.assign(document.createElement("a"), { href: url, download: filename }).click();
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (error) { preview?.close(); problem(error); }
}

function modal(title, body, footer = "") {
  document.querySelector("#modal")?.remove();
  const el = document.createElement("div"); el.id = "modal"; el.className = "modal-backdrop";
  el.innerHTML = `<section class="modal" role="dialog" aria-modal="true" aria-label="${escapeHtml(title)}"><header class="modal-head"><h2>${escapeHtml(title)}</h2><button class="close" data-close-modal aria-label="Close">×</button></header><div class="modal-body">${body}</div>${footer ? `<footer class="modal-foot">${footer}</footer>` : ""}</section>`;
  el.addEventListener("click", (event) => { if (event.target === el || event.target.closest("[data-close-modal]")) el.remove(); }); document.body.append(el);
  return el;
}

function confirmAction(title, message, actionLabel = "Delete") {
  return new Promise((resolve) => {
    const el = modal(title, `<p style="margin:0;color:var(--muted);line-height:1.55">${escapeHtml(message)}</p>`, `<button class="button secondary" data-cancel>Cancel</button><button class="button danger" data-confirm>${escapeHtml(actionLabel)}</button>`);
    el.querySelector("[data-cancel]").onclick = () => { el.remove(); resolve(false); };
    el.querySelector("[data-confirm]").onclick = () => { el.remove(); resolve(true); };
  });
}

function loginScreen(message = "Sign in with an authorized Firebase administrator account.") {
  root.innerHTML = `<main class="auth-shell"><section class="auth-card"><div class="brand-mark">C</div><h1>College Control</h1><p>${escapeHtml(message)}</p><form id="login-form"><div class="field"><label>Email address</label><input required type="email" name="email" autocomplete="email" /></div><div class="field"><label>Password</label><input required type="password" name="password" autocomplete="current-password" /></div><button class="button" type="submit">Sign in securely</button></form><form id="totp-form" hidden><div class="field"><label>Authenticator code</label><input required inputmode="numeric" autocomplete="one-time-code" name="code" placeholder="123456" /></div><button class="button" type="submit">Verify code</button></form></section></main>`;
  root.querySelector("#login-form").onsubmit = async (event) => {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    try { await signInWithEmailAndPassword(state.auth, form.get("email"), form.get("password")); }
    catch (error) {
      if (error.code === "auth/multi-factor-auth-required") {
        state.resolver = getMultiFactorResolver(state.auth, error); root.querySelector("#login-form").hidden = true; root.querySelector("#totp-form").hidden = false; notice("Enter the code from Google Authenticator.");
      } else problem(error);
    }
  };
  root.querySelector("#totp-form").onsubmit = async (event) => {
    event.preventDefault();
    try { const code = new FormData(event.currentTarget).get("code"); const hint = state.resolver?.hints?.[0]; if (!hint) throw new Error("No authenticator factor is available for this account."); await state.resolver.resolveSignIn(TotpMultiFactorGenerator.assertionForSignIn(hint.uid, code)); }
    catch (error) { problem(error); }
  };
}

async function enrollAuthenticator(user) {
  try {
    const session = await multiFactor(user).getSession();
    const secret = await TotpMultiFactorGenerator.generateSecret(session);
    const accountName = user.email || "College administrator";
    root.innerHTML = `<main class="auth-shell"><section class="auth-card"><div class="brand-mark">C</div><h1>Set up Google Authenticator</h1><p>Open Google Authenticator, choose <strong>Enter a setup key</strong>, then enter the details below. Use a time-based code.</p><div class="auth-secret"><span>Account</span><strong>${escapeHtml(accountName)}</strong><span>Issuer</span><strong>College Control</strong><span>Setup key</span><code>${escapeHtml(secret.secretKey)}</code></div><form id="enroll-totp-form"><div class="field"><label>6-digit authenticator code</label><input required inputmode="numeric" autocomplete="one-time-code" name="code" placeholder="123456" /></div><button class="button" type="submit">Complete secure setup</button><button class="text-button" type="button" id="cancel-enrolment">Sign out</button></form></section></main>`;
    root.querySelector("#cancel-enrolment").onclick = () => signOut(state.auth);
    root.querySelector("#enroll-totp-form").onsubmit = async (event) => {
      event.preventDefault();
      try {
        const code = new FormData(event.currentTarget).get("code");
        const assertion = TotpMultiFactorGenerator.assertionForEnrollment(secret, code);
        await multiFactor(user).enroll(assertion, "College Control");
        await user.getIdToken(true);
        notice("Google Authenticator is set up.");
        shell(); renderPage();
      } catch (error) { problem(error); }
    };
  } catch (error) {
    problem(error);
    await signOut(state.auth);
  }
}

function shell() {
  const initial = (state.user?.email || "A").slice(0, 1).toUpperCase();
  root.innerHTML = `<div class="shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">C</span><span>College Admin</span></div><nav>${nav.map(([id, icon, label]) => `<button class="nav-item ${state.page === id ? "active" : ""}" data-page="${id}"><span class="nav-icon">${icon}</span><span>${label}</span></button>`).join("")}</nav><p class="sidebar-footer">Securely connected to the existing FastAPI administration APIs.</p></aside><main class="main"><header class="topbar"><div><strong>Administration</strong><div class="eyebrow">Content, admissions and student services</div></div><div class="user-menu"><span class="user-email">${escapeHtml(state.user?.email || "")}</span><span class="avatar">${initial}</span><button class="text-button" id="sign-out">Sign out</button></div></header><section id="page" class="page"><div class="loading"><div class="spinner"></div></div></section></main></div>`;
  root.querySelectorAll("[data-page]").forEach((button) => button.onclick = () => { state.page = button.dataset.page; shell(); renderPage(); });
  root.querySelector("#sign-out").onclick = () => signOut(state.auth);
}

const title = (heading, copy, action = "") => `<div class="page-title"><div><h1>${heading}</h1><p>${copy}</p></div>${action}</div>`;
const panel = (heading, body, action = "") => `<section class="panel"><header class="panel-head"><h2>${heading}</h2>${action}</header>${body}</section>`;
const table = (headers, rows, empty = "No records yet.") => `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows || `<tr><td colspan="${headers.length}" class="empty">${empty}</td></tr>`}</tbody></table></div>`;

async function renderPage() {
  const target = root.querySelector("#page");
  try {
    const pages = { dashboard, settings, courses, batches, brochures, banners, announcements, gallery, videos, exam, leads };
    await pages[state.page](target);
  } catch (error) {
    if (error.status === 401 || error.status === 403) { notice("Your administrator session is no longer authorized.", true); await signOut(state.auth); return; }
    target.innerHTML = `${title("Unable to load this page", "The API returned an error.")}<section class="panel"><div class="empty">${escapeHtml(error.detail || error.message)}</div></section>`;
  }
}

async function dashboard(target) {
  const [courses, batches, brochures, sets, lead] = await Promise.all([api("/admin/courses"), api("/admin/batches"), api("/admin/brochures"), api("/admin/exam/sets"), api("/admin/lead-sync/status")]);
  target.innerHTML = `${title("Welcome back", "Manage your website content and admissions operations from one place.")}<div class="grid cards"><div class="card metric"><small>Active courses</small><strong>${courses.filter((x) => x.is_active).length}</strong></div><div class="card metric"><small>Active batches</small><strong>${batches.filter((x) => x.is_active).length}</strong></div><div class="card metric"><small>Brochures ready</small><strong>${brochures.filter((x) => x.has_brochure).length}/3</strong></div><div class="card metric"><small>Queued sheet rows</small><strong>${lead.pending_rows}</strong></div></div><div class="grid two-col" style="margin-top:18px">${panel("Exam-set readiness", `<div class="detail-list">${sets.map((item) => `<div><span>Question set ${item.slot}</span><strong>${item.exam_set ? `${item.exam_set.question_count} questions` : "Not uploaded"}</strong></div>`).join("")}</div>`, `<button class="button secondary small" data-page-link="exam">Manage sets</button>`)}${panel("Quick actions", `<div class="actions"><button class="button secondary" data-page-link="courses">Edit courses</button><button class="button secondary" data-page-link="brochures">Upload brochure</button><button class="button secondary" data-page-link="banners">Manage banners</button><button class="button secondary" data-page-link="leads">Lead delivery</button></div>`)}</div>`;
  bindPageLinks(target);
}

async function settings(target) {
  const item = await api("/admin/site-settings");
  target.innerHTML = `${title("Contact & website settings", "Changes are saved to the existing site_settings database row.")}<section class="panel"><div class="panel-body"><form id="settings-form"><div class="form-grid"><div class="field"><label>Phone number</label><input name="phone" value="${escapeHtml(item.phone || "")}" /></div><div class="field"><label>WhatsApp number</label><input name="whatsapp" value="${escapeHtml(item.whatsapp || "")}" /></div><div class="field"><label>Email address</label><input name="email" type="email" value="${escapeHtml(item.email || "")}" /></div><div class="field"><label>Google Form link</label><input name="google_form_url" type="url" value="${escapeHtml(item.google_form_url || "")}" /></div><div class="field full"><label>College address</label><textarea name="address">${escapeHtml(item.address || "")}</textarea></div><div class="field"><label>Facebook URL</label><input name="facebook" value="${escapeHtml(item.social_links.facebook || "")}" /></div><div class="field"><label>Instagram URL</label><input name="instagram" value="${escapeHtml(item.social_links.instagram || "")}" /></div><div class="field"><label>YouTube URL</label><input name="youtube" value="${escapeHtml(item.social_links.youtube || "")}" /></div><div class="field"><label>LinkedIn URL</label><input name="linkedin" value="${escapeHtml(item.social_links.linkedin || "")}" /></div><div class="field"><label>X / Twitter URL</label><input name="x" value="${escapeHtml(item.social_links.x || "")}" /></div></div><div class="actions"><button class="button" type="submit">Save contact settings</button></div></form></div></section>`;
  target.querySelector("#settings-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); const social = Object.fromEntries(["facebook", "instagram", "youtube", "linkedin", "x"].map((k) => [k, f.get(k) || null])); try { await api("/admin/site-settings", { method: "PUT", body: { phone: f.get("phone") || null, whatsapp: f.get("whatsapp") || null, email: f.get("email") || null, address: f.get("address") || null, google_form_url: f.get("google_form_url") || null, social_links: social } }); notice("Contact settings saved."); } catch (error) { problem(error); } };
}

async function courses(target) {
  const items = await api("/admin/courses"); state.cache.courses = items;
  target.innerHTML = `${title("Courses & fees", "Edit the existing course records, information and year-wise fee structures.")}${panel("Course catalogue", table(["Course", "Duration", "Total fee", "Status", ""], items.map((item) => `<tr><td><strong>${escapeHtml(item.name)}</strong><br><small>${escapeHtml(item.code)}</small></td><td>${escapeHtml(item.duration_text)}</td><td>${money(item.total_fee_inr)}</td><td>${status(item.is_active)}</td><td><button class="button secondary small" data-edit-course="${item.code}">Edit</button></td></tr>`).join("")))}`;
  target.querySelectorAll("[data-edit-course]").forEach((button) => button.onclick = () => courseModal(items.find((x) => x.code === button.dataset.editCourse)));
}

function courseModal(item) {
  const fees = item.fee_breakup || [];
  const rows = fees.map((row) => feeRow(row.label, row.amount_inr)).join("");
  const el = modal(`Edit ${item.name}`, `<form id="course-form"><div class="form-grid"><div class="field"><label>Course name</label><input name="name" required value="${escapeHtml(item.name)}" /></div><div class="field"><label>Duration</label><input name="duration_text" required value="${escapeHtml(item.duration_text)}" /></div><div class="field"><label>Total fee (₹)</label><input name="total_fee_inr" required type="number" min="0" value="${item.total_fee_inr}" /></div><div class="field"><label>Display order</label><input name="display_order" required type="number" min="0" value="${item.display_order}" /></div><div class="field full"><label>Summary</label><textarea name="summary">${escapeHtml(item.summary || "")}</textarea></div><div class="field full"><label>Eligibility</label><textarea name="eligibility">${escapeHtml(item.eligibility || "")}</textarea></div><div class="field full"><label>Fee note</label><input name="fee_note" value="${escapeHtml(item.fee_note || "")}" /></div><label class="check"><input name="is_active" type="checkbox" ${item.is_active ? "checked" : ""} /> Show this course on the public site</label></div><div class="field"><label>Year-wise fee breakdown</label><div id="fee-rows">${rows}</div><button class="button secondary small" id="add-fee" type="button">+ Add fee year</button></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="course-form">Save course</button>`);
  el.querySelector("#add-fee").onclick = () => el.querySelector("#fee-rows").insertAdjacentHTML("beforeend", feeRow("", ""));
  el.querySelector("#fee-rows").addEventListener("click", (event) => event.target.closest("[data-remove-fee]")?.parentElement.remove());
  el.querySelector("#course-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); const fee_breakup = [...el.querySelectorAll(".fee-row")].map((row) => ({ label: row.querySelector("[name=fee_label]").value.trim(), amount_inr: Number(row.querySelector("[name=fee_amount]").value) })).filter((row) => row.label); try { await api(`/admin/courses/${item.code}`, { method: "PATCH", body: { name: f.get("name"), duration_text: f.get("duration_text"), total_fee_inr: Number(f.get("total_fee_inr")), display_order: Number(f.get("display_order")), summary: f.get("summary") || null, eligibility: f.get("eligibility") || null, fee_note: f.get("fee_note") || null, fee_breakup, is_active: f.get("is_active") === "on" } }); el.remove(); notice("Course saved."); renderPage(); } catch (error) { problem(error); } };
}
const feeRow = (label, amount) => `<div class="fee-row"><input name="fee_label" placeholder="Year 1" value="${escapeHtml(label)}" /><input name="fee_amount" type="number" min="0" placeholder="Amount" value="${escapeHtml(amount)}" /><button type="button" class="button secondary small" data-remove-fee>×</button></div>`;

async function batches(target) {
  const [items, courses] = await Promise.all([api("/admin/batches"), api("/admin/courses")]); state.cache.courses = courses;
  target.innerHTML = `${title("Batches", "Schedule online and offline batches for each course.", `<button class="button" id="add-batch">+ Add batch</button>`)}<div class="toolbar"><input class="search" placeholder="Search course, timing or mode" data-filter /></div>${panel("Batch timeline", table(["Course", "Dates", "Timings", "Mode", "Status", ""], items.map((item) => `<tr data-search="${escapeHtml(`${item.course_name} ${item.timings} ${item.mode}`)}"><td><strong>${escapeHtml(item.course_name)}</strong></td><td>${date(item.start_date)}<br><small>to ${date(item.end_date)}</small></td><td>${escapeHtml(item.timings)}</td><td>${escapeHtml(item.mode)}</td><td>${batchPhase(item)}</td><td><button class="button secondary small" data-edit-batch="${item.id}">Edit</button> <button class="button danger small" data-delete-batch="${item.id}">Delete</button></td></tr>`).join("")))}`;
  filterTable(target); target.querySelector("#add-batch").onclick = () => batchModal(null, courses);
  target.querySelectorAll("[data-edit-batch]").forEach((button) => button.onclick = () => batchModal(items.find((x) => x.id === button.dataset.editBatch), courses));
  target.querySelectorAll("[data-delete-batch]").forEach((button) => button.onclick = async () => { if (await confirmAction("Delete batch", "This batch will no longer appear on the website.")) { try { await api(`/admin/batches/${button.dataset.deleteBatch}`, { method: "DELETE" }); notice("Batch deleted."); renderPage(); } catch (error) { problem(error); } } });
}

function batchModal(item, courses) {
  const create = !item; const el = modal(create ? "Add batch" : "Edit batch", `<form id="batch-form"><div class="form-grid">${create ? `<div class="field full"><label>Course</label><select name="course_code">${courses.map((course) => `<option value="${course.code}">${escapeHtml(course.name)}</option>`).join("")}</select></div>` : `<div class="field full"><label>Course</label><input disabled value="${escapeHtml(item.course_name)}" /></div>`}<div class="field"><label>Start date</label><input name="start_date" type="date" required value="${item?.start_date || ""}" /></div><div class="field"><label>End date</label><input name="end_date" type="date" required value="${item?.end_date || ""}" /></div><div class="field"><label>Batch timing</label><input name="timings" required value="${escapeHtml(item?.timings || "")}" placeholder="10:00 AM - 1:00 PM" /></div><div class="field"><label>Mode</label><select name="mode"><option value="offline" ${item?.mode === "offline" ? "selected" : ""}>Offline</option><option value="online" ${item?.mode === "online" ? "selected" : ""}>Online</option></select></div><label class="check"><input name="is_active" type="checkbox" ${item?.is_active !== false ? "checked" : ""}/> Active on website</label></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="batch-form">${create ? "Add batch" : "Save changes"}</button>`);
  el.querySelector("#batch-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); const payload = { start_date: f.get("start_date"), end_date: f.get("end_date"), timings: f.get("timings"), mode: f.get("mode"), is_active: f.get("is_active") === "on" }; if (create) payload.course_code = f.get("course_code"); try { await api(create ? "/admin/batches" : `/admin/batches/${item.id}`, { method: create ? "POST" : "PATCH", body: payload }); el.remove(); notice(create ? "Batch added." : "Batch updated."); renderPage(); } catch (error) { problem(error); } };
}

async function brochures(target) {
  const items = await api("/admin/brochures");
  target.innerHTML = `${title("Brochures", "Upload one private PDF per course. Students receive it only after verified OTP.")}${panel("Course brochures", table(["Course", "File", "Updated", ""], items.map((item) => `<tr><td><strong>${escapeHtml(item.course_name)}</strong><br><small>${item.course_code}</small></td><td>${item.has_brochure ? `${escapeHtml(item.original_filename)}<br><small>${Math.ceil(item.size_bytes / 1024)} KB</small>` : `<span class="status warning">Missing</span>`}</td><td>${date(item.updated_at)}</td><td><div class="actions"><button class="button secondary small" data-upload-brochure="${item.course_code}">${item.has_brochure ? "Replace" : "Upload"}</button>${item.has_brochure ? `<a class="button secondary small" target="_blank" href="/api/v1/admin/brochures/${item.course_code}/file">Preview</a><button class="button danger small" data-delete-brochure="${item.course_code}">Delete</button>` : ""}</div></td></tr>`).join("")))}`;
  target.querySelectorAll("[data-upload-brochure]").forEach((button) => button.onclick = () => brochureModal(button.dataset.uploadBrochure));
  target.querySelectorAll("[data-delete-brochure]").forEach((button) => button.onclick = async () => { if (await confirmAction("Remove brochure", "Students will no longer be able to download this PDF.")) { try { await api(`/admin/brochures/${button.dataset.deleteBrochure}`, { method: "DELETE" }); notice("Brochure removed."); renderPage(); } catch (error) { problem(error); } } });
}

function brochureModal(code) {
  const el = modal(`Upload ${code} brochure`, `<form id="brochure-form"><div class="file-drop"><label>Choose a PDF brochure<input style="margin-top:10px" name="file" accept="application/pdf,.pdf" type="file" required /></label><p id="file-name">Maximum size follows the backend limit.</p></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="brochure-form">Upload PDF</button>`);
  el.querySelector("input").onchange = (event) => { el.querySelector("#file-name").textContent = event.target.files[0]?.name || ""; };
  el.querySelector("#brochure-form").onsubmit = async (event) => { event.preventDefault(); const data = new FormData(event.currentTarget); try { await api(`/admin/brochures/${code}`, { method: "PUT", body: data, form: true }); el.remove(); notice("Brochure uploaded."); renderPage(); } catch (error) { problem(error); } };
}

async function banners(target) {
  const [items, courses] = await Promise.all([api("/admin/banners"), api("/admin/courses")]);
  target.innerHTML = `${title("Banners", "Control the website hero slider and optional brochure call-to-actions.", `<button class="button" id="add-banner">+ Add banner</button>`)}<div class="toolbar"><input class="search" placeholder="Search banners" data-filter /></div>${panel("Website banners", table(["Image", "Title", "Brochure button", "Order", "Status", ""], items.map((item) => `<tr data-search="${escapeHtml(item.title)}"><td><img class="preview" src="${escapeHtml(item.thumb_url)}" alt="" /></td><td><strong>${escapeHtml(item.title)}</strong></td><td>${item.course_code || "—"}</td><td>${item.display_order}</td><td>${status(item.is_active)}</td><td><button class="button secondary small" data-edit-banner="${item.id}">Edit</button> <button class="button secondary small" data-image-banner="${item.id}">Image</button> <button class="button danger small" data-delete-banner="${item.id}">Delete</button></td></tr>`).join("")))}`;
  filterTable(target); target.querySelector("#add-banner").onclick = () => bannerModal(null, courses); target.querySelectorAll("[data-edit-banner]").forEach((button) => button.onclick = () => bannerModal(items.find((x) => x.id === button.dataset.editBanner), courses)); target.querySelectorAll("[data-image-banner]").forEach((button) => button.onclick = () => imageReplaceModal("banner", button.dataset.imageBanner)); target.querySelectorAll("[data-delete-banner]").forEach((button) => button.onclick = async () => { if (await confirmAction("Delete banner", "The banner image will be removed from storage and the website.")) { try { await api(`/admin/banners/${button.dataset.deleteBanner}`, { method: "DELETE" }); notice("Banner deleted."); renderPage(); } catch (error) { problem(error); } } });
}

function bannerModal(item, courses) {
  const create = !item; const el = modal(create ? "Add banner" : "Edit banner", `<form id="banner-form"><div class="form-grid"><div class="field full"><label>Title</label><input required name="title" value="${escapeHtml(item?.title || "")}" /></div><div class="field"><label>Optional brochure button</label><select name="course_code"><option value="">No brochure button</option>${courses.map((c) => `<option value="${c.code}" ${item?.course_code === c.code ? "selected" : ""}>${escapeHtml(c.name)}</option>`).join("")}</select></div><div class="field"><label>Display order</label><input type="number" min="0" name="display_order" value="${item?.display_order || 0}" /></div><label class="check"><input type="checkbox" name="is_active" ${item?.is_active !== false ? "checked" : ""}/> Show on website</label>${create ? `<div class="field full"><label>Banner image</label><input required name="image" accept="image/jpeg,image/png,image/webp" type="file" /></div>` : ""}</div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="banner-form">${create ? "Upload banner" : "Save banner"}</button>`);
  el.querySelector("#banner-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); const payload = { title: f.get("title"), course_code: f.get("course_code") || null, display_order: Number(f.get("display_order")), is_active: f.get("is_active") === "on" }; try { if (create) { const data = new FormData(); Object.entries(payload).forEach(([k, v]) => data.append(k, v === null ? "" : v)); data.append("image", f.get("image")); await api("/admin/banners/", { method: "POST", body: data, form: true }); } else await api(`/admin/banners/${item.id}`, { method: "PATCH", body: payload }); el.remove(); notice(create ? "Banner uploaded." : "Banner saved."); renderPage(); } catch (error) { problem(error); } };
}

async function announcements(target) {
  const items = await api("/admin/announcements");
  target.innerHTML = `${title("Announcements", "Schedule prominent website notices, links and visibility.", `<button class="button" id="add-announcement">+ Add announcement</button>`)}<div class="toolbar"><input class="search" placeholder="Search announcements" data-filter /></div>${panel("Announcement strip", table(["Message", "Schedule", "Order", "Status", ""], items.map((item) => `<tr data-search="${escapeHtml(item.message)}"><td><strong>${escapeHtml(item.message)}</strong>${item.link_url ? `<br><small>${escapeHtml(item.link_url)}</small>` : ""}</td><td>${date(item.starts_at)} — ${date(item.ends_at)}</td><td>${item.display_order}</td><td>${status(item.is_active)}</td><td><button class="button secondary small" data-edit-announcement="${item.id}">Edit</button> <button class="button danger small" data-delete-announcement="${item.id}">Delete</button></td></tr>`).join("")))}`;
  filterTable(target); target.querySelector("#add-announcement").onclick = () => announcementModal(null); target.querySelectorAll("[data-edit-announcement]").forEach((button) => button.onclick = () => announcementModal(items.find((x) => x.id === button.dataset.editAnnouncement))); target.querySelectorAll("[data-delete-announcement]").forEach((button) => button.onclick = async () => { if (await confirmAction("Delete announcement", "This notice will be permanently removed.")) { try { await api(`/admin/announcements/${button.dataset.deleteAnnouncement}`, { method: "DELETE" }); notice("Announcement deleted."); renderPage(); } catch (error) { problem(error); } } });
}

function announcementModal(item) {
  const create = !item; const el = modal(create ? "Add announcement" : "Edit announcement", `<form id="announcement-form"><div class="form-grid"><div class="field full"><label>Message</label><textarea required name="message">${escapeHtml(item?.message || "")}</textarea></div><div class="field full"><label>Optional link</label><input type="url" name="link_url" value="${escapeHtml(item?.link_url || "")}" /></div><div class="field"><label>Show from</label><input type="datetime-local" name="starts_at" value="${datetimeLocal(item?.starts_at)}" /></div><div class="field"><label>Show until</label><input type="datetime-local" name="ends_at" value="${datetimeLocal(item?.ends_at)}" /></div><div class="field"><label>Display order</label><input type="number" min="0" name="display_order" value="${item?.display_order || 0}" /></div><label class="check"><input type="checkbox" name="is_active" ${item?.is_active !== false ? "checked" : ""}/> Show on website</label></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="announcement-form">Save announcement</button>`);
  el.querySelector("#announcement-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); const body = { message: f.get("message"), link_url: f.get("link_url") || null, starts_at: f.get("starts_at") ? new Date(f.get("starts_at")).toISOString() : null, ends_at: f.get("ends_at") ? new Date(f.get("ends_at")).toISOString() : null, display_order: Number(f.get("display_order")), is_active: f.get("is_active") === "on" }; try { await api(create ? "/admin/announcements" : `/admin/announcements/${item.id}`, { method: create ? "POST" : "PUT", body }); el.remove(); notice("Announcement saved."); renderPage(); } catch (error) { problem(error); } };
}

async function gallery(target) {
  const items = await api("/admin/gallery");
  target.innerHTML = `${title("Gallery", "Upload photos, captions and website order.", `<button class="button" id="add-gallery">+ Upload photos</button>`)}<div class="toolbar"><input class="search" placeholder="Search captions" data-filter /></div>${panel("Gallery images", table(["Image", "Caption", "Order", "Status", ""], items.map((item) => `<tr data-search="${escapeHtml(item.caption || "")}"><td><img class="preview" src="${escapeHtml(item.thumb_url)}" alt="" /></td><td>${escapeHtml(item.caption || "—")}</td><td>${item.display_order}</td><td>${status(item.is_active)}</td><td><button class="button secondary small" data-edit-gallery="${item.id}">Edit</button> <button class="button danger small" data-delete-gallery="${item.id}">Delete</button></td></tr>`).join("")))}`;
  filterTable(target); target.querySelector("#add-gallery").onclick = () => galleryUploadModal(); target.querySelectorAll("[data-edit-gallery]").forEach((button) => button.onclick = () => galleryEditModal(items.find((x) => x.id === button.dataset.editGallery))); target.querySelectorAll("[data-delete-gallery]").forEach((button) => button.onclick = async () => { if (await confirmAction("Delete gallery image", "The image will be removed from storage and the website.")) { try { await api(`/admin/gallery/${button.dataset.deleteGallery}`, { method: "DELETE" }); notice("Image deleted."); renderPage(); } catch (error) { problem(error); } } });
}

function galleryUploadModal() {
  const el = modal("Upload gallery photos", `<form id="gallery-upload"><div class="file-drop"><label>Select one or more JPEG, PNG or WebP photos<input required name="images" multiple accept="image/jpeg,image/png,image/webp" type="file" /></label><p id="image-count">Each photo is resized and stored using the existing image pipeline.</p></div><div class="form-grid"><div class="field"><label>Caption for one image (optional)</label><input name="caption" /></div><div class="field"><label>Starting display order</label><input name="display_order" type="number" min="0" value="0" /></div></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="gallery-upload">Upload photos</button>`);
  el.querySelector("input[type=file]").onchange = (event) => { el.querySelector("#image-count").textContent = `${event.target.files.length} photo(s) selected.`; };
  el.querySelector("#gallery-upload").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); const files = [...f.getAll("images")].filter((x) => x instanceof File && x.size); try { for (let i = 0; i < files.length; i += 1) { const data = new FormData(); data.append("image", files[i]); data.append("caption", files.length === 1 ? f.get("caption") : ""); data.append("display_order", String(Number(f.get("display_order")) + i)); await api("/admin/gallery", { method: "POST", body: data, form: true }); } el.remove(); notice(`${files.length} photo(s) uploaded.`); renderPage(); } catch (error) { problem(error); } };
}

function galleryEditModal(item) {
  const el = modal("Edit gallery image", `<img class="preview-large" src="${escapeHtml(item.image_url)}" alt="" /><form id="gallery-form" style="margin-top:16px"><div class="form-grid"><div class="field full"><label>Caption</label><input name="caption" value="${escapeHtml(item.caption || "")}" /></div><div class="field"><label>Display order</label><input name="display_order" type="number" min="0" value="${item.display_order}" /></div><label class="check"><input name="is_active" type="checkbox" ${item.is_active ? "checked" : ""}/> Show on website</label></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="gallery-form">Save image</button>`);
  el.querySelector("#gallery-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); try { await api(`/admin/gallery/${item.id}`, { method: "PATCH", body: { caption: f.get("caption") || null, display_order: Number(f.get("display_order")), is_active: f.get("is_active") === "on" } }); el.remove(); notice("Gallery image saved."); renderPage(); } catch (error) { problem(error); } };
}

async function videos(target) {
  const items = await api("/admin/videos");
  target.innerHTML = `${title("Videos", "Manage YouTube, YouTube Shorts and Instagram Reel links.", `<button class="button" id="add-video">+ Add video</button>`)}<div class="toolbar"><input class="search" placeholder="Search videos" data-filter /></div>${panel("Video library", table(["Video", "Platform", "Preview", "Order", "Status", ""], items.map((item) => `<tr data-search="${escapeHtml(`${item.title} ${item.platform}`)}"><td><strong>${escapeHtml(item.title)}</strong><br><small>${escapeHtml(item.url)}</small></td><td>${escapeHtml(item.platform.replaceAll("_", " "))}</td><td><a class="button secondary small" target="_blank" href="${escapeHtml(item.embed_url)}">Preview</a></td><td>${item.display_order}</td><td>${status(item.is_active)}</td><td><button class="button secondary small" data-edit-video="${item.id}">Edit</button> <button class="button danger small" data-delete-video="${item.id}">Delete</button></td></tr>`).join("")))}`;
  filterTable(target); target.querySelector("#add-video").onclick = () => videoModal(null); target.querySelectorAll("[data-edit-video]").forEach((button) => button.onclick = () => videoModal(items.find((x) => x.id === button.dataset.editVideo))); target.querySelectorAll("[data-delete-video]").forEach((button) => button.onclick = async () => { if (await confirmAction("Delete video", "This embedded video will be removed from the website.")) { try { await api(`/admin/videos/${button.dataset.deleteVideo}`, { method: "DELETE" }); notice("Video deleted."); renderPage(); } catch (error) { problem(error); } } });
}

function videoModal(item) {
  const create = !item; const el = modal(create ? "Add video" : "Edit video", `<form id="video-form"><div class="form-grid"><div class="field full"><label>Title</label><input required name="title" value="${escapeHtml(item?.title || "")}" /></div><div class="field full"><label>YouTube, Shorts or Instagram Reel URL</label><input required type="url" name="url" value="${escapeHtml(item?.url || "")}" /></div><div class="field"><label>Display order</label><input name="display_order" type="number" min="0" value="${item?.display_order || 0}" /></div><label class="check"><input name="is_active" type="checkbox" ${item?.is_active !== false ? "checked" : ""}/> Show on website</label></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="video-form">Save video</button>`);
  el.querySelector("#video-form").onsubmit = async (event) => { event.preventDefault(); const f = new FormData(event.currentTarget); try { await api(create ? "/admin/videos" : `/admin/videos/${item.id}`, { method: create ? "POST" : "PUT", body: { title: f.get("title"), url: f.get("url"), display_order: Number(f.get("display_order")), is_active: f.get("is_active") === "on" } }); el.remove(); notice("Video saved."); renderPage(); } catch (error) { problem(error); } };
}

async function exam(target) {
  const sets = await api("/admin/exam/sets");
  target.innerHTML = `${title("Mock exam", "Validate, preview and manage the three existing question-set slots.", `<a class="button secondary" href="/api/v1/admin/exam/template">Download Excel template</a>`)}${panel("Question sets", `<div class="grid cards">${sets.map((item) => `<article class="card metric"><small>Set ${item.slot}</small><strong>${item.exam_set ? item.exam_set.question_count : 0}</strong><p>${item.exam_set ? escapeHtml(item.exam_set.name) : "No file uploaded"}</p><div class="actions"><button class="button secondary small" data-exam-upload="${item.slot}">${item.exam_set ? "Replace" : "Upload"}</button>${item.exam_set ? `<button class="button danger small" data-exam-delete="${item.slot}">Remove</button>` : ""}</div></article>`).join("")}</div>`)}`;
  target.querySelectorAll("[data-exam-upload]").forEach((button) => button.onclick = () => examUploadModal(Number(button.dataset.examUpload), sets.find((x) => x.slot === Number(button.dataset.examUpload)))); target.querySelectorAll("[data-exam-delete]").forEach((button) => button.onclick = () => deleteExamSet(Number(button.dataset.examDelete)));
}

function examUploadModal(slot, existing) {
  const el = modal(`Question set ${slot}`, `<form id="exam-form"><div class="field"><label>Set name</label><input name="name" value="${escapeHtml(existing?.exam_set?.name || `Set ${slot}`)}" /></div><div class="file-drop"><label>Excel question file (.xlsx)<input required name="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" type="file" /></label><p id="exam-validation">Select a file, then validate before importing.</p></div><div class="actions"><button class="button secondary" id="validate-exam" type="button">Validate file</button></div><div id="validation-report"></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" id="import-exam" form="exam-form" disabled>${existing?.exam_set ? "Replace set" : "Import set"}</button>`);
  let validated = false;
  el.querySelector("#validate-exam").onclick = async () => {
    const input = el.querySelector("input[type=file]");
    if (!input.files[0]) return notice("Choose an Excel file first.", true);
    const data = new FormData(); data.append("file", input.files[0]);
    try {
      const preview = await api("/admin/exam/sets/preview", { method: "POST", body: data, form: true });
      const report = preview.report; validated = report.ok; el.querySelector("#import-exam").disabled = !validated;
      const issues = [...report.errors, ...report.warnings];
      const questionPreview = preview.questions.length ? `<h3>Question preview</h3><ol>${preview.questions.map((q) => `<li><strong>${escapeHtml(`${q.section} · ${q.subsection}`)}</strong><br>${escapeHtml(q.content.map((part) => part.text || "").join(" "))}<br><small>${q.options.map(escapeHtml).join(" · ")}</small></li>`).join("")}</ol>` : "";
      el.querySelector("#validation-report").innerHTML = `<div class="detail-list" style="margin-top:14px"><div><span>Questions found</span><strong>${report.question_count}</strong></div><div><span>Passages found</span><strong>${report.passage_count}</strong></div><div><span>Validation</span>${report.ok ? status(true, "Ready to import") : `<span class="status warning">Fix issues first</span>`}</div></div>${issues.length ? `<ul>${issues.slice(0, 12).map((issue) => `<li>${escapeHtml(`${issue.sheet}${issue.row ? ` row ${issue.row}` : ""}: ${issue.message}`)}</li>`).join("")}</ul>` : ""}${questionPreview}`;
    } catch (error) { problem(error); }
  };
  el.querySelector("#exam-form").onsubmit = async (event) => { event.preventDefault(); if (!validated) return notice("Validate the file successfully before importing.", true); const f = new FormData(event.currentTarget); try { if (existing?.exam_set && !(await confirmAction("Replace question set", "The current set will be deleted before this validated file is imported. Active student attempts using it will expire.", "Replace"))) return; if (existing?.exam_set) await api(`/admin/exam/sets/${slot}`, { method: "DELETE" }); await api(`/admin/exam/sets/${slot}`, { method: "POST", body: f, form: true }); el.remove(); notice("Question set imported."); renderPage(); } catch (error) { problem(error); } };
}

async function deleteExamSet(slot) { if (await confirmAction("Remove question set", "Students will not be assigned this set after it is removed.")) { try { await api(`/admin/exam/sets/${slot}`, { method: "DELETE" }); notice("Question set removed."); renderPage(); } catch (error) { problem(error); } } }

async function leads(target) {
  const item = await api("/admin/lead-sync/status");
  target.innerHTML = `${title("Lead delivery", "Brochure-download and exam-registration leads continue to use the existing Google Sheets integration.", item.spreadsheet_url ? `<a class="button" target="_blank" href="${escapeHtml(item.spreadsheet_url)}">Open connected spreadsheet</a>` : "")}<div class="grid cards"><div class="card metric"><small>Rows waiting to sync</small><strong>${item.pending_rows}</strong></div><div class="card metric"><small>Oldest queued row</small><strong style="font-size:17px">${date(item.oldest_pending_since)}</strong></div><div class="card metric"><small>Highest retry count</small><strong>${item.max_attempts_so_far}</strong></div></div><section class="panel" style="margin-top:18px"><div class="panel-body"><p style="color:var(--muted);margin-top:0">If Google Sheets is temporarily unavailable, the backend retains a retry row in PostgreSQL and Cloud Scheduler retries it. You can trigger a secure retry now.</p><button id="flush-leads" class="button">Retry pending rows</button></div></section>`;
  target.querySelector("#flush-leads").onclick = async () => { try { const result = await api("/admin/lead-sync/flush", { method: "POST" }); notice(`Delivered: ${result.delivered}; still pending: ${result.still_pending}.`); renderPage(); } catch (error) { problem(error); } };
}

function imageReplaceModal(kind, id) {
  const el = modal("Replace banner image", `<form id="replace-image"><div class="field"><label>New JPEG, PNG or WebP image</label><input name="image" required accept="image/jpeg,image/png,image/webp" type="file" /></div></form>`, `<button class="button secondary" data-close-modal>Cancel</button><button class="button" form="replace-image">Replace image</button>`);
  el.querySelector("#replace-image").onsubmit = async (event) => { event.preventDefault(); try { await api(`/admin/${kind}s/${id}/image`, { method: "PUT", body: new FormData(event.currentTarget), form: true }); el.remove(); notice("Image replaced."); renderPage(); } catch (error) { problem(error); } };
}

function filterTable(target) { const input = target.querySelector("[data-filter]"); if (!input) return; input.oninput = () => target.querySelectorAll("tr[data-search]").forEach((row) => { row.hidden = !row.dataset.search.toLowerCase().includes(input.value.toLowerCase()); }); }
function bindPageLinks(target) { target.querySelectorAll("[data-page-link]").forEach((button) => button.onclick = () => { state.page = button.dataset.pageLink; shell(); renderPage(); }); }

root.addEventListener("click", (event) => {
  const link = event.target.closest('a[href^="/api/v1/admin/"]');
  if (!link) return;
  event.preventDefault();
  secureFile(link.getAttribute("href").replace("/api/v1", ""), "download");
});

async function boot() {
  const config = window.__FIREBASE_CONFIG__;
  if (!config?.apiKey || !config?.authDomain || !config?.appId) { loginScreen("Firebase web configuration is missing. Set FIREBASE_WEB_* values for this environment before signing in."); return; }
  state.auth = getAuth(initializeApp(config));
  onAuthStateChanged(state.auth, async (user) => {
    state.user = user;
    if (!user) { loginScreen(); return; }
    try {
      await user.getIdToken(true);
      await api("/admin/me");
      shell(); renderPage();
    } catch (error) {
      if (error.code === "MFA_REQUIRED") { await enrollAuthenticator(user); return; }
      problem(error);
      await signOut(state.auth);
    }
  });
}
boot();
