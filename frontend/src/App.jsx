import { useState, useEffect, useRef } from "react";

const styles = `
  body { 
    margin: 0; 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
    background: #E5E9EC;
    color: #000; 
    overflow-x: hidden;
  }
  
  .container { 
    width: 100%; 
    min-height: 100vh; 
    display: flex; 
    flex-direction: column; 
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes ellipsis {
    0% { content: '.'; }
    33% { content: '..'; }
    66% { content: '...'; }
    100% { content: '.'; }
  }

  .loading-dots::after {
    content: '.';
    animation: ellipsis 1.5s infinite;
    display: inline-block;
    width: 20px;
    text-align: left;
  }

  /* Initial Welcome Screen (Screen 1) */
  .initial-welcome {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 40px 24px 100px 24px;
    animation: fadeIn 0.6s ease-out;
    position: relative;
  }

  .welcome-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 600px;
    width: 100%;
    margin: 0 auto;
  }

  .welcome-greeting {
    margin-top: 40px;
    margin-bottom: 32px;
  }

  .welcome-greeting h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #000;
    margin: 0 0 24px 0;
    line-height: 1.3;
  }

  .welcome-description {
    font-size: 1rem;
    color: #000;
    line-height: 1.6;
    margin-bottom: 16px;
  }

  .start-button-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 20px 24px;
    background: #E5E9EC;
    display: flex;
    justify-content: center;
  }

  .start-button {
    width: 100%;
    max-width: 600px;
    padding: 16px 32px;
    background: #000;
    color: white;
    border: none;
    border-radius: 30px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }

  .start-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
  }

  /* Document Selection Screen (Screen 2) */
  .selection-screen {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 40px 24px;
    animation: fadeIn 0.6s ease-out;
  }

  .selection-header {
    margin-bottom: 32px;
    max-width: 800px;
    width: 100%;
    margin-left: auto;
    margin-right: auto;
  }

  .selection-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #000;
    margin: 0 0 12px 0;
  }

  .templates-grid { 
    display: grid; 
    gap: 16px; 
    max-width: 800px;
    width: 100%;
    margin: 0 auto;
  }
  
  .card { 
    background: white;
    border: 1px solid #D1D5DB;
    padding: 24px; 
    border-radius: 16px; 
    cursor: pointer; 
    transition: all 0.2s ease;
  }
  
  .card:hover { 
    transform: translateY(-2px); 
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-color: #9CA3AF;
  }

  .card h3 { 
    margin: 0 0 8px 0; 
    color: #000;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .card p {
    margin: 0;
    color: #6B7280;
    font-size: 0.9rem;
    line-height: 1.5;
  }

  /* Chat Screen (Screen 3) */
  .chat-container {
    width: 100%;
    min-height: 100vh;
    background: #E5E9EC;
    display: flex;
    flex-direction: column;
  }
  
  .chat-container.with-preview {
    max-width: 50%;
    box-shadow: 2px 0 20px rgba(0,0,0,0.1);
  }

  .app-header { 
    padding: 20px 24px; 
    border-bottom: 1px solid #D1D5DB; 
    font-weight: 700; 
    font-size: 1.2rem; 
    text-align: center; 
    color: #000;
    background: #E5E9EC;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .messages-area { 
    flex: 1; 
    overflow-y: auto; 
    padding: 24px; 
    padding-bottom: 112px;
    display: flex; 
    flex-direction: column; 
    gap: 12px;
    background: #E5E9EC;
    max-width: 1000px;
    width: 100%;
    margin: 0 auto;
  }
  
  .message { 
    max-width: 75%; 
    padding: 14px 18px; 
    border-radius: 16px; 
    font-size: 0.95rem; 
    white-space: pre-wrap;
    line-height: 1.5;
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .message.bot { 
    align-self: flex-start; 
    background: white; 
    color: #000;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  
  .message.user { 
    align-self: flex-end; 
    background: #000;
    color: white;
    border-bottom-right-radius: 4px;
  }
  
  .message.error { 
    align-self: center; 
    background: #FEE2E2; 
    color: #991B1B;
    border: 1px solid #FCA5A5;
    border-radius: 12px;
    max-width: 90%;
  }
  
  .message.system { 
    align-self: center; 
    font-size: 0.85rem; 
    color: #6B7280;
    background: transparent;
  }

  .input-area { 
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);

    display: flex; 
    gap: 12px; 
    padding: 20px 24px; 
    background: #E5E9EC;

    max-width: 1000px;
    width: 100%;
    box-sizing: border-box;

    /* Щоб не перекривав інші елементи */
    z-index: 999; 
}
  
  input { 
    flex: 1; 
    padding: 14px 18px; 
    border: 1px solid #D1D5DB; 
    border-radius: 24px; 
    outline: none; 
    font-size: 1rem; 
    color: #000;
    background: white;
    transition: border-color 0.2s;
  }

  input:focus {
    border-color: #9CA3AF;
  }
  
  button { 
    padding: 0 28px; 
    background: #000;
    color: white;
    border: none; 
    border-radius: 24px; 
    cursor: pointer; 
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.2s;
  }

  button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }
  
  button:disabled { 
    background: #9CA3AF; 
    cursor: not-allowed;
    transform: none;
  }

  .download-link {
    display: inline-block;
    background: #000;
    color: white;
    padding: 14px 28px;
    border-radius: 24px;
    text-decoration: none;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: all 0.2s;
  }

  .download-link:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
  }

  @media (max-width: 768px) {
    .welcome-greeting h1 {
      font-size: 1.75rem;
    }
    .card {
      padding: 20px;
    }
  }
`;

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [step, setStep] = useState("welcome");
  const [templates, setTemplates] = useState([]);
  const [sessionId, setSessionId] = useState(null);

  // Зберігаємо код шаблону для AI в режимі перевірки
  const [currentTemplateCode, setCurrentTemplateCode] = useState(null);

  const [fieldGroups, setFieldGroups] = useState([]);
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0);

  // === НОВИЙ СТАН: Режим перевірки ===
  const [isReviewMode, setIsReviewMode] = useState(false);

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetch(`${API_URL}/templates`)
      .then((r) => r.json())
      .then(setTemplates)
      .catch((e) => console.error("API Error", e));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startSession = async (template) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/start_session?template_code=${template.code}`, { method: "POST" });
      if (!res.ok) throw new Error("Server error");
      const data = await res.json();

      setSessionId(data.session_id);
      setCurrentTemplateCode(template.code);

      setFieldGroups(data.field_groups || []);
      setCurrentGroupIndex(0);
      setIsReviewMode(false); // Спочатку режим перевірки вимкнено

      setMessages([
        { type: "system", text: `Шаблон: ${template.name}` },
        { type: "bot", text: data.start_message },
      ]);

      setStep("chat");
    } catch (e) {
      console.error(e);
      alert("Помилка старту сесії");
    }
    setLoading(false);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const text = inputValue;
    setInputValue("");
    setMessages((prev) => [...prev, { type: "user", text }]);
    setLoading(true);

    try {
      // Підготовка історії чату (потрібна і для збору, і для перевірки)
      const chatHistory = messages.map((m) => ({
        role: m.type === "bot" ? "assistant" : "user",
        content: m.text,
      }));

      // ========================================================
      // ЛОГІКА РЕЖИМУ ПЕРЕВІРКИ (REVIEW MODE)
      // ========================================================
      if (isReviewMode) {
        const res = await fetch(`${API_URL}/assistant/review_mode`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            user_message: text,
            chat_history: chatHistory, // <--- Передаємо історію!
            template_code: currentTemplateCode,
          }),
        });
        const aiData = await res.json();

        if (aiData.action === "generate") {
          // Користувач підтвердив -> йдемо генерувати
          setMessages((prev) => [...prev, { type: "bot", text: aiData.message }]);
          finishSession();
        } else if (aiData.action === "update") {
          // Користувач хоче змінити дані
          // Перевіряємо, чи AI справді повернув поля для оновлення
          const fieldsToUpdate = aiData.fields || {};

          if (Object.keys(fieldsToUpdate).length > 0) {
            setMessages((prev) => [...prev, { type: "bot", text: aiData.message }]);

            // Зберігаємо нові значення
            const saveRes = await fetch(`${API_URL}/session/${sessionId}/answer`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(fieldsToUpdate),
            });

            if (saveRes.ok) {
              // Тільки після успішного оновлення показуємо нове САММАРІ
              const summaryRes = await fetch(`${API_URL}/session/${sessionId}/formatted_summary`);
              const summaryData = await summaryRes.json();
              setMessages((prev) => [...prev, { type: "bot", text: summaryData.summary }]);
            } else {
              setMessages((prev) => [...prev, { type: "error", text: "Помилка при оновленні даних." }]);
            }
          } else {
            // Якщо action="update", але полів немає (AI просто каже "Добре, змінюю", але ще не знає на що)
            setMessages((prev) => [...prev, { type: "bot", text: aiData.message }]);
          }
        } else {
          // action: "chat" -> Просто балакаємо (уточнюємо деталі)
          setMessages((prev) => [...prev, { type: "bot", text: aiData.message }]);
        }

        setLoading(false);
        return; // Виходимо з функції
      }

      // ========================================================
      // СТАНДАРТНА ЛОГІКА (ЗБІР ДАНИХ ПО ГРУПАХ)
      // ========================================================
      const currentGroup = fieldGroups[currentGroupIndex];
      const groupFields = currentGroup ? currentGroup.fields : [];

      const res = await fetch(`${API_URL}/assistant/conversational_collect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          user_message: text,
          chat_history: chatHistory,
          current_group_fields: groupFields,
        }),
      });

      const aiData = await res.json();

      if (aiData.action === "chat") {
        setMessages((prev) => [...prev, { type: "bot", text: aiData.message }]);
      } else if (aiData.action === "extract") {
        if (aiData.message) {
          setMessages((prev) => [...prev, { type: "bot", text: aiData.message }]);
        }

        const saveRes = await fetch(`${API_URL}/session/${sessionId}/answer`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(aiData.fields),
        });

        if (!saveRes.ok) {
          const errorJson = await saveRes.json();
          let errorText = "Дані не прийнято.";
          if (errorJson.detail && errorJson.detail.validation_errors) {
            errorText = errorJson.detail.validation_errors.map((e) => `🔴 ${e.field}: ${e.message}`).join("\n");
          }
          setMessages((prev) => [
            ...prev,
            { type: "error", text: `Помилка перевірки:\n${errorText}` },
            { type: "bot", text: "Спробуйте, будь ласка, ввести ці дані ще раз коректно." },
          ]);
        } else {
          // === ТУТ ПОВЕРНУТО ПОВІДОМЛЕННЯ ПРО УСПІШНИЙ ЗАПИС ===
          setMessages((prev) => [...prev, { type: "system", text: "Дані записано ✓" }]);

          // Перевіряємо, чи заповнена поточна група
          const saveData = await saveRes.json();
          const currentAnswers = saveData.current_answers || {};
          const updatedFields = saveData.updated_fields || [];

          const missingFields = groupFields.filter((requiredField) => {
            return !currentAnswers[requiredField] && !currentAnswers[requiredField.toLowerCase()];
          });

          if (missingFields.length > 0) {
            // Є пропущені поля в групі -> просимо AI уточнити
            try {
              const clarifyRes = await fetch(`${API_URL}/assistant/clarify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ missing_fields: missingFields, filled_fields: updatedFields }),
              });
              const clarifyData = await clarifyRes.json();
              setMessages((prev) => [...prev, { type: "bot", text: clarifyData.message }]);
            } catch (err) {
              setMessages((prev) => [
                ...prev,
                { type: "bot", text: `Будь ласка, доповніть: ${missingFields.join(", ")}` },
              ]);
            }
          } else {
            // Всі поля групи заповнені -> переходимо далі
            const nextIdx = currentGroupIndex + 1;

            if (nextIdx < fieldGroups.length) {
              setCurrentGroupIndex(nextIdx);
              const nextGroup = fieldGroups[nextIdx];
              setTimeout(() => {
                setMessages((prev) => [...prev, { type: "bot", text: nextGroup.prompt || nextGroup.initial_prompt }]);
              }, 600);
            } else {
              // === ВСІ ГРУПИ ПРОЙДЕНО -> ВМИКАЄМО РЕЖИМ ПЕРЕВІРКИ ===
              enterReviewMode();
            }
          }
        }
      }
    } catch (e) {
      console.error(e);
      setMessages((prev) => [...prev, { type: "error", text: "Помилка сервера" }]);
    }
    setLoading(false);
  };

  // Функція активації режиму перевірки
  const enterReviewMode = async () => {
    setIsReviewMode(true);
    try {
      const res = await fetch(`${API_URL}/session/${sessionId}/formatted_summary`);
      const data = await res.json();
      setMessages((prev) => [...prev, { type: "bot", text: data.summary }]);
    } catch (e) {
      setMessages((prev) => [...prev, { type: "error", text: "Не вдалося завантажити підсумок." }]);
    }
  };

  const finishSession = async () => {
    setMessages((prev) => [...prev, { type: "system", text: "Генерую файл..." }]);
    try {
      const res = await fetch(`${API_URL}/session/${sessionId}/generate`, { method: "POST" });
      if (res.ok) {
        setDownloadUrl(sessionId);
        setMessages((prev) => [...prev, { type: "bot", text: "Готово! Натисніть кнопку нижче." }]);
      } else {
        throw new Error("Generation failed");
      }
    } catch (e) {
      setMessages((prev) => [...prev, { type: "error", text: "Не вдалося згенерувати файл." }]);
    }
  };

  const handleDownload = async () => {
    try {
      const res = await fetch(`${API_URL}/session/${downloadUrl}/generate`, { method: "POST" });
      if (!res.ok) throw new Error("Download failed");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "contract.docx";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setMessages((prev) => [...prev, { type: "system", text: "Файл завантажено ✓" }]);
    } catch (e) {
      setMessages((prev) => [...prev, { type: "error", text: "Помилка завантаження файлу." }]);
    }
  };

  return (
    <div className="container">
      <style>{styles}</style>

      {/* Screen 1: Initial Welcome */}
      {step === "welcome" && (
        <div className="initial-welcome">
          <div className="welcome-content">
            <div className="welcome-greeting">
              <h1>Вітаємо в Дія.Контракт 👋</h1>
              <p className="welcome-description">
                Створюйте юридичні документи швидко та легко за допомогою штучного інтелекту.
              </p>
              <p className="welcome-description">
                Дія.Контракт — це інструмент, який допомагає вам заповнювати шаблони документів у розмовному режимі.
                Просто відповідайте на запитання, і система автоматично створить готовий документ у форматі DOCX.
              </p>
              <p className="welcome-description">
                Всі ваші дані зберігаються конфіденційно та використовуються виключно для створення документа.
              </p>
            </div>
          </div>
          <div className="start-button-container">
            <button className="start-button" onClick={() => setStep("select")}>
              Почати
            </button>
          </div>
        </div>
      )}

      {/* Screen 2: Document Selection */}
      {step === "select" && (
        <div className="selection-screen">
          <div className="selection-header">
            <h1>Оберіть тип документа</h1>
          </div>
          <div className="templates-grid">
            {templates.map((t) => (
              <div key={t.id} className="card" onClick={() => startSession(t)}>
                <h3>{t.name}</h3>
                <p>Натисніть, щоб розпочати заповнення</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Screen 3: Chat Interface */}
      {step === "chat" && (
        <div className="chat-container">
          <div className="app-header">Дія.Контракт</div>
          <div className="messages-area">
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.type}`}>
                {m.text}
              </div>
            ))}
            {downloadUrl && (
              <div style={{ textAlign: "center", margin: "20px 0" }}>
                <button
                  onClick={handleDownload}
                  className="download-link"
                  style={{ border: "none", cursor: "pointer" }}
                >
                  📄 Завантажити DOCX
                </button>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="input-area">
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ваша відповідь..."
              disabled={loading}
              autoFocus
            />
            <button onClick={handleSend} disabled={loading}>
              {loading ? <span className="loading-dots">Обробка</span> : "Надіслати"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
