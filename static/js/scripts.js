document.addEventListener("DOMContentLoaded", function () {
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const clearBtn = document.getElementById("clear-btn");
  const chatBox = document.getElementById("chat-box");
  const languageSelect = document.getElementById("language-select"); // Assuming you have a language select element

  let selectedLanguage = "en"; // Default language is English

  languageSelect.addEventListener("change", function () {
    selectedLanguage = languageSelect.value;
    clearChat();
    appendMessage(
      "assistant",
      `Language switched to ${
        languageSelect.options[languageSelect.selectedIndex].text
      }`
    );
  });

  // Function to handle sending the message on button click or Enter press
  function sendMessage() {
    const question = userInput.value.trim();
    if (question) {
      appendMessage("user", question);
      fetchResponse(question);
    }
    userInput.value = "";
  }

  // Event listener for clicking the Send button
  sendBtn.addEventListener("click", sendMessage);

  // Event listener for pressing Enter in the input field
  userInput.addEventListener("keydown", function (event) {
    if (event.keyCode === 13) {
      // 13 is the key code for Enter
      sendMessage();
    }
  });

  clearBtn.addEventListener("click", function () {
    clearChat();
  });

  function clearChat() {
    chatBox.innerHTML = `
      <div class="message assistant">
        <img src="/static/images/bot.png" alt="Bot" class="avatar" />
        <div class="message-content"><span>Ask me a question based on the guidelines</span></div>
      </div>`;
  }

  function appendMessage(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src =
      role === "user" ? "/static/images/user.png" : "/static/images/bot.png";
    avatar.alt = role;

    const textDiv = document.createElement("div");
    textDiv.className = "message-content";
    const textSpan = document.createElement("span");
    textSpan.innerHTML = formatText(content);
    textDiv.appendChild(textSpan);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(textDiv);

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function formatText(text) {
    return text
      .replace(/\*\*Challenges:\*\*/g, "<b>Challenges:</b>")
      .replace(/\*\*Solutions:\*\*/g, "<b>Solutions:</b>")
      .replace(/\*\*/g, "")
      .replace(/\n/g, "<br>");
  }

  async function fetchResponse(question) {
    appendTypingIndicator();
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, language: selectedLanguage }),
    });
    const result = await response.json();
    removeTypingIndicator();
    appendMessage("assistant", result.answer);

    if (!result.available) {
      const googleButton = document.createElement("button");
      googleButton.textContent = "Search on Google";
      googleButton.className = "google-btn";
      googleButton.onclick = async function () {
        googleButton.textContent = "Searching in Google...";
        googleButton.disabled = true;
        await googleSearch(question);
        googleButton.remove();
      };
      chatBox.appendChild(googleButton);
    }
  }

  async function googleSearch(query) {
    appendMessage("assistant", "Searching in Google...");
    const response = await fetch("/google_search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, language: selectedLanguage }),
    });
    const result = await response.json();
    removeTypingIndicator();
    appendMessage("assistant", result.answers.join("<br>"));
  }

  function appendTypingIndicator() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "message assistant typing-indicator";

    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src = "/static/images/bot.png";
    avatar.alt = "Bot";

    const typingDot1 = document.createElement("div");
    typingDot1.className = "typing";

    const typingDot2 = document.createElement("div");
    typingDot2.className = "typing";

    const typingDot3 = document.createElement("div");
    typingDot3.className = "typing";

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(typingDot1);
    typingDiv.appendChild(typingDot2);
    typingDiv.appendChild(typingDot3);

    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function removeTypingIndicator() {
    const typingIndicator = document.querySelector(".typing-indicator");
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }
});
