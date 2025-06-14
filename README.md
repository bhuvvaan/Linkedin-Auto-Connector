Credits- Ahmed Mujtaba - [Linkedin](https://www.linkedin.com/in/creative-programmer/)

# LinkedIn Auto Connector

This script automates the process of sending connection requests on LinkedIn based on search criteria.

## Setup Instructions

1. Make sure you have Python installed on your system.

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your input parameters in `input_config.ini`:
   - The first time you run the script, it will create a default `input_config.ini` file
   - Edit this file with your login details

4. Run the script:
   ```
   python main.py
   ```

## Configuration Options

### SearchCriteria
- `connection_degree`: The degree of connection (1st, 2nd, or 3rd)
- `keyword`: Search keyword (e.g., "software engineer")
- `location`: Location to filter results (e.g., "United States")
- `limit`: Maximum number of connection requests to send

### Messages
- `include_note`: Set to True to include a personalized note with connection requests (for 2nd and 3rd connections)
- `connection_message`: The message to send with connection requests. Use {name} to include the recipient's first name
- `message_letter`: Message for 1st connections (leave empty if not using)

## Notes
- The script will create a default `input_config.ini` file if one doesn't exist
- Edit the configuration file with your preferences before running the script
- The script uses cookies for authentication to avoid LinkedIn's login detection systems

## Features

- Login using LinkedIn cookies or credentials
- Select location filters for connection requests
- Send personalized connection requests
- Configurable via `setup.ini` file
- Color-coded console outputs for better readability

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/ahmedmujtaba1/Linkedin-Auto-Connector.git
    cd Linkedin-Auto-Connector
    ```

2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure your LinkedIn credentials and settings in the `setup.ini` file:
    ```ini
    [LinkedIn]
    email = YOUR_EMAIL_HERE
    password = YOUR_PASSWORD_HERE
    ```

4. The script uses a more comprehensive `input_config.ini` file for configuration. Edit this file with your search criteria, LinkedIn credentials, and message templates.

## Usage

1. Run the script:
    ```bash
    python main.py
    ```

2. Edit the `input_config.ini` file to configure your search criteria and connection request details.

## How to Get `li_at` LinkedIn Cookies

1. Open Chrome and log in to your LinkedIn account.
2. Press `F12` or `Ctrl+Shift+I` to open Developer Tools.
3. Go to the `Application` tab.
4. In the left sidebar, under `Storage`, click on `Cookies` and then select `https://www.linkedin.com`.
5. Look for the `li_at` cookie in the list.
6. Copy the value of the `li_at` cookie and paste it into the `input_config.ini` file under `[LinkedIn]`.

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a pull request.

