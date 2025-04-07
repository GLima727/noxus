const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send");
const feedbackTrigger = document.getElementById("feedback-trigger");

let conversationId = null;
let lastBotMessageId = null;
let currentThumb = null;

sendButton.onclick = async () => {
  const message = messageInput.value.trim();
  if (!message) return;

  chatBox.innerHTML += `<div class='user'><strong>You:</strong> ${message}</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;
  messageInput.value = "";

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId, max_length: 500, temperature: 0.7 })
  });

  const data = await response.json();
  const reply = data.reply || "(No reply)";
  if (data.conversation_id) conversationId = data.conversation_id;
  if (data.message_id) lastBotMessageId = data.message_id;

  const botDiv = document.createElement("div");
  botDiv.className = "assistant";
  botDiv.innerHTML = `<strong>Bot:</strong> ${reply}`;
  chatBox.appendChild(botDiv);

  feedbackTrigger.style.display = "inline-block";
  feedbackTrigger.onclick = () => {
    feedbackTrigger.style.display = "none";
    showFeedbackForm(lastBotMessageId);
  };

  chatBox.scrollTop = chatBox.scrollHeight;
};

function showFeedbackForm(messageId) {
  const feedbackDiv = document.createElement("div");
  feedbackDiv.className = "feedback";
  feedbackDiv.innerHTML = `
    <div class="feedback-form">
      <button onclick="selectThumb(this, true)">👍</button>
      <button onclick="selectThumb(this, false)">👎</button><br><br>
      <textarea rows="2" cols="40" placeholder="Leave a comment..."></textarea><br>
      <button onclick="submitCombinedFeedback(this, '${messageId}')">Send</button>
    </div>`;
  chatBox.appendChild(feedbackDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function selectThumb(button, isThumbUp) {
  const form = button.closest(".feedback-form");
  const buttons = form.querySelectorAll("button");
  buttons.forEach(btn => btn.classList.remove("selected"));
  button.classList.add("selected");
  currentThumb = isThumbUp;
}

function submitCombinedFeedback(button, messageId) {
  const form = button.closest(".feedback-form");
  const text = form.querySelector("textarea").value;

  const payload = {
    message_id: messageId
  };
  if (currentThumb === true) {
    payload.thumbs_up = true;
  } else if (currentThumb === false) {
    payload.thumbs_down = true;
  }
  if (text.trim() !== "") {
    payload.feedback_text = text.trim();
  }

  fetch('/feedback', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(res => res.json()).then(console.log);

  form.parentElement.style.display = "none";
}

messageInput.addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendButton.click();
});
