import { useState, useEffect } from "react";
import "./App.css";

// URL твого бекенду (перевір порт!)
const API_URL = "http://127.0.0.1:8000";

function App() {
  const [step, setStep] = useState("select"); // select, form, success
  const [templates, setTemplates] = useState([]);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [schema, setSchema] = useState({});
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState(null);

  // 1. Завантаження списку шаблонів при старті
  useEffect(() => {
    fetch(`${API_URL}/templates`)
      .then((res) => res.json())
      .then((data) => setTemplates(data))
      .catch((err) => console.error("API Error:", err));
  }, []);

  // 2. Початок сесії
  const startSession = async (template) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/start_session?template_code=${template.code}`, {
        method: "POST",
      });
      const data = await res.json();

      setSessionId(data.session_id);
      setSchema(data.schema); // Тут приходять питання з бекенду
      setCurrentTemplate(template);
      setStep("form");
    } catch (e) {
      alert("Помилка старту сесії");
    }
    setLoading(false);
  };

  // 3. Обробка змін у формі
  const handleInputChange = (key, value) => {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  };

  // 4. Генерація документу
  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Спочатку відправляємо відповіді
      const answerRes = await fetch(`${API_URL}/session/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answers),
      });

      if (!answerRes.ok) {
        throw new Error("Помилка при збереженні відповідей");
      }

      // Потім генеруємо файл
      const generateRes = await fetch(`${API_URL}/session/${sessionId}/generate`, {
        method: "POST",
      });

      if (!generateRes.ok) {
        const errorData = await generateRes.json();
        throw new Error(errorData.detail || "Помилка генерації файлу");
      }

      const data = await generateRes.json();

      setFileUrl(`${API_URL}${data.file_url}`);
      setStep("success");
    } catch (e) {
      console.error(e);
      alert(e.message || "Помилка генерації");
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <header>
        <div className="logo"></div>
        <span>Конструктор Договорів</span>
      </header>

      <main>
        {/* ЕКРАН 1: Вибір шаблону */}
        {step === "select" && (
          <>
            <h1>Оберіть документ</h1>
            <p>Створіть юридично грамотний документ за 2 хвилини.</p>

            {templates.length === 0 && <p>Завантаження шаблонів...</p>}

            {templates.map((t) => (
              <div key={t.id} className="card" onClick={() => startSession(t)}>
                <h3>{t.name}</h3>
                {/* Використовуємо description, яке генерує AI */}
                <span>{t.description}</span>
              </div>
            ))}
          </>
        )}

        {/* ЕКРАН 2: Заповнення форми */}
        {step === "form" && (
          <>
            <button
              onClick={() => setStep("select")}
              style={{ background: "none", border: "none", color: "#666", cursor: "pointer", marginBottom: "10px" }}
            >
              ← Назад
            </button>
            <h1>{currentTemplate.name}</h1>
            <p>Заповніть необхідні дані для формування документу.</p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSubmit();
              }}
            >
              {/* Рендеримо поля (всі текстові) */}
              {Object.entries(schema).map(([key, field]) => (
                <div key={key} className="form-group">
                  {/* 'field.question' - це наше запитання */}
                  <label>{field.question || key}</label>

                  {/* Всі поля тепер текстові */}
                  <input
                    type="text"
                    required
                    onChange={(e) => handleInputChange(key, e.target.value)}
                    placeholder={"Введіть відповідь..."}
                  />
                </div>
              ))}

              <button type="submit" className="primary" disabled={loading}>
                {loading ? "Генеруємо документ..." : "Створити документ"}
              </button>
            </form>
          </>
        )}

        {/* ЕКРАН 3: Успіх */}
        {step === "success" && (
          <div className="success-box">
            <h1 style={{ fontSize: "40px", margin: "0" }}>🎉</h1>
            <h2>Документ готовий!</h2>
            <p>Ваш договір успішно згенеровано. Ви можете завантажити його нижче.</p>

            <a href={fileUrl} target="_blank" className="download-btn" download>
              Завантажити .DOCX
            </a>

            <br />
            <br />
            <button
              onClick={() => setStep("select")}
              style={{ background: "none", border: "none", color: "#666", cursor: "pointer" }}
            >
              Створити ще один
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
