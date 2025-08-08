import React, { useEffect, useState, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import OnlineUsers from "./components/OnlineUsers";
import ChatWindow from "./components/ChatWindow";

const WS_URL = "ws://localhost:8000/ws";

export default function App() {
  const [ws, setWs] = useState(null);
  const [userId, setUserId] = useState(null);
  const [name, setName] = useState("");
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [chatTarget, setChatTarget] = useState(null);
  const [messages, setMessages] = useState([]);

  const messagesRef = useRef([]);

  useEffect(() => {
    const myName = prompt("Enter your name") || `anon-${uuidv4().slice(0, 8)}`;
    setName(myName);

    const socket = new WebSocket(WS_URL);
    setWs(socket);

    socket.onopen = () => {
      console.log("✅ Connected to backend WS");
      socket.send(JSON.stringify({
        type: "register",
        name: myName // don't send empty user_id unless required by backend
      }));
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("📩 WS message:", data);

      switch (data.type) {
        case "registered":
          setUserId(data.user_id);
          break;

        case "presence":
          setOnlineUsers(data.users.filter(u => u.id !== userId));
          break;

        case "chat_started":
          const otherId = data.pair.find(id => id !== userId);
          setChatTarget(otherId);
          messagesRef.current = [];
          setMessages([]);
          break;

        case "chat_ended":
          setChatTarget(null);
          messagesRef.current = [];
          setMessages([]);
          break;

        case "message":
          messagesRef.current = [...messagesRef.current, {
            from: data.from,
            content: data.content
          }];
          setMessages([...messagesRef.current]);
          break;

        default:
          console.warn("Unknown WS type:", data.type);
      }
    };

    socket.onclose = () => {
      console.log("❌ WS closed");
    };

    return () => {
      socket.close();
    };
  }, []); // ✅ empty dependency array — run once

  const startChat = (targetId) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "start_chat",
        target_id: targetId
      }));
    }
  };

  const sendMessage = (text) => {
    if (ws && chatTarget && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "message",
        to: chatTarget,
        content: text
      }));
      messagesRef.current = [...messagesRef.current, {
        from: userId,
        content: text
      }];
      setMessages([...messagesRef.current]);
    }
  };

  const endChat = () => {
    if (ws && chatTarget && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "end_chat",
        target_id: chatTarget
      }));
    }
    setChatTarget(null);
    messagesRef.current = [];
    setMessages([]);
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "Arial, sans-serif" }}>
      <OnlineUsers users={onlineUsers} startChat={startChat} />
      <ChatWindow
        messages={messages}
        sendMessage={sendMessage}
        endChat={endChat}
        chatTarget={chatTarget}
        myId={userId}
      />
    </div>
  );
}
