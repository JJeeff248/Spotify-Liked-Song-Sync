document.addEventListener('DOMContentLoaded', function() {
    const processingElement = document.getElementById('processing');
    const contentElement = document.getElementById('content');
    const syncProgress = document.getElementById('sync-progress');
    const currentSong = document.getElementById('current-song');
    const totalSongs = document.getElementById('total-songs');
    const progressBar = document.getElementById('progress-bar');
    const toggleButton = document.getElementById('toggleButton');
    const newPlaylistBtn = document.getElementById('newPlaylistBtn');
    const newPlaylistForm = document.getElementById('newPlaylistForm');
    const createPlaylistBtn = document.getElementById('createPlaylistBtn');
    const playlistSelect = document.getElementById('playlist_id');

    // Show processing spinner when form is submitted
    document.getElementById('settingsForm').addEventListener('submit', function() {
        processingElement.hidden = false;
        contentElement.hidden = true;
    });

    // Handle sync progress updates
    const eventSource = new EventSource("{{ url_for('sync_progress') }}");
    eventSource.onmessage = function(event) {
        const progress = JSON.parse(event.data);
        currentSong.textContent = progress.current;
        totalSongs.textContent = progress.total;
        progressBar.value = progress.percentage;
        syncProgress.hidden = false;
    };

    // Update button text based on sync status
    toggleButton.textContent = toggleButton.classList.contains('button-stop') ? 'Stop Syncing' : 'Start Sync';

    newPlaylistBtn.addEventListener('click', function() {
        newPlaylistForm.hidden = false;
        newPlaylistBtn.hidden = true;
    });

    createPlaylistBtn.addEventListener('click', function() {
        const playlistName = document.getElementById('newPlaylistName').value;
        if (playlistName) {
            createPlaylist(playlistName);
        }
    });

    function createPlaylist(playlistName) {
        fetch('/create_playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({name: playlistName}),
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                const option = new Option(data.name, data.id);
                option.dataset.image = data.images[0]?.url || '';
                playlistSelect.add(option);
                playlistSelect.value = data.id;
                newPlaylistForm.hidden = true;
                newPlaylistBtn.hidden = false;
            } else {
                alert('Failed to create playlist');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An error occurred while creating the playlist');
        });
    }
});
