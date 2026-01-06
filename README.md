# 🚗 SafeSpot - AI-Powered Road Safety Platform

<div align="center">

![SafeSpot Logo](https://img.shields.io/badge/SafeSpot-Road%20Safety-4A90E2?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptLTIgMTVsLTUtNSAxLjQxLTEuNDFMMTAgMTQuMTdsNy41OS03LjU5TDE5IDhsLTkgOXoiIGZpbGw9IiNGRkZGRkYiLz48L3N2Zz4=)
[![Django](https://img.shields.io/badge/Django-5.2.9-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Your intelligent companion for safer roads**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Tech Stack](#-tech-stack) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents
- [About](#-about)
- [Features](#-features)
- [Demo](#-demo)
- [Installation](#-installation)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 About

**SafeSpot** is an advanced, AI-powered road safety platform designed to revolutionize how we predict, prevent, and respond to traffic accidents. By combining real-time weather data, machine learning predictions, and comprehensive accident analysis, SafeSpot empowers users and administrators to make data-driven decisions for safer journeys.

### 🌟 Why SafeSpot?

- **🔮 Predictive Intelligence**: AI-powered cost prediction for potential accidents
- **🌦️ Real-Time Weather Integration**: Live weather-based risk assessment
- **📊 Data-Driven Insights**: Comprehensive accident analytics and visualizations
- **👥 User-Centric Design**: Intuitive dashboard for both users and administrators
- **💬 Instant Support**: Real-time messaging system for user assistance
- **📱 Responsive Design**: Beautiful UI that works on all devices

---

## ✨ Features

### For Users

#### 🛣️ Route Safety Analysis
- Real-time route risk assessment based on weather conditions
- Historical accident data integration
- Safe route recommendations

#### 💰 Accident Cost Prediction
- **AI-Powered Predictions**: Estimate potential accident costs based on:
  - Vehicle make, model, and year
  - Damage type (Minor, Moderate, Severe, Total Loss)
  - Road conditions (Urban, Highway, Residential, Rural)
  - Severity levels (1-4)
- **Detailed Cost Breakdown**:
  - Repair costs
  - Medical expenses
  - Other costs (towing, legal, administrative)
  - Vehicle value estimation
- **Visual Reports**: Export beautiful PDF reports with charts and statistics

#### 🌤️ Weather-Based Risk Scoring
- Integration with OpenWeather API
- Real-time weather condition monitoring
- Dynamic risk score calculation (0-100%)
- 5-day weather forecast with risk predictions

#### 📝 Incident Reporting
- Quick accident report submission
- Location-based incident tracking
- Upload photos and descriptions
- Track report status

#### 💬 Support System
- WhatsApp-style messaging interface
- Real-time communication with support team
- Conversation history management
- Message read receipts

#### 📊 Personal Dashboard
- Prediction history tracking
- Accident reports overview
- Risk statistics
- Export data functionality

### For Administrators

#### 🎛️ Advanced Analytics Dashboard
- **City-Level Analytics**:
  - Top 20 cities by accident count
  - Peak hour analysis
  - Cost estimation by city
  - Hourly accident distribution

- **Interactive Visualizations**:
  - Risk distribution charts
  - Accident heatmaps with clustering
  - Time-based trend analysis
  - Severity distribution graphs

- **Real-Time Metrics**:
  - Total users count
  - Daily predictions statistics
  - Live accident risk scores
  - System health monitoring

#### 📧 User Management
- View all registered users
- User activity tracking
- Role-based access control

#### 💬 Support Management
- Unified inbox for all user conversations
- Unread message notifications
- Quick response tools
- Conversation history

#### 📈 Prediction Management
- View all user predictions
- Delete individual or all predictions
- Generate comprehensive reports
- Export prediction data

---

## 🎥 Demo

### User Dashboard
Beautiful, intuitive interface with real-time data and predictions.

### Cost Prediction Report
Professional PDF reports with detailed cost breakdowns and visualizations.

### Admin Analytics
Comprehensive city-level analytics with interactive charts.

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/Wahbijn/safeSpot.git
cd safeSpot
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

### Step 3: Install Dependencies

```bash
cd safespot/core
pip install -r requirements.txt
```

### Step 4: Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```env
OPENWEATHER_API_KEY=your_openweather_api_key_here
SECRET_KEY=your_django_secret_key_here
```

**Get API Keys:**
- OpenWeather API: [https://openweathermap.org/api](https://openweathermap.org/api)
- Django Secret Key: [https://djecrety.ir/](https://djecrety.ir/)

### Step 5: Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### Step 7: Run the Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser!

---

## 🛠️ Tech Stack

### Backend
- **Django 5.2.9** - High-level Python web framework
- **Python 3.10+** - Programming language
- **SQLite** - Database (can be replaced with PostgreSQL/MySQL)
- **Django Humanize** - Human-friendly data formatting

### Frontend
- **Bootstrap 5** - Responsive CSS framework
- **Font Awesome** - Icon library
- **Chart.js** - Data visualization
- **Leaflet.js** - Interactive maps
- **Custom CSS** - Modern gradient designs

### APIs & Services
- **OpenWeather API** - Real-time weather data
- **GeoPy** - Geocoding and location services

### Machine Learning
- Custom accident cost prediction model
- Weather-based risk scoring algorithm
- Historical data analysis

---

## 📁 Project Structure

```
safespot/
├── core/                      # Main Django project
│   ├── core/                  # Project settings
│   │   ├── settings.py       # Configuration
│   │   ├── urls.py           # URL routing
│   │   └── wsgi.py           # WSGI config
│   ├── accounts/             # User authentication
│   ├── dashboard/            # Main dashboard app
│   │   ├── views.py         # Dashboard logic
│   │   ├── urls.py          # Dashboard routes
│   │   └── templates/       # Dashboard templates
│   ├── predictions/          # Prediction system
│   │   ├── models.py        # Prediction models
│   │   └── views.py         # Prediction logic
│   ├── incidents/            # Incident reporting
│   ├── routes/               # Route analysis
│   ├── messaging/            # Support system
│   ├── gamification/         # User engagement
│   ├── static/              # Static files (CSS, JS, images)
│   ├── media/               # User uploads
│   └── manage.py            # Django management
├── data/                     # CSV datasets
│   ├── accidents_city_detail.csv
│   ├── vehicle_database.csv
│   └── Total Accidents by Severity.csv
├── .gitignore               # Git ignore rules
├── .env.example             # Environment template
└── README.md                # This file
```

---

## 📖 Usage

### For Users

1. **Register/Login**: Create an account or log in
2. **Check Route Safety**: Enter departure and destination to get risk assessment
3. **Predict Accident Costs**:
   - Select your vehicle details
   - Choose damage type and severity
   - Get instant cost predictions
   - Export professional PDF reports
4. **Report Incidents**: Submit accident reports with location and details
5. **Contact Support**: Use the messaging system for help

### For Administrators

1. **Access Admin Dashboard**: Login with admin credentials
2. **Monitor Analytics**:
   - View city-level statistics
   - Analyze accident trends
   - Track prediction usage
3. **Manage Users**: View and manage registered users
4. **Handle Support**: Respond to user messages
5. **Generate Reports**: Export comprehensive data reports

---

## 🔌 API Documentation

### Prediction API

**Endpoint:** `POST /dashboard/api/predict-cost/`

**Request Body:**
```json
{
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_year": 2020,
  "severity": 2,
  "damage_type": "Moderate",
  "road_type": "Urban"
}
```

**Response:**
```json
{
  "success": true,
  "total_cost": 15000.50,
  "repair_cost": 8500.00,
  "medical_cost": 4000.00,
  "other_costs": 2500.50,
  "vehicle_value": 25000.00,
  "confidence": 85
}
```

### Weather API

**Endpoint:** `GET /dashboard/api/weather/{city}/`

**Response:**
```json
{
  "success": true,
  "current_weather": {
    "temp": 22.5,
    "description": "Clear sky",
    "risk_score": 15
  },
  "forecast": [...]
}
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guide for Python code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Contact

**Project Maintainer**: Wahbi

- GitHub: [@Wahbijn](https://github.com/Wahbijn)
- Project Link: [https://github.com/Wahbijn/safeSpot](https://github.com/Wahbijn/safeSpot)

---

## 🙏 Acknowledgments

- OpenWeather API for weather data
- Django community for the amazing framework
- Bootstrap team for the UI framework
- All contributors who help improve SafeSpot

---

<div align="center">

**Made with ❤️ for safer roads**

⭐ Star this repo if you find it helpful!

</div>
