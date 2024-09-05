# HOO YOU GOT
#### Video Demo:  <URL HERE>
#### Description:

My project, *Hoo You Got*, is a fully functional sports betting web application built using Flask. The application allows users to place bets on live sporting events, view real-time data and odds, and manage their accounts. Disclaimer: there is no real money involved. The purpose of the app is to experience or practice betting without financial stress. The app integrates with external data sources through The-Odds-API, providing users with accurate, up-to-date information for various sports. The web application allows users to register, log in, and place bets on sporting events across various sports, such as baseball, football, basketball, and soccer. The app tracks user balances, bet outcomes, and past bets. It also displays live game scores and odds, ensuring that users have the latest information when making decisions.

- **static/styles.css**: This file contains all the CSS styles that define the look and feel of the HTML templates. CSS was important when I worked on the aesthetic of the navbar and sidebar. It was also necessary to design the look of the table displaying a user's bets and the live games. I was inspired by the CS50 finance problem set in my design, using Bootstrap classes for responsiveness and user interface elements.

The HTML templates were the backbone of the frontend, using Jinja for dynamic rendering of data. The following files were key to the structue of the project:

- **layout.html**: This is the base template that all other templates extend. It contains the navigation bar, sidebar, and footer. The main block in this template is filled by content from child templates. It also includes links to Bootstrap CSS/JS and the main stylesheet.
- **index.html**: Displays active bets for the user. It retrieves game results such as the scores, teams, and results, and shows them in a table format. The user can view pending or completed bets and their outcomes The table rows display color based on bet outcome. Green for win, Red for loss.
- **bet.html**: Where users place a bet on a particular game. The user can choose an outcome and bet amount, and the form submits this information to the backend for processing.
- **balance.html**: Shows the user’s current account balance. This page can be used for account management, such as adding funds or viewing recent transactions.
- **past_bets.html**: Displays bets that have been completed, showing whether the user won or lost and the amount won. Meant to be a history of all bets, versus only the currently pending ones.
- **baseball.html, basketball.html, football.html, soccer.html**: These pages display live sports data and odds for the respective sports. Each page retrieves data from The-Odds-API and allows users to choose which game they would like to bet on.
- **login.html and register.html**: These are the user authentication pages. They allow new users to create an account and existing users to log in. Form validation ensures that users input valid credentials.
- **settings.html**: Allows users to change their account settings, such as updating their username or password.

The backend of the project is managed by app.py, the main Flask driver, and helpers.py, which contains helper functions.

- **app.py**: This is the main driver of the application. It handles all the routes (URLs) for the web app, connecting each route to an HTML template and corresponding functionality. Each route handles a specific feature of the application. For example:
  - **Index route**: Displays active bets and handles real-time updates for ongoing games.
  - **Betting route**: Allows users to place bets, validates inputs, and updates the database accordingly.
  - **Balance route**: Displays the user’s balance and handles account updates.
  - **Authentication routes**: Handle registration, login, and logout functionality.

- **`helpers.py`**: This file contains various functions that simplify database and API operations:
  - **Database Access**: Functions that abstract database queries (using `SQLite`) for users, bets, and past bets. This file simplifies interactions with `bets.db`, ensuring that data is retrieved and stored efficiently.
  - **API Access**: Functions for interacting with The-Odds-API, fetching live game data, scores, and betting odds. These functions handle the necessary API calls and process the returned data before passing it to app.py.
  - **Bet Calculation**: Functions to calculate bet outcomes and update user balances based on game results. This includes calculating winnings based on odds and ensuring that bets are only processed once. There is also some functions that manage time so that current and upcoming infromation is received from the API.

**Database Schema:**
- **bets.db**: This SQLite database stores all the persistent data for the web app. It contains three key tables:
  - **users**: Stores user information, including username, hashed password, and cash balance.
  - **bets**: Stores active bets placed by users. Each record includes the game ID, sport, bet amount, outcome, and whether the bet has been completed or is still pending.
  - **past_bets**: Stores completed bets to allow users to track their betting history. This table adds to the bets table with information about team scores and whether the bet was won or lost.
  
  By using a relational database, the app can efficiently manage user data, bets, and results, ensuring that data is persistent between sessions.

### Design Choices:
One of the major design choices was using The-Odds-API to fetch real-time data, which allowed the app to remain dynamic and engaging for users. I chose to use Flask due to its simplicity and the fact that it had already been a major topic in the course. It also enabled  the integration of Python which is a language I am comfortable with. I chose to work with Bootstrap in the frontend for similar reasons, and I had already used it for past projects. It made design of web features less of a worry. In terms of database design, using SQLite made sense given the scale of the project. It provided easy setup and management while still having all the functionality needed to track users, bets, and game data. The structure of separating app.py and helpers.py helped maintain cleaner code, with helpers.py handling helper functions, and app.py managing the core routes and logic.

### Conclusion:
The *Hoo You Got* sports betting web app is a full-featured, user-friendly platform built using Flask, SQLite, and The-Odds-API. Designing this web application taught me alot about accessing APIs, full-stack development of software, and how python can interact with backend and frontend. I learned alot about how databases are interlinked with user interaction. The project was meant to provide a fun and interesting way to learn about software design, while working with something I find entertaining and interesting. This helped keep me motivated to work on it and excited to see the final result.
