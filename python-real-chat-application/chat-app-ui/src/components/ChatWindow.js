import React, { useState } from "react";

export default function ChatWindow({ messages, sendMessage, endChat, chatTarget, myId }) {
  const [text, setText] = useState("");

  if (!chatTarget) {
    return (
      <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <p>Select a user to start chat</p>
      </div>
    );
  }

  const handleSend = () => {
    if (text.trim()) {
      sendMessage(text.trim());
      setText("");
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "10px", background: "#fafafa" }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            textAlign: msg.from === myId ? "right" : "left",
            marginBottom: "5px"
          }}>
            <span style={{
              display: "inline-block",
              padding: "5px 10px",
              borderRadius: "5px",
              background: msg.from === myId ? "#c8e6c9" : "#e1f5fe"
            }}>
              {msg.content}
            </span>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", padding: "10px", borderTop: "1px solid #ccc" }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={{ flex: 1, padding: "5px" }}
          placeholder="Type a message..."
        />
        <button onClick={handleSend} style={{ marginLeft: "5px" }}>Send</button>
        <button onClick={endChat} style={{ marginLeft: "5px", background: "#f44336", color: "#fff" }}>
          End
        </button>
      </div>
    </div>
  );
}
