# Email Management Frontend (Vue.js)

This is the Vue.js frontend for the Email Management Application. It provides a user interface for interacting with the backend services, managing email accounts, viewing emails in an IM-like layout, and utilizing AI-powered features.

## Features

*   User authentication forms (Login, Registration).
*   Token-based session management (JWT stored in localStorage).
*   State management with Pinia (`authStore`, `emailAccountsStore`, `threadStore`, `composeStore`, `aiFeaturesStore`, `complaintsStore`).
*   Routing with Vue Router, including navigation guards for protected routes.
*   Dashboard/View for managing linked email accounts.
*   IM-like interface (`IMView.vue`) for:
    *   Displaying a list of email threads for the active account.
    *   Displaying messages within a selected thread.
    *   Showing email metadata (sender, subject, date, category, attachments).
*   Multi-account switching capability.
*   Email composition through a modal (`ComposeModal.vue`).
*   Sending new emails and replies.
*   AI-powered features:
    *   Display of AI-assigned email categories.
    *   Fetching and using AI-generated reply suggestions.
*   View for displaying extracted data from "Complaints/Suggestions" emails, including basic charts (`ComplaintsView.vue` using `vue-chartjs`).
*   Display of email attachments with placeholder download links.
*   Basic unit tests for key components (e.g., `ComposeModal.spec.js`) using Vue Test Utils and Jest.

## Tech Stack

*   Vue.js 3
*   Vue Router 4
*   Pinia 2 (for state management)
*   Vue CLI (`@vue/cli-service`) for project scaffolding, development server, and builds.
*   JavaScript (ES6+)
*   Chart.js and Vue-Chartjs for data visualization.
*   Jest and Vue Test Utils for unit testing.
*   ESLint for linting.
*   Nginx (for serving the built application in Docker).

## Project Structure

*   `public/`: Static assets and `index.html`.
*   `src/`: Main application source code.
    *   `assets/`: Static assets like images, fonts.
    *   `components/`: Reusable Vue components.
        *   `im_ui/`: Components specific to the IM-like interface.
        *   `ComposeModal.vue`: Modal for composing emails.
    *   `router/`: Vue Router configuration (`index.js`).
    *   `stores/`: Pinia store modules.
    *   `views/`: Top-level route components.
    *   `App.vue`: Root Vue component.
    *   `main.js`: Application entry point (initializes Vue, Pinia, Router).
*   `tests/unit/`: Unit tests.
*   `babel.config.js`: Babel configuration.
*   `.eslintrc.js`: ESLint configuration.
*   `jest.config.js`: Jest test runner configuration.
*   `nginx.conf`: Nginx configuration for serving the built app (used in Docker).
*   `package.json`: Project dependencies and scripts.
*   `vue.config.js`: Vue CLI configuration (e.g., for dev server proxy).

## Local Development (using Vue CLI Dev Server)

Refer to the main project `README.md` in the root directory for instructions on setting up and running the entire application stack (including this frontend served via Nginx) using Docker Compose.

For standalone frontend development (connecting to a running backend):

1.  **Navigate to Frontend Directory**:
    ```bash
    cd email_management_frontend
    ```
2.  **Install Dependencies**:
    ```bash
    npm install
    # Or: yarn install
    ```
3.  **Configure API Proxy (if backend is running separately)**:
    *   Ensure `vue.config.js` has the correct `devServer.proxy` configuration to point to your running backend API (e.g., `target: 'http://localhost:8000'`).
4.  **Run Development Server**:
    ```bash
    npm run serve
    # Or: yarn serve
    ```
    The application will typically be available at `http://localhost:8080` (or another port if 8080 is busy).

## Available npm/yarn Scripts

*   `npm run serve` / `yarn serve`: Starts the development server with hot-reloading.
*   `npm run build` / `yarn build`: Compiles and minifies the application for production into the `dist/` directory.
*   `npm run lint` / `yarn lint`: Lints and formats code using ESLint.
*   `npm run test:unit` / `yarn test:unit`: Runs unit tests using Jest (or configured test runner).

## Key Frontend Stores and Their Purpose

*   `authStore.js`: Manages user authentication state (token, user info, login/logout actions).
*   `emailAccountsStore.js`: Manages linked email accounts (fetching, adding, active account).
*   `threadStore.js`: Manages email threads and messages for the active account/thread.
*   `composeStore.js`: Handles logic for sending composed emails.
*   `aiFeaturesStore.js`: Manages state for AI-generated reply suggestions.
*   `complaintsStore.js`: Manages state for displaying extracted complaint/suggestion data.
