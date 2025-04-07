async function loadConversations() {
    const response = await fetch('/talks-data');
    const conversations = await response.json();
    const container = document.getElementById('content');
    container.innerHTML = '';
  
    conversations.forEach(convo => {
      const convoDiv = document.createElement('div');
      convoDiv.className = 'conversation';
      convoDiv.innerHTML = `<h2>Conversation ID: ${convo.conversation_id}</h2>`;
  
      convo.messages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${msg.role}`;
        msgDiv.innerHTML = `<strong>${msg.role}:</strong> ${msg.content} <small>(${msg.timestamp})</small>`;
        console.log(msg);
  
        if (msg.thumbs_up || msg.thumbs_down || msg.feedback_text) {
          const feedback = document.createElement('div');
          feedback.className = 'feedback';
          let feedbackStr = 'Feedback: ';
          if (msg.thumbs_up) feedbackStr += '👍 ';
          if (msg.thumbs_down) feedbackStr += '👎 ';
          if (msg.feedback_text) feedbackStr += `"${msg.feedback_text}"`;
          feedback.textContent = feedbackStr;
          msgDiv.appendChild(feedback);
        }
  
        convoDiv.appendChild(msgDiv);
      });
  
      container.appendChild(convoDiv);
    });
  }
  
  loadConversations();
  