import { useState } from "react";
import LoginPage from "./pages/LoginPage";
import ChatPage from "./pages/ChatPage";

export default function App() {
  const [user, setUser] = useState(null);

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

  return <ChatPage user={user} onLogout={logout} />;
}