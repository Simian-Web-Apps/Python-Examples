# EV Truck route "planner"
1. For local usage create an free https://openrouteservice.org/ account [here](https://openrouteservice.org/dev/#/signup) and get your API key (token).
1. Copy the `local_application_data.json.sample` to `local_application_data.json`.
1. Store your API key (token) in `local_application_data.json`.
1. Make sure that simian-gui is installed (see `requirements.txt`).
1. Run the application:
   ```
   python -m run routeplanner.route_planner.py
   ```
Note that the app uses truck images from `https://downloads.simiansuite.com` so Python should have access to that server.
