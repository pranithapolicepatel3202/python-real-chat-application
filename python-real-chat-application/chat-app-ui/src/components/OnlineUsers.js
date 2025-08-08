import React from "react";

export default function OnlineUsers({ users, startChat }) {
  return (
    <div style={{
      width: "250px",
      borderRight: "1px solid #ccc",
      padding: "10px",
      overflowY: "auto"
    }}>
      <h3>Online Users</h3>
      {users.length === 0 && <p>No one online</p>}
      <ul style={{ listStyle: "none", padding: 0 }}>
        {users.map(user => (
          <li key={user.id}
              style={{
                marginBottom: "10px",
                cursor: "pointer",
                background: "#f0f0f0",
                padding: "5px",
                borderRadius: "5px"
              }}
              onClick={() => startChat(user.id)}>
            {user.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
