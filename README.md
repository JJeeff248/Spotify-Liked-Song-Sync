# Spotify Sync

Spotify Sync is a web application that allows users to automatically sync their liked songs to a selected playlist. It provides an easy way to create a shareable playlist of your favourite tracks.

## Features

- Authenticate with Spotify
- Select an existing playlist or create a new one
- Automatically sync liked songs to the chosen playlist
- Real-time progress tracking during sync
- Customizable sync interval

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7+
- Docker (optional, for containerized deployment)
- A Spotify Developer account

## Setup

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/spotify-sync.git
   cd spotify-sync
   ```

2. Create a Spotify application:
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new application
   - Note your Client ID and Client Secret
   - Add `http://localhost:5000/callback` to your application's Redirect URIs

3. Create a `.env` file in the project root with the following content:

   ```sh
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   REDIRECT_URI=http://localhost:5000/callback
   FLASK_SECRET_KEY=a_random_secret_key
   ```

4. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Running the Application

### Local Development

1. Start the Flask application:

   ```sh
   python app/main.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

### Docker Deployment

1. Build the Docker image:

   ```sh
   docker build -t spotify-sync .
   ```

2. Run the container:

   ```sh
   docker run -p 5000:5000 --env-file .env spotify-sync
   ```

3. Open a web browser and navigate to `http://localhost:5000`

## Usage

1. Log in with your Spotify account
2. Select an existing playlist or create a new one
3. Set your desired sync interval
4. Click "Start Sync" to begin syncing your liked songs
5. The application will automatically sync your liked songs to the chosen playlist at the specified interval

## Contributing

Contributions to Spotify Sync are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [Flask](https://flask.palletsprojects.com/)
