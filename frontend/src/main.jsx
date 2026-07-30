import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowClockwise,
  Books,
  Broadcast,
  CaretLeft,
  ChartLine,
  ChatsCircle,
  CheckCircle,
  CloudArrowUp,
  CreditCard,
  DoorOpen,
  DownloadSimple,
  Eye,
  GraduationCap,
  Heartbeat,
  House,
  Key,
  ListChecks,
  Lock,
  MonitorPlay,
  PlayCircle,
  Plus,
  ShieldCheck,
  SignOut,
  Student,
  Trash,
  UploadSimple,
  UsersThree,
  VideoCamera,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace("http://", "ws://").replace("https://", "wss://");

function unwrap(data) {
  if (data && typeof data === "object" && "success" in data && "payload" in data) return data.payload;
  return data;
}

async function api(path, options = {}, token) {
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await response.text();
  const json = text ? JSON.parse(text) : null;
  if (!response.ok || json?.success === false) {
    throw new Error(json?.message || json?.detail || `HTTP ${response.status}`);
  }
  return unwrap(json);
}

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .trim()
    .replace(/['"]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function useForm(initial) {
  const [values, setValues] = useState(initial);
  const bind = (name) => ({
    value: values[name] ?? "",
    onChange: (event) => setValues((current) => ({ ...current, [name]: event.target.value })),
  });
  const set = (patch) => setValues((current) => ({ ...current, ...patch }));
  const reset = (next = initial) => setValues(next);
  return { values, bind, set, reset };
}

function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

function TextInput(props) {
  return <input {...props} />;
}

function TextArea(props) {
  return <textarea rows={props.rows || 3} {...props} />;
}

function Select({ children, ...props }) {
  return <select {...props}>{children}</select>;
}

function Button({ children, variant = "primary", busy, icon, ...props }) {
  return (
    <button className={`btn ${variant}`} disabled={busy || props.disabled} {...props}>
      {busy ? <ArrowClockwise className="spin" size={17} /> : icon}
      <span>{children}</span>
    </button>
  );
}

function IconButton({ label, icon, variant = "ghost", ...props }) {
  return (
    <button className={`icon-btn ${variant}`} aria-label={label} title={label} {...props}>
      {icon}
    </button>
  );
}

function Toast({ notice, onClose }) {
  if (!notice) return null;
  const destructive = notice.type === "delete" || notice.type === "error";
  return (
    <div className={`toast ${notice.type || "success"}`} role="status" aria-live="polite">
      {destructive ? <WarningCircle size={18} /> : <CheckCircle size={18} />}
      <span>{notice.message}</span>
      <button className="toast-close" type="button" aria-label="Notification yopish" onClick={onClose}>
        <X size={16} />
      </button>
    </div>
  );
}

function Modal({ title, open, onClose, children, width = "medium" }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className={`modal ${width}`} role="dialog" aria-modal="true" aria-labelledby="modal-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="modal-head">
          <h2 id="modal-title">{title}</h2>
          <IconButton label="Yopish" icon={<X size={18} />} onClick={onClose} />
        </header>
        {children}
      </section>
    </div>
  );
}

function Empty({ title, text, action, icon }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon || <WarningCircle size={22} />}</div>
      <strong>{title}</strong>
      <p>{text}</p>
      {action}
    </div>
  );
}

function DataLine({ label, value }) {
  return (
    <div className="data-line">
      <span>{label}</span>
      <strong>{value ?? "-"}</strong>
    </div>
  );
}

function IdPill({ value }) {
  if (!value) return <span className="muted">-</span>;
  return <code className="id-pill">{String(value).slice(0, 8)}</code>;
}

function Panel({ title, action, children }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function PageHeader({ title, eyebrow, actions }) {
  return (
    <header className="page-head">
      <div>
        <span className="section-kicker">{eyebrow}</span>
        <h1>{title}</h1>
      </div>
      <div className="page-actions">{actions}</div>
    </header>
  );
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token") || "");
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem("refresh_token") || "");
  const [me, setMe] = useState(null);
  const [schools, setSchools] = useState([]);
  const [schoolId, setSchoolId] = useState(localStorage.getItem("school_id") || "");
  const [courses, setCourses] = useState([]);
  const [publicCourses, setPublicCourses] = useState([]);
  const [products, setProducts] = useState([]);
  const [chats, setChats] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [exports, setExports] = useState([]);
  const [liveSessions, setLiveSessions] = useState([]);
  const [notice, setNotice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState("overview");

  const activeSchool = schools.find((school) => school.id === schoolId);

  const notify = (message, type = "success") => {
    setNotice({ message, type });
    window.clearTimeout(window.__exodeToast);
    window.__exodeToast = window.setTimeout(() => setNotice(null), 4000);
  };

  const saveTokens = (data) => {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);
  };

  const logout = async () => {
    if (refreshToken) {
      api("/api/v1/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) }).catch(() => null);
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("school_id");
    setToken("");
    setRefreshToken("");
    setMe(null);
    setSchools([]);
    setSchoolId("");
  };

  async function loadCore() {
    if (!token) return;
    setLoading(true);
    try {
      const [user, schoolRows] = await Promise.all([
        api("/api/v1/auth/me", {}, token),
        api("/api/v1/schools", {}, token),
      ]);
      setMe(user);
      setSchools(schoolRows || []);
      const nextSchoolId = schoolId || schoolRows?.[0]?.id || "";
      if (nextSchoolId) {
        setSchoolId(nextSchoolId);
        localStorage.setItem("school_id", nextSchoolId);
        await loadSchoolData(nextSchoolId);
      }
    } catch (error) {
      notify(error.message, "error");
      if (error.message.includes("Token")) logout();
    } finally {
      setLoading(false);
    }
  }

  async function loadSchoolData(id = schoolId) {
    if (!id || !token) return;
    const [courseRows, publicRows, productRows, chatRows, dashboard] = await Promise.all([
      api(`/api/v1/courses?school_id=${id}`, {}, token).catch(() => []),
      api(`/api/v1/public/courses?school_id=${id}`).catch(() => []),
      api(`/api/v1/products?school_id=${id}`).catch(() => []),
      api("/api/v1/chats", {}, token).catch(() => []),
      api(`/api/v1/analytics/dashboard?school_id=${id}`, {}, token).catch(() => null),
    ]);
    setCourses(courseRows || []);
    setPublicCourses(publicRows || []);
    setProducts(productRows || []);
    setChats(chatRows || []);
    setAnalytics(dashboard);
  }

  useEffect(() => {
    loadCore();
  }, [token]);

  if (!token) {
    return <AuthScreen onAuth={saveTokens} notify={notify} notice={notice} setNotice={setNotice} />;
  }

  const nav = [
    ["overview", "Umumiy", <House size={19} />],
    ["schools", "Schools", <GraduationCap size={19} />],
    ["courses", "Courses", <Books size={19} />],
    ["catalog", "Catalog", <Eye size={19} />],
    ["media", "Media", <VideoCamera size={19} />],
    ["payments", "Payments", <CreditCard size={19} />],
    ["learning", "Learning", <ListChecks size={19} />],
    ["messenger", "Messenger", <ChatsCircle size={19} />],
    ["analytics", "Analytics", <ChartLine size={19} />],
    ["exports", "Exports", <DownloadSimple size={19} />],
    ["live", "Live", <Broadcast size={19} />],
  ];

  return (
    <main className="shell">
      <Toast notice={notice} onClose={() => setNotice(null)} />
      <aside className="sidebar">
        <div className="brand">
          <div className="mark">E</div>
          <div>
            <strong>Exode</strong>
            <span>School platform</span>
          </div>
        </div>
        <nav className="nav-list">
          {nav.map(([key, label, icon]) => (
            <button key={key} className={active === key ? "active" : ""} onClick={() => setActive(key)}>
              {icon}
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div>
            <span>Account</span>
            <strong>{me?.email || "user"}</strong>
          </div>
          <Button variant="ghost" icon={<SignOut size={17} />} onClick={logout}>
            Chiqish
          </Button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="section-kicker">{activeSchool?.name || "School tanlanmagan"}</span>
            <h1>{nav.find(([key]) => key === active)?.[1] || "Dashboard"}</h1>
          </div>
          <div className="topbar-actions">
            <Select
              value={schoolId}
              onChange={(event) => {
                setSchoolId(event.target.value);
                localStorage.setItem("school_id", event.target.value);
                loadSchoolData(event.target.value);
              }}
            >
              <option value="">School tanlang</option>
              {schools.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </Select>
            <Button variant="secondary" icon={<ArrowClockwise size={17} />} busy={loading} onClick={loadCore}>
              Yangilash
            </Button>
          </div>
        </header>

        {active === "overview" && <Overview me={me} schools={schools} courses={courses} products={products} chats={chats} analytics={analytics} setActive={setActive} />}
        {active === "schools" && <SchoolsPanel token={token} notify={notify} schools={schools} schoolId={schoolId} setSchoolId={setSchoolId} reload={loadCore} />}
        {active === "courses" && <CoursesPanel token={token} notify={notify} schoolId={schoolId} courses={courses} reload={loadSchoolData} />}
        {active === "catalog" && <CatalogPanel publicCourses={publicCourses} schoolId={schoolId} reload={loadSchoolData} />}
        {active === "media" && <MediaPanel token={token} notify={notify} schoolId={schoolId} courses={courses} />}
        {active === "payments" && <PaymentsPanel token={token} notify={notify} schoolId={schoolId} courses={courses} products={products} reload={loadSchoolData} />}
        {active === "learning" && <LearningPanel token={token} notify={notify} courses={courses} />}
        {active === "messenger" && <MessengerPanel token={token} notify={notify} chats={chats} reload={loadSchoolData} />}
        {active === "analytics" && <AnalyticsPanel analytics={analytics} schoolId={schoolId} reload={loadSchoolData} />}
        {active === "exports" && <ExportsPanel token={token} notify={notify} schoolId={schoolId} exports={exports} setExports={setExports} />}
        {active === "live" && <LivePanel token={token} notify={notify} courses={courses} liveSessions={liveSessions} setLiveSessions={setLiveSessions} />}
      </section>
    </main>
  );
}

function AuthScreen({ onAuth, notify, notice, setNotice }) {
  const [mode, setMode] = useState("login");
  const [busy, setBusy] = useState(false);
  const form = useForm({ email: "owner@example.com", password: "password123", first_name: "Owner", last_name: "" });

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    try {
      const payload = mode === "register" ? form.values : { email: form.values.email, password: form.values.password };
      const data = await api(`/api/v1/auth/${mode}`, { method: "POST", body: JSON.stringify(payload) });
      onAuth(data);
      notify(mode === "register" ? "Account yaratildi" : "Login qilindi");
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <Toast notice={notice} onClose={() => setNotice(null)} />
      <section className="auth-card">
        <div className="auth-copy">
          <div className="mark">E</div>
          <h1>Exode Platform</h1>
          <p>Kurs, to'lov, media, chat va analyticsni bitta paneldan boshqaring.</p>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <div className="segmented">
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
              Login
            </button>
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
              Register
            </button>
          </div>
          <Field label="Email">
            <TextInput type="email" required autoComplete="email" {...form.bind("email")} />
          </Field>
          <Field label="Password">
            <TextInput type="password" required minLength={6} autoComplete={mode === "login" ? "current-password" : "new-password"} {...form.bind("password")} />
          </Field>
          {mode === "register" && (
            <div className="grid two">
              <Field label="First name">
                <TextInput {...form.bind("first_name")} />
              </Field>
              <Field label="Last name">
                <TextInput {...form.bind("last_name")} />
              </Field>
            </div>
          )}
          <Button busy={busy} icon={<Key size={17} />}>
            {mode === "register" ? "Account yaratish" : "Kirish"}
          </Button>
          <p className="form-note">Seed account: owner@example.com / password123</p>
        </form>
      </section>
    </main>
  );
}

function Overview({ me, schools, courses, products, chats, analytics, setActive }) {
  const stats = [
    ["Schools", schools.length, <GraduationCap size={22} />, "schools"],
    ["Courses", courses.length, <Books size={22} />, "courses"],
    ["Products", products.length, <CreditCard size={22} />, "payments"],
    ["Chats", chats.length, <ChatsCircle size={22} />, "messenger"],
  ];
  return (
    <div className="content-stack">
      <section className="hero-panel">
        <div>
          <span className="section-kicker">{me?.email}</span>
          <h2>Bugungi boshqaruv paneli</h2>
          <p>Kurslar, a'zolar, to'lovlar va dars jarayonlari holatini kuzating.</p>
        </div>
        <div className="hero-actions">
          <Button icon={<Plus size={17} />} onClick={() => setActive("courses")}>
            Kurslar
          </Button>
          <Button variant="secondary" icon={<ChartLine size={17} />} onClick={() => setActive("analytics")}>
            Hisobotlar
          </Button>
        </div>
      </section>
      <section className="stat-grid">
        {stats.map(([label, value, icon, target]) => (
          <button className="stat-card" key={label} onClick={() => setActive(target)}>
            <div>{icon}</div>
            <span>{label}</span>
            <strong>{value}</strong>
          </button>
        ))}
      </section>
      <section className="grid two">
        <Panel title="Daromad">
          <DataLine label="Revenue" value={`${analytics?.revenue || 0} UZS`} />
          <DataLine label="Paid invoices" value={analytics?.paid_invoices || 0} />
          <DataLine label="Students" value={analytics?.total_students || 0} />
          <DataLine label="Completed lessons" value={analytics?.completed_lessons || 0} />
        </Panel>
        <Panel title="Top kurslar">
          {analytics?.top_courses?.length ? (
            analytics.top_courses.map((course) => <DataLine key={course.title} label={course.title} value={`${course.students} student`} />)
          ) : (
            <Empty title="Hali data yo'q" text="Sotuv va enrolment bo'lganda top kurslar chiqadi." icon={<ChartLine size={22} />} />
          )}
        </Panel>
      </section>
    </div>
  );
}

function SchoolsPanel({ token, notify, schools, schoolId, setSchoolId, reload }) {
  const [createOpen, setCreateOpen] = useState(false);
  const [members, setMembers] = useState([]);
  const schoolForm = useForm({
    name: "",
    slug: "",
    description: "",
    primary_color: "#22c55e",
    secondary_color: "#111827",
    contact_phone: "",
    contact_telegram: "",
    timezone: "Asia/Tashkent",
    currency: "UZS",
  });
  const memberForm = useForm({ user_id: "", role: "student" });
  const activeSchool = schools.find((school) => school.id === schoolId);

  function setSchoolName(value) {
    schoolForm.set({ name: value, slug: slugify(value) });
  }

  async function createSchool(event) {
    event.preventDefault();
    try {
      const school = await api(
        "/api/v1/schools",
        { method: "POST", body: JSON.stringify({ ...schoolForm.values, slug: slugify(schoolForm.values.name), settings: {} }) },
        token
      );
      setSchoolId(school.id);
      localStorage.setItem("school_id", school.id);
      schoolForm.reset();
      setCreateOpen(false);
      await reload();
      notify("School yaratildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function loadMembers() {
    if (!schoolId) return;
    try {
      setMembers(await api(`/api/v1/schools/${schoolId}/members`, {}, token));
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function addMember(event) {
    event.preventDefault();
    try {
      await api(`/api/v1/schools/${schoolId}/members`, { method: "POST", body: JSON.stringify(memberForm.values) }, token);
      memberForm.reset();
      await loadMembers();
      notify("Member qo'shildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  useEffect(() => {
    loadMembers();
  }, [schoolId]);

  return (
    <div className="content-stack">
      <PageHeader
        title="Schoollar"
        eyebrow="Workspace"
        actions={<Button icon={<Plus size={17} />} onClick={() => setCreateOpen(true)}>School yaratish</Button>}
      />
      {schools.length ? (
        <section className="split-layout">
          <Panel title="Schoollar ro'yxati">
            <div className="entity-list">
              {schools.map((school) => (
                <button key={school.id} className={`entity-row ${school.id === schoolId ? "selected" : ""}`} onClick={() => setSchoolId(school.id)}>
                  <div className="entity-main">
                    <strong>{school.name}</strong>
                    <span>{school.slug}</span>
                  </div>
                  <IdPill value={school.id} />
                </button>
              ))}
            </div>
          </Panel>
          <Panel title={activeSchool?.name || "School detail"} action={<Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={loadMembers}>Members</Button>}>
            {activeSchool ? (
              <div className="detail-stack">
                <div className="detail-card">
                  <DataLine label="Slug" value={activeSchool.slug} />
                  <DataLine label="Currency" value={activeSchool.currency} />
                  <DataLine label="Timezone" value={activeSchool.timezone} />
                </div>
                <form className="inline-form" onSubmit={addMember}>
                  <TextInput required placeholder="User ID" {...memberForm.bind("user_id")} />
                  <Select {...memberForm.bind("role")}>
                    <option value="student">student</option>
                    <option value="curator">curator</option>
                    <option value="instructor">instructor</option>
                    <option value="admin">admin</option>
                  </Select>
                  <Button variant="secondary" icon={<UsersThree size={17} />}>Qo'shish</Button>
                </form>
                <div className="entity-list compact">
                  {members.map((member) => (
                    <div className="entity-row" key={member.id}>
                      <div className="entity-main">
                        <strong>{member.role}</strong>
                        <span>{member.user_id}</span>
                      </div>
                      <span className={member.is_active ? "badge ok" : "badge"}>{member.is_active ? "active" : "off"}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <Empty title="School tanlang" text="Member va sozlamalarni ko'rish uchun school tanlang." />
            )}
          </Panel>
        </section>
      ) : (
        <Empty title="School yo'q" text="Platformani boshlash uchun birinchi school yarating." action={<Button icon={<Plus size={17} />} onClick={() => setCreateOpen(true)}>School yaratish</Button>} />
      )}

      <Modal title="School yaratish" open={createOpen} onClose={() => setCreateOpen(false)}>
        <form className="form-grid" onSubmit={createSchool}>
          <Field label="Nomi">
            <TextInput required value={schoolForm.values.name} onChange={(event) => setSchoolName(event.target.value)} />
          </Field>
          <Field label="Tavsif">
            <TextArea {...schoolForm.bind("description")} />
          </Field>
          <div className="grid two">
            <Field label="Brand rangi">
              <TextInput type="color" {...schoolForm.bind("primary_color")} />
            </Field>
            <Field label="Valyuta">
              <TextInput {...schoolForm.bind("currency")} />
            </Field>
          </div>
          <div className="modal-actions">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Bekor qilish</Button>
            <Button icon={<Plus size={17} />}>Yaratish</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function CoursesPanel({ token, notify, schoolId, courses, reload }) {
  const [createOpen, setCreateOpen] = useState(false);
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [tree, setTree] = useState(null);
  const [builderModal, setBuilderModal] = useState(null);
  const courseForm = useForm({ title: "", slug: "", short_description: "", description: "", price_amount: 0, currency: "UZS", level: "beginner", language: "uz", estimated_duration_minutes: 60 });
  const categoryForm = useForm({ name: "", slug: "", sort_order: 1 });
  const moduleForm = useForm({ title: "", description: "", sort_order: 1 });
  const lessonForm = useForm({ module_id: "", title: "", description: "", status: "published", is_preview: "true", sort_order: 1 });
  const blockForm = useForm({ lesson_id: "", block_type: "text", title: "", content: "", file_url: "", video_asset_id: "", quiz_id: "", homework_id: "", sort_order: 1 });
  const selectedCourse = courses.find((course) => course.id === selectedCourseId);

  function setCourseTitle(value) {
    courseForm.set({ title: value, slug: slugify(value) });
  }

  function setCategoryName(value) {
    categoryForm.set({ name: value, slug: slugify(value) });
  }

  async function run(label, fn, type = "success") {
    try {
      await fn();
      await reload(schoolId);
      if (selectedCourseId) await loadTree(selectedCourseId);
      notify(label, type);
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function createCourse(event) {
    event.preventDefault();
    const payload = {
      ...courseForm.values,
      slug: slugify(courseForm.values.title),
      school_id: schoolId,
      price_amount: Number(courseForm.values.price_amount),
      estimated_duration_minutes: Number(courseForm.values.estimated_duration_minutes),
    };
    await run("Course yaratildi", async () => {
      const course = await api("/api/v1/courses", { method: "POST", body: JSON.stringify(payload) }, token);
      setSelectedCourseId(course.id);
      setCreateOpen(false);
      courseForm.reset();
      await loadTree(course.id);
    });
  }

  async function createCategory(event) {
    event.preventDefault();
    await run("Category yaratildi", async () => {
      await api(
        `/api/v1/courses/categories?school_id=${schoolId}`,
        { method: "POST", body: JSON.stringify({ ...categoryForm.values, slug: slugify(categoryForm.values.name) }) },
        token
      );
      setCategoryOpen(false);
      categoryForm.reset();
    });
  }

  async function loadTree(courseId) {
    try {
      const data = await api(`/api/v1/courses/${courseId}/tree`, {}, token);
      setTree(data);
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function openCourse(courseId) {
    setSelectedCourseId(courseId);
    await loadTree(courseId);
  }

  async function createModule(event) {
    event.preventDefault();
    await run("Module qo'shildi", async () => {
      await api(`/api/v1/courses/${selectedCourseId}/modules`, { method: "POST", body: JSON.stringify({ ...moduleForm.values, sort_order: Number(moduleForm.values.sort_order) }) }, token);
      moduleForm.reset();
      setBuilderModal(null);
    });
  }

  async function createLesson(event) {
    event.preventDefault();
    await run("Lesson qo'shildi", async () => {
      await api(`/api/v1/courses/${selectedCourseId}/modules/${lessonForm.values.module_id}/lessons`, {
        method: "POST",
        body: JSON.stringify({ ...lessonForm.values, is_preview: lessonForm.values.is_preview === "true", sort_order: Number(lessonForm.values.sort_order) }),
      }, token);
      lessonForm.reset();
      setBuilderModal(null);
    });
  }

  async function createBlock(event) {
    event.preventDefault();
    await run("Block qo'shildi", async () => {
      await api(`/api/v1/courses/${selectedCourseId}/lessons/${blockForm.values.lesson_id}/blocks`, {
        method: "POST",
        body: JSON.stringify({
          block_type: blockForm.values.block_type,
          title: blockForm.values.title,
          content: blockForm.values.content,
          file_url: blockForm.values.file_url || null,
          video_asset_id: blockForm.values.video_asset_id || null,
          quiz_id: blockForm.values.quiz_id || null,
          homework_id: blockForm.values.homework_id || null,
          sort_order: Number(blockForm.values.sort_order),
        }),
      }, token);
      blockForm.reset();
      setBuilderModal(null);
    });
  }

  async function deleteCourse(courseId) {
    await run("Course o'chirildi", () => api(`/api/v1/courses/${courseId}`, { method: "DELETE" }, token), "delete");
    if (selectedCourseId === courseId) {
      setSelectedCourseId("");
      setTree(null);
    }
  }

  async function deleteModule(moduleId) {
    await run("Module o'chirildi", () => api(`/api/v1/courses/${selectedCourseId}/modules/${moduleId}`, { method: "DELETE" }, token), "delete");
  }

  async function deleteLesson(lessonId) {
    await run("Lesson o'chirildi", () => api(`/api/v1/courses/${selectedCourseId}/lessons/${lessonId}`, { method: "DELETE" }, token), "delete");
  }

  async function deleteBlock(lessonId, blockId) {
    await run("Block o'chirildi", () => api(`/api/v1/courses/${selectedCourseId}/lessons/${lessonId}/blocks/${blockId}`, { method: "DELETE" }, token), "delete");
  }

  async function publish(courseId) {
    await run("Course published", () => api(`/api/v1/courses/${courseId}/publish`, { method: "POST" }, token));
  }

  const lessonRows = useMemo(() => (tree?.modules || []).flatMap((module) => module.lessons.map((lesson) => ({ ...lesson, module_title: module.title }))), [tree]);

  if (selectedCourseId) {
    return (
      <CourseDetail
        course={selectedCourse}
        tree={tree}
        lessons={lessonRows}
        onBack={() => {
          setSelectedCourseId("");
          setTree(null);
        }}
        onPublish={() => publish(selectedCourseId)}
        onAddModule={() => setBuilderModal("module")}
        onAddLesson={(moduleId) => {
          lessonForm.set({ module_id: moduleId || "" });
          setBuilderModal("lesson");
        }}
        onAddBlock={(lessonId) => {
          blockForm.set({ lesson_id: lessonId || "" });
          setBuilderModal("block");
        }}
        onDeleteModule={deleteModule}
        onDeleteLesson={deleteLesson}
        onDeleteBlock={deleteBlock}
      >
        <Modal title="Module qo'shish" open={builderModal === "module"} onClose={() => setBuilderModal(null)}>
          <form className="form-grid" onSubmit={createModule}>
            <Field label="Module nomi"><TextInput required autoFocus {...moduleForm.bind("title")} /></Field>
            <Field label="Tavsif"><TextArea {...moduleForm.bind("description")} /></Field>
            <Field label="Tartib"><TextInput type="number" {...moduleForm.bind("sort_order")} /></Field>
            <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setBuilderModal(null)}>Bekor</Button><Button icon={<Plus size={17} />}>Qo'shish</Button></div>
          </form>
        </Modal>
        <Modal title="Lesson qo'shish" open={builderModal === "lesson"} onClose={() => setBuilderModal(null)}>
          <form className="form-grid" onSubmit={createLesson}>
            <Field label="Module"><Select required {...lessonForm.bind("module_id")}><option value="">Module tanlang</option>{tree?.modules?.map((module) => <option key={module.id} value={module.id}>{module.title}</option>)}</Select></Field>
            <Field label="Lesson nomi"><TextInput required autoFocus {...lessonForm.bind("title")} /></Field>
            <Field label="Tavsif"><TextArea {...lessonForm.bind("description")} /></Field>
            <div className="grid two">
              <Field label="Status"><Select {...lessonForm.bind("status")}><option value="draft">draft</option><option value="published">published</option></Select></Field>
              <Field label="Preview"><Select {...lessonForm.bind("is_preview")}><option value="true">Ha</option><option value="false">Yo'q</option></Select></Field>
            </div>
            <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setBuilderModal(null)}>Bekor</Button><Button icon={<Plus size={17} />}>Qo'shish</Button></div>
          </form>
        </Modal>
        <Modal title="Block qo'shish" open={builderModal === "block"} onClose={() => setBuilderModal(null)}>
          <form className="form-grid" onSubmit={createBlock}>
            <Field label="Lesson"><Select required {...blockForm.bind("lesson_id")}><option value="">Lesson tanlang</option>{lessonRows.map((lesson) => <option key={lesson.id} value={lesson.id}>{lesson.module_title} / {lesson.title}</option>)}</Select></Field>
            <Field label="Block turi"><Select {...blockForm.bind("block_type")}><option value="text">Text</option><option value="video">Video</option><option value="file">File</option><option value="quiz">Quiz</option><option value="homework">Homework</option></Select></Field>
            <Field label="Sarlavha"><TextInput required {...blockForm.bind("title")} /></Field>
            <Field label="Matn yoki izoh"><TextArea {...blockForm.bind("content")} /></Field>
            <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setBuilderModal(null)}>Bekor</Button><Button icon={<Plus size={17} />}>Qo'shish</Button></div>
          </form>
        </Modal>
      </CourseDetail>
    );
  }

  return (
    <div className="content-stack">
      <PageHeader
        title="Kurslar"
        eyebrow="Course manager"
        actions={
          <>
            <Button variant="secondary" icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCategoryOpen(true)}>Category</Button>
            <Button icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCreateOpen(true)}>Kurs qo'shish</Button>
          </>
        }
      />
      {courses.length ? (
        <div className="card-grid">
          {courses.map((course) => (
            <article className="course-card" key={course.id}>
              <div className="course-card-head">
                <span className={`badge ${course.status === "published" ? "ok" : ""}`}>{course.status}</span>
                <IdPill value={course.id} />
              </div>
              <h3>{course.title}</h3>
              <p>{course.short_description || course.description || "Tavsif qo'shilmagan"}</p>
              <DataLine label="Narx" value={`${course.price_amount} ${course.currency}`} />
              <div className="row-actions">
                <Button variant="secondary" icon={<Eye size={17} />} onClick={() => openCourse(course.id)}>Ochish</Button>
                <Button variant="secondary" icon={<CheckCircle size={17} />} onClick={() => publish(course.id)}>Publish</Button>
                <IconButton label="O'chirish" variant="danger" icon={<Trash size={17} />} onClick={() => deleteCourse(course.id)} />
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty title="Kurs yo'q" text="Yangi kurs qo'shing. Module, lesson va materiallar kurs ichida boshqariladi." icon={<Books size={22} />} action={<Button icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCreateOpen(true)}>Kurs qo'shish</Button>} />
      )}

      <Modal title="Kurs qo'shish" open={createOpen} onClose={() => setCreateOpen(false)}>
        <form className="form-grid" onSubmit={createCourse}>
          <Field label="Kurs nomi"><TextInput required value={courseForm.values.title} onChange={(event) => setCourseTitle(event.target.value)} /></Field>
          <Field label="Qisqa tavsif"><TextInput {...courseForm.bind("short_description")} /></Field>
          <div className="grid two">
            <Field label="Narx"><TextInput type="number" {...courseForm.bind("price_amount")} /></Field>
            <Field label="Davomiylik (min)"><TextInput type="number" {...courseForm.bind("estimated_duration_minutes")} /></Field>
          </div>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Bekor</Button><Button icon={<Plus size={17} />}>Yaratish</Button></div>
        </form>
      </Modal>
      <Modal title="Category qo'shish" open={categoryOpen} onClose={() => setCategoryOpen(false)}>
        <form className="form-grid" onSubmit={createCategory}>
          <Field label="Nomi"><TextInput required value={categoryForm.values.name} onChange={(event) => setCategoryName(event.target.value)} /></Field>
          <Field label="Tartib"><TextInput type="number" {...categoryForm.bind("sort_order")} /></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setCategoryOpen(false)}>Bekor</Button><Button icon={<Plus size={17} />}>Qo'shish</Button></div>
        </form>
      </Modal>
    </div>
  );
}

function CourseDetail({ course, tree, lessons, onBack, onPublish, onAddModule, onAddLesson, onAddBlock, onDeleteModule, onDeleteLesson, onDeleteBlock, children }) {
  return (
    <div className="content-stack">
      <PageHeader
        title={course?.title || tree?.course?.title || "Course"}
        eyebrow="Course detail"
        actions={
          <>
            <Button variant="secondary" icon={<CaretLeft size={17} />} onClick={onBack}>Kurslarga qaytish</Button>
            <Button variant="secondary" icon={<CheckCircle size={17} />} onClick={onPublish}>Publish</Button>
            <Button icon={<Plus size={17} />} onClick={onAddModule}>Module qo'shish</Button>
          </>
        }
      />
      <Panel title="Course strukturasi">
        {tree?.modules?.length ? (
          <div className="builder-list">
            {tree.modules.map((module) => (
              <section className="builder-module" key={module.id}>
                <header>
                  <div>
                    <strong>{module.title}</strong>
                    <span>{module.lessons.length} lesson</span>
                  </div>
                  <div className="row-actions">
                    <Button variant="secondary" icon={<Plus size={17} />} onClick={() => onAddLesson(module.id)}>Lesson</Button>
                    <IconButton label="Module o'chirish" variant="danger" icon={<Trash size={17} />} onClick={() => onDeleteModule(module.id)} />
                  </div>
                </header>
                {module.lessons.length ? (
                  <div className="lesson-list">
                    {module.lessons.map((lesson) => (
                      <article className="lesson-row" key={lesson.id}>
                        <div>
                          <strong>{lesson.title}</strong>
                          <span>{lesson.status} / {lesson.blocks.length} block</span>
                        </div>
                        <div className="row-actions">
                          <Button variant="secondary" icon={<Plus size={17} />} onClick={() => onAddBlock(lesson.id)}>Block</Button>
                          <IconButton label="Lesson o'chirish" variant="danger" icon={<Trash size={17} />} onClick={() => onDeleteLesson(lesson.id)} />
                        </div>
                        {lesson.blocks.length ? (
                          <div className="block-list">
                            {lesson.blocks.map((block) => (
                              <div className="block-chip" key={block.id}>
                                <span>{block.block_type}</span>
                                <strong>{block.title || "Untitled"}</strong>
                                <IconButton label="Block o'chirish" variant="danger slim" icon={<Trash size={14} />} onClick={() => onDeleteBlock(lesson.id, block.id)} />
                              </div>
                            ))}
                          </div>
                        ) : (
                          <Empty title="Block yo'q" text="Lesson ichiga video, text, file yoki quiz block qo'shing." action={<Button variant="secondary" icon={<Plus size={17} />} onClick={() => onAddBlock(lesson.id)}>Block qo'shish</Button>} />
                        )}
                      </article>
                    ))}
                  </div>
                ) : (
                  <Empty title="Lesson yo'q" text="Bu module ichiga birinchi lesson qo'shing." action={<Button variant="secondary" icon={<Plus size={17} />} onClick={() => onAddLesson(module.id)}>Lesson qo'shish</Button>} />
                )}
              </section>
            ))}
          </div>
        ) : (
          <Empty title="Module yo'q" text="Kursni boshlash uchun birinchi module qo'shing." icon={<Books size={22} />} action={<Button icon={<Plus size={17} />} onClick={onAddModule}>Module qo'shish</Button>} />
        )}
      </Panel>
      {lessons.length ? (
        <Panel title="Tezkor lessonlar">
          <div className="entity-list">
            {lessons.map((lesson) => (
              <div className="entity-row" key={lesson.id}>
                <div className="entity-main"><strong>{lesson.title}</strong><span>{lesson.module_title}</span></div>
                <Button variant="secondary" icon={<Plus size={17} />} onClick={() => onAddBlock(lesson.id)}>Material</Button>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}
      {children}
    </div>
  );
}

function CatalogPanel({ publicCourses, schoolId, reload }) {
  return (
    <div className="content-stack">
      <PageHeader title="Catalog" eyebrow="Published courses" actions={<Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={() => reload(schoolId)}>Yangilash</Button>} />
      {publicCourses.length ? (
        <div className="card-grid">
          {publicCourses.map((course) => (
            <article className="course-card" key={course.id}>
              <span className="badge ok">{course.level}</span>
              <h3>{course.title}</h3>
              <p>{course.short_description || course.description || "Published course"}</p>
              <DataLine label="Narx" value={`${course.price_amount} ${course.currency}`} />
            </article>
          ))}
        </div>
      ) : (
        <Empty title="Catalog bo'sh" text="Course publish qilingandan keyin shu yerda chiqadi." icon={<Eye size={22} />} />
      )}
    </div>
  );
}

function MediaPanel({ token, notify, schoolId, courses }) {
  const [tree, setTree] = useState(null);
  const [courseId, setCourseId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const selectedLesson = useMemo(() => (tree?.modules || []).flatMap((module) => module.lessons).find((lesson) => lesson.id === lessonId), [tree, lessonId]);

  async function loadTree(id) {
    setCourseId(id);
    setLessonId("");
    setTree(null);
    if (!id) return;
    try {
      setTree(await api(`/api/v1/courses/${id}/tree`, {}, token));
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function uploadFile() {
    if (!file || !courseId || !lessonId) return notify("Kurs, lesson va fayl tanlang", "error");
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("school_id", schoolId);
      formData.append("course_id", courseId);
      formData.append("lesson_id", lessonId);
      formData.append("file", file);
      await api("/api/v1/media/files/r2/upload", {
        method: "POST",
        body: formData,
      }, token);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      notify("Video yuklandi");
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setUploading(false);
    }
  }

  const lessons = (tree?.modules || []).flatMap((module) => module.lessons.map((lesson) => ({ ...lesson, module_title: module.title })));

  return (
    <div className="content-stack">
      <PageHeader title="Media" eyebrow="Lesson materiallari" />
      <Panel title="Video yoki fayl biriktirish">
        <div className="wizard-grid">
          <Field label="Kurs"><Select value={courseId} onChange={(event) => loadTree(event.target.value)}><option value="">Kurs tanlang</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</Select></Field>
          <Field label="Lesson"><Select value={lessonId} onChange={(event) => setLessonId(event.target.value)} disabled={!lessons.length}><option value="">Lesson tanlang</option>{lessons.map((lesson) => <option key={lesson.id} value={lesson.id}>{lesson.module_title} / {lesson.title}</option>)}</Select></Field>
          <Field label="Fayl"><input ref={fileInputRef} type="file" onChange={(event) => setFile(event.target.files?.[0] || null)} /></Field>
        </div>
        <div className="helper-box">
          <strong>{selectedLesson ? selectedLesson.title : "Lesson tanlanmagan"}</strong>
          <span>{file ? `${file.name} / ${file.type || "unknown"} / ${file.size} bytes` : "Fayl tanlang. Key, file size va content type avtomatik olinadi."}</span>
        </div>
        <div className="row-actions">
          <Button icon={<CloudArrowUp size={17} />} busy={uploading} disabled={!file || !courseId || !lessonId} onClick={uploadFile}>Faylni yuklash</Button>
        </div>
      </Panel>
    </div>
  );
}

function PaymentsPanel({ token, notify, schoolId, courses, products, reload }) {
  const [createOpen, setCreateOpen] = useState(false);
  const origin = window.location.origin;
  const productForm = useForm({ title: "", description: "", price_amount: 99000, currency: "UZS", status: "active", course_id: "" });

  async function createProduct(event) {
    event.preventDefault();
    try {
      await api("/api/v1/products", {
        method: "POST",
        body: JSON.stringify({
          school_id: schoolId,
          title: productForm.values.title,
          description: productForm.values.description,
          price_amount: Number(productForm.values.price_amount),
          currency: productForm.values.currency,
          status: productForm.values.status,
          course_ids: productForm.values.course_id ? [productForm.values.course_id] : [],
        }),
      }, token);
      await reload(schoolId);
      setCreateOpen(false);
      productForm.reset();
      notify("Product yaratildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function createCheckout(productId) {
    try {
      const session = await api("/api/v1/checkout/sessions", {
        method: "POST",
        body: JSON.stringify({ product_id: productId, success_url: `${origin}/success`, cancel_url: `${origin}/cancel` }),
      }, token);
      const opened = window.open(session.checkout_url, "_blank", "noopener,noreferrer");
      if (!opened) {
        await navigator.clipboard?.writeText(session.checkout_url);
        notify("To'lov linki copy qilindi");
        return;
      }
      notify("To'lov sahifasi ochildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function deleteProduct(productId) {
    try {
      await api(`/api/v1/products/${productId}`, { method: "DELETE" }, token);
      await reload(schoolId);
      notify("Product o'chirildi", "delete");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  return (
    <div className="content-stack">
      <div className="section-toolbar">
        <div>
          <span className="section-kicker">Product va checkout</span>
          <h2>Productlar</h2>
        </div>
        <Button icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCreateOpen(true)}>Product qo'shish</Button>
      </div>
      {products.length ? (
        <div className="card-grid">
          {products.map((product) => (
            <article className="course-card" key={product.id}>
              <div className="course-card-head"><span className="badge ok">{product.status}</span></div>
              <h3>{product.title}</h3>
              {product.description ? <p>{product.description}</p> : null}
              <DataLine label="Narx" value={`${product.price_amount} ${product.currency}`} />
              <div className="row-actions">
                <Button variant="secondary" icon={<DoorOpen size={17} />} onClick={() => createCheckout(product.id)}>To'lov sahifasi</Button>
                <IconButton label="O'chirish" variant="danger" icon={<Trash size={17} />} onClick={() => deleteProduct(product.id)} />
              </div>
            </article>
          ))}
        </div>
      ) : (
        <Empty title="Product yo'q" text="Kurs sotish uchun product yarating." icon={<CreditCard size={22} />} action={<Button icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCreateOpen(true)}>Product qo'shish</Button>} />
      )}
      <Modal title="Product qo'shish" open={createOpen} onClose={() => setCreateOpen(false)}>
        <form className="form-grid" onSubmit={createProduct}>
          <Field label="Product nomi"><TextInput required {...productForm.bind("title")} /></Field>
          <Field label="Narx"><TextInput type="number" {...productForm.bind("price_amount")} /></Field>
          <Field label="Kurs"><Select value={productForm.values.course_id} onChange={(event) => productForm.set({ course_id: event.target.value })}><option value="">Kurs tanlang</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</Select></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Bekor</Button><Button icon={<CreditCard size={17} />}>Yaratish</Button></div>
        </form>
      </Modal>
    </div>
  );
}

function LearningPanel({ token, notify, courses }) {
  const [courseId, setCourseId] = useState("");
  const [tree, setTree] = useState(null);
  const [lessonId, setLessonId] = useState("");
  const [modal, setModal] = useState(null);
  const [result, setResult] = useState(null);
  const [quizzes, setQuizzes] = useState([]);
  const [homeworks, setHomeworks] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [options, setOptions] = useState([]);
  const [selectedQuizId, setSelectedQuizId] = useState("");
  const [selectedQuestionId, setSelectedQuestionId] = useState("");
  const quizForm = useForm({ title: "Quiz", passing_score: 60 });
  const questionForm = useForm({ quiz_id: "", question_type: "single_choice", text: "", correct_answer: "", score: 1, sort_order: 1 });
  const optionForm = useForm({ question_id: "", text: "", is_correct: "true", sort_order: 1 });
  const homeworkForm = useForm({ title: "Uy vazifa", description: "", max_attempts: 1, max_score: 100, review_required: "true" });
  const attemptForm = useForm({ quiz_id: "", homework_id: "", answer_text: "", file_url: "", answers: "{}" });
  const reviewForm = useForm({ attempt_id: "", score: 100, status: "graded", comment: "Qabul qilindi" });

  async function loadTree(id) {
    setCourseId(id);
    setLessonId("");
    setTree(null);
    clearLearningLists();
    if (!id) return;
    try {
      setTree(await api(`/api/v1/courses/${id}/tree`, {}, token));
    } catch (error) {
      notify(error.message, "error");
    }
  }

  function clearLearningLists() {
    setQuizzes([]);
    setHomeworks([]);
    setAttempts([]);
    setQuestions([]);
    setOptions([]);
    setSelectedQuizId("");
    setSelectedQuestionId("");
  }

  async function loadLessonData(id = lessonId) {
    if (!id) {
      clearLearningLists();
      return;
    }
    try {
      const [quizRows, homeworkRows, attemptRows] = await Promise.all([
        api(`/api/v1/lessons/${id}/quizzes`, {}, token).catch(() => []),
        api(`/api/v1/lessons/${id}/homeworks`, {}, token).catch(() => []),
        api(`/api/v1/lessons/${id}/attempts`, {}, token).catch(() => []),
      ]);
      setQuizzes(quizRows || []);
      setHomeworks(homeworkRows || []);
      setAttempts(attemptRows || []);
      const nextQuizId = selectedQuizId || quizRows?.[0]?.id || "";
      setSelectedQuizId(nextQuizId);
      if (nextQuizId) await loadQuestions(nextQuizId);
      else {
        setQuestions([]);
        setOptions([]);
        setSelectedQuestionId("");
      }
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function selectLesson(id) {
    setLessonId(id);
    await loadLessonData(id);
  }

  async function loadQuestions(quizId) {
    if (!quizId) {
      setQuestions([]);
      setOptions([]);
      setSelectedQuestionId("");
      return;
    }
    try {
      const rows = await api(`/api/v1/quizzes/${quizId}/questions`, {}, token);
      setQuestions(rows || []);
      const nextQuestionId = rows?.[0]?.id || "";
      setSelectedQuestionId(nextQuestionId);
      if (nextQuestionId) await loadOptions(nextQuestionId);
      else setOptions([]);
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function selectQuiz(id) {
    setSelectedQuizId(id);
    questionForm.set({ quiz_id: id });
    await loadQuestions(id);
  }

  async function loadOptions(questionId) {
    if (!questionId) {
      setOptions([]);
      setSelectedQuestionId("");
      return;
    }
    try {
      setSelectedQuestionId(questionId);
      optionForm.set({ question_id: questionId });
      setOptions(await api(`/api/v1/questions/${questionId}/options`, {}, token));
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function submit(label, event, fn, after) {
    event.preventDefault();
    try {
      const data = await fn();
      setResult(data);
      setModal(null);
      if (after) await after(data);
      notify(label);
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function completeLesson(id) {
    try {
      setResult(await api(`/api/v1/lessons/${id}/complete`, { method: "POST" }, token));
      notify("Lesson complete");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function getProgress() {
    if (!courseId) return;
    try {
      setResult(await api(`/api/v1/me/courses/${courseId}/progress`, {}, token));
      notify("Progress olindi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  const lessons = (tree?.modules || []).flatMap((module) => module.lessons.map((lesson) => ({ ...lesson, module_title: module.title })));
  const selectedLesson = lessons.find((lesson) => lesson.id === lessonId);
  const reviewableAttempts = attempts.filter((attempt) => attempt.status !== "graded" || !attempt.review_comment);

  return (
    <div className="content-stack">
      <PageHeader title="Learning" eyebrow="Quiz, homework, progress" actions={<Button variant="secondary" icon={<Heartbeat size={17} />} disabled={!courseId} onClick={getProgress}>Progress</Button>} />
      <Panel title="Dars tanlash">
        <div className="wizard-grid">
          <Field label="Kurs"><Select value={courseId} onChange={(event) => loadTree(event.target.value)}><option value="">Kurs tanlang</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</Select></Field>
          <Field label="Lesson"><Select value={lessonId} onChange={(event) => selectLesson(event.target.value)} disabled={!lessons.length}><option value="">Lesson tanlang</option>{lessons.map((lesson) => <option key={lesson.id} value={lesson.id}>{lesson.module_title} / {lesson.title}</option>)}</Select></Field>
          <div className="quick-actions"><Button variant="secondary" icon={<ArrowClockwise size={17} />} disabled={!lessonId} onClick={() => loadLessonData()}>Yangilash</Button></div>
        </div>
      </Panel>
      {selectedLesson ? (
        <Panel title={selectedLesson.title}>
          <div className="quick-actions">
            <Button icon={<ListChecks size={17} />} onClick={() => setModal("quiz")}>Quiz qo'shish</Button>
            <Button variant="secondary" icon={<Plus size={17} />} disabled={!quizzes.length} onClick={() => { questionForm.set({ quiz_id: selectedQuizId || quizzes[0]?.id || "" }); setModal("question"); }}>Question qo'shish</Button>
            <Button variant="secondary" icon={<Plus size={17} />} disabled={!questions.length} onClick={() => { optionForm.set({ question_id: selectedQuestionId || questions[0]?.id || "" }); setModal("option"); }}>Option qo'shish</Button>
            <Button variant="secondary" icon={<Plus size={17} />} onClick={() => setModal("homework")}>Homework qo'shish</Button>
            <Button variant="secondary" icon={<UploadSimple size={17} />} disabled={!quizzes.length && !homeworks.length} onClick={() => setModal("attempt")}>Attempt yuborish</Button>
            <Button variant="secondary" icon={<ShieldCheck size={17} />} disabled={!attempts.length} onClick={() => { reviewForm.set({ attempt_id: reviewableAttempts[0]?.id || attempts[0]?.id || "" }); setModal("review"); }}>Review</Button>
            <Button variant="secondary" icon={<CheckCircle size={17} />} onClick={() => completeLesson(selectedLesson.id)}>Complete</Button>
          </div>
        </Panel>
      ) : (
        <Empty title="Lesson tanlang" text="Learning amallari tanlangan lesson kontekstida ochiladi." icon={<ListChecks size={22} />} />
      )}
      {selectedLesson ? (
        <section className="grid three">
          <Panel title="Quizlar">
            {quizzes.length ? (
              <div className="entity-list">
                {quizzes.map((quiz) => (
                  <button key={quiz.id} className={`entity-row ${quiz.id === selectedQuizId ? "selected" : ""}`} onClick={() => selectQuiz(quiz.id)}>
                    <div className="entity-main"><strong>{quiz.title}</strong><span>Passing score: {quiz.passing_score}</span></div>
                    <IdPill value={quiz.id} />
                  </button>
                ))}
              </div>
            ) : <Empty title="Quiz yo'q" text="Bu lesson uchun quiz qo'shing." />}
          </Panel>
          <Panel title="Homeworklar">
            {homeworks.length ? (
              <div className="entity-list">
                {homeworks.map((homework) => (
                  <div key={homework.id} className="entity-row">
                    <div className="entity-main"><strong>{homework.title}</strong><span>{homework.max_score} ball / {homework.max_attempts} urinish</span></div>
                    <IdPill value={homework.id} />
                  </div>
                ))}
              </div>
            ) : <Empty title="Homework yo'q" text="Uy vazifa kerak bo'lsa qo'shing." />}
          </Panel>
          <Panel title="Attemptlar">
            {attempts.length ? (
              <div className="entity-list">
                {attempts.map((attempt) => (
                  <button key={attempt.id} className={`entity-row ${attempt.id === reviewForm.values.attempt_id ? "selected" : ""}`} onClick={() => reviewForm.set({ attempt_id: attempt.id })}>
                    <div className="entity-main"><strong>{attempt.status}</strong><span>Score: {attempt.score} / User: {String(attempt.user_id).slice(0, 8)}</span></div>
                    <IdPill value={attempt.id} />
                  </button>
                ))}
              </div>
            ) : <Empty title="Attempt yo'q" text="Student javob yuborganda shu yerda chiqadi." />}
          </Panel>
        </section>
      ) : null}
      {selectedQuizId ? (
        <section className="grid two">
          <Panel title="Questionlar">
            {questions.length ? (
              <div className="entity-list">
                {questions.map((question) => (
                  <button key={question.id} className={`entity-row ${question.id === selectedQuestionId ? "selected" : ""}`} onClick={() => loadOptions(question.id)}>
                    <div className="entity-main"><strong>{question.text}</strong><span>{question.question_type} / {question.score} ball</span></div>
                    <IdPill value={question.id} />
                  </button>
                ))}
              </div>
            ) : <Empty title="Question yo'q" text="Tanlangan quizga savol qo'shing." />}
          </Panel>
          <Panel title="Optionlar">
            {options.length ? (
              <div className="entity-list">
                {options.map((option) => (
                  <div key={option.id} className="entity-row">
                    <div className="entity-main"><strong>{option.text}</strong><span>{option.is_correct ? "correct" : "incorrect"}</span></div>
                    <IdPill value={option.id} />
                  </div>
                ))}
              </div>
            ) : <Empty title="Option yo'q" text="Tanlangan question uchun variant qo'shing." />}
          </Panel>
        </section>
      ) : null}
      {result ? <Panel title="Oxirgi javob"><pre className="code-box">{JSON.stringify(result, null, 2)}</pre></Panel> : null}

      <Modal title="Quiz qo'shish" open={modal === "quiz"} onClose={() => setModal(null)}>
        <form className="form-grid" onSubmit={(event) => submit("Quiz yaratildi", event, () => api("/api/v1/quizzes", { method: "POST", body: JSON.stringify({ lesson_id: lessonId, title: quizForm.values.title, passing_score: Number(quizForm.values.passing_score) }) }, token), () => loadLessonData())}>
          <Field label="Title"><TextInput required {...quizForm.bind("title")} /></Field>
          <Field label="Passing score"><TextInput type="number" {...quizForm.bind("passing_score")} /></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setModal(null)}>Bekor</Button><Button icon={<ListChecks size={17} />}>Yaratish</Button></div>
        </form>
      </Modal>
      <Modal title="Question qo'shish" open={modal === "question"} onClose={() => setModal(null)}>
        <form className="form-grid" onSubmit={(event) => submit("Question yaratildi", event, () => api("/api/v1/questions", { method: "POST", body: JSON.stringify({ quiz_id: questionForm.values.quiz_id, question_type: questionForm.values.question_type, text: questionForm.values.text, correct_answer: questionForm.values.correct_answer || null, score: Number(questionForm.values.score), sort_order: Number(questionForm.values.sort_order) }) }, token), () => loadQuestions(questionForm.values.quiz_id))}>
          <Field label="Quiz"><Select required {...questionForm.bind("quiz_id")}>{quizzes.map((quiz) => <option key={quiz.id} value={quiz.id}>{quiz.title}</option>)}</Select></Field>
          <Field label="Question"><TextArea required {...questionForm.bind("text")} /></Field>
          <div className="grid two">
            <Field label="Type"><Select {...questionForm.bind("question_type")}><option value="single_choice">single_choice</option><option value="multiple_choice">multiple_choice</option><option value="text">text</option></Select></Field>
            <Field label="Score"><TextInput type="number" {...questionForm.bind("score")} /></Field>
          </div>
          <Field label="Correct answer"><TextInput {...questionForm.bind("correct_answer")} /></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setModal(null)}>Bekor</Button><Button icon={<Plus size={17} />}>Qo'shish</Button></div>
        </form>
      </Modal>
      <Modal title="Option qo'shish" open={modal === "option"} onClose={() => setModal(null)}>
        <form className="form-grid" onSubmit={(event) => submit("Option yaratildi", event, () => api("/api/v1/question-options", { method: "POST", body: JSON.stringify({ question_id: optionForm.values.question_id, text: optionForm.values.text, is_correct: optionForm.values.is_correct === "true", sort_order: Number(optionForm.values.sort_order) }) }, token), () => loadOptions(optionForm.values.question_id))}>
          <Field label="Question"><Select required {...optionForm.bind("question_id")}>{questions.map((question) => <option key={question.id} value={question.id}>{question.text}</option>)}</Select></Field>
          <Field label="Option text"><TextInput required {...optionForm.bind("text")} /></Field>
          <Field label="To'g'ri javob"><Select {...optionForm.bind("is_correct")}><option value="true">Ha</option><option value="false">Yo'q</option></Select></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setModal(null)}>Bekor</Button><Button icon={<Plus size={17} />}>Qo'shish</Button></div>
        </form>
      </Modal>
      <Modal title="Homework qo'shish" open={modal === "homework"} onClose={() => setModal(null)}>
        <form className="form-grid" onSubmit={(event) => submit("Homework yaratildi", event, () => api("/api/v1/homeworks", { method: "POST", body: JSON.stringify({ lesson_id: lessonId, title: homeworkForm.values.title, description: homeworkForm.values.description, max_attempts: Number(homeworkForm.values.max_attempts), max_score: Number(homeworkForm.values.max_score), review_required: homeworkForm.values.review_required === "true" }) }, token), () => loadLessonData())}>
          <Field label="Title"><TextInput required {...homeworkForm.bind("title")} /></Field>
          <Field label="Description"><TextArea {...homeworkForm.bind("description")} /></Field>
          <div className="grid two"><Field label="Max attempts"><TextInput type="number" {...homeworkForm.bind("max_attempts")} /></Field><Field label="Max score"><TextInput type="number" {...homeworkForm.bind("max_score")} /></Field></div>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setModal(null)}>Bekor</Button><Button icon={<Plus size={17} />}>Yaratish</Button></div>
        </form>
      </Modal>
      <Modal title="Attempt yuborish" open={modal === "attempt"} onClose={() => setModal(null)}>
        <form className="form-grid" onSubmit={(event) => submit("Attempt yuborildi", event, () => api("/api/v1/attempts", { method: "POST", body: JSON.stringify({ lesson_id: lessonId, quiz_id: attemptForm.values.quiz_id || null, homework_id: attemptForm.values.homework_id || null, answer_text: attemptForm.values.answer_text, file_url: attemptForm.values.file_url || null, answers: JSON.parse(attemptForm.values.answers || "{}") }) }, token), () => loadLessonData())}>
          <Field label="Quiz"><Select {...attemptForm.bind("quiz_id")}><option value="">Quiz tanlanmagan</option>{quizzes.map((quiz) => <option key={quiz.id} value={quiz.id}>{quiz.title}</option>)}</Select></Field>
          <Field label="Homework"><Select {...attemptForm.bind("homework_id")}><option value="">Homework tanlanmagan</option>{homeworks.map((homework) => <option key={homework.id} value={homework.id}>{homework.title}</option>)}</Select></Field>
          <Field label="Answer"><TextArea {...attemptForm.bind("answer_text")} /></Field>
          <Field label="Answers JSON"><TextArea {...attemptForm.bind("answers")} /></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setModal(null)}>Bekor</Button><Button icon={<UploadSimple size={17} />}>Yuborish</Button></div>
        </form>
      </Modal>
      <Modal title="Attempt review" open={modal === "review"} onClose={() => setModal(null)}>
        <form className="form-grid" onSubmit={(event) => submit("Attempt baholandi", event, () => api(`/api/v1/attempts/${reviewForm.values.attempt_id}/review`, { method: "PATCH", body: JSON.stringify({ score: Number(reviewForm.values.score), status: reviewForm.values.status, comment: reviewForm.values.comment }) }, token), () => loadLessonData())}>
          <Field label="Attempt"><Select required {...reviewForm.bind("attempt_id")}>{attempts.map((attempt) => <option key={attempt.id} value={attempt.id}>{attempt.status} / {String(attempt.user_id).slice(0, 8)} / {attempt.score} ball</option>)}</Select></Field>
          <Field label="Score"><TextInput type="number" {...reviewForm.bind("score")} /></Field>
          <Field label="Comment"><TextArea {...reviewForm.bind("comment")} /></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setModal(null)}>Bekor</Button><Button icon={<ShieldCheck size={17} />}>Saqlash</Button></div>
        </form>
      </Modal>
    </div>
  );
}

function MessengerPanel({ token, notify, chats, reload }) {
  const [channelId, setChannelId] = useState("");
  const [messages, setMessages] = useState([]);
  const [liveMessages, setLiveMessages] = useState([]);
  const msgForm = useForm({ body: "" });
  const wsRef = useRef(null);

  async function loadMessages(id = channelId) {
    if (!id) return;
    try {
      setMessages(await api(`/api/v1/chats/${id}/messages`, {}, token));
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    try {
      await api(`/api/v1/chats/${channelId}/messages`, { method: "POST", body: JSON.stringify(msgForm.values) }, token);
      msgForm.reset();
      await loadMessages();
      notify("Message yuborildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  function connectWs() {
    if (!channelId) return;
    wsRef.current?.close();
    const socket = new WebSocket(`${WS_BASE}/api/v1/ws/chats/${channelId}?token=${encodeURIComponent(token)}`);
    socket.onmessage = (event) => setLiveMessages((rows) => [event.data, ...rows].slice(0, 20));
    socket.onerror = () => notify("WebSocket ulanmadi", "error");
    wsRef.current = socket;
    notify("WebSocket ulandi");
  }

  useEffect(() => () => wsRef.current?.close(), []);

  return (
    <div className="split-layout">
      <Panel title="Chatlar" action={<Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={reload}>Yangilash</Button>}>
        <div className="entity-list">
          {chats.map((chat) => (
            <button key={chat.id} className={`entity-row ${channelId === chat.id ? "selected" : ""}`} onClick={() => { setChannelId(chat.id); loadMessages(chat.id); }}>
              <div className="entity-main"><strong>{chat.title}</strong><span>{chat.channel_type}</span></div>
              <IdPill value={chat.id} />
            </button>
          ))}
        </div>
      </Panel>
      <Panel title="Messages">
        <form className="inline-form" onSubmit={sendMessage}>
          <TextInput required placeholder="Message" {...msgForm.bind("body")} />
          <Button icon={<ChatsCircle size={17} />} disabled={!channelId}>Send</Button>
        </form>
        <div className="inline-form">
          <Button variant="secondary" icon={<MonitorPlay size={17} />} onClick={connectWs} disabled={!channelId}>WS connect</Button>
          <Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={() => loadMessages()} disabled={!channelId}>History</Button>
        </div>
        <div className="message-list">
          {[...liveMessages.map((body, index) => ({ id: `live-${index}`, body, live: true })), ...messages].map((msg) => (
            <div key={msg.id} className="message"><span>{msg.live ? "live" : msg.sender_id}</span><p>{msg.body}</p></div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function AnalyticsPanel({ analytics, schoolId, reload }) {
  return (
    <div className="content-stack">
      <PageHeader title="Analytics" eyebrow="School metrics" actions={<Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={() => reload(schoolId)}>Yangilash</Button>} />
      {analytics ? (
        <section className="stat-grid">
          <div className="stat-card"><span>Total students</span><strong>{analytics.total_students}</strong></div>
          <div className="stat-card"><span>Active students</span><strong>{analytics.active_students}</strong></div>
          <div className="stat-card"><span>Revenue</span><strong>{analytics.revenue}</strong></div>
          <div className="stat-card"><span>Paid invoices</span><strong>{analytics.paid_invoices}</strong></div>
        </section>
      ) : (
        <Empty title="Analytics yo'q" text="School tanlang yoki ma'lumotlar yig'ilishini kuting." icon={<ChartLine size={22} />} />
      )}
    </div>
  );
}

function ExportsPanel({ token, notify, schoolId, exports, setExports }) {
  const [createOpen, setCreateOpen] = useState(false);
  const form = useForm({ export_type: "students", file_format: "csv" });

  async function createExport(event) {
    event.preventDefault();
    try {
      const job = await api("/api/v1/exports", { method: "POST", body: JSON.stringify({ school_id: schoolId, ...form.values }) }, token);
      setExports((rows) => [job, ...rows]);
      setCreateOpen(false);
      notify("Export job yaratildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function refreshJob(id) {
    try {
      const job = await api(`/api/v1/exports/${id}`, {}, token);
      setExports((rows) => rows.map((row) => (row.id === id ? job : row)));
      notify("Export status yangilandi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  return (
    <div className="content-stack">
      <PageHeader title="Exports" eyebrow="CSV jobs" actions={<Button icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCreateOpen(true)}>Export yaratish</Button>} />
      {exports.length ? (
        <div className="entity-list">
          {exports.map((job) => (
            <div className="entity-row" key={job.id}>
              <div className="entity-main"><strong>{job.export_type}</strong><span>{job.status} / {job.result_url || "pending"}</span></div>
              <Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={() => refreshJob(job.id)}>Status</Button>
            </div>
          ))}
        </div>
      ) : (
        <Empty title="Export yo'q" text="CSV olish uchun export job yarating." icon={<DownloadSimple size={22} />} action={<Button icon={<Plus size={17} />} disabled={!schoolId} onClick={() => setCreateOpen(true)}>Export yaratish</Button>} />
      )}
      <Modal title="Export yaratish" open={createOpen} onClose={() => setCreateOpen(false)}>
        <form className="form-grid" onSubmit={createExport}>
          <Field label="Export type"><Select {...form.bind("export_type")}><option value="students">students</option><option value="payments">payments</option><option value="progress">progress</option></Select></Field>
          <Field label="Format"><Select {...form.bind("file_format")}><option value="csv">csv</option></Select></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Bekor</Button><Button icon={<DownloadSimple size={17} />}>Yaratish</Button></div>
        </form>
      </Modal>
    </div>
  );
}

function LivePanel({ token, notify, courses, liveSessions, setLiveSessions }) {
  const [createOpen, setCreateOpen] = useState(false);
  const form = useForm({ course_id: "", title: "Haftalik live dars", starts_at: "", ends_at: "", room_url: "https://meet.jit.si/exode-demo", provider: "jitsi" });

  async function createLive(event) {
    event.preventDefault();
    try {
      const session = await api("/api/v1/live-sessions", { method: "POST", body: JSON.stringify(form.values) }, token);
      setLiveSessions((rows) => [session, ...rows]);
      setCreateOpen(false);
      notify("Live session yaratildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function loadLive() {
    if (!form.values.course_id) return;
    try {
      setLiveSessions(await api(`/api/v1/live-sessions?course_id=${form.values.course_id}`, {}, token));
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function join(sessionId) {
    try {
      const data = await api(`/api/v1/live-sessions/${sessionId}/join`, {}, token);
      window.open(data.room_url, "_blank", "noopener,noreferrer");
      notify("Join link ochildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  async function finish(sessionId) {
    try {
      const data = await api(`/api/v1/live-sessions/${sessionId}/finish`, { method: "POST" }, token);
      setLiveSessions((rows) => rows.map((row) => (row.id === sessionId ? data : row)));
      notify("Live tugatildi");
    } catch (error) {
      notify(error.message, "error");
    }
  }

  return (
    <div className="content-stack">
      <PageHeader title="Live sessions" eyebrow="Online darslar" actions={<Button icon={<Plus size={17} />} onClick={() => setCreateOpen(true)}>Live yaratish</Button>} />
      <Panel title="Course live darslari" action={<Button variant="secondary" icon={<ArrowClockwise size={17} />} onClick={loadLive}>Load</Button>}>
        <Field label="Kurs"><Select {...form.bind("course_id")}><option value="">Kurs tanlang</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</Select></Field>
        {liveSessions.length ? (
          <div className="entity-list">
            {liveSessions.map((session) => (
              <div className="entity-row" key={session.id}>
                <div className="entity-main"><strong>{session.title}</strong><span>{session.status} / {session.provider}</span></div>
                <div className="row-actions"><Button variant="secondary" icon={<PlayCircle size={17} />} onClick={() => join(session.id)}>Join</Button><Button variant="secondary" icon={<CheckCircle size={17} />} onClick={() => finish(session.id)}>Finish</Button></div>
              </div>
            ))}
          </div>
        ) : <Empty title="Live session yo'q" text="Kurs tanlab live dars yarating yoki listni yuklang." icon={<Broadcast size={22} />} />}
      </Panel>
      <Modal title="Live dars yaratish" open={createOpen} onClose={() => setCreateOpen(false)}>
        <form className="form-grid" onSubmit={createLive}>
          <Field label="Course"><Select required {...form.bind("course_id")}><option value="">Tanlang</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</Select></Field>
          <Field label="Title"><TextInput required {...form.bind("title")} /></Field>
          <div className="grid two"><Field label="Starts at"><TextInput type="datetime-local" required {...form.bind("starts_at")} /></Field><Field label="Ends at"><TextInput type="datetime-local" required {...form.bind("ends_at")} /></Field></div>
          <Field label="Room URL"><TextInput required {...form.bind("room_url")} /></Field>
          <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Bekor</Button><Button icon={<Broadcast size={17} />}>Yaratish</Button></div>
        </form>
      </Modal>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
