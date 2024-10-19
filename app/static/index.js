document.addEventListener('DOMContentLoaded', function() {
    const loadingElement = document.getElementById('loading');
    const loginButton = document.getElementById('loginButton');
    const privacyButton = document.getElementById('privacyButton');
    const privacyModal = document.getElementById('privacyModal');
    const closeModal = document.getElementById('closeModal');
    const loadingMessageElement = document.getElementById('loading-message');

    const loadingMessages = [
        "Connecting to Spotify...",
        "Comparing playlists...",
        "Analyzing your music taste...",
    ];

    let currentMessageIndex = 0;
    let messageInterval;

    function showLoading() {
        loadingElement.hidden = false;
        loginButton.parentElement.hidden = true;
        rotateLoadingMessage();
    }

    function rotateLoadingMessage() {
        messageInterval = setInterval(() => {
            currentMessageIndex = (currentMessageIndex + 1) % loadingMessages.length;
            loadingMessageElement.textContent = loadingMessages[currentMessageIndex];
        }, Math.floor(Math.random() * (8000 - 6000 + 1)) + 6000);
    }

    function openPrivacyModal() {
        privacyModal.hidden = false;
    }

    function closePrivacyModal() {
        privacyModal.hidden = true;
    }

    loginButton.addEventListener('click', showLoading);
    privacyButton.addEventListener('click', openPrivacyModal);
    closeModal.addEventListener('click', closePrivacyModal);

    // Close the modal if the user clicks outside of it
    window.addEventListener('click', function(event) {
        if (event.target === privacyModal) {
            closePrivacyModal();
        }
    });
});
