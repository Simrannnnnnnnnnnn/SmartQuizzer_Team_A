let timeLeft = 30;
let timerId = setInterval(countdown, 1000);
const timerDisplay = document.getElementById('timer');

function countdown() {
    if (timeLeft == -1) {
        clearTimeout(timerId);
        showFeedback("Time's Up!", "incorrect");
    } else {
        timerDisplay.innerHTML = timeLeft + 's remaining';
        timeLeft--;
    }
}

function showFeedback(message, status) {
    const feedbackDiv = document.getElementById('feedback-popup');
    feedbackDiv.innerHTML = message;
    feedbackDiv.className = status; // 'correct' or 'incorrect'
    feedbackDiv.style.display = 'block';
}