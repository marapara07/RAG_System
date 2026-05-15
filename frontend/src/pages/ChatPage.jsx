import { useEffect, useState } from "react";
import api from "../api/client";

export default function ChatPage({ user, onLogout }) {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [indexing, setIndexing] = useState(false);
  const [uploading, setUploading] = useState(false);

  const isAdmin = user.role === "Administrator";

  const loadConversations = async () => {
    const response = await api.get(`/conversations/${user.id}`);
    setConversations(response.data);

    if (response.data.length > 0 && !currentConversation) {
      setCurrentConversation(response.data[0]);
    }
  };

  const loadDocuments = async () => {
    const response = await api.get("/documents/");
    setDocuments(response.data);
  };

  const createConversation = async () => {
    const response = await api.post("/conversations/", {
      employee_id: user.id,
      title: "New conversation",
    });

    setCurrentConversation(response.data);
    setMessages([]);
    await loadConversations();
  };

  const deleteConversation = async (conversationId) => {
    await api.delete(`/conversations/${conversationId}`);

    if (currentConversation?.id === conversationId) {
      setCurrentConversation(null);
      setMessages([]);
    }

    await loadConversations();
  };

  const uploadDocument = async () => {
    if (!selectedFile) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      await api.post("/documents/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setSelectedFile(null);
      await loadDocuments();

      alert("Document uploaded successfully.");
    } catch {
      alert("Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const reindexDocuments = async () => {
    setIndexing(true);

    try {
      await api.post("/documents/reindex");
      alert("Documents reindexed successfully.");
    } catch {
      alert("Reindex failed.");
    } finally {
      setIndexing(false);
    }
  };

  const sendQuestion = async () => {
    if (!question.trim() || !currentConversation) return;

    const currentQuestion = question;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: currentQuestion,
        sources: null,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await api.post("/chat/ask", {
        conversation_id: currentConversation.id,
        question: currentQuestion,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.data.answer,
          sources: JSON.stringify(response.data.sources),
        },
      ]);

      await loadConversations();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "An error occurred while generating the answer.",
          sources: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    async function fetchInitialData() {
      const conversationsResponse = await api.get(`/conversations/${user.id}`);
      setConversations(conversationsResponse.data);

      if (conversationsResponse.data.length > 0) {
        setCurrentConversation(conversationsResponse.data[0]);
      }

      const documentsResponse = await api.get("/documents/");
      setDocuments(documentsResponse.data);
    }

    fetchInitialData();
  }, [user.id]);

  useEffect(() => {
    async function fetchMessages() {
      if (!currentConversation) return;

      const response = await api.get(
        `/conversations/${currentConversation.id}/messages`
      );

      setMessages(response.data);
    }

    fetchMessages();
  }, [currentConversation]);

  return (
    <div style={styles.page}>
      <aside style={styles.sidebar}>
        <h2>AI Helper</h2>

        <div style={styles.userBox}>
          <b>{user.name}</b>
          <span>{user.email}</span>
          <span>{user.role}</span>
        </div>

        {isAdmin && (
          <div style={styles.documentBox}>
            <p style={styles.sectionTitle}>Documents</p>

            <input
              type="file"
              accept=".pdf,.txt"
              style={styles.fileInput}
              onChange={(e) => setSelectedFile(e.target.files[0])}
            />

            <button
              style={styles.smallButton}
              onClick={uploadDocument}
              disabled={!selectedFile || uploading}
            >
              {uploading ? "Uploading..." : "Upload"}
            </button>

            <button
              style={styles.smallButtonSecondary}
              onClick={reindexDocuments}
              disabled={indexing}
            >
              {indexing ? "Indexing..." : "Reindex"}
            </button>

            <div style={styles.documentList}>
              {documents.length === 0 ? (
                <span style={styles.emptyText}>No documents uploaded</span>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} style={styles.documentItem}>
                    {doc.filename}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        <button style={styles.newButton} onClick={createConversation}>
          + New conversation
        </button>

        <div style={styles.history}>
          {conversations.length === 0 ? (
            <p>No conversations yet</p>
          ) : (
            conversations.map((conv) => (
              <div key={conv.id} style={styles.conversationRow}>
                <button
                  style={{
                    ...styles.conversationButton,
                    background:
                      currentConversation?.id === conv.id
                        ? "#334155"
                        : "transparent",
                  }}
                  onClick={() => setCurrentConversation(conv)}
                >
                  {conv.title}
                </button>

                <button
                  style={styles.deleteButton}
                  onClick={() => deleteConversation(conv.id)}
                  title="Delete conversation"
                >
                  🗑️
                </button>
              </div>
            ))
          )}
        </div>

        <button style={styles.logoutButton} onClick={onLogout}>
          Log out
        </button>
      </aside>

      <main style={styles.chatArea}>
        <div style={styles.header}>
          <h1>Your Internal Assistant</h1>
          <p>
            {currentConversation
              ? currentConversation.title
              : "Create a conversation to start asking questions."}
          </p>
        </div>

        <div style={styles.messages}>
          {messages.length === 0 && (
            <div style={styles.assistantMessage}>
              Hello, {user.name}. How can I help you today?
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                ...styles.messageWrapper,
                justifyContent:
                  msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={
                  msg.role === "user"
                    ? styles.userMessage
                    : styles.assistantMessage
                }
              >
                {msg.content}

                {msg.role === "assistant" && msg.sources && (
                  <div style={styles.sources}>
                    Sources: {formatSources(msg.sources)}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div style={styles.assistantMessage}>
              Looking for the best answer...
            </div>
          )}
        </div>

        <div style={styles.inputArea}>
          <input
            style={styles.chatInput}
            placeholder="Write your question here..."
            value={question}
            disabled={!currentConversation || loading}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendQuestion();
              }
            }}
          />

          <button
            style={styles.sendButton}
            disabled={!currentConversation || loading}
            onClick={sendQuestion}
          >
            Send
          </button>
        </div>
      </main>
    </div>
  );
}

function formatSources(sources) {
  try {
    const parsed = JSON.parse(sources);
    return parsed.join(" | ");
  } catch {
    return sources;
  }
}

const styles = {
  page: {
    height: "100vh",
    display: "flex",
    background: "#0f172a",
    color: "white",
  },

  sidebar: {
    width: "340px",
    background: "#020617",
    padding: "24px",
    display: "flex",
    flexDirection: "column",
    gap: "18px",
    borderRight: "1px solid #1e293b",
  },

  userBox: {
    background: "#1e293b",
    padding: "14px",
    borderRadius: "14px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    fontSize: "14px",
    color: "#cbd5e1",
  },

  documentBox: {
    background: "#0f172a",
    border: "1px solid #1e293b",
    padding: "12px",
    borderRadius: "14px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },

  sectionTitle: {
    fontSize: "13px",
    color: "#94a3b8",
    fontWeight: "bold",
  },

  fileInput: {
    fontSize: "12px",
    color: "#cbd5e1",
  },

  smallButton: {
    padding: "9px",
    borderRadius: "8px",
    border: "none",
    background: "#7c3aed",
    color: "white",
    fontWeight: "bold",
  },

  smallButtonSecondary: {
    padding: "9px",
    borderRadius: "8px",
    border: "1px solid #334155",
    background: "transparent",
    color: "#cbd5e1",
    fontWeight: "bold",
  },

  documentList: {
    maxHeight: "90px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },

  documentItem: {
    fontSize: "12px",
    color: "#cbd5e1",
    background: "#1e293b",
    padding: "7px",
    borderRadius: "8px",
  },

  emptyText: {
    fontSize: "12px",
    color: "#64748b",
  },

  newButton: {
    padding: "12px",
    borderRadius: "10px",
    border: "none",
    background: "#7c3aed",
    color: "white",
    fontWeight: "bold",
  },

  history: {
    flex: 1,
    color: "#94a3b8",
    fontSize: "14px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },

  conversationRow: {
    display: "flex",
    gap: "6px",
    alignItems: "center",
  },

  conversationButton: {
    flex: 1,
    padding: "12px",
    borderRadius: "10px",
    border: "1px solid #1e293b",
    color: "#cbd5e1",
    textAlign: "left",
  },

  deleteButton: {
    opacity: 0.7,
    padding: "8px",
    borderRadius: "8px",
    border: "1px solid #1e293b",
    background: "transparent",
    color: "#cbd5e1",
  },

  logoutButton: {
    padding: "12px",
    borderRadius: "10px",
    border: "1px solid #334155",
    background: "transparent",
    color: "#cbd5e1",
  },

  chatArea: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
  },

  header: {
    padding: "28px 40px",
    borderBottom: "1px solid #1e293b",
  },

  messages: {
    flex: 1,
    padding: "40px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },

  messageWrapper: {
    display: "flex",
    width: "100%",
  },

  assistantMessage: {
    background: "#1e293b",
    padding: "16px",
    borderRadius: "16px",
    maxWidth: "700px",
    lineHeight: "1.5",
  },

  userMessage: {
    background: "#7c3aed",
    padding: "16px",
    borderRadius: "16px",
    maxWidth: "700px",
    lineHeight: "1.5",
  },

  sources: {
    marginTop: "10px",
    fontSize: "12px",
    color: "#cbd5e1",
    fontStyle: "italic",
  },

  inputArea: {
    padding: "24px 40px",
    display: "flex",
    gap: "12px",
    borderTop: "1px solid #1e293b",
  },

  chatInput: {
    flex: 1,
    padding: "14px",
    borderRadius: "12px",
    background: "#1e293b",
    color: "white",
  },

  sendButton: {
    padding: "14px 22px",
    borderRadius: "12px",
    border: "none",
    background: "#7c3aed",
    color: "white",
    fontWeight: "bold",
  },
};